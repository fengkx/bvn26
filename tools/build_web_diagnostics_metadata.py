#!/usr/bin/env python3
"""Create non-circular embedded and post-export Web diagnostics metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
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
    git_commit = git_commit.strip()
    if not git_commit:
        raise ValueError("build metadata requires a non-empty git commit")
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
    *,
    git_project_path: Path | None = None,
    allow_missing_git: bool = False,
) -> list[str]:
    """Return Git paths whose bytes in the staged project differ from HEAD."""
    if git_project_path is None:
        try:
            git_project_path = source_project.resolve().relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError(
                "--git-project-path is required when --source-project is outside --repo"
            ) from exc
    if git_project_path.is_absolute() or ".." in git_project_path.parts:
        raise ValueError("git project path must be relative to the repository")

    try:
        tree = subprocess.run(
            [
                "git",
                "ls-tree",
                "-r",
                "-z",
                "HEAD",
                "--",
                git_project_path.as_posix(),
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
    except OSError:
        if allow_missing_git:
            return []
        raise
    if tree.returncode != 0:
        if allow_missing_git:
            return []
        detail = tree.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot inspect committed project tree in {repo_root}: {detail}")

    tracked: dict[str, str] = {}
    for record in tree.stdout.split(b"\0"):
        if not record:
            continue
        try:
            header, raw_path = record.split(b"\t", 1)
            _mode, kind, object_id = header.split()
        except ValueError as exc:
            raise RuntimeError(f"cannot parse Git tree record: {record!r}") from exc
        if kind != b"blob":
            continue
        tracked[os.fsdecode(raw_path)] = object_id.decode("ascii")

    object_format_result = subprocess.run(
        ["git", "rev-parse", "--show-object-format"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    object_format = object_format_result.stdout.strip() if object_format_result.returncode == 0 else "sha1"
    if object_format not in {"sha1", "sha256"}:
        raise RuntimeError(f"unsupported Git object format: {object_format}")

    def staged_blob_id(path: Path) -> str:
        digest = hashlib.new(object_format)
        if path.is_symlink():
            contents = os.fsencode(os.readlink(path))
            digest.update(f"blob {len(contents)}\0".encode("ascii"))
            digest.update(contents)
            return digest.hexdigest()
        size = path.stat().st_size
        digest.update(f"blob {size}\0".encode("ascii"))
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def included_path(repo_path: str, relative: Path) -> bool:
        if relative == METADATA_RELATIVE_PATH or ".godot" in relative.parts:
            return False
        packaged_path = packaged_project / relative
        head_blob_id = tracked.get(repo_path)
        if head_blob_id is None and (
            packaged_path.suffix == ".import"
            or packaged_path.name in {".DS_Store", "Thumbs.db"}
            or packaged_path.name.startswith("._")
        ):
            return False
        if packaged_path.is_file() or packaged_path.is_symlink():
            return head_blob_id != staged_blob_id(packaged_path)
        return head_blob_id is not None

    included: list[str] = []
    for repo_path, _head_blob_id in tracked.items():
        try:
            relative = Path(repo_path).relative_to(git_project_path)
        except ValueError as exc:
            raise ValueError(f"Git returned a path outside {git_project_path}: {repo_path}") from exc
        if included_path(repo_path, relative):
            included.append(repo_path)

    for path in packaged_project.rglob("*"):
        if not (path.is_file() or path.is_symlink()):
            continue
        relative = path.relative_to(packaged_project)
        if relative == METADATA_RELATIVE_PATH or ".godot" in relative.parts:
            continue
        repo_path = (git_project_path / relative).as_posix()
        if repo_path not in tracked and included_path(repo_path, relative):
            included.append(repo_path)
    return sorted(set(included))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(serialized)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def finalize_metadata(embedded_path: Path, pck_path: Path) -> dict[str, Any]:
    embedded = json.loads(embedded_path.read_text(encoding="utf-8"))
    if embedded.get("schemaVersion") != 1 or not isinstance(embedded.get("buildID"), str):
        raise ValueError(f"Invalid embedded build metadata: {embedded_path}")
    if not isinstance(embedded.get("gitCommit"), str) or not embedded["gitCommit"].strip():
        raise ValueError(f"Embedded build metadata has no git commit: {embedded_path}")
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


def git_commit(repo_root: Path, *, vercel_fallback: str | None = None) -> str:
    return resolve_git_commit(repo_root, vercel_fallback=vercel_fallback)[0]


def resolve_git_commit(repo_root: Path, *, vercel_fallback: str | None = None) -> tuple[str, str]:
    """Prefer readable HEAD; a .git path alone does not prove Git is usable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip(), "git"

    fallback = (vercel_fallback or "").strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", fallback):
        return fallback.lower(), "vercel"
    git_exit = result.returncode if result is not None else "unavailable"
    raise ValueError(
        "cannot resolve a non-empty git commit; provide a Git checkout or "
        "a full VERCEL_GIT_COMMIT_SHA when Git cannot read HEAD. "
        f"gitExit={git_exit}, gitPathExists={(repo_root / '.git').exists()}, "
        f"vercelCommit={'invalid' if fallback else 'missing'}. "
        "If system variables are disabled, enable access in Project Settings > "
        "Environment Variables. If already enabled, inspect the deployment's Git source "
        "and commit metadata. "
        "For source uploads, pass the exact source commit as VERCEL_GIT_COMMIT_SHA "
        "for that deployment; do not pin a permanent commit value."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight", help="check commit provenance before downloading build tools")
    preflight.add_argument("--repo", type=Path, required=True)
    prepare = subparsers.add_parser("prepare", help="write metadata to the temporary Godot project")
    prepare.add_argument("--repo", type=Path, required=True)
    prepare.add_argument("--source-project", type=Path, required=True)
    prepare.add_argument("--project", type=Path, required=True)
    prepare.add_argument(
        "--git-project-path",
        type=Path,
        help="repository-relative project path when the staged source is outside --repo",
    )
    prepare.add_argument("--template", type=Path, required=True)
    prepare.add_argument("--engine-version", required=True)
    finish = subparsers.add_parser("finalize", help="write the post-export PCK-hash sidecar")
    finish.add_argument("--embedded", type=Path, required=True)
    finish.add_argument("--pck", type=Path, required=True)
    finish.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "preflight":
        try:
            commit, source = resolve_git_commit(args.repo, vercel_fallback=os.environ.get("VERCEL_GIT_COMMIT_SHA"))
        except ValueError as exc:
            parser.exit(1, f"WEB_BUILD_PROVENANCE_ERROR: {exc}\n")
        print(f"WEB_BUILD_PROVENANCE_OK gitCommit={commit} source={source}")
        return 0

    if args.command == "prepare":
        fallback_commit = os.environ.get("VERCEL_GIT_COMMIT_SHA")
        commit, source = resolve_git_commit(args.repo, vercel_fallback=fallback_commit)
        dirty_paths = discover_included_dirty_paths(
            args.repo,
            args.source_project,
            args.project,
            git_project_path=args.git_project_path,
            allow_missing_git=source == "vercel",
        )
        metadata = prepare_metadata(
            args.project,
            git_commit=commit,
            dirty_paths=dirty_paths,
            template_sha256=sha256_file(args.template),
            engine_version=args.engine_version,
        )
        if source == "vercel":
            # Without a readable HEAD, an empty path list is not proof of a
            # clean checkout. Source bytes are still covered by the build ID.
            metadata["dirty"] = None
        embedded_path = args.project / METADATA_RELATIVE_PATH
        write_json(embedded_path, metadata)
        print(
            json.dumps(
                {
                    "embedded": str(embedded_path),
                    "buildID": metadata["buildID"],
                    "gitCommitSource": source,
                    "dirtyCheckAvailable": source == "git",
                    "dirtyPathCount": len(dirty_paths),
                    "dirtyPathSample": dirty_paths[:20],
                    "dirtyPathSampleTruncated": len(dirty_paths) > 20,
                }
            )
        )
        return 0

    try:
        metadata = finalize_metadata(args.embedded, args.pck)
    except Exception:
        args.output.unlink(missing_ok=True)
        raise
    write_json(args.output, metadata)
    print(json.dumps({"sidecar": str(args.output), "buildID": metadata["buildID"], "pckSha256": metadata["pckSha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
