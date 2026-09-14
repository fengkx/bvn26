#!/usr/bin/env python3
"""Create non-circular embedded and post-export Web diagnostics metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METADATA_RELATIVE_PATH = Path("generated/build_metadata.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: Path, *, exclude: set[Path] | None = None) -> str:
    excluded = exclude or set()
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if ".godot" in relative.parts or relative in excluded:
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def prepare_metadata(
    project_root: Path,
    *,
    git_commit: str,
    dirty_paths: list[str],
    template_sha256: str,
    engine_version: str,
    built_at: str | None = None,
) -> dict[str, Any]:
    metadata_path = project_root / METADATA_RELATIVE_PATH
    source_tree_sha256 = sha256_tree(
        project_root,
        exclude={METADATA_RELATIVE_PATH},
    )
    resource_version = sha256_tree(
        project_root / "generated",
        exclude={Path("build_metadata.json")},
    )
    identity = {
        "gitCommit": git_commit,
        "dirtyPaths": sorted(set(dirty_paths)),
        "sourceTreeSha256": source_tree_sha256,
        "resourceVersion": resource_version,
        "templateSha256": template_sha256,
        "engineVersion": engine_version,
    }
    build_id = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schemaVersion": 1,
        "buildID": build_id,
        **identity,
        "dirty": bool(identity["dirtyPaths"]),
        "builtAt": built_at or utc_now(),
    }


def discover_included_dirty_paths(
    repo_root: Path,
    source_project: Path,
    packaged_project: Path,
) -> list[str]:
    """Return dirty Godot paths whose bytes are actually present in the export copy."""
    project_relative = source_project.resolve().relative_to(repo_root.resolve())
    status = subprocess.run(
        ["git", "status", "--porcelain=1", "--untracked-files=all", "--", project_relative.as_posix()],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    included: list[str] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        status_code, repo_path = line[:2], line[3:]
        # Rename records contain two paths; leave them out unless explicitly resolved.
        if "R" in status_code or "C" in status_code:
            continue
        source_path = repo_root / repo_path
        relative = Path(repo_path).relative_to(project_relative)
        packaged_path = packaged_project / relative
        if source_path.is_file() and packaged_path.is_file():
            if sha256_file(source_path) == sha256_file(packaged_path):
                included.append(repo_path)
        elif not source_path.exists() and not packaged_path.exists():
            included.append(repo_path)
    return sorted(set(included))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def finalize_metadata(embedded_path: Path, pck_path: Path) -> dict[str, Any]:
    embedded = json.loads(embedded_path.read_text(encoding="utf-8"))
    if embedded.get("schemaVersion") != 1 or not isinstance(embedded.get("buildID"), str):
        raise ValueError(f"Invalid embedded build metadata: {embedded_path}")
    if not pck_path.is_file() or pck_path.stat().st_size == 0:
        raise ValueError(f"Exported PCK is missing or empty: {pck_path}")
    return {
        "schemaVersion": 1,
        "buildID": embedded["buildID"],
        "gitCommit": embedded["gitCommit"],
        "dirty": embedded["dirty"],
        "dirtyPaths": embedded["dirtyPaths"],
        "resourceVersion": embedded["resourceVersion"],
        "sourceTreeSha256": embedded["sourceTreeSha256"],
        "templateSha256": embedded["templateSha256"],
        "engineVersion": embedded["engineVersion"],
        "builtAt": embedded["builtAt"],
        "exportedAt": utc_now(),
        "pckSha256": sha256_file(pck_path),
        "pckHashKind": "exported_artifact",
    }


def git_commit(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="write metadata to the temporary Godot project")
    prepare.add_argument("--repo", type=Path, required=True)
    prepare.add_argument("--source-project", type=Path, required=True)
    prepare.add_argument("--project", type=Path, required=True)
    prepare.add_argument("--template", type=Path, required=True)
    prepare.add_argument("--engine-version", required=True)
    finish = subparsers.add_parser("finalize", help="write the post-export PCK-hash sidecar")
    finish.add_argument("--embedded", type=Path, required=True)
    finish.add_argument("--pck", type=Path, required=True)
    finish.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "prepare":
        dirty_paths = discover_included_dirty_paths(
            args.repo, args.source_project, args.project
        )
        metadata = prepare_metadata(
            args.project,
            git_commit=git_commit(args.repo),
            dirty_paths=dirty_paths,
            template_sha256=sha256_file(args.template),
            engine_version=args.engine_version,
        )
        embedded_path = args.project / METADATA_RELATIVE_PATH
        write_json(embedded_path, metadata)
        print(json.dumps({"embedded": str(embedded_path), "buildID": metadata["buildID"], "dirtyPaths": dirty_paths}))
        return 0

    metadata = finalize_metadata(args.embedded, args.pck)
    write_json(args.output, metadata)
    print(json.dumps({"sidecar": str(args.output), "buildID": metadata["buildID"], "pckSha256": metadata["pckSha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
