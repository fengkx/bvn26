#!/usr/bin/env python3
"""Bind the staged Web release preset to the template whose hash is recorded."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SECTION_HEADER = re.compile(r"^\[([^\]]+)\]$")
NAME_ENTRY = re.compile(r'^\s*name\s*=\s*"Web"\s*$')
TEMPLATE_ENTRY = re.compile(r"^\s*custom_template/release\s*=")


def bind_template(preset_path: Path, template_path: Path) -> str:
    template_path = template_path.resolve(strict=True)
    if not template_path.is_file():
        raise ValueError(f"Web export template is not a file: {template_path}")
    if "\n" in str(template_path) or "\r" in str(template_path):
        raise ValueError("Web export template path cannot contain a newline")

    lines = preset_path.read_text(encoding="utf-8").splitlines()
    headers: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = SECTION_HEADER.fullmatch(line.strip())
        if match:
            headers.append((index, match.group(1)))

    web_presets: list[tuple[int, int, str]] = []
    for position, (start, section) in enumerate(headers):
        if not re.fullmatch(r"preset\.\d+", section):
            continue
        end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
        if any(NAME_ENTRY.fullmatch(line) for line in lines[start + 1 : end]):
            web_presets.append((start, end, section))
    if len(web_presets) != 1:
        raise ValueError(f"expected one Web export preset in {preset_path}, found {len(web_presets)}")

    _preset_start, _preset_end, preset_section = web_presets[0]
    options_section = f"{preset_section}.options"
    section_bounds = [
        (start, headers[position + 1][0] if position + 1 < len(headers) else len(lines))
        for position, (start, section) in enumerate(headers)
        if section == options_section
    ]
    if len(section_bounds) != 1:
        raise ValueError(f"missing unique [{options_section}] section in {preset_path}")

    start, end = section_bounds[0]
    entries = [index for index in range(start + 1, end) if TEMPLATE_ENTRY.match(lines[index])]
    if len(entries) != 1:
        raise ValueError(
            f"expected one custom_template/release entry in [{options_section}], found {len(entries)}"
        )

    template_hash = hashlib.sha256(template_path.read_bytes()).hexdigest()
    lines[entries[0]] = f"custom_template/release={json.dumps(str(template_path), ensure_ascii=False)}"
    preset_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return template_hash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    args = parser.parse_args()
    try:
        template_hash = bind_template(args.preset, args.template)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"WEB_EXPORT_TEMPLATE_BOUND path={args.template.resolve()} sha256={template_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
