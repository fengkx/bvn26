"""Cache Godot's default texture/audio imports for clean Web builds."""

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

MEDIA = {".png", ".webp", ".mp3", ".wav"}


def import_stem(relative: Path) -> str:
    digest = hashlib.md5(("res://" + relative.as_posix()).encode()).hexdigest()
    return f"{relative.name}-{digest}"


def restore(project: Path, cache: Path, engine: str) -> list:
    settings = (project / "project.godot").read_bytes()
    # Custom importers can depend on arbitrary project files. Leave those to Godot.
    if (project / "addons").exists() or b"[importer_defaults]" in settings or b"[editor_plugins]" in settings:
        return []
    imported = project / ".godot/imported"
    imported.mkdir(parents=True, exist_ok=True)
    misses = []
    hits = 0
    for folder, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        directory = Path(folder).relative_to(project)
        # Checked-in import settings may reference other resources.
        filenames = set(files)
        names = sorted(n for n in filenames if Path(n).suffix in MEDIA and n + ".import" not in filenames)
        if not names:
            continue
        digest = hashlib.sha256(engine.encode() + b"\0" + settings)
        for name in names:
            digest.update(name.encode() + b"\0" + hashlib.sha256((Path(folder) / name).read_bytes()).digest())
        key = digest.hexdigest()
        archive = cache / (hashlib.sha256(directory.as_posix().encode()).hexdigest() + ".zip")
        if archive.is_file():
            try:
                with zipfile.ZipFile(archive) as previous:
                    if previous.comment == key.encode():
                        prefixes = {import_stem(directory / n) for n in names}
                        sidecars = {n + ".import" for n in names}
                        entries = previous.namelist()
                        if (sidecars.issubset(entries) and
                            all(n == Path(n).name and (n in sidecars or n.rsplit(".", 1)[0] in prefixes) for n in entries)
                            and previous.testzip() is None):
                            for n in entries:
                                previous.extract(n, folder if n in sidecars else imported)
                            hits += len(names)
                            continue
            except (zipfile.BadZipFile, EOFError):
                pass
        misses.append([directory.as_posix(), names, archive.name, key])
    print(f"Godot import cache: {hits} media hits, {sum(len(row[1]) for row in misses)} misses")
    return misses


def store(project: Path, cache: Path, misses: list) -> None:
    imported = project / ".godot/imported"
    if not imported.is_dir():
        return
    artifacts = {}
    for output in imported.iterdir():
        artifacts.setdefault(output.name.rsplit(".", 1)[0], []).append(output)
    cache.mkdir(parents=True, exist_ok=True)
    for directory, names, archive, key in misses:
        sources = []
        for name in names:
            relative = Path(directory) / name
            outputs = artifacts.get(import_stem(relative), [])
            sidecar = project / (relative.as_posix() + ".import")
            if not sidecar.is_file() or len(outputs) < 2:
                break
            sources.extend([sidecar, *outputs])
        else:
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as tmp:
                temporary = Path(tmp.name)
            try:
                with zipfile.ZipFile(temporary, "w") as bundle:
                    for path in sources:
                        bundle.write(path, path.name)
                    bundle.comment = key.encode()
                os.replace(temporary, cache / archive)
            finally:
                temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("restore", "store"))
    parser.add_argument("project", type=Path)
    parser.add_argument("cache", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("engine")
    args = parser.parse_args()
    if args.action == "restore":
        args.plan.write_text(json.dumps(restore(args.project, args.cache, args.engine)))
    else:
        store(args.project, args.cache, json.loads(args.plan.read_text()))
