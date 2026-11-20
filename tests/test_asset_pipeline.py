"""Unit and integration tests for the Neo Geo MVS asset & audio pipeline."""

from __future__ import annotations

import io
import math
import struct
import sys
import tempfile
import unittest
import wave
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from assets.neogeo_encode import (  # noqa: E402
    NEOGEO_REF_BLACK,
    build_palette_16,
    decode_c_tile_16x16,
    decode_s_tile_8x8,
    decode_ym2610_adpcm_a,
    encode_c_tile_16x16,
    encode_s_tile_8x8,
    encode_ym2610_adpcm_a,
    neogeo_word_to_rgb,
    partition_scene_palettes,
    rgb_to_neogeo_word,
)
from assets.pack_pipeline import (  # noqa: E402
    GENERATED_DIR,
    PackReader,
    build_all_assets,
    load_catalog,
    run_asset_check,
    run_budgets,
)
from assets.png_rgba import RGBAImage, decode_png_bytes, encode_indexed_png, encode_rgba_png  # noqa: E402


class TestNeoGeoAssetEncoders(unittest.TestCase):
    def test_png_rgba_and_indexed_roundtrip(self) -> None:
        img = RGBAImage(17, 13)
        for y in range(13):
            for x in range(17):
                off = (y * 17 + x) * 4
                img.data[off : off + 4] = bytes(
                    ((x * 13) & 0xFF, (y * 19) & 0xFF, ((x + y) * 7) & 0xFF, 0 if (x == 0 or y == 0) else 255)
                )
        raw_png = encode_rgba_png(img)
        dec = decode_png_bytes(raw_png)
        self.assertEqual((dec.width, dec.height), (17, 13))
        self.assertEqual(bytes(dec.data), bytes(img.data))

        pal = [(0, 0, 0), (250, 40, 40), (40, 240, 100), (60, 120, 250)]
        indices = bytearray((x + y) % 4 for y in range(8) for x in range(8))
        idx_png = encode_indexed_png(8, 8, indices, pal)
        dec_idx = decode_png_bytes(idx_png)
        self.assertEqual(dec_idx.data[3], 0)  # index 0 transparent
        self.assertEqual(tuple(dec_idx.data[4:8]), (250, 40, 40, 255))

    def test_neogeo_palette_word_encoding(self) -> None:
        pal16 = build_palette_16([(255, 255, 255), (0, 0, 0), (248, 128, 16)])
        self.assertEqual(pal16[0], NEOGEO_REF_BLACK)
        self.assertEqual(pal16[0], 0x8000)
        w_white = rgb_to_neogeo_word(255, 255, 255)
        # 31 in 5-bit + dark=0 -> R0/G0/B0=1, R4..1/G4..1/B4..1=0xF -> 0x7FFF
        self.assertEqual(w_white, 0x7FFF)
        r, g, b = neogeo_word_to_rgb(pal16[3])
        self.assertLessEqual(abs(r - 248), 8)
        self.assertLessEqual(abs(g - 128), 8)
        self.assertLessEqual(abs(b - 16), 8)

    def test_crom_16x16_hardware_bit_order(self) -> None:
        # Place distinct pens at (x=8, y=0) [right half leftmost] and (x=0, y=0) [left half leftmost]
        tile = bytearray(256)
        tile[0 * 16 + 8] = 0b1010  # pen 10 -> bp0=0, bp1=1, bp2=0, bp3=1 (LSB bit 0 of row 0 in right half)
        tile[0 * 16 + 0] = 0b0101  # pen 5  -> bp0=1, bp1=0, bp2=1, bp3=0 (LSB bit 0 of row 0 in left half)
        tile[15 * 16 + 15] = 0b1111  # pen 15 -> MSB bit 7 of row 15 in right half
        c1, c2 = encode_c_tile_16x16(tile)
        self.assertEqual(len(c1), 64)
        self.assertEqual(len(c2), 64)
        # Right half row 0 is bytes 0,1: pen 10 at x=8 -> c1[0]=0, c1[1]=1, c2[0]=0, c2[1]=1
        self.assertEqual((c1[0] & 1, c1[1] & 1, c2[0] & 1, c2[1] & 1), (0, 1, 0, 1))
        # Left half row 0 is bytes 32,33: pen 5 at x=0 -> c1[32]=1, c1[33]=0, c2[32]=1, c2[33]=0
        self.assertEqual((c1[32] & 1, c1[33] & 1, c2[32] & 1, c2[33] & 1), (1, 0, 1, 0))
        # Right half row 15 x=15 -> bit 7 of bytes 30,31
        self.assertEqual((c1[30] >> 7, c1[31] >> 7, c2[30] >> 7, c2[31] >> 7), (1, 1, 1, 1))
        self.assertEqual(decode_c_tile_16x16(c1, c2), tile)

    def test_srom_8x8_column_pair_order(self) -> None:
        tile = bytearray((x + y * 3) % 16 for y in range(8) for x in range(8))
        # Specific check: byte 0 covers row y=0, columns x=4 (low nibble) and x=5 (high nibble)
        tile[0 * 8 + 4] = 0x03
        tile[0 * 8 + 5] = 0x0C
        s_bytes = encode_s_tile_8x8(tile)
        self.assertEqual(len(s_bytes), 32)
        self.assertEqual(s_bytes[0], 0xC3)
        self.assertEqual(decode_s_tile_8x8(s_bytes), tile)

    def test_scene_palette_partitioning(self) -> None:
        # Two 16x16 tiles with 12 distinct colors each (24 total colors across scene)
        tile_a = bytearray()
        tile_b = bytearray()
        for i in range(256):
            ca = i % 12
            cb = 12 + (i % 12)
            tile_a.extend((20 + ca * 9, 40 + ca * 5, 220 - ca * 7, 255))
            tile_b.extend((20 + cb * 9, 40 + cb * 5, 220 - cb * 7, 255))
        sub_pals, assignments = partition_scene_palettes([tile_a, tile_b], max_palettes=4)
        self.assertEqual(len(sub_pals), 2)
        self.assertEqual(assignments, [0, 1])
        self.assertTrue(all(len(p) <= 15 for p in sub_pals))

    def test_ym2610_adpcm_a_alignment_and_waveform_correlation(self) -> None:
        samples = [int(14000 * math.sin(2.0 * math.pi * 440.0 * i / 18500.0)) for i in range(1200)]
        adpcm = encode_ym2610_adpcm_a(samples, pad_align=256)
        self.assertEqual(len(adpcm) % 256, 0)
        decoded = decode_ym2610_adpcm_a(adpcm)[: len(samples)]
        # Verify positive dot-product correlation with source 440 Hz sine wave
        dot = sum(a * b for a, b in zip(samples[100:], decoded[100:]))
        self.assertGreater(dot, 0)

    def test_full_catalog_and_real_pack_zip_ingestion(self) -> None:
        # 1. Verify full generated catalog check & budgets
        if not (GENERATED_DIR / "asset_manifest.json").is_file():
            build_all_assets(None)
        passed, check_rep = run_asset_check()
        self.assertTrue(passed, msg=f"asset-check errors: {check_rep['errors']}")
        self.assertEqual(check_rep["c_tiles_verified"], 8203)
        self.assertEqual(check_rep["occupancy_tiles_verified"], 336)
        self.assertEqual(check_rep["intentional_blank_frames"], 22)

        budgets = run_budgets()
        self.assertTrue(budgets["scanline_sprite_strips"]["within_eng_ceiling_84"])

        # 2. Build a synthetic zip matching real pack paths for one sprite family + one WAV cue
        _val, families, audio_cat = load_catalog()
        pooka = next(f for f in families if f["id"] == "enm_pooka")
        max_x = max(fr[2][0] + fr[2][2] for fr in pooka["frames"])
        max_y = max(fr[2][1] + fr[2][3] for fr in pooka["frames"])
        atlas = RGBAImage(max_x + 2, max_y + 2)
        pr, pg, pb = pooka["pal"][0]
        for _fname, (_fw, _fh), (ax, ay, aw, ah), _piv in pooka["frames"]:
            for yy in range(ay + 2, ay + ah - 2):
                for xx in range(ax + 2, ax + aw - 2):
                    off = (yy * atlas.width + xx) * 4
                    atlas.data[off : off + 4] = bytes((pr, pg, pb, 255))

        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(i * 0.1))) for i in range(600)))

        with tempfile.TemporaryDirectory() as tmpd:
            zpath = Path(tmpd) / "Super-Dig-Dug-Complete-Asset-Pack.zip"
            with zipfile.ZipFile(zpath, "w") as zf:
                zf.writestr(f"{pooka['dir']}/atlas.png", encode_rgba_png(atlas))
                zf.writestr(audio_cat["sfx"][0], wav_buf.getvalue())

            reader = PackReader(zpath)
            try:
                self.assertEqual(reader.mode, "real_pack_zip")
                self.assertIsNotNone(reader.read_bytes(f"{pooka['dir']}/atlas.png"))
                self.assertIsNotNone(reader.read_bytes(audio_cat["sfx"][0]))
            finally:
                reader.close()


if __name__ == "__main__":
    unittest.main()
