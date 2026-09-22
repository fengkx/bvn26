#!/usr/bin/env python3
"""Fail-closed preflight for an instrumented Flash freeze build."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import unquote, urlparse


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path)
    parser.add_argument("--ffdec", type=Path, required=True)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--reject-run-id", action="append", default=[])
    args = parser.parse_args()
    metadata = json.loads((args.build / "build.json").read_text())
    if metadata.get("run_id") != args.expected_run_id:
        raise SystemExit(f"metadata run_id mismatch: {metadata.get('run_id')!r}")
    main_swf = args.build / "game/main.swf"
    if not main_swf.is_file():
        raise SystemExit(f"missing final SWF: {main_swf}")
    expected_sha = metadata.get("outputs_sha256", {}).get("game/main.swf")
    actual_sha = sha256(main_swf)
    if expected_sha != actual_sha:
        raise SystemExit(f"final main SHA mismatch: metadata={expected_sha!r} actual={actual_sha}")
    with tempfile.TemporaryDirectory(prefix="freeze-build-preflight-") as temp:
        export = Path(temp) / "scripts"
        subprocess.run(
            ["java", "-Djava.awt.headless=true", "-jar", str(args.ffdec),
             "-export", "script", str(export), str(main_swf)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        entry = export / "scripts/frame_1/DoAction.as"
        bootstrap = export / "scripts/frame_10/DoAction.as"
        if not entry.is_file():
            raise SystemExit(f"missing exported entry script: {entry}")
        if not bootstrap.is_file():
            raise SystemExit(f"missing exported bootstrap script: {bootstrap}")
        source = entry.read_text(errors="replace")
        bootstrap_source = bootstrap.read_text(errors="replace")
    match = re.search(r'_root\.aiRun\s*=\s*["\']([^"\']+)', source)
    if match is None:
        raise SystemExit("final SWF has no aiRun assignment")
    actual_run_id = match.group(1)
    if actual_run_id != args.expected_run_id:
        raise SystemExit(f"final SWF aiRun mismatch: {actual_run_id!r}")
    for rejected in args.reject_run_id:
        if rejected in source:
            raise SystemExit(f"rejected stale run id remains in final SWF: {rejected}")
        if rejected in bootstrap_source:
            raise SystemExit(f"rejected stale run id remains in final SWF frame_10: {rejected}")
    build_root = str(args.build.resolve())
    required_paths = [
        f"{build_root}/case.txt",
        f"{build_root}/game/fighter/",
        f"{build_root}/game/music/",
    ]
    missing_paths = [path for path in required_paths if path not in bootstrap_source]
    if missing_paths:
        raise SystemExit("final SWF frame_10 has stale or missing build paths: " + ", ".join(missing_paths))
    case_path = (args.build / "case.txt").resolve()
    if not case_path.is_file():
        raise SystemExit(f"missing current fixture: {case_path}")
    case_hash = sha256(case_path)
    declared_case_hash = metadata.get("outputs_sha256", {}).get("case.txt")
    if declared_case_hash != case_hash:
        raise SystemExit(
            f"current fixture SHA mismatch: metadata={declared_case_hash!r} actual={case_hash}"
        )
    fixture_match = re.search(
        r"aiFixtureLoader\.load\(\s*[\"'](file:///[^\"']+/case\.txt)[\"']\s*\)",
        bootstrap_source,
    )
    if fixture_match is None:
        raise SystemExit("final SWF frame_10 has no literal aiFixtureLoader case URL")
    fixture_url = fixture_match.group(1)
    declared_fixture_url = metadata.get("fixture_url")
    if declared_fixture_url is not None and declared_fixture_url != fixture_url:
        raise SystemExit(
            f"metadata fixture URL mismatch: metadata={declared_fixture_url!r} embedded={fixture_url!r}"
        )
    parsed_fixture = urlparse(fixture_url)
    if parsed_fixture.scheme != "file" or parsed_fixture.netloc:
        raise SystemExit(f"unsupported fixture URL: {fixture_url!r}")
    embedded_case = Path(unquote(parsed_fixture.path)).resolve()
    if embedded_case != case_path:
        raise SystemExit(
            f"final SWF fixture URL mismatch: embedded={embedded_case} current={case_path}"
        )
    try:
        fixture_text = case_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"cannot read current fixture: {case_path}: {exc}")
    run_match = re.search(r"(?:^|&)run_id=([^&]+)", fixture_text)
    if run_match is None or unquote(run_match.group(1)) != args.expected_run_id:
        raise SystemExit(
            "current fixture run_id mismatch: "
            f"expected={args.expected_run_id!r} fixture={run_match.group(1) if run_match else None!r}"
        )
    print(json.dumps({
        "status": "passed",
        "metadata_run_id": metadata["run_id"],
        "swf_aiRun": actual_run_id,
        "frame10_paths": "validated",
        "fixture_url": fixture_url,
        "fixture_path": str(case_path),
        "fixture_sha256": case_hash,
        "main_sha256": actual_sha,
        "source": str(main_swf),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
