"""Hardware-exact SNK Neo Geo MVS graphics, palette, and YM2610 ADPCM encoders/decoders.

References verified against NeoGeo Development Wiki & MAME `neogeo.cpp`:
- 16-bit Palette RAM word:
    Bit 15   : Dark bit (1 = attenuate common half-LSB; $8000 = pure reference black)
    Bit 14   : R0 (LSB of 5-bit Red)
    Bit 13   : G0 (LSB of 5-bit Green)
    Bit 12   : B0 (LSB of 5-bit Blue)
    Bits 11-8: R4..R1
    Bits  7-4: G4..G1
    Bits  3-0: B4..B1
- C-ROM 16x16 4bpp sprite tile (128 bytes total: 64 bytes in C1, 64 bytes in C2):
    Stored as Right 8x16 half (x=8..15, y=0..15) followed by Left 8x16 half (x=0..7, y=0..15).
    Within each row, C1 stores [bp0, bp1] and C2 stores [bp2, bp3].
    Within each byte, bit 0 (LSB) is the leftmost pixel of the 8-pixel row segment.
- S-ROM 8x8 4bpp FIX tile (32 bytes in S1):
    Stored in four 2-pixel-wide vertical column pairs of 8 bytes each (y=0..7):
      Bytes  0..7 : x = 4, 5
      Bytes  8..15: x = 6, 7
      Bytes 16..23: x = 0, 1
      Bytes 24..31: x = 2, 3
    Within each byte, bits 0..3 = left pixel, bits 4..7 = right pixel.
- V-ROM YM2610 ADPCM-A (18.5 kHz, 4-bit OKI/JEDI ADPCM, 256-byte aligned).
"""

from __future__ import annotations

import struct
import wave
from io import BytesIO

NEOGEO_REF_BLACK = 0x8000


def rgb_to_neogeo_word(r: int, g: int, b: int) -> int:
    """Convert 8-bit RGB (0..255) to 16-bit Neo Geo palette word."""
    r6 = (max(0, min(255, r)) * 63 + 127) // 255
    g6 = (max(0, min(255, g)) * 63 + 127) // 255
    b6 = (max(0, min(255, b)) * 63 + 127) // 255

    r5 = r6 >> 1
    g5 = g6 >> 1
    b5 = b6 >> 1
    # Common 6th bit: luma-weighted vote; dark=1 means no half-step boost ($8000 for 0,0,0)
    common_lsb = 1 if ((r6 & 1) + (g6 & 1) * 2 + (b6 & 1)) >= 2 else 0
    dark = 0 if common_lsb else 1

    word = (
        (dark << 15)
        | ((r5 & 1) << 14)
        | ((g5 & 1) << 13)
        | ((b5 & 1) << 12)
        | (((r5 >> 1) & 0x0F) << 8)
        | (((g5 >> 1) & 0x0F) << 4)
        | ((b5 >> 1) & 0x0F)
    )
    return word & 0xFFFF


