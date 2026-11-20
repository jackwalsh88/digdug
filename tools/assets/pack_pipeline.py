"""Dual-mode Neo Geo MVS asset & audio compiler, validator, previewer, and budget reporter.

Ingests either:
  1. The user's `Super-Dig-Dug-Complete-Asset-Pack.zip` (or extracted `Super-Dig-Dug-Art/`
     directory) via `--pack <path>` / `SDD_ASSET_PACK` / auto-detection in repo root, OR
  2. Deterministic stand-in sprites & PCM synthesized from `assets/pack_catalog.jsonl`
     and `assets/audio_catalog.json` when the 150 MB binary zip is absent (e.g. cloud CI).

Both modes emit identical C symbol names, tile offsets, palette IDs, S-ROM FIX maps,
and V-ROM cue tables under `assets/generated/`.
"""

from __future__ import annotations

import json
import math
import os
import re
import struct
import zipfile
from pathlib import Path
from typing import Any

from assets.neogeo_encode import (
    NEOGEO_REF_BLACK,
    build_palette_16,
    decode_c_tile_16x16,
    decode_s_tile_8x8,
    encode_c_tile_16x16,
    encode_s_tile_8x8,
    encode_ym2610_adpcm_a,
    map_rgba_tile_to_palette,
    neogeo_word_to_rgb,
    partition_scene_palettes,
    read_wav_mono16,
    resample_linear,
)
from assets.png_rgba import (
    RGBAImage,
    decode_png_bytes,
    encode_indexed_png,
    encode_rgba_png,
    write_png,
)
from assets.standin_art import (
    INTENTIONAL_BLANK_NAMES,
    render_standin_indices,
    synth_standin_pcm18500,
)

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = ROOT / "assets" / "pack_catalog.jsonl"
AUDIO_CATALOG_PATH = ROOT / "assets" / "audio_catalog.json"
GENERATED_DIR = ROOT / "assets" / "generated"
REVIEW_DIR = ROOT / "assets" / "review"
EXPORT_DIR = ROOT / "assets" / "export"

# Fixed palette slot assignments (0..15 reserved for FIX layer + HUD)
PAL_FIX_TEXT = 0
PAL_FIX_GOLD = 1
PAL_FIX_P1 = 2
PAL_FIX_P2 = 3
PAL_FIX_DANGER = 4
PAL_FIX_UI_HUD = 5
PAL_FIX_UI_EQUIP = 6
PAL_FIX_FX_SCORE = 7
PAL_FIX_FX_COOP = 8
PAL_FIX_UI_FRAMES = 9

PAL_SPRITE_FIRST = 16
PAL_DD1982_STRATUM_0 = 80
PAL_DD1982_STRATUM_1 = 81
PAL_DD1982_STRATUM_2 = 82
PAL_DD1982_STRATUM_3 = 83
PAL_DD1982_SURFACE = 84
PAL_SCENE_WORLD_CARDS_BASE = 96   # 96..107 (12 sub-palettes)
PAL_SCENE_ENDING_BASE = 108       # 108..119 (12 sub-palettes)
PAL_BACKDROP = 255


