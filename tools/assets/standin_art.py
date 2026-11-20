"""Deterministic stand-in pixel-art & PCM generator matching `pack_catalog.jsonl`.

Used ONLY when `Super-Dig-Dug-Complete-Asset-Pack.zip` is not present locally
(such as inside the cloud build/test sandbox). Produces crisp 8x8 arcade font
glyphs, true 4-bit quadrant-masked terrain occupancy tiles, silhouette-readable
actor/prop/UI sprites using each family's real 15-color palette, and short
synthesized PCM cues so C builds, ROM packing, and `asset-check` run identically
in both environments.
"""

from __future__ import annotations

import math

# Crisp 8x8 arcade bitmap rows (MSB = x=0..6, bit 0 = x=7 left as 0 spacing)
FONT_8X8: dict[str, list[int]] = {
    "u0041": [0x38, 0x6C, 0xC6, 0xC6, 0xFE, 0xC6, 0xC6, 0x00],  # A
    "u0042": [0xFC, 0xC6, 0xC6, 0xFC, 0xC6, 0xC6, 0xFC, 0x00],  # B
    "u0043": [0x7C, 0xC6, 0xC0, 0xC0, 0xC0, 0xC6, 0x7C, 0x00],  # C
    "u0044": [0xF8, 0xCC, 0xC6, 0xC6, 0xC6, 0xCC, 0xF8, 0x00],  # D
    "u0045": [0xFE, 0xC0, 0xC0, 0xF8, 0xC0, 0xC0, 0xFE, 0x00],  # E
    "u0046": [0xFE, 0xC0, 0xC0, 0xF8, 0xC0, 0xC0, 0xC0, 0x00],  # F
    "u0047": [0x7C, 0xC6, 0xC0, 0xCE, 0xC6, 0xC6, 0x7E, 0x00],  # G
    "u0048": [0xC6, 0xC6, 0xC6, 0xFE, 0xC6, 0xC6, 0xC6, 0x00],  # H
    "u0049": [0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00],  # I
    "u004a": [0x3E, 0x0C, 0x0C, 0x0C, 0xCC, 0xCC, 0x78, 0x00],  # J
    "u004b": [0xC6, 0xCC, 0xD8, 0xF0, 0xD8, 0xCC, 0xC6, 0x00],  # K
    "u004c": [0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xFE, 0x00],  # L
    "u004d": [0xC6, 0xEE, 0xFE, 0xD6, 0xC6, 0xC6, 0xC6, 0x00],  # M
    "u004e": [0xC6, 0xE6, 0xF6, 0xDE, 0xCE, 0xC6, 0xC6, 0x00],  # N
    "u004f": [0x7C, 0xC6, 0xC6, 0xC6, 0xC6, 0xC6, 0x7C, 0x00],  # O
    "u0050": [0xFC, 0xC6, 0xC6, 0xFC, 0xC0, 0xC0, 0xC0, 0x00],  # P
    "u0051": [0x7C, 0xC6, 0xC6, 0xC6, 0xDA, 0xCC, 0x76, 0x00],  # Q
    "u0052": [0xFC, 0xC6, 0xC6, 0xFC, 0xD8, 0xCC, 0xC6, 0x00],  # R
    "u0053": [0x7C, 0xC6, 0xC0, 0x7C, 0x06, 0xC6, 0x7C, 0x00],  # S
    "u0054": [0xFE, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00],  # T
    "u0055": [0xC6, 0xC6, 0xC6, 0xC6, 0xC6, 0xC6, 0x7C, 0x00],  # U
    "u0056": [0xC6, 0xC6, 0xC6, 0xC6, 0x6C, 0x38, 0x10, 0x00],  # V
    "u0057": [0xC6, 0xC6, 0xC6, 0xD6, 0xFE, 0xEE, 0xC6, 0x00],  # W
    "u0058": [0xC6, 0x6C, 0x38, 0x38, 0x38, 0x6C, 0xC6, 0x00],  # X
    "u0059": [0xC6, 0xC6, 0x6C, 0x38, 0x18, 0x18, 0x18, 0x00],  # Y
    "u005a": [0xFE, 0x0C, 0x18, 0x30, 0x60, 0xC0, 0xFE, 0x00],  # Z
    "u0030": [0x7C, 0xC6, 0xCE, 0xD6, 0xE6, 0xC6, 0x7C, 0x00],  # 0
    "u0031": [0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00],  # 1
    "u0032": [0x7C, 0xC6, 0x06, 0x3C, 0x60, 0xC0, 0xFE, 0x00],  # 2
    "u0033": [0x7C, 0xC6, 0x06, 0x3C, 0x06, 0xC6, 0x7C, 0x00],  # 3
    "u0034": [0x1C, 0x3C, 0x6C, 0xCC, 0xFE, 0x0C, 0x0C, 0x00],  # 4
    "u0035": [0xFE, 0xC0, 0xFC, 0x06, 0x06, 0xC6, 0x7C, 0x00],  # 5
    "u0036": [0x3C, 0x60, 0xC0, 0xFC, 0xC6, 0xC6, 0x7C, 0x00],  # 6
    "u0037": [0xFE, 0xC6, 0x0C, 0x18, 0x30, 0x30, 0x30, 0x00],  # 7
    "u0038": [0x7C, 0xC6, 0xC6, 0x7C, 0xC6, 0xC6, 0x7C, 0x00],  # 8
    "u0039": [0x7C, 0xC6, 0xC6, 0x7E, 0x06, 0x0C, 0x78, 0x00],  # 9
    "u002e": [0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x30, 0x00],  # .
    "u002c": [0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x30, 0x60],  # ,
    "u0021": [0x30, 0x30, 0x30, 0x30, 0x30, 0x00, 0x30, 0x00],  # !
    "u003f": [0x7C, 0xC6, 0x0C, 0x18, 0x18, 0x00, 0x18, 0x00],  # ?
    "u002d": [0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00],  # -
    "u002b": [0x00, 0x18, 0x18, 0x7E, 0x18, 0x18, 0x00, 0x00],  # +
    "u002f": [0x06, 0x0C, 0x18, 0x30, 0x60, 0xC0, 0x80, 0x00],  # /
    "u003a": [0x00, 0x30, 0x30, 0x00, 0x30, 0x30, 0x00, 0x00],  # :
    "u0027": [0x30, 0x30, 0x60, 0x00, 0x00, 0x00, 0x00, 0x00],  # '
    "u0028": [0x18, 0x30, 0x60, 0x60, 0x60, 0x30, 0x18, 0x00],  # (
    "u0029": [0x60, 0x30, 0x18, 0x18, 0x18, 0x30, 0x60, 0x00],  # )
    "u003d": [0x00, 0x00, 0x7E, 0x00, 0x7E, 0x00, 0x00, 0x00],  # =
    "u003e": [0x60, 0x30, 0x18, 0x0C, 0x18, 0x30, 0x60, 0x00],  # >
    "u003c": [0x18, 0x30, 0x60, 0xC0, 0x60, 0x30, 0x18, 0x00],  # <
    "u00d7": [0x00, 0xC6, 0x6C, 0x38, 0x6C, 0xC6, 0x00, 0x00],  # ×
    "u2191": [0x10, 0x38, 0x7C, 0x10, 0x10, 0x10, 0x10, 0x00],  # ↑
    "u2193": [0x10, 0x10, 0x10, 0x10, 0x7C, 0x38, 0x10, 0x00],  # ↓
    "u2192": [0x00, 0x10, 0x18, 0xFC, 0x18, 0x10, 0x00, 0x00],  # →
    "u2190": [0x00, 0x20, 0x60, 0xFC, 0x60, 0x20, 0x00, 0x00],  # ←
    "u0025": [0xC6, 0xCC, 0x18, 0x30, 0x66, 0xC6, 0x00, 0x00],  # %
    "u005f": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFE, 0x00],  # _
    "u0020": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # space
}

