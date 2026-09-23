"""Build a broad, redistributable CJK fallback for dynamic online user text."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from fontTools import subset, version as fonttools_version
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIRECTORY = ROOT / "godot/generated/main/fonts"
OUTPUT_FONT = OUTPUT_DIRECTORY / "user-cjk.woff2"
OUTPUT_LICENSE = OUTPUT_DIRECTORY / "FONT-LICENSE.txt"
OUTPUT_METADATA = OUTPUT_DIRECTORY / "font.json"
SOURCE_FAMILY = "Sarasa UI SC"
DERIVATIVE_FAMILY = "BVN Online CJK"
LICENSE_MARKER = "SIL Open Font License, Version 1.1"
LICENSE_URL = "https://github.com/be5invis/Sarasa-Gothic/blob/master/LICENSE"

# Include the source face's available glyphs in these useful text ranges.
# The output intentionally does not claim all Unicode or every CJK extension.
CODEPOINT_RANGES = (
    ("Latin and common accents", 0x0020, 0x024F),
    ("General punctuation", 0x2000, 0x206F),
    ("CJK radicals supplement", 0x2E80, 0x2EFF),
    ("Kangxi radicals", 0x2F00, 0x2FDF),
    ("CJK punctuation", 0x3000, 0x303F),
    ("Japanese kana", 0x3040, 0x30FF),
    ("Bopomofo", 0x3100, 0x312F),
    ("Bopomofo extensions", 0x31A0, 0x31BF),
    ("CJK strokes", 0x31C0, 0x31EF),
    ("CJK Extension A", 0x3400, 0x4DBF),
    ("CJK Unified Ideographs", 0x4E00, 0x9FFF),
    ("CJK compatibility ideographs", 0xF900, 0xFAFF),
    ("CJK Extension B source glyphs", 0x20000, 0x2A6DF),
    ("Halfwidth and fullwidth forms", 0xFF00, 0xFFEF),
)

SAMPLE_STRINGS = ("输入角色昵称", "繁體姓名", "龘璟姍𠮷㐀")
RENAME_NAME_IDS = {1, 3, 4, 6, 16}


def _encoded_name(value: str, record) -> bytes:
    return value.encode(record.getEncoding())


def _coverage_metadata(codepoints: set[int]) -> list[dict[str, object]]:
    return [
        {
            "name": name,
            "start": f"U+{start:04X}",
            "end": f"U+{end:04X}",
            "included_codepoints": sum(start <= codepoint <= end for codepoint in codepoints),
        }
        for name, start, end in CODEPOINT_RANGES
    ]


def build(font_path: Path, font_number: int, license_path: Path) -> dict[str, object]:
    license_text = license_path.read_text(encoding="utf-8")
    if LICENSE_MARKER not in license_text:
        raise ValueError("input license is not the expected SIL OFL 1.1 license")

    font = TTFont(font_path, fontNumber=font_number)
    source_family = font["name"].getDebugName(1)
    if source_family != SOURCE_FAMILY:
        raise ValueError(f"font face {font_number} is {source_family!r}, expected {SOURCE_FAMILY!r}")

    source_cmap = font.getBestCmap()
    if source_cmap is None:
        raise ValueError("selected source face has no Unicode cmap")
    selected_codepoints = {
        codepoint
        for codepoint in source_cmap
        if any(start <= codepoint <= end for _name, start, end in CODEPOINT_RANGES)
    }
    missing_samples = sorted(
        {ord(character) for sample in SAMPLE_STRINGS for character in sample}
        - selected_codepoints
    )
    if missing_samples:
        rendered = ", ".join(f"U+{codepoint:04X}" for codepoint in missing_samples)
        raise ValueError(f"source face does not cover required dynamic-text samples: {rendered}")

    options = subset.Options()
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14, 16, 17]
    options.name_legacy = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=selected_codepoints)
    subsetter.subset(font)

    for record in font["name"].names:
        if record.nameID in RENAME_NAME_IDS:
            name = "BVNOnlineCJK" if record.nameID == 6 else DERIVATIVE_FAMILY
            record.string = _encoded_name(name, record)

    # Keep the output stable across repeated builds from the same pinned input.
    font.recalcTimestamp = False
    font.flavor = "woff2"
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    font.save(OUTPUT_FONT)

    generated_font = TTFont(OUTPUT_FONT)
    generated_cmap = generated_font.getBestCmap()
    if generated_cmap is None:
        raise ValueError("generated WOFF2 has no Unicode cmap")
    generated_codepoints = set(generated_cmap)
    if generated_codepoints != selected_codepoints:
        raise ValueError("generated WOFF2 coverage differs from the selected source cmap ranges")
    for name_id in (1, 4, 6, 16):
        if any(
            record.nameID == name_id and "Sarasa" in record.toUnicode()
            for record in generated_font["name"].names
        ):
            raise ValueError("generated primary font names must not retain the Sarasa reserved name")

    if license_path.resolve() != OUTPUT_LICENSE.resolve():
        shutil.copyfile(license_path, OUTPUT_LICENSE)

    font_bytes = OUTPUT_FONT.read_bytes()
    metadata: dict[str, object] = {
        "source_family": source_family,
        "source_style": font["name"].getDebugName(2) or "Regular",
        "source_font_number": font_number,
        "source_sha256": hashlib.sha256(font_path.read_bytes()).hexdigest(),
        "source_cmap_codepoint_count": len(source_cmap),
        "font_family": DERIVATIVE_FAMILY,
        "format": "WOFF2",
        "font_file": OUTPUT_FONT.name,
        "font_bytes": len(font_bytes),
        "font_sha256": hashlib.sha256(font_bytes).hexdigest(),
        "included_codepoint_count": len(generated_codepoints),
        "included_glyph_count": generated_font["maxp"].numGlyphs,
        "codepoint_ranges": _coverage_metadata(generated_codepoints),
        "coverage_characters": "".join(chr(codepoint) for codepoint in sorted(generated_codepoints)),
        "coverage_samples": list(SAMPLE_STRINGS),
        "license_file": OUTPUT_LICENSE.name,
        "license_url": LICENSE_URL,
        "fonttools_version": fonttools_version,
        "coverage_limit": (
            "Includes only codepoints present in this Sarasa UI SC Regular source cmap and "
            "inside the listed ranges. It is not full Unicode or complete coverage of every "
            "CJK extension; unsupported input can still render as a missing-glyph box."
        ),
    }
    OUTPUT_METADATA.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, required=True, help="Sarasa Regular TTC source file")
    parser.add_argument("--font-number", type=int, default=7, help="Sarasa UI SC Regular collection index")
    parser.add_argument("--license", type=Path, required=True, help="source OFL 1.1 license file")
    args = parser.parse_args()
    metadata = build(args.font, args.font_number, args.license)
    print(
        "ONLINE_USER_FONT_BUILT "
        f"format=WOFF2 codepoints={metadata['included_codepoint_count']} "
        f"bytes={metadata['font_bytes']} family={metadata['font_family']}"
    )


if __name__ == "__main__":
    main()
