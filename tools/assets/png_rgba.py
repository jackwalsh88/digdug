"""Pure-Python PNG reader and writer (RGBA8 and Indexed8 with tRNS).

Zero external dependencies (uses Python stdlib `struct` and `zlib`), supporting
all five PNG scanline filter types (None, Sub, Up, Average, Paeth) so the asset
pipeline runs identically in minimal containers and on developer workstations.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"


class RGBAImage:
    """Simple 8-bit RGBA image buffer stored row-major (`width * height * 4` bytes)."""

    __slots__ = ("width", "height", "data")

    def __init__(self, width: int, height: int, data: bytes | bytearray | None = None) -> None:
        self.width = width
        self.height = height
        expected = width * height * 4
        if data is None:
            self.data = bytearray(expected)
        else:
            if len(data) != expected:
                raise ValueError(f"Expected {expected} RGBA bytes, got {len(data)}")
            self.data = bytearray(data)

    def crop(self, x: int, y: int, w: int, h: int) -> "RGBAImage":
        out = bytearray(w * h * 4)
        src = self.data
        sw = self.width
        for row in range(h):
            sy = y + row
            if 0 <= sy < self.height:
                sx0 = max(0, x)
                sx1 = min(sw, x + w)
                if sx1 > sx0:
                    dx0 = sx0 - x
                    span = (sx1 - sx0) * 4
                    s_off = (sy * sw + sx0) * 4
                    d_off = (row * w + dx0) * 4
                    out[d_off : d_off + span] = src[s_off : s_off + span]
        return RGBAImage(w, h, out)

    def blit(self, src_img: "RGBAImage", dst_x: int, dst_y: int) -> None:
        sw, sh = src_img.width, src_img.height
        for ry in range(sh):
            dy = dst_y + ry
            if not (0 <= dy < self.height):
                continue
            sx0 = max(0, -dst_x)
            sx1 = min(sw, self.width - dst_x)
            if sx1 <= sx0:
                continue
            span = (sx1 - sx0) * 4
            s_off = (ry * sw + sx0) * 4
            d_off = (dy * self.width + dst_x + sx0) * 4
            self.data[d_off : d_off + span] = src_img.data[s_off : s_off + span]

    def scale_nearest(self, factor: int) -> "RGBAImage":
        if factor <= 1:
            return RGBAImage(self.width, self.height, self.data)
        nw = self.width * factor
        nh = self.height * factor
        out = bytearray(nw * nh * 4)
        src = self.data
        for y in range(self.height):
            row_buf = bytearray(nw * 4)
            s_row = y * self.width * 4
            for x in range(self.width):
                px = src[s_row + x * 4 : s_row + x * 4 + 4]
                d_col = x * factor * 4
                row_buf[d_col : d_col + factor * 4] = px * factor
            for fy in range(factor):
                d_row = (y * factor + fy) * nw * 4
                out[d_row : d_row + nw * 4] = row_buf
        return RGBAImage(nw, nh, out)


def _paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter_scanlines(raw: bytes, width: int, height: int, bpp: int) -> bytearray:
    stride = width * bpp
    expected = height * (1 + stride)
    if len(raw) < expected:
        raise ValueError(f"Truncated PNG IDAT stream ({len(raw)} < {expected})")
    out = bytearray(height * stride)
    pos = 0
    for y in range(height):
        ftype = raw[pos]
        pos += 1
        row_out = y * stride
        prev_row = (y - 1) * stride
        if ftype == 0:  # None
            out[row_out : row_out + stride] = raw[pos : pos + stride]
        elif ftype == 1:  # Sub
            for i in range(stride):
                left = out[row_out + i - bpp] if i >= bpp else 0
                out[row_out + i] = (raw[pos + i] + left) & 0xFF
        elif ftype == 2:  # Up
            if y == 0:
                out[row_out : row_out + stride] = raw[pos : pos + stride]
            else:
                for i in range(stride):
                    out[row_out + i] = (raw[pos + i] + out[prev_row + i]) & 0xFF
        elif ftype == 3:  # Average
            for i in range(stride):
                left = out[row_out + i - bpp] if i >= bpp else 0
                up = out[prev_row + i] if y > 0 else 0
                out[row_out + i] = (raw[pos + i] + ((left + up) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            for i in range(stride):
                left = out[row_out + i - bpp] if i >= bpp else 0
                up = out[prev_row + i] if y > 0 else 0
                up_left = out[prev_row + i - bpp] if (y > 0 and i >= bpp) else 0
                out[row_out + i] = (raw[pos + i] + _paeth_predictor(left, up, up_left)) & 0xFF
        else:
            raise ValueError(f"Unsupported PNG filter type {ftype} on row {y}")
        pos += stride
    return out


def decode_png_bytes(blob: bytes) -> RGBAImage:
    """Decode non-interlaced 8-bit PNG bytes into an RGBAImage."""
    if not blob.startswith(PNG_SIG):
        raise ValueError("Not a valid PNG signature")
    pos = 8
    width = height = bit_depth = color_type = interlace = 0
    plte: list[tuple[int, int, int]] = []
    trns: bytes = b""
    idat_parts: list[bytes] = []

    while pos + 8 <= len(blob):
        length, ctype = struct.unpack(">I4s", blob[pos : pos + 8])
        cdata = blob[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", cdata
            )
            if interlace != 0:
                raise ValueError("Interlaced PNG is not supported")
            if bit_depth != 8:
                raise ValueError(f"Only 8-bit PNG supported, got bit_depth={bit_depth}")
        elif ctype == b"PLTE":
            plte = [
                (cdata[i], cdata[i + 1], cdata[i + 2]) for i in range(0, len(cdata), 3)
            ]
        elif ctype == b"tRNS":
            trns = cdata
        elif ctype == b"IDAT":
            idat_parts.append(cdata)
        elif ctype == b"IEND":
            break

    raw = zlib.decompress(b"".join(idat_parts))
    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    if color_type not in channels_map:
        raise ValueError(f"Unsupported PNG color_type={color_type}")
    bpp = channels_map[color_type]
    unfiltered = _unfilter_scanlines(raw, width, height, bpp)

    if color_type == 6:
        return RGBAImage(width, height, unfiltered)

    rgba = bytearray(width * height * 4)
    if color_type == 2:
        for i in range(width * height):
            rgba[i * 4 : i * 4 + 3] = unfiltered[i * 3 : i * 3 + 3]
            rgba[i * 4 + 3] = 255
    elif color_type == 3:
        alphas = [trns[i] if i < len(trns) else 255 for i in range(len(plte))]
        for i, idx in enumerate(unfiltered):
            r, g, b = plte[idx] if idx < len(plte) else (0, 0, 0)
            a = alphas[idx] if idx < len(alphas) else 255
            rgba[i * 4 : i * 4 + 4] = bytes((r, g, b, a))
    elif color_type == 0:
        for i, g in enumerate(unfiltered):
            rgba[i * 4 : i * 4 + 4] = bytes((g, g, g, 255))
    elif color_type == 4:
        for i in range(width * height):
            g = unfiltered[i * 2]
            a = unfiltered[i * 2 + 1]
            rgba[i * 4 : i * 4 + 4] = bytes((g, g, g, a))
    return RGBAImage(width, height, rgba)


def _png_chunk(ctype: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(ctype + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + ctype + data + struct.pack(">I", crc)


def encode_rgba_png(img: RGBAImage) -> bytes:
    ihdr = struct.pack(">IIBBBBB", img.width, img.height, 8, 6, 0, 0, 0)
    stride = img.width * 4
    scanlines = bytearray()
    for y in range(img.height):
        scanlines.append(0)  # Filter 0 (None)
        scanlines.extend(img.data[y * stride : (y + 1) * stride])
    compressed = zlib.compress(bytes(scanlines), level=6)
    return (
        PNG_SIG
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )


def encode_indexed_png(
    width: int,
    height: int,
    indices: bytes | bytearray,
    palette_rgb: list[tuple[int, int, int]],
    transparent_zero: bool = True,
) -> bytes:
    """Encode an 8-bit indexed PNG with explicit PLTE and index-0 tRNS."""
    if len(indices) != width * height:
        raise ValueError("Index buffer size mismatch")
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)
    padded_pal = list(palette_rgb[:256])
    if not padded_pal:
        padded_pal = [(0, 0, 0)]
    plte = b"".join(bytes((r & 0xFF, g & 0xFF, b & 0xFF)) for r, g, b in padded_pal)
    trns = b"\x00" if transparent_zero else b""
    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0)
        scanlines.extend(indices[y * width : (y + 1) * width])
    compressed = zlib.compress(bytes(scanlines), level=6)
    parts = [PNG_SIG, _png_chunk(b"IHDR", ihdr), _png_chunk(b"PLTE", plte)]
    if trns:
        parts.append(_png_chunk(b"tRNS", trns))
    parts.append(_png_chunk(b"IDAT", compressed))
    parts.append(_png_chunk(b"IEND", b""))
    return b"".join(parts)


def write_png(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