INTENTIONAL_BLANK_NAMES = {"u0020", "occupancy_v1_00", "occupancy_v2_00", "occupancy_v3_00"}


def render_standin_indices(
    family_id: str,
    frame_name: str,
    width: int,
    height: int,
    num_colors: int,
) -> bytearray:
    """Synthesize 4bpp indices (0..num_colors) for a stand-in frame."""
    buf = bytearray(width * height)
    if frame_name in INTENTIONAL_BLANK_NAMES:
        return buf

    max_pen = max(1, min(15, num_colors))

    # 1. Monochrome 8x8 font / audio cue glyphs
    if family_id == "ui_font":
        rows = FONT_8X8.get(frame_name, FONT_8X8["u003f"])
        for y in range(8):
            bits = rows[y]
            for x in range(8):
                if (bits >> (7 - x)) & 1:
                    buf[y * 8 + x] = 1
                elif x > 0 and y > 0 and ((rows[y - 1] >> (7 - (x - 1))) & 1):
                    buf[y * 8 + x] = 2  # subtle drop shadow pen
        return buf

    if family_id == "ui_audio_cue":
        note = [0x0E, 0x0A, 0x0A, 0x0A, 0x6E, 0xEE, 0x60, 0x00]
        for y in range(8):
            for x in range(8):
                if (note[y] >> (7 - x)) & 1:
                    buf[y * 8 + x] = 1
        return buf

    # 2. Terrain occupancy_v{1..3}_{00..0f} 4-bit quadrant tiles (NW=1, NE=2, SW=4, SE=8)
    if family_id.startswith("tile_") and frame_name.startswith("occupancy_v"):
        var_num = int(frame_name.split("_")[1][1:])
        mask = int(frame_name.split("_")[2], 16)
        if mask == 0:
            return buf
        hi_pen = min(max_pen, 2)
        mid_pen = min(max_pen, 6)
        dark_pen = max_pen
        speck_pen = min(max_pen, 4)
        for y in range(16):
            qy = 1 if y >= 8 else 0
            for x in range(16):
                qx = 1 if x >= 8 else 0
                qbit = 1 << (qy * 2 + qx)
                if not (mask & qbit):
                    buf[y * 16 + x] = 0
                    continue
                # Check if pixel borders an open quadrant for clean tunnel bevel
                near_open = False
                if x < 8 and not (mask & (1 << (qy * 2 + 1))) and x == 7:
                    near_open = True
                if x >= 8 and not (mask & (1 << (qy * 2 + 0))) and x == 8:
                    near_open = True
                if y < 8 and not (mask & (1 << (1 * 2 + qx))) and y == 7:
                    near_open = True
                if y >= 8 and not (mask & (1 << (0 * 2 + qx))) and y == 8:
                    near_open = True
                if near_open:
                    buf[y * 16 + x] = dark_pen
                elif ((x * 5 + y * 3 + var_num * 7) % 19) == 0:
                    buf[y * 16 + x] = hi_pen
                elif (y // 4 + var_num) % 2 == 0:
                    buf[y * 16 + x] = mid_pen
                else:
                    buf[y * 16 + x] = speck_pen
        return buf

    # 3. Solid / special terrain tiles (16x16 or 16x32)
    if family_id.startswith("tile_") and width >= 16 and not frame_name.endswith("_icon"):
        for y in range(height):
            for x in range(width):
                if frame_name.startswith("icicle") or "icicle" in frame_name:
                    half = max(1, (width // 2) * (height - y) // height)
                    if abs(x - width // 2) <= half and 1 <= y < height - 1:
                        buf[y * width + x] = 1 if abs(x - width // 2) < half else max_pen
                elif "surface_trim" in frame_name or "grass" in frame_name:
                    if y < 5:
                        buf[y * width + x] = 1
                    else:
                        buf[y * width + x] = min(max_pen, 5 + ((x + y) % 3))
                else:
                    buf[y * width + x] = min(max_pen, 1 + ((x * 3 + y * 5 + hash(frame_name)) % max_pen))
        return buf

    # 4. Full-bleed UI cards / victory scenes / frames
    if family_id in ("ui_ending", "ui_world_cards", "ui_screen_frames"):
        for y in range(height):
            for x in range(width):
                border = x < 2 or x >= width - 2 or y < 2 or y >= height - 2
                if family_id == "ui_screen_frames":
                    if border:
                        buf[y * width + x] = min(max_pen, 7)
                    elif 2 <= x < width - 2 and 2 <= y < height - 2:
                        buf[y * width + x] = 1
                else:
                    band = ((y * max_pen) // max(1, height)) % max_pen
                    buf[y * width + x] = max_pen if border else (1 + band)
        return buf

    # 5. Non-tile sprites & 8x8 icons: guarantee >=1px index-0 transparent border
    # and recognizable circular/capsule/character silhouette inside [1..w-2, 1..h-2].
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    rx = max(1.5, (width / 2.0) - 1.5)
    ry = max(1.5, (height / 2.0) - 1.5)
    seed = sum(ord(ch) for ch in (family_id + ":" + frame_name))

    hi = 1
    mid = max(1, min(max_pen, max_pen // 2 + 1))
    accent = max(1, min(max_pen, (seed % max_pen) + 1))
    outline = max_pen

    for y in range(1, height - 1):
        ny = (y - cy) / ry
        for x in range(1, width - 1):
            nx = (x - cx) / rx
            d2 = nx * nx + ny * ny
            if d2 <= 1.0:
                if d2 >= 0.72:
                    buf[y * width + x] = outline
                elif nx < -0.2 and ny < -0.2:
                    buf[y * width + x] = hi
                elif abs(ny) < 0.22 and ((x + seed) % 3 == 0):
                    buf[y * width + x] = accent
                else:
                    buf[y * width + x] = mid
    return buf


def synth_standin_pcm18500(cue_name: str, is_stem: bool = False) -> list[int]:
    """Generate a compact, deterministic 18.5 kHz mono PCM waveform for stand-in builds."""
    rate = 18500
    if is_stem:
        # Compact 1-second loopable stand-in stem in sandbox (real build uses full 8-bar WAV)
        n = rate
    else:
        n = rate // 6  # ~166 ms SFX cue
    seed = sum(ord(c) for c in cue_name)
    base_hz = 165.0 + (seed % 11) * 55.0
    samples = [0] * n
    for i in range(n):
        t = i / rate
        env = min(1.0, i / 120.0) * max(0.15 if is_stem else 0.0, 1.0 - (i / n) * (0.1 if is_stem else 0.95))
        val = math.sin(2.0 * math.pi * base_hz * t) + 0.35 * math.sin(4.0 * math.pi * base_hz * t)
        samples[i] = int(max(-30000, min(30000, val * 9000.0 * env)))
    return samples
