"""Create a pinned, reproducible JPEXS XML workspace for SWF conversion."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


EXPECTED_GENERATOR = "JPEXS Free Flash Decompiler v.26.2.1"
EXPECTED_XML_EXPORT = (3, 2)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_swf(ffdec_jar: Path, swf_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "export-report.json"
    if report_path.is_file():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        for file_record in previous.get("files", []):
            generated_path = (output_dir / file_record["path"]).resolve()
            generated_path.relative_to(output_dir.resolve())
            generated_path.unlink(missing_ok=True)
        report_path.unlink(missing_ok=True)
        for directory in sorted(
            (path for path in output_dir.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
    unexpected_files = [path for path in output_dir.rglob("*") if path.is_file()]
    if unexpected_files:
        raise RuntimeError(f"Output directory contains unmanaged files: {unexpected_files[0]}")
    xml_path = output_dir / f"{swf_path.stem}.xml"
    command = [
        "java",
        "-Djava.awt.headless=true",
        "-jar",
        str(ffdec_jar.resolve()),
        "-config",
        "parallelSpeedUp=false",
        "-swf2xml",
        "-external",
        "image,definesound",
        str(swf_path.resolve()),
        str(xml_path.resolve()),
    ]
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    subprocess.run(
        [
            "java",
            "-Djava.awt.headless=true",
            "-jar",
            str(ffdec_jar.resolve()),
            "-config",
            "parallelSpeedUp=false",
            "-format",
            "image:png",
            "-export",
            "image",
            str((output_dir / "images-png").resolve()),
            str(swf_path.resolve()),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    root = ET.parse(xml_path).getroot()
    generator = root.attrib.get("_generator")
    if generator != EXPECTED_GENERATOR:
        raise RuntimeError(f"Unexpected JPEXS generator: {generator!r}")
    xml_export = (
        int(root.attrib["_xmlExportMajor"]),
        int(root.attrib["_xmlExportMinor"]),
    )
    if xml_export != EXPECTED_XML_EXPORT:
        raise RuntimeError(f"Unexpected JPEXS XML export version: {xml_export}")

    external_files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    files = [
        {
            "path": path.relative_to(output_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in external_files
    ]
    report = {
        "format": "bvn26-jpexs-workspace-v1",
        "generator": generator,
        "xml_export": {
            "major": xml_export[0],
            "minor": xml_export[1],
        },
        "source": {
            "path": swf_path.as_posix(),
            "bytes": swf_path.stat().st_size,
            "sha256": file_sha256(swf_path),
        },
        "files": files,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffdec-jar", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("swf", type=Path)
    args = parser.parse_args()
    report = export_swf(args.ffdec_jar, args.swf, args.output_dir)
    print(json.dumps(report["source"]))


if __name__ == "__main__":
    main()