def neogeo_word_to_rgb(word: int) -> tuple[int, int, int]:
    """Decode a 16-bit Neo Geo palette word back to 8-bit RGB."""
    dark = (word >> 15) & 1
    common = 0 if dark else 1
    r5 = (((word >> 8) & 0x0F) << 1) | ((word >> 14) & 1)
    g5 = (((word >> 4) & 0x0F) << 1) | ((word >> 13) & 1)
    b5 = ((word & 0x0F) << 1) | ((word >> 12) & 1)
    r6 = (r5 << 1) | common
    g6 = (g5 << 1) | common
    b6 = (b5 << 1) | common
    return ((r6 * 255 + 31) // 63, (g6 * 255 + 31) // 63, (b6 * 255 + 31) // 63)


def build_palette_16(rgb_entries: list[list[int] | tuple[int, int, int]]) -> list[int]:
    """Build a 16-word Neo Geo palette with index 0 = NEOGEO_REF_BLACK (transparent)."""
    if len(rgb_entries) > 15:
        raise ValueError(f"Neo Geo 4bpp palette allows at most 15 opaque colors, got {len(rgb_entries)}")
    words = [NEOGEO_REF_BLACK]
    for r, g, b in rgb_entries:
        words.append(rgb_to_neogeo_word(int(r), int(g), int(b)))
    while len(words) < 16:
        words.append(NEOGEO_REF_BLACK)
    return words


def encode_c_tile_16x16(indices_256: bytes | bytearray | list[int]) -> tuple[bytes, bytes]:
    """Encode a 16x16 row-major 4bpp index array (0..15) into (c1_64b, c2_64b)."""
    if len(indices_256) != 256:
        raise ValueError(f"Expected 256 pixels for 16x16 tile, got {len(indices_256)}")
    c1 = bytearray(64)
    c2 = bytearray(64)
    # Half 0: Right 8x16 (x_ofs = 8), Half 1: Left 8x16 (x_ofs = 0)
    for half_idx, x_ofs in enumerate((8, 0)):
        base = half_idx * 32
        for y in range(16):
            bp0 = bp1 = bp2 = bp3 = 0
            row_off = y * 16 + x_ofs
            for px in range(8):
                pen = indices_256[row_off + px] & 0x0F
                # Bit 0 (LSB) is leftmost pixel of the 8-pixel half
                bp0 |= ((pen >> 0) & 1) << px
                bp1 |= ((pen >> 1) & 1) << px
                bp2 |= ((pen >> 2) & 1) << px
                bp3 |= ((pen >> 3) & 1) << px
            c1[base + y * 2 + 0] = bp0
            c1[base + y * 2 + 1] = bp1
            c2[base + y * 2 + 0] = bp2
            c2[base + y * 2 + 1] = bp3
    return bytes(c1), bytes(c2)


def decode_c_tile_16x16(c1_64b: bytes, c2_64b: bytes) -> bytearray:
    """Independently decode (c1_64b, c2_64b) back into 256 row-major 4bpp indices."""
    if len(c1_64b) != 64 or len(c2_64b) != 64:
        raise ValueError("C1 and C2 tile chunks must each be 64 bytes")
    out = bytearray(256)
    # Four 8x8 hardware blocks: top-right, bottom-right, top-left, bottom-left
    blocks = ((8, 0, 0), (8, 8, 16), (0, 0, 32), (0, 8, 48))
    for x_ofs, y_ofs, byte_ofs in blocks:
        for ry in range(8):
            bp0 = c1_64b[byte_ofs + ry * 2]
            bp1 = c1_64b[byte_ofs + ry * 2 + 1]
            bp2 = c2_64b[byte_ofs + ry * 2]
            bp3 = c2_64b[byte_ofs + ry * 2 + 1]
            y = y_ofs + ry
            for px in range(8):
                pen = (
                    (((bp0 >> px) & 1) << 0)
                    | (((bp1 >> px) & 1) << 1)
                    | (((bp2 >> px) & 1) << 2)
                    | (((bp3 >> px) & 1) << 3)
                )
                out[y * 16 + x_ofs + px] = pen
    return out


def encode_s_tile_8x8(indices_64: bytes | bytearray | list[int]) -> bytes:
    """Encode an 8x8 row-major 4bpp index array (0..15) into 32 S-ROM bytes."""
    if len(indices_64) != 64:
        raise ValueError(f"Expected 64 pixels for 8x8 FIX tile, got {len(indices_64)}")
    out = bytearray(32)
    # Column pairs: (4,5), (6,7), (0,1), (2,3)
    col_pairs = ((4, 5), (6, 7), (0, 1), (2, 3))
    pos = 0
    for xl, xr in col_pairs:
        for y in range(8):
            pl = indices_64[y * 8 + xl] & 0x0F
            pr = indices_64[y * 8 + xr] & 0x0F
            out[pos] = pl | (pr << 4)
            pos += 1
    return bytes(out)


def decode_s_tile_8x8(s1_32b: bytes) -> bytearray:
    """Independently decode 32 S-ROM bytes back into 64 row-major 4bpp indices."""
    if len(s1_32b) != 32:
        raise ValueError("S1 FIX tile chunk must be 32 bytes")
    out = bytearray(64)
    for addr in range(32):
        half = (addr >> 4) & 1  # 0 = right half (x=4..7), 1 = left half (x=0..3)
        col_in_half = (addr >> 3) & 1
        y = addr & 7
        x_base = (0 if half == 1 else 4) + col_in_half * 2
        b = s1_32b[addr]
        out[y * 8 + x_base] = b & 0x0F
        out[y * 8 + x_base + 1] = (b >> 4) & 0x0F
    return out


# --- Multi-palette tile quantizer for >15-color scene sheets (ui_ending, ui_world_cards) ---


def map_rgba_tile_to_palette(
    tile_rgba: bytes | bytearray,
    palette_rgb: list[tuple[int, int, int]],
    alpha_threshold: int = 128,
) -> bytearray:
    """Map a 16x16 (or 8x8) RGBA buffer to 0..15 indices of a 15-color palette."""
    npix = len(tile_rgba) // 4
    out = bytearray(npix)
    exact_lookup = {rgb: idx + 1 for idx, rgb in enumerate(palette_rgb)}
    for i in range(npix):
        a = tile_rgba[i * 4 + 3]
        if a < alpha_threshold:
            out[i] = 0
            continue
        rgb = (tile_rgba[i * 4], tile_rgba[i * 4 + 1], tile_rgba[i * 4 + 2])
        found = exact_lookup.get(rgb)
        if found is not None:
            out[i] = found
            continue
        # Nearest RGB fallback
        best_idx = 1
        best_dist = 1 << 30
        for idx, (pr, pg, pb) in enumerate(palette_rgb):
            d = (rgb[0] - pr) ** 2 + (rgb[1] - pg) ** 2 + (rgb[2] - pb) ** 2
            if d < best_dist:
                best_dist = d
                best_idx = idx + 1
        out[i] = best_idx
    return out


def partition_scene_palettes(
    tiles_rgba: list[bytes | bytearray],
    max_palettes: int = 12,
    alpha_threshold: int = 128,
) -> tuple[list[list[tuple[int, int, int]]], list[int]]:
    """Assign 16x16 scene tiles into up to `max_palettes` 15-color sub-palettes."""
    tile_color_sets: list[list[tuple[int, int, int]]] = []
    for tbuf in tiles_rgba:
        seen: dict[tuple[int, int, int], int] = {}
        for i in range(0, len(tbuf), 4):
            if tbuf[i + 3] >= alpha_threshold:
                c = (tbuf[i], tbuf[i + 1], tbuf[i + 2])
                seen[c] = seen.get(c, 0) + 1
        # Reduce single tile if it somehow has >15 unique RGBs by keeping top-15 frequent colors
        ordered = [c for c, _ in sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))[:15]]
        tile_color_sets.append(ordered)

    palettes: list[set[tuple[int, int, int]]] = []
    assignments: list[int] = []

    for cset in tile_color_sets:
        placed = -1
        best_union_len = 999
        s = set(cset)
        for pidx, pset in enumerate(palettes):
            u = pset | s
            if len(u) <= 15 and len(u) < best_union_len:
                best_union_len = len(u)
                placed = pidx
        if placed >= 0:
            palettes[placed] |= s
            assignments.append(placed)
        elif len(palettes) < max_palettes:
            palettes.append(set(s))
            assignments.append(len(palettes) - 1)
        else:
            # Pick existing palette minimizing total RGB quantization error
            best_p = 0
            best_err = 1 << 60
            for pidx, pset in enumerate(palettes):
                plist = list(pset)
                err = 0
                for r, g, b in s:
                    err += min((r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2 for pr, pg, pb in plist)
                if err < best_err:
                    best_err = err
                    best_p = pidx
            assignments.append(best_p)

    if not palettes:
        palettes.append({(0, 0, 0)})
    final_pals = [sorted(pset)[:15] for pset in palettes]
    return final_pals, assignments


# --- YM2610 ADPCM-A (12-bit, 49-step table, 18.5 kHz) ---
# Matches the decoder MAME uses for the YM2610 (ymfm adpcm_a_channel::clock):
#   delta = (2 * (nibble & 7) + 1) * step / 8, negated when bit 3 is set;
#   the 12-bit accumulator wraps (it does not saturate), so the encoder must
#   keep its predictor inside [-2048, 2047];
#   step index += {-1, -1, -1, -1, 2, 5, 7, 9}[nibble & 7], clamped to 0..48.

_JEDI_STEP_SIZE = [
    16, 17, 19, 21, 23, 25, 28, 31, 34, 37,
    41, 45, 50, 55, 60, 66, 73, 80, 88, 97,
    107, 118, 130, 143, 157, 173, 190, 209, 230, 253,
    279, 307, 337, 371, 408, 449, 494, 544, 598, 658,
    724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552,
]

_JEDI_INDEX_ADJ = [-1, -1, -1, -1, 2, 5, 7, 9]


def read_wav_mono16(wav_bytes: bytes) -> tuple[int, list[int]]:
    """Read mono/stereo 16-bit PCM WAV bytes and return (sample_rate, mono_int16_samples)."""
    with wave.open(BytesIO(wav_bytes), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)
    if sampwidth != 2:
        raise ValueError(f"Expected 16-bit PCM WAV, got sampwidth={sampwidth}")
    total_i16 = len(raw) // 2
    vals = struct.unpack(f"<{total_i16}h", raw[: total_i16 * 2])
    if channels == 1:
        return rate, list(vals)
    mono = [
        sum(vals[i : i + channels]) // channels for i in range(0, len(vals), channels)
    ]
    return rate, mono


def resample_linear(samples: list[int], src_hz: int, dst_hz: int) -> list[int]:
    """Resample 16-bit PCM samples from src_hz to dst_hz via linear interpolation."""
    if not samples or src_hz == dst_hz:
        return list(samples)
    out_len = max(2, int(round(len(samples) * dst_hz / src_hz)))
    if out_len % 2 == 1:
        out_len += 1
    out = [0] * out_len
    ratio = src_hz / dst_hz
    limit = len(samples) - 1
    for i in range(out_len):
        pos = i * ratio
        idx = int(pos)
        if idx >= limit:
            out[i] = samples[limit]
        else:
            frac = pos - idx
            out[i] = int(round(samples[idx] * (1.0 - frac) + samples[idx + 1] * frac))
    return out


def _adpcm_a_delta(nibble: int, step: int) -> int:
    delta = ((2 * (nibble & 7) + 1) * step) // 8
    return -delta if (nibble & 8) else delta


def _encode_adpcm_a_nibble(sample12: int, state: list[int]) -> int:
    pred, step_idx = state
    step = _JEDI_STEP_SIZE[step_idx]
    diff = sample12 - pred
    sign = 8 if diff < 0 else 0
    mag = min(7, (abs(diff) * 4) // step)
    nibble = sign | mag
    # The hardware accumulator wraps at 12 bits: back off until the result fits.
    while mag > 0 and not (-2048 <= pred + _adpcm_a_delta(nibble, step) <= 2047):
        mag -= 1
        nibble = sign | mag
    new_pred = pred + _adpcm_a_delta(nibble, step)
    if not (-2048 <= new_pred <= 2047):
        nibble ^= 8  # smallest step in the other direction always fits
        new_pred = pred + _adpcm_a_delta(nibble, step)
    state[0] = new_pred
    state[1] = max(0, min(48, step_idx + _JEDI_INDEX_ADJ[nibble & 7]))
    return nibble & 0x0F


def encode_ym2610_adpcm_a(pcm16_18500: list[int], pad_align: int = 256) -> bytes:
    """Encode 16-bit 18.5 kHz mono PCM to 256-byte-aligned YM2610 ADPCM-A bytes."""
    if len(pcm16_18500) % 2 == 1:
        pcm16_18500 = list(pcm16_18500) + [0]
    state = [0, 0]
    out = bytearray(len(pcm16_18500) // 2)
    for i in range(0, len(pcm16_18500), 2):
        s0 = max(-2048, min(2047, pcm16_18500[i] >> 4))
        s1 = max(-2048, min(2047, pcm16_18500[i + 1] >> 4))
        hi = _encode_adpcm_a_nibble(s0, state)
        lo = _encode_adpcm_a_nibble(s1, state)
        out[i // 2] = (hi << 4) | lo

    # Pad to 256-byte YM2610 ADPCM-A start/end page boundary using silence nibbles (0x80/0x08)
    while len(out) == 0 or (len(out) % pad_align) != 0:
        hi = _encode_adpcm_a_nibble(0, state)
        lo = _encode_adpcm_a_nibble(0, state)
        out.append((hi << 4) | lo)
    return bytes(out)


def decode_ym2610_adpcm_a(adpcm_bytes: bytes) -> list[int]:
    """Decode YM2610 ADPCM-A bytes to 16-bit signed PCM exactly as the chip does."""
    acc = 0
    step_idx = 0
    out: list[int] = []
    for b in adpcm_bytes:
        for nibble in ((b >> 4) & 0x0F, b & 0x0F):
            acc = (acc + _adpcm_a_delta(nibble, _JEDI_STEP_SIZE[step_idx])) & 0xFFF
            step_idx = max(0, min(48, step_idx + _JEDI_INDEX_ADJ[nibble & 7]))
            signed = acc - 0x1000 if acc & 0x800 else acc
            out.append(signed << 4)
    return out
