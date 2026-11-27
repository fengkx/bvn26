"""Regression tests for restoring JPEG3 transparency after XML round-trips."""

from __future__ import annotations

import binascii
import json
import math
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_selection_portraits import displayed_character_ids, jpeg3_ids_for_symbols  # noqa: E402


def png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)


def write_rgba_png(path: Path, pixels: list[tuple[int, int, int, int]]) -> None:
    width = len(pixels)
    header = struct.pack(">IIBBBBB", width, 1, 8, 6, 0, 0, 0)
    row = b"\0" + bytes(channel for pixel in pixels for channel in pixel)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(row))
        + png_chunk(b"IEND", b"")
    )


def read_rgba_row(path: Path) -> list[tuple[int, int, int, int]]:
    data = path.read_bytes()
    offset = 8
    compressed = bytearray()
    while offset < len(data):
        size = struct.unpack(">I", data[offset : offset + 4])[0]
        tag = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + size]
        offset += size + 12
        if tag == b"IDAT":
            compressed.extend(chunk)
    row = zlib.decompress(compressed)[1:]
    return [tuple(row[index : index + 4]) for index in range(0, len(row), 4)]


def read_rgba_png(path: Path) -> tuple[int, int, list[list[tuple[int, int, int, int]]]]:
    data = path.read_bytes()
    offset = 8
    compressed = bytearray()
    width = height = 0
    while offset < len(data):
        size = struct.unpack(">I", data[offset : offset + 4])[0]
        tag = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + size]
        offset += size + 12
        if tag == b"IHDR":
            width, height, depth, color_type, *_ = struct.unpack(">IIBBBBB", chunk)
            if depth != 8 or color_type != 6:
                raise AssertionError("Expected an 8-bit RGBA PNG")
        elif tag == b"IDAT":
            compressed.extend(chunk)
    raw = zlib.decompress(compressed)
    stride = width * 4
    previous = bytearray(stride)
    rows = []
    position = 0
    for _ in range(height):
        filter_type = raw[position]
        position += 1
        source = raw[position : position + stride]
        position += stride
        row = bytearray(stride)
        for index, value in enumerate(source):
            left = row[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 1:
                value += left
            elif filter_type == 2:
                value += above
            elif filter_type == 3:
                value += (left + above) // 2
            elif filter_type == 4:
                predictor = left + above - upper_left
                distance_left = abs(predictor - left)
                distance_above = abs(predictor - above)
                distance_upper_left = abs(predictor - upper_left)
                value += (
                    left if distance_left <= distance_above and distance_left <= distance_upper_left
                    else above if distance_above <= distance_upper_left
                    else upper_left
                )
            elif filter_type != 0:
                raise AssertionError(f"Unsupported PNG filter: {filter_type}")
            row[index] = value & 0xFF
        rows.append([tuple(row[index : index + 4]) for index in range(0, stride, 4)])
        previous = row
    return width, height, rows


class SelectionPortraitAlphaTests(unittest.TestCase):
    def test_resolves_jpeg3_images_from_frozen_sprite_placements(self):
        tags = ET.fromstring(
            """<tags>
              <item type="DefineBitsJPEG3Tag" characterID="30" />
              <item type="DefineBitsJPEG2Tag" characterID="31" />
              <item type="PlaceObject2Tag" depth="2" characterId="30" />
              <item type="DefineShapeTag" shapeId="20">
                <shapes><fillStyles><fillStyles>
                  <item bitmapId="30" /><item bitmapId="31" />
                </fillStyles></fillStyles></shapes>
              </item>
              <item type="DefineSpriteTag" spriteId="1346"><subTags>
                <item type="PlaceObject2Tag" depth="1" characterId="20" />
                <item type="ShowFrameTag" />
                <item type="ShowFrameTag" />
              </subTags></item>
            </tags>"""
        )
        sprite = next(tag for tag in tags if tag.get("spriteId") == "1346")

        symbols = displayed_character_ids(sprite, 2)
        self.assertEqual(symbols, {"20"})
        self.assertEqual(jpeg3_ids_for_symbols(tags, symbols), {"30"})

    def test_generated_naruto_portrait_has_transparent_cutout_and_alpha_edges(self):
        path = ROOT / "godot/generated/main/character_selection/portrait-0-1.png"
        width, height, pixels = read_rgba_png(path)
        alphas = [pixel[3] for row in pixels for pixel in row]
        self.assertGreater(alphas.count(0), 0)
        self.assertTrue(any(0 < alpha < 255 for alpha in alphas))
        self.assertGreater(alphas.count(255), 0)
        self.assertEqual(pixels[120][250][3], 0)
        self.assertEqual((width, height), (639, 869))

        portraits = json.loads(
            (ROOT / "godot/generated/main/character_selection/portraits.json").read_text()
        )
        portrait = portraits["鸣人"]
        self.assertEqual(portrait["raster_scale"], 2)
        bounds = portrait["bounds_twips"]
        self.assertEqual(width / portrait["raster_scale"], (bounds[2] - bounds[0]) / 20)
        self.assertEqual(height / portrait["raster_scale"], (bounds[3] - bounds[1]) / 20)

    def test_all_roster_frames_use_high_resolution_raster_at_source_logical_size(self):
        directory = ROOT / "godot/generated/main/character_selection"
        portraits = json.loads((directory / "portraits.json").read_text())
        fighters = json.loads((directory / "available.json").read_text())["fighters"]
        self.assertEqual(set(portraits), set(fighters))
        for name, portrait in portraits.items():
            self.assertEqual(portrait["raster_scale"], 2, name)
            self.assertEqual(len(portrait["textures"]), 5, name)
            bounds = portrait["bounds_twips"]
            expected_size = tuple(
                math.ceil((bounds[end] - bounds[start]) / 20 * 2)
                for start, end in ((0, 2), (1, 3))
            )
            for texture in portrait["textures"]:
                data = (directory / texture).read_bytes()
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"), texture)
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual((width, height), expected_size, texture)

    @unittest.skipUnless(shutil.which("java"), "Java is required for portrait raster import")
    def test_alpha_merge_preserves_transparent_black_and_dark_opaque_pixels(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            # The transparent pixel is black RGB; the final opaque pixel is a
            # very dark color. Neither may be inferred from RGB values.
            write_rgba_png(directory / "rgb.png", [(0, 0, 0, 255), (24, 25, 26, 255), (4, 5, 6, 255)])
            write_rgba_png(directory / "alpha.png", [(0, 0, 0, 0), (0, 0, 0, 127), (0, 0, 0, 255)])
            output = directory / "merged.png"
            subprocess.run(
                [
                    shutil.which("java"),
                    "-Djava.awt.headless=true",
                    str(ROOT / "tools/importer/MergeJpeg3Alpha.java"),
                    str(directory / "rgb.png"),
                    str(directory / "alpha.png"),
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                read_rgba_row(output),
                [(0, 0, 0, 0), (24, 25, 26, 127), (4, 5, 6, 255)],
            )

            write_rgba_png(directory / "opaque-alpha.png", [(0, 0, 0, 255)] * 3)
            opaque_output = directory / "opaque.png"
            subprocess.run(
                [
                    shutil.which("java"),
                    "-Djava.awt.headless=true",
                    str(ROOT / "tools/importer/MergeJpeg3Alpha.java"),
                    str(directory / "rgb.png"),
                    str(directory / "opaque-alpha.png"),
                    str(opaque_output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                read_rgba_row(opaque_output),
                [(0, 0, 0, 255), (24, 25, 26, 255), (4, 5, 6, 255)],
            )


if __name__ == "__main__":
    unittest.main()