def _c_ident(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_").upper()
    if not s or s[0].isdigit():
        s = "ID_" + s
    return s


class PackReader:
    """Uniform file reader over a zip archive, directory, or None (stand-in mode)."""

    def __init__(self, pack_path: Path | None) -> None:
        self.pack_path = pack_path
        self.mode = "standin_catalog"
        self._zf: zipfile.ZipFile | None = None
        self._dir: Path | None = None
        if pack_path is not None and pack_path.exists():
            if pack_path.is_file() and zipfile.is_zipfile(pack_path):
                self._zf = zipfile.ZipFile(pack_path, "r")
                self.mode = "real_pack_zip"
            elif pack_path.is_dir():
                # Allow pointing either at parent of Super-Dig-Dug-Art or inside it
                if (pack_path / "Super-Dig-Dug-Art").is_dir():
                    self._dir = pack_path
                else:
                    self._dir = pack_path.parent
                self.mode = "real_pack_dir"

    def close(self) -> None:
        if self._zf is not None:
            self._zf.close()
            self._zf = None

    def read_bytes(self, rel_path: str) -> bytes | None:
        if self._zf is not None:
            try:
                return self._zf.read(rel_path)
            except KeyError:
                return None
        if self._dir is not None:
            candidate = self._dir / rel_path
            if candidate.is_file():
                return candidate.read_bytes()
        return None


def resolve_pack_path(explicit: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_val = os.environ.get("SDD_ASSET_PACK")
    if env_val:
        candidates.append(Path(env_val).expanduser())
    candidates.append(ROOT / "Super-Dig-Dug-Complete-Asset-Pack.zip")
    candidates.append(ROOT / "Super-Dig-Dug-Art")
    for c in candidates:
        if c.exists():
            return c.resolve()
    return None


def load_catalog() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    lines = [json.loads(line) for line in CATALOG_PATH.read_text().splitlines() if line.strip()]
    validation = lines[0]["__validation__"]
    families = [entry for entry in lines if "id" in entry]
    audio_cat = json.loads(AUDIO_CATALOG_PATH.read_text())
    return validation, families, audio_cat


def _build_fixed_palettes(families_by_id: dict[str, dict[str, Any]]) -> list[list[int]]:
    palettes = [[NEOGEO_REF_BLACK] * 16 for _ in range(256)]

    # 0: Crisp arcade text palette (index 1 = ivory white, index 2 = dark shadow)
    palettes[PAL_FIX_TEXT] = build_palette_16([
        (252, 249, 236), (24, 18, 32), (252, 212, 36), (104, 228, 248),
        (244, 56, 48), (112, 224, 96), (184, 188, 204), (116, 120, 140),
    ])
    palettes[PAL_FIX_GOLD] = build_palette_16([
        (253, 218, 44), (36, 16, 8), (255, 248, 196), (224, 132, 16),
    ])
    palettes[PAL_FIX_P1] = build_palette_16([
        (110, 223, 243), (18, 24, 48), (253, 247, 227), (237, 56, 52),
    ])
    palettes[PAL_FIX_P2] = build_palette_16([
        (108, 236, 148), (12, 32, 28), (253, 253, 253), (48, 132, 244),
    ])
    palettes[PAL_FIX_DANGER] = build_palette_16([
        (252, 64, 48), (36, 6, 12), (254, 232, 84), (188, 20, 20),
    ])

    fix_family_map = {
        PAL_FIX_UI_HUD: "ui_hud",
        PAL_FIX_UI_EQUIP: "ui_equipment_menu",
        PAL_FIX_FX_SCORE: "fx_score",
        PAL_FIX_FX_COOP: "fx_coop",
        PAL_FIX_UI_FRAMES: "ui_screen_frames",
    }
    for slot, fid in fix_family_map.items():
        palettes[slot] = build_palette_16(families_by_id[fid]["pal"])

    # Phase 1 1982 Dig Dug 4 depth-strata palettes derived from topsoil luminance structure
    palettes[PAL_DD1982_STRATUM_0] = build_palette_16([
        (248, 224, 96), (236, 196, 68), (220, 168, 44), (196, 144, 32),
        (244, 184, 40), (224, 156, 24), (184, 124, 24), (140, 96, 20),
        (208, 140, 20), (192, 128, 16), (176, 112, 12), (156, 96, 12),
        (132, 76, 12), (88, 52, 16), (108, 56, 12),
    ])
    palettes[PAL_DD1982_STRATUM_1] = build_palette_16([
        (248, 180, 76), (232, 152, 56), (216, 128, 40), (184, 108, 36),
        (236, 124, 20), (216, 104, 12), (172, 88, 28), (124, 68, 24),
        (196, 92, 12), (184, 80, 12), (168, 72, 10), (152, 60, 10),
        (128, 48, 12), (76, 36, 20), (96, 36, 16),
    ])
    palettes[PAL_DD1982_STRATUM_2] = build_palette_16([
        (224, 136, 68), (200, 112, 52), (184, 88, 36), (152, 76, 36),
        (196, 76, 16), (176, 60, 12), (140, 56, 28), (104, 48, 28),
        (160, 52, 12), (148, 44, 12), (136, 38, 10), (120, 32, 12),
        (100, 26, 14), (64, 24, 20), (80, 20, 16),
    ])
    palettes[PAL_DD1982_STRATUM_3] = build_palette_16([
        (196, 92, 68), (172, 68, 52), (156, 52, 40), (128, 44, 40),
        (164, 36, 20), (144, 28, 16), (116, 32, 28), (88, 28, 28),
        (132, 24, 16), (120, 20, 16), (108, 16, 14), (96, 14, 14),
        (80, 12, 16), (48, 14, 20), (64, 10, 18),
    ])
    palettes[PAL_DD1982_SURFACE] = build_palette_16([
        (252, 252, 252), (104, 216, 72), (56, 164, 36), (248, 72, 64),
        (252, 216, 48), (96, 184, 248), (36, 88, 184), (24, 40, 96),
        (204, 132, 64), (156, 92, 40), (112, 60, 24), (72, 36, 16),
        (232, 40, 120), (168, 24, 84), (20, 16, 28),
    ])

    # Backdrop palette (slot 255, entry 15 = pure reference black)
    palettes[PAL_BACKDROP][15] = NEOGEO_REF_BLACK
    return palettes


def build_all_assets(pack_arg: str | None = None) -> dict[str, Any]:
    """Compile all 65 sprite/tile families and 53 audio files into `assets/generated/`."""
    validation, families, audio_cat = load_catalog()
    pack_path = resolve_pack_path(pack_arg)
    reader = PackReader(pack_path)

    try:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

        families_by_id = {f["id"]: f for f in families}
        palettes = _build_fixed_palettes(families_by_id)

        # Assign sprite palette IDs to families
        family_pal_id: dict[str, int] = {}
        next_spr_pal = PAL_SPRITE_FIRST
        for fam in families:
            fid = fam["id"]
            pal = fam["pal"]
            if pal is None:
                family_pal_id[fid] = PAL_FIX_TEXT
            elif fid == "ui_world_cards":
                family_pal_id[fid] = PAL_SCENE_WORLD_CARDS_BASE
                # Seed default sub-palettes from chunks of the 127-color table
                for sub in range(12):
                    chunk = pal[sub * 11 : sub * 11 + 15]
                    if chunk:
                        palettes[PAL_SCENE_WORLD_CARDS_BASE + sub] = build_palette_16(chunk[:15])
            elif fid == "ui_ending":
                family_pal_id[fid] = PAL_SCENE_ENDING_BASE
                for sub in range(12):
                    chunk = pal[sub * 11 : sub * 11 + 15]
                    if chunk:
                        palettes[PAL_SCENE_ENDING_BASE + sub] = build_palette_16(chunk[:15])
            else:
                family_pal_id[fid] = next_spr_pal
                palettes[next_spr_pal] = build_palette_16(pal)
                next_spr_pal += 1

        # Initialize C1/C2 with Tile 0 = blank transparent 16x16
        c1_stream = bytearray(64)
        c2_stream = bytearray(64)
        c_tile_source_indices: list[bytearray] = [bytearray(256)]
        c_tile_count = 1

        # Initialize S1 with 4096 8x8 tiles? Keep compact active range (e.g. 512 tiles = 16 KB)
        # and pad to 128 KB when packaging MAME S1 ROM.
        s1_tiles: dict[int, bytearray] = {0: bytearray(64)}
        next_s_icon_tile = 0x0100

        manifest_families: list[dict[str, Any]] = []
        scene_tile_pal_overrides: dict[int, int] = {}

        for fam_idx, fam in enumerate(families):
            fid = fam["id"]
            fdir = fam["dir"]
            pal_list = fam["pal"]
            base_pal_id = family_pal_id[fid]

            atlas_img: RGBAImage | None = None
            if reader.mode != "standin_catalog":
                png_bytes = reader.read_bytes(f"{fdir}/atlas.png")
                if png_bytes is not None:
                    atlas_img = decode_png_bytes(png_bytes)

            is_multi_pal_scene = fid in ("ui_world_cards", "ui_ending")
            scene_rgba_tiles: list[bytes] = []
            scene_c_tile_ids: list[int] = []

            frame_records: list[dict[str, Any]] = []
            first_family_tile = c_tile_count

            for frame_idx, (fname, size, rect, pivot) in enumerate(fam["frames"]):
                fw, fh = int(size[0]), int(size[1])
                rx, ry, rw, rh = (int(v) for v in rect)
                px, py = int(pivot[0]), int(pivot[1])

                cols = math.ceil(fw / 16)
                rows = math.ceil(fh / 16)
                pad_w = cols * 16
                pad_h = rows * 16
                tile_base = c_tile_count

                # Extract or synthesize frame pixels
                if atlas_img is not None:
                    crop_rgba = atlas_img.crop(rx, ry, rw, rh)
                    if is_multi_pal_scene:
                        # Collect 16x16 RGBA tiles in column-major order for sub-palette partitioning
                        padded_rgba = RGBAImage(pad_w, pad_h)
                        padded_rgba.blit(crop_rgba, 0, 0)
                        for tx in range(cols):
                            for ty in range(rows):
                                sub_crop = padded_rgba.crop(tx * 16, ty * 16, 16, 16)
                                scene_rgba_tiles.append(bytes(sub_crop.data))
                                scene_c_tile_ids.append(c_tile_count)
                                c_tile_source_indices.append(bytearray(256))
                                c1_stream.extend(b"\x00" * 64)
                                c2_stream.extend(b"\x00" * 64)
                                c_tile_count += 1
                        s_tile_id = -1
                    else:
                        if pal_list is None:
                            # Monochrome alpha font/cue: alpha >= 128 -> pen 1
                            idx_crop = bytearray(fw * fh)
                            for i in range(fw * fh):
                                idx_crop[i] = 1 if crop_rgba.data[i * 4 + 3] >= 128 else 0
                        else:
                            rgb_tuples = [(int(c[0]), int(c[1]), int(c[2])) for c in pal_list]
                            idx_crop = map_rgba_tile_to_palette(crop_rgba.data, rgb_tuples)
                        s_tile_id = _pack_frame_tiles(
                            fid,
                            fname,
                            fw,
                            fh,
                            cols,
                            rows,
                            idx_crop,
                            c1_stream,
                            c2_stream,
                            c_tile_source_indices,
                            s1_tiles,
                            next_s_icon_tile,
                        )
                        if s_tile_id >= next_s_icon_tile:
                            next_s_icon_tile = s_tile_id + (2 if (fw == 16 and fh == 8) else 1)
                        c_tile_count += cols * rows
                else:
                    num_cols_avail = 15 if is_multi_pal_scene else (2 if pal_list is None else len(pal_list))
                    idx_crop = render_standin_indices(fid, fname, fw, fh, num_cols_avail)
                    s_tile_id = _pack_frame_tiles(
                        fid,
                        fname,
                        fw,
                        fh,
                        cols,
                        rows,
                        idx_crop,
                        c1_stream,
                        c2_stream,
                        c_tile_source_indices,
                        s1_tiles,
                        next_s_icon_tile,
                    )
                    if s_tile_id >= next_s_icon_tile:
                        next_s_icon_tile = s_tile_id + (2 if (fw == 16 and fh == 8) else 1)
                    c_tile_count += cols * rows

                    # Export representative stand-in master PNG for key families
                    if frame_idx == 0 and fid in (
                        "chr_player_1",
                        "enm_pooka",
                        "enm_fygar",
                        "prop_rocks",
                        "pick_rewards",
                        "tile_topsoil",
                    ):
                        pal_rgb = [(0, 0, 0)] + [
                            (int(c[0]), int(c[1]), int(c[2])) for c in (pal_list or [(255, 255, 255)])[:15]
                        ]
                        write_png(
                            EXPORT_DIR / f"{fid}_{fname}.png",
                            encode_indexed_png(fw, fh, idx_crop, pal_rgb, transparent_zero=True),
                        )

                frame_records.append(
                    {
                        "index": frame_idx,
                        "name": fname,
                        "width": fw,
                        "height": fh,
                        "cols": cols,
                        "rows": rows,
                        "pivot": [px, py],
                        "c_tile_base": tile_base,
                        "s_tile_id": s_tile_id if s_tile_id >= 0 else None,
                    }
                )

            # Finalize multi-palette scene tiles if loaded from real RGBA atlas
            if is_multi_pal_scene and scene_rgba_tiles:
                sub_pals, sub_assign = partition_scene_palettes(scene_rgba_tiles, max_palettes=12)
                for sp_i, sp_rgb in enumerate(sub_pals):
                    palettes[base_pal_id + sp_i] = build_palette_16(sp_rgb)
                for local_i, c_tid in enumerate(scene_c_tile_ids):
                    sp_i = sub_assign[local_i]
                    scene_tile_pal_overrides[c_tid] = base_pal_id + sp_i
                    indices_256 = map_rgba_tile_to_palette(scene_rgba_tiles[local_i], sub_pals[sp_i])
                    c_tile_source_indices[c_tid] = indices_256
                    c1_b, c2_b = encode_c_tile_16x16(indices_256)
                    c1_stream[c_tid * 64 : (c_tid + 1) * 64] = c1_b
                    c2_stream[c_tid * 64 : (c_tid + 1) * 64] = c2_b

            # Alias lowercase ASCII in S-ROM to uppercase glyphs when ui_font is processed
            if fid == "ui_font":
                for ch_ord in range(ord("A"), ord("Z") + 1):
                    if ch_ord in s1_tiles:
                        s1_tiles[ch_ord + 32] = bytearray(s1_tiles[ch_ord])

            manifest_families.append(
                {
                    "family_index": fam_idx,
                    "id": fid,
                    "dir": fdir,
                    "palette_id": base_pal_id,
                    "ticks_per_second": fam["tps"],
                    "first_c_tile": first_family_tile,
                    "c_tile_span": c_tile_count - first_family_tile,
                    "frames": frame_records,
                    "animations": fam["anims"],
                }
            )

        # Assemble S1 binary up to max_s_tile + 1 (minimum 512 tiles = 16 KB; padded on ROM build)
        max_s_tile = max(511, max(s1_tiles.keys()))
        s1_stream = bytearray((max_s_tile + 1) * 32)
        s_tile_source_list: list[bytearray] = [bytearray(64) for _ in range(max_s_tile + 1)]
        for st_id, pix64 in s1_tiles.items():
            s_tile_source_list[st_id] = pix64
            s1_stream[st_id * 32 : (st_id + 1) * 32] = encode_s_tile_8x8(pix64)

        # Compile Audio V-ROM (ADPCM-A 18.5 kHz, 256-byte page aligned)
        v1_stream, audio_records = _compile_vrom(audio_cat, reader)

        # Write binary outputs
        (GENERATED_DIR / "c1.bin").write_bytes(c1_stream)
        (GENERATED_DIR / "c2.bin").write_bytes(c2_stream)
        (GENERATED_DIR / "s1.bin").write_bytes(s1_stream)
        (GENERATED_DIR / "v1.bin").write_bytes(v1_stream)

        # Save source index reference cache for independent round-trip verification in `asset-check`
        pal_bin = bytearray()
        for p16 in palettes:
            for w16 in p16:
                pal_bin.extend(struct.pack(">H", w16))
        (GENERATED_DIR / "palettes.bin").write_bytes(pal_bin)

        manifest = {
            "asset_source_mode": reader.mode,
            "pack_path": str(pack_path) if pack_path else None,
            "approval_status": "imported_unreviewed" if reader.mode != "standin_catalog" else "standin_placeholder",
            "expected_validation": validation,
            "counts": {
                "families": len(manifest_families),
                "frames": sum(len(f["frames"]) for f in manifest_families),
                "animations": sum(len(f["animations"]) for f in manifest_families),
                "c_tiles_16x16": c_tile_count,
                "c1_bytes": len(c1_stream),
                "c2_bytes": len(c2_stream),
                "s_tiles_8x8": max_s_tile + 1,
                "s1_bytes": len(s1_stream),
                "v1_bytes": len(v1_stream),
                "runtime_audio_cues": len(audio_records),
                "active_palettes": next_spr_pal + 30,
            },
            "palettes_hex": [[f"0x{w:04X}" for w in p16] for p16 in palettes],
            "families": manifest_families,
            "audio_cues": audio_records,
            "scene_tile_pal_overrides": {str(k): v for k, v in scene_tile_pal_overrides.items()},
        }
        (GENERATED_DIR / "asset_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

        # Write reference indices archive (compressed) for fast independent `asset-check`
        import zlib as _zlib

        ref_blob = (
            struct.pack(">II", len(c_tile_source_indices), len(s_tile_source_list))
            + b"".join(bytes(t) for t in c_tile_source_indices)
            + b"".join(bytes(t) for t in s_tile_source_list)
        )
        (GENERATED_DIR / "roundtrip_ref.zbin").write_bytes(_zlib.compress(ref_blob, level=6))

        _emit_c_headers(manifest, palettes)
        return manifest
    finally:
        reader.close()


def _pack_frame_tiles(
    fid: str,
    fname: str,
    fw: int,
    fh: int,
    cols: int,
    rows: int,
    idx_crop: bytearray,
    c1_stream: bytearray,
    c2_stream: bytearray,
    c_tile_source_indices: list[bytearray],
    s1_tiles: dict[int, bytearray],
    next_s_icon_tile: int,
) -> int:
    """Slice an indexed frame into column-major 16x16 C-ROM tiles and optional 8x8 S-ROM tiles."""
    pad_w = cols * 16
    pad_h = rows * 16
    padded = bytearray(pad_w * pad_h)
    for y in range(fh):
        padded[y * pad_w : y * pad_w + fw] = idx_crop[y * fw : (y + 1) * fw]

    for tx in range(cols):
        for ty in range(rows):
            tile256 = bytearray(256)
            for ry in range(16):
                sy = ty * 16 + ry
                sx = tx * 16
                tile256[ry * 16 : (ry + 1) * 16] = padded[sy * pad_w + sx : sy * pad_w + sx + 16]
            c_tile_source_indices.append(tile256)
            c1_b, c2_b = encode_c_tile_16x16(tile256)
            c1_stream.extend(c1_b)
            c2_stream.extend(c2_b)

    # Also register 8x8 (or 16x8) frames into S-ROM FIX layer
    s_tile_id = -1
    if fid == "ui_font" and fname.startswith("u") and len(fname) == 5:
        codepoint = int(fname[1:], 16)
        if 0x20 <= codepoint <= 0x7E:
            s_tile_id = codepoint
        else:
            special_map = {
                0x00D7: 0x80,  # ×
                0x2191: 0x81,  # ↑
                0x2193: 0x82,  # ↓
                0x2192: 0x83,  # →
                0x2190: 0x84,  # ←
            }
            s_tile_id = special_map.get(codepoint, next_s_icon_tile)
        s1_tiles[s_tile_id] = bytearray(idx_crop[:64])
    elif fw == 8 and fh == 8:
        s_tile_id = next_s_icon_tile
        s1_tiles[s_tile_id] = bytearray(idx_crop[:64])
    elif fw == 16 and fh == 8:
        s_tile_id = next_s_icon_tile
        left64 = bytearray(64)
        right64 = bytearray(64)
        for y in range(8):
            left64[y * 8 : (y + 1) * 8] = idx_crop[y * 16 : y * 16 + 8]
            right64[y * 8 : (y + 1) * 8] = idx_crop[y * 16 + 8 : y * 16 + 16]
        s1_tiles[s_tile_id] = left64
        s1_tiles[s_tile_id + 1] = right64
    return s_tile_id


def _compile_vrom(audio_cat: dict[str, Any], reader: PackReader) -> tuple[bytearray, list[dict[str, Any]]]:
    v1 = bytearray()
    records: list[dict[str, Any]] = []

    ordered_cues: list[tuple[str, str, str, bool]] = []
    for suite in audio_cat["music_suites"]:
        sid = suite["id"]
        for stem_path in suite["stems"]:
            stem_name = Path(stem_path).stem
            ordered_cues.append((f"mus_{sid}_{stem_name}", stem_path, "music_stem", True))
    for sfx_path in audio_cat["sfx"]:
        ordered_cues.append((f"sfx_{Path(sfx_path).stem}", sfx_path, "sfx", False))
    for st_path in audio_cat["stingers"]:
        ordered_cues.append((f"stg_{Path(st_path).stem}", st_path, "stinger", False))

    for cue_idx, (cue_id, rel_wav, category, is_stem) in enumerate(ordered_cues):
        wav_bytes = reader.read_bytes(rel_wav) if reader.mode != "standin_catalog" else None
        if wav_bytes is not None:
            src_rate, pcm = read_wav_mono16(wav_bytes)
            pcm_18500 = resample_linear(pcm, src_rate, 18500)
        else:
            pcm_18500 = synth_standin_pcm18500(cue_id, is_stem=is_stem)

        adpcm = encode_ym2610_adpcm_a(pcm_18500, pad_align=256)
        start_byte = len(v1)
        v1.extend(adpcm)
        end_byte_inclusive = len(v1) - 1
        records.append(
            {
                "index": cue_idx,
                "id": cue_id,
                "source_wav": rel_wav,
                "category": category,
                "is_looping_stem": is_stem,
                "start_page_256": start_byte >> 8,
                "end_page_256": end_byte_inclusive >> 8,
                "byte_length": len(adpcm),
                "samples_18500": len(pcm_18500),
            }
        )

    return v1, records


def _emit_c_headers(manifest: dict[str, Any], palettes: list[list[int]]) -> None:
    fams = manifest["families"]
    cues = manifest["audio_cues"]

    h_lines = [
        "/* AUTO-GENERATED BY tools/assets/pack_pipeline.py — DO NOT EDIT MANUALLY */",
        "#ifndef SDD_ASSETS_H",
        "#define SDD_ASSETS_H",
        "",
        "#include <stdint.h>",
        "",
        f"#define SDD_ASSET_FAMILY_COUNT {len(fams)}u",
        f"#define SDD_ASSET_FRAME_COUNT  {manifest['counts']['frames']}u",
        f"#define SDD_CROM_TILE_COUNT    {manifest['counts']['c_tiles_16x16']}u",
        f"#define SDD_SROM_TILE_COUNT    {manifest['counts']['s_tiles_8x8']}u",
        f"#define SDD_AUDIO_CUE_COUNT    {len(cues)}u",
        "",
        "/* Fixed & Phase-1 Palette Slot IDs */",
        f"#define PAL_FIX_TEXT          {PAL_FIX_TEXT}u",
        f"#define PAL_FIX_GOLD          {PAL_FIX_GOLD}u",
        f"#define PAL_FIX_P1            {PAL_FIX_P1}u",
        f"#define PAL_FIX_P2            {PAL_FIX_P2}u",
        f"#define PAL_FIX_DANGER        {PAL_FIX_DANGER}u",
        f"#define PAL_FIX_UI_HUD        {PAL_FIX_UI_HUD}u",
        f"#define PAL_FIX_UI_EQUIP      {PAL_FIX_UI_EQUIP}u",
        f"#define PAL_FIX_FX_SCORE      {PAL_FIX_FX_SCORE}u",
        f"#define PAL_FIX_FX_COOP       {PAL_FIX_FX_COOP}u",
        f"#define PAL_FIX_UI_FRAMES     {PAL_FIX_UI_FRAMES}u",
        f"#define PAL_DD1982_STRATUM_0  {PAL_DD1982_STRATUM_0}u",
        f"#define PAL_DD1982_STRATUM_1  {PAL_DD1982_STRATUM_1}u",
        f"#define PAL_DD1982_STRATUM_2  {PAL_DD1982_STRATUM_2}u",
        f"#define PAL_DD1982_STRATUM_3  {PAL_DD1982_STRATUM_3}u",
        f"#define PAL_DD1982_SURFACE    {PAL_DD1982_SURFACE}u",
        f"#define PAL_BACKDROP          {PAL_BACKDROP}u",
        "",
        "typedef enum {",
    ]
    for fam in fams:
        h_lines.append(f"    FAM_{_c_ident(fam['id'])} = {fam['family_index']},")
    h_lines.extend(
        [
            "} sdd_family_id_t;",
            "",
            "/* Per-family default sprite palette IDs */",
        ]
    )
    for fam in fams:
        h_lines.append(f"#define PAL_{_c_ident(fam['id'])} {fam['palette_id']}u")

    h_lines.extend(["", "/* Audio V-ROM Cue IDs */", "typedef enum {"])
    for cue in cues:
        h_lines.append(f"    AUDIO_{_c_ident(cue['id'])} = {cue['index']},")
    h_lines.extend(
        [
            "} sdd_audio_cue_id_t;",
            "",
            "typedef struct {",
            "    uint16_t c_tile_base;",
            "    int16_t  s_tile_id;   /* -1 if sprite-only */",
            "    uint8_t  width;",
            "    uint8_t  height;",
            "    uint8_t  cols;",
            "    uint8_t  rows;",
            "    int8_t   pivot_x;",
            "    int8_t   pivot_y;",
            "} sdd_frame_desc_t;",
            "",
            "typedef struct {",
            "    const char *id;",
            "    uint16_t    first_frame;",
            "    uint16_t    frame_count;",
            "    uint16_t    first_c_tile;",
            "    uint8_t     palette_id;",
            "} sdd_family_desc_t;",
            "",
            "typedef struct {",
            "    uint16_t start_page_256;",
            "    uint16_t end_page_256;",
            "    uint8_t  is_looping_stem;",
            "} sdd_audio_cue_desc_t;",
            "",
            "extern const uint16_t sdd_palettes[256][16];",
            "extern const sdd_family_desc_t sdd_families[SDD_ASSET_FAMILY_COUNT];",
            "extern const sdd_frame_desc_t  sdd_frames[SDD_ASSET_FRAME_COUNT];",
            "extern const sdd_audio_cue_desc_t sdd_audio_cues[SDD_AUDIO_CUE_COUNT];",
            "",
            "#endif /* SDD_ASSETS_H */",
            "",
        ]
    )
    (GENERATED_DIR / "sdd_assets.h").write_text("\n".join(h_lines))

    c_lines = [
        "/* AUTO-GENERATED BY tools/assets/pack_pipeline.py — DO NOT EDIT MANUALLY */",
        '#include "sdd_assets.h"',
        "",
        "const uint16_t sdd_palettes[256][16] = {",
    ]
    for p_idx, p16 in enumerate(palettes):
        hex_words = ", ".join(f"0x{w:04X}u" for w in p16)
        c_lines.append(f"    /* {p_idx:3d} */ {{ {hex_words} }},")
    c_lines.extend(["};", "", "const sdd_frame_desc_t sdd_frames[SDD_ASSET_FRAME_COUNT] = {"])

    running_frame = 0
    fam_entries: list[str] = []
    for fam in fams:
        first_f = running_frame
        for fr in fam["frames"]:
            stid = -1 if fr["s_tile_id"] is None else int(fr["s_tile_id"])
            px, py = fr["pivot"]
            c_lines.append(
                f"    {{ {fr['c_tile_base']}u, {stid}, {fr['width']}u, {fr['height']}u, "
                f"{fr['cols']}u, {fr['rows']}u, {px}, {py} }},"
            )
            running_frame += 1
        fam_entries.append(
            f'    {{ "{fam["id"]}", {first_f}u, {len(fam["frames"])}u, '
            f'{fam["first_c_tile"]}u, {fam["palette_id"]}u }},'
        )
    c_lines.extend(["};", "", "const sdd_family_desc_t sdd_families[SDD_ASSET_FAMILY_COUNT] = {"])
    c_lines.extend(fam_entries)
    c_lines.extend(["};", "", "const sdd_audio_cue_desc_t sdd_audio_cues[SDD_AUDIO_CUE_COUNT] = {"])
    for cue in cues:
        stem_flag = 1 if cue["is_looping_stem"] else 0
        c_lines.append(
            f"    {{ 0x{cue['start_page_256']:04X}u, 0x{cue['end_page_256']:04X}u, {stem_flag}u }},"
        )
    c_lines.extend(["};", ""])
    (GENERATED_DIR / "sdd_assets.c").write_text("\n".join(c_lines))


def run_asset_check() -> tuple[bool, dict[str, Any]]:
    """Run strict hardware & sprite-guide validation over `assets/generated/`."""
    import zlib as _zlib

    manifest_path = GENERATED_DIR / "asset_manifest.json"
    if not manifest_path.is_file():
        return False, {"errors": ["assets/generated/asset_manifest.json missing; run `assets` first."]}

    manifest = json.loads(manifest_path.read_text())
    c1 = (GENERATED_DIR / "c1.bin").read_bytes()
    c2 = (GENERATED_DIR / "c2.bin").read_bytes()
    s1 = (GENERATED_DIR / "s1.bin").read_bytes()
    v1 = (GENERATED_DIR / "v1.bin").read_bytes()
    pal_bin = (GENERATED_DIR / "palettes.bin").read_bytes()
    ref_raw = _zlib.decompress((GENERATED_DIR / "roundtrip_ref.zbin").read_bytes())

    n_c, n_s = struct.unpack(">II", ref_raw[:8])
    c_ref_off = 8
    s_ref_off = 8 + n_c * 256

    errors: list[str] = []

    # 1. Expected catalog counts
    exp = manifest["expected_validation"]
    if manifest["counts"]["families"] != exp["families"]:
        errors.append(f"Family count mismatch: {manifest['counts']['families']} != {exp['families']}")
    if manifest["counts"]["frames"] != exp["native_sprites"]:
        errors.append(f"Frame count mismatch: {manifest['counts']['frames']} != {exp['native_sprites']}")

    # 2. Palette RAM index 0 transparency & reference black ($8000) check
    if len(pal_bin) != 256 * 16 * 2:
        errors.append(f"Invalid palettes.bin size: {len(pal_bin)}")
    else:
        for p in range(256):
            w0 = struct.unpack(">H", pal_bin[p * 32 : p * 32 + 2])[0]
            if w0 != NEOGEO_REF_BLACK:
                errors.append(f"Palette {p} entry 0 must be 0x8000 (transparent/ref black), got 0x{w0:04X}")
        backdrop_w = struct.unpack(">H", pal_bin[255 * 32 + 30 : 255 * 32 + 32])[0]
        if backdrop_w != NEOGEO_REF_BLACK:
            errors.append(f"Backdrop color ($401FFE) must be 0x8000, got 0x{backdrop_w:04X}")

    # 3. Independent C-ROM 16x16 bitplane round-trip decode check across ALL tiles
    if len(c1) != n_c * 64 or len(c2) != n_c * 64:
        errors.append(f"C1/C2 byte length mismatch ({len(c1)}/{len(c2)} vs {n_c * 64})")
    else:
        for tid in range(n_c):
            dec = decode_c_tile_16x16(c1[tid * 64 : (tid + 1) * 64], c2[tid * 64 : (tid + 1) * 64])
            expected_tile = ref_raw[c_ref_off + tid * 256 : c_ref_off + (tid + 1) * 256]
            if bytes(dec) != expected_tile:
                errors.append(f"C-ROM tile {tid} failed independent bitplane round-trip decode")
                if len(errors) > 25:
                    break

    # 4. Independent S-ROM 8x8 column-pair round-trip decode check across ALL tiles
    if len(s1) != n_s * 32:
        errors.append(f"S1 byte length mismatch ({len(s1)} vs {n_s * 32})")
    else:
        for stid in range(n_s):
            dec_s = decode_s_tile_8x8(s1[stid * 32 : (stid + 1) * 32])
            expected_s = ref_raw[s_ref_off + stid * 64 : s_ref_off + (stid + 1) * 64]
            if bytes(dec_s) != expected_s:
                errors.append(f"S-ROM tile {stid} failed independent column-pair round-trip decode")
                break

    # 5. Terrain 4-bit occupancy quadrant check across all 7 terrain families (336 tiles)
    occ_checked = 0
    blank_frames_seen = 0
    for fam in manifest["families"]:
        fid = fam["id"]
        fnames = {fr["name"]: fr for fr in fam["frames"]}
        for fr in fam["frames"]:
            fname = fr["name"]
            tid = fr["c_tile_base"]
            cols, rows = fr["cols"], fr["rows"]
            # Check accidental completely empty frames
            all_zero = True
            for sub_t in range(tid, tid + cols * rows):
                tbytes = ref_raw[c_ref_off + sub_t * 256 : c_ref_off + (sub_t + 1) * 256]
                if any(tbytes):
                    all_zero = False
                    break
            if all_zero:
                blank_frames_seen += 1
                if fname not in INTENTIONAL_BLANK_NAMES:
                    errors.append(f"Unexpected completely transparent frame: {fid}/{fname}")

            # Verify terrain occupancy masks (NW=1, NE=2, SW=4, SE=8)
            if fid.startswith("tile_") and fname.startswith("occupancy_v"):
                occ_checked += 1
                mask = int(fname.split("_")[2], 16)
                tbytes = ref_raw[c_ref_off + tid * 256 : c_ref_off + (tid + 1) * 256]
                if mask == 0 and any(tbytes):
                    errors.append(f"{fid}/{fname} (mask 0x00) must be completely transparent")
                elif mask != 0:
                    # Check center 4x4 of each 8x8 quadrant matches mask occupancy
                    quads = ((0, 0, 1), (8, 0, 2), (0, 8, 4), (8, 8, 8))
                    for qx, qy, qbit in quads:
                        center_nonzero = sum(
                            1
                            for yy in range(qy + 2, qy + 6)
                            for xx in range(qx + 2, qx + 6)
                            if tbytes[yy * 16 + xx] != 0
                        )
                        if (mask & qbit) and center_nonzero == 0:
                            errors.append(f"{fid}/{fname} occupied quadrant {qbit} center is empty")
                        if not (mask & qbit) and center_nonzero == 16:
                            errors.append(f"{fid}/{fname} cleared quadrant {qbit} center is solid")

        # 6. Animation clip integrity check
        for aname, adef in fam["animations"].items():
            if adef["ticks_per_pose"] <= 0:
                errors.append(f"{fid}:{aname} has non-positive ticks_per_pose")
            for ref_name in adef["frames"]:
                if ref_name not in fnames:
                    errors.append(f"{fid}:{aname} references missing frame {ref_name}")

    if occ_checked != 7 * 3 * 16:
        errors.append(f"Expected 336 terrain occupancy tiles, checked {occ_checked}")

    # 7. Audio V-ROM 256-byte page alignment check
    if len(v1) % 256 != 0:
        errors.append(f"V1 ROM size ({len(v1)}) is not 256-byte aligned")
    for cue in manifest["audio_cues"]:
        if cue["byte_length"] % 256 != 0 or cue["end_page_256"] < cue["start_page_256"]:
            errors.append(f"Audio cue {cue['id']} failed 256-byte page alignment")

    report = {
        "passed": len(errors) == 0,
        "asset_source_mode": manifest["asset_source_mode"],
        "c_tiles_verified": n_c,
        "s_tiles_verified": n_s,
        "occupancy_tiles_verified": occ_checked,
        "intentional_blank_frames": blank_frames_seen,
        "audio_cues_verified": len(manifest["audio_cues"]),
        "errors": errors,
    }
    (ROOT / "build").mkdir(parents=True, exist_ok=True)
    (ROOT / "build" / "asset_check_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return len(errors) == 0, report


def _render_c_frame_rgba(
    fr: dict[str, Any],
    c1: bytes,
    c2: bytes,
    pal_words: list[int],
) -> RGBAImage:
    cols, rows = fr["cols"], fr["rows"]
    img = RGBAImage(cols * 16, rows * 16)
    rgb_lut = [(0, 0, 0, 0)] + [(*neogeo_word_to_rgb(w), 255) for w in pal_words[1:]]
    tbase = fr["c_tile_base"]
    idx = 0
    for tx in range(cols):
        for ty in range(rows):
            tid = tbase + idx
            idx += 1
            dec = decode_c_tile_16x16(c1[tid * 64 : (tid + 1) * 64], c2[tid * 64 : (tid + 1) * 64])
            for ry in range(16):
                for rx in range(16):
                    pen = dec[ry * 16 + rx]
                    px_off = ((ty * 16 + ry) * img.width + (tx * 16 + rx)) * 4
                    img.data[px_off : px_off + 4] = bytes(rgb_lut[pen])
    return img.crop(0, 0, fr["width"], fr["height"])


def run_asset_preview() -> list[Path]:
    """Decode packed C-ROM & S-ROM tiles and write 1x and 8x review sheets to `assets/review/`."""
    manifest = json.loads((GENERATED_DIR / "asset_manifest.json").read_text())
    c1 = (GENERATED_DIR / "c1.bin").read_bytes()
    c2 = (GENERATED_DIR / "c2.bin").read_bytes()
    s1 = (GENERATED_DIR / "s1.bin").read_bytes()
    pal_bin = (GENERATED_DIR / "palettes.bin").read_bytes()

    palettes = [
        [struct.unpack(">H", pal_bin[p * 32 + i * 2 : p * 32 + i * 2 + 2])[0] for i in range(16)]
        for p in range(256)
    ]
    fams = {f["id"]: f for f in manifest["families"]}
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    # Sheet 1: Phase 1 Core Cast (Taizo P1, Pooka, Fygar, Rock, Rewards) decoded from C1/C2
    core_ids = ["chr_player_1", "enm_pooka", "enm_fygar", "prop_rocks", "pick_rewards"]
    sheet1 = RGBAImage(256, 192)
    # Fill dark neutral slate background for silhouette & dark-outline inspection
    for i in range(0, len(sheet1.data), 4):
        sheet1.data[i : i + 4] = bytes((28, 32, 44, 255))
    y_cursor = 4
    for fid in core_ids:
        fam = fams[fid]
        pal_w = palettes[fam["palette_id"]]
        x_cursor = 4
        for fr in fam["frames"][:6]:
            fimg = _render_c_frame_rgba(fr, c1, c2, pal_w)
            # Composite alpha over slate background
            for yy in range(fimg.height):
                for xx in range(fimg.width):
                    so = (yy * fimg.width + xx) * 4
                    if fimg.data[so + 3] > 0 and x_cursor + xx < sheet1.width and y_cursor + yy < sheet1.height:
                        do = ((y_cursor + yy) * sheet1.width + (x_cursor + xx)) * 4
                        sheet1.data[do : do + 4] = fimg.data[so : so + 4]
            x_cursor += fimg.width + 4
        y_cursor += 36

    for scale, suffix in ((1, "1x"), (8, "8x")):
        out_p = REVIEW_DIR / f"phase1_core_sheet_{suffix}.png"
        write_png(out_p, encode_rgba_png(sheet1.scale_nearest(scale)))
        written.append(out_p)

    # Sheet 2: Topsoil 16-mask occupancy v1 decoded from C1/C2 using Stratum 0..3 palettes
    sheet2 = RGBAImage(16 * 18 + 4, 4 * 18 + 4)
    for i in range(0, len(sheet2.data), 4):
        sheet2.data[i : i + 4] = bytes((12, 12, 16, 255))
    top_frames = {fr["name"]: fr for fr in fams["tile_topsoil"]["frames"]}
    strata_pals = [
        palettes[PAL_DD1982_STRATUM_0],
        palettes[PAL_DD1982_STRATUM_1],
        palettes[PAL_DD1982_STRATUM_2],
        palettes[PAL_DD1982_STRATUM_3],
    ]
    for row_s, sp in enumerate(strata_pals):
        for m in range(16):
            fr = top_frames[f"occupancy_v1_{m:02x}"]
            fimg = _render_c_frame_rgba(fr, c1, c2, sp)
            dx = 4 + m * 18
            dy = 4 + row_s * 18
            for yy in range(16):
                for xx in range(16):
                    so = (yy * 16 + xx) * 4
                    if fimg.data[so + 3] > 0:
                        do = ((dy + yy) * sheet2.width + (dx + xx)) * 4
                        sheet2.data[do : do + 4] = fimg.data[so : so + 4]

    for scale, suffix in ((1, "1x"), (8, "8x")):
        out_p = REVIEW_DIR / f"topsoil_4strata_masks_{suffix}.png"
        write_png(out_p, encode_rgba_png(sheet2.scale_nearest(scale)))
        written.append(out_p)

    # Sheet 3: S-ROM FIX 8x8 Font & HUD Icons decoded from S1
    sheet3 = RGBAImage(16 * 10 + 4, 8 * 10 + 4)
    for i in range(0, len(sheet3.data), 4):
        sheet3.data[i : i + 4] = bytes((18, 20, 30, 255))
    text_rgb = [(0, 0, 0, 0)] + [(*neogeo_word_to_rgb(w), 255) for w in palettes[PAL_FIX_TEXT][1:]]
    hud_rgb = [(0, 0, 0, 0)] + [(*neogeo_word_to_rgb(w), 255) for w in palettes[PAL_FIX_UI_HUD][1:]]
    sample_stiles = list(range(0x20, 0x5B)) + list(range(0x100, min(len(s1) // 32, 0x118)))
    for idx_s, stid in enumerate(sample_stiles[:128]):
        dec64 = decode_s_tile_8x8(s1[stid * 32 : (stid + 1) * 32])
        lut = hud_rgb if stid >= 0x100 else text_rgb
        gx = 4 + (idx_s % 16) * 10
        gy = 4 + (idx_s // 16) * 10
        for yy in range(8):
            for xx in range(8):
                pen = dec64[yy * 8 + xx]
                if pen != 0:
                    do = ((gy + yy) * sheet3.width + (gx + xx)) * 4
                    sheet3.data[do : do + 4] = bytes(lut[pen])

    for scale, suffix in ((1, "1x"), (8, "8x")):
        out_p = REVIEW_DIR / f"fix_font_and_hud_{suffix}.png"
        write_png(out_p, encode_rgba_png(sheet3.scale_nearest(scale)))
        written.append(out_p)

    return written


def run_budgets() -> dict[str, Any]:
    """Compute Neo Geo MVS ROM, RAM, Palette, Sprite, and Scanline-Strip budgets."""
    manifest = json.loads((GENERATED_DIR / "asset_manifest.json").read_text())
    counts = manifest["counts"]

    # Power-of-two cartridge chip sizes required by MAME Neo Geo MVS
    def next_pow2(n: int, floor_val: int) -> int:
        v = max(floor_val, 1)
        while v < n:
            v <<= 1
        return v

    c_chip_bytes = next_pow2(counts["c1_bytes"], 1024 * 1024)   # 1 MB C1 + 1 MB C2
    s_chip_bytes = next_pow2(counts["s1_bytes"], 128 * 1024)    # 128 KB S1
    v_chip_bytes = next_pow2(counts["v1_bytes"], 1024 * 1024)   # 1 MB or 2 MB V1
    p_chip_bytes = 512 * 1024                                    # 512 KB P1 (68000 code/rodata)
    m_chip_bytes = 128 * 1024                                    # 128 KB M1 (Z80 sound driver)

    # Worst-case scanline sprite-strip accounting (16px-wide hardware sprite strips)
    # Confirmed Layout: 224x224 playfield (14 background strips) + 96x224 FIX Side-HUD (0 sprite strips!)
    scenarios = {
        "phase1_1982_replica_worst_scanline": {
            "playfield_terrain_strips": 14,   # 14 columns x 16px = 224px playfield
            "side_hud_strips": 0,             # 100% on S-ROM FIX layer (x=224..319)
            "player_taizo": 2,                # 32x32 sprite = 2 strips
            "pump_hose_and_harpoon": 4,       # up to 64px reach = 4 strips
            "enemies_8_inflated_or_walking": 8 * 3,  # even if 8 enemies share 1 scanline @ 48x48 = 24 strips
            "falling_rocks_4": 4 * 1,         # 4 rocks @ 16x16 = 4 strips
            "fygar_fire_breath": 3,           # 48px flame = 3 strips
            "bonus_veggie_and_score_pop": 3,
        },
        "phase2_coop_gameplay_worst_scanline": {
            "playfield_terrain_strips": 14,
            "side_hud_strips": 0,
            "players_2p_plus_tool_attach": 2 * (2 + 2),  # 8 strips
            "tethers_and_tri_pump": 6,
            "enemies_6_inflated_48x48": 6 * 3,           # 18 strips
            "rocks_and_hazards_4": 4 * 1,
            "projectiles_traps_blast_fx": 8,             # 48x48 blast (3) + projectiles/pickups (5)
        },
        "phase2_king_fygar_or_iron_mole_boss_scanline": {
            "playfield_terrain_strips": 14,
            "side_hud_strips": 0,
            "boss_96x64_body_plus_weakpoint": 6 + 2,     # 96px = 6 strips + 32x32 sac/module = 8 strips
            "players_2p_plus_weapons": 8,
            "summoned_minions_4": 4 * 3,                 # 12 strips
            "boss_fire_or_hazard_telegraph": 6,
            "blast_and_hit_fx": 6,
        },
    }
    for sc_val in scenarios.values():
        sc_val["total_strips_on_scanline"] = sum(sc_val.values())

    max_scanline_strips = max(s["total_strips_on_scanline"] for s in scenarios.values())

    # Static 68000 Work RAM budget (64 KB total at $100000-$10FFFF; ~$61 KB user RAM below BIOS $10F300)
    ram_budget_bytes = {
        "world_grid_28x28_occupancy_and_flags": 28 * 28 * 4,    # 3,136 B
        "actor_table_players_enemies_rocks_boss": 64 * 128,     # 8,192 B
        "combat_projectiles_traps_fx_pools": 48 * 64,           # 3,072 B
        "shadow_scb1_scb2_scb3_scb4_vram_staging": 16 * 1024,   # 16,384 B
        "fix_hud_dirty_buffer_and_score_state": 2 * 1024,       # 2,048 B
        "audio_cmd_ring_and_stem_mix_state": 512,               # 512 B
        "stack_and_system_headroom": 8 * 1024,                  # 8,192 B
    }
    total_work_ram = sum(ram_budget_bytes.values())

    report = {
        "hardware_limits": {
            "work_ram_user_bytes": 62208,      # $100000..$10F2FF
            "palettes_per_bank": 256,
            "fix_palettes": 16,
            "srom_tiles_no_bankswitch": 4096,
            "crom_tiles_1mb_pair": 16384,
            "total_sprites_max": 381,
            "sprites_per_scanline_hw_max": 96,
            "sprites_per_scanline_eng_ceiling": 84,
        },
        "rom_regions": {
            "P1_68k_prog": {"chip_bytes": p_chip_bytes},
            "M1_z80_audio": {"chip_bytes": m_chip_bytes},
            "S1_fix_8x8": {
                "used_tiles": counts["s_tiles_8x8"],
                "used_bytes": counts["s1_bytes"],
                "chip_bytes": s_chip_bytes,
                "utilization_pct": round(counts["s_tiles_8x8"] * 100.0 / 4096, 2),
            },
            "C1_C2_sprites_16x16": {
                "used_tiles": counts["c_tiles_16x16"],
                "c1_used_bytes": counts["c1_bytes"],
                "c2_used_bytes": counts["c2_bytes"],
                "c1_chip_bytes": c_chip_bytes,
                "c2_chip_bytes": c_chip_bytes,
                "utilization_pct": round(counts["c_tiles_16x16"] * 100.0 / (c_chip_bytes // 64), 2),
            },
            "V1_ym2610_adpcm": {
                "used_bytes": counts["v1_bytes"],
                "chip_bytes": v_chip_bytes,
                "cues": counts["runtime_audio_cues"],
            },
        },
        "work_ram": {
            "breakdown_bytes": ram_budget_bytes,
            "total_estimated_bytes": total_work_ram,
            "utilization_pct": round(total_work_ram * 100.0 / 62208, 2),
        },
        "palettes": {
            "fix_slots_used": 10,
            "fix_dynamic_slots_reserved": 6,
            "sprite_and_scene_slots_used": counts["active_palettes"],
            "total_limit": 256,
        },
        "scanline_sprite_strips": {
            "scenarios": scenarios,
            "worst_case_strips": max_scanline_strips,
            "within_eng_ceiling_84": max_scanline_strips <= 84,
            "within_hw_limit_96": max_scanline_strips <= 96,
        },
    }
    (ROOT / "build").mkdir(parents=True, exist_ok=True)
    (ROOT / "build" / "budget_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
