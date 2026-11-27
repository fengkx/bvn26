"""Split the pinned Godot v4 pack without reimporting or re-encoding resources."""
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import re
import struct

from diagnostic_roster import publish as publish_diagnostics

# The main scene instantiates these two actors before the menu is interactive.
BOOT_FIGHTERS = {"minren", "yihu"}


def family_directories(project):
    owners = {}
    fighters = project / "generated/fighters"
    for fighter_dir in sorted(fighters.iterdir()):
        if not fighter_dir.is_dir() or fighter_dir.name in BOOT_FIGHTERS:
            continue
        fighter = fighter_dir.name
        base = "fighters/" + fighter
        owners[base] = fighter
        profiles = project / "generated" / base / "form_profiles.json"
        declared = set()
        if profiles.is_file():
            for profile in json.loads(profiles.read_text())["profiles"].values():
                path = profile["directory"]
                if not path.startswith("res://generated/forms/"):
                    raise ValueError(f"Unexpected form directory: {path}")
                directory = path.removeprefix("res://generated/")
                if not (project / "generated" / directory / "timeline.json").is_file():
                    raise ValueError(f"Missing form: {path}")
                if directory in owners and owners[directory] != fighter:
                    raise ValueError(f"Conflicting owners for {directory}")
                owners[directory] = fighter
                declared.add(directory)
        for directory in (project / "generated/forms").glob(fighter + "-*"):
            if "forms/" + directory.name not in declared:
                raise ValueError(f"Undeclared form of {fighter}: {directory.name}")
    return owners


def digest(path):
    with path.open("rb") as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
        return h.hexdigest()


def split(source, project, output, reuse=None):
    plan = json.loads((reuse / "plan.json").read_text()) if reuse else {}
    hits = plan.get("hits", {})
    uid_path = ".godot/uid_cache.bin"
    uid_data = None
    imports = {}
    families = family_directories(project)
    for directory, family in families.items():
        root = "generated/" + directory + "/"
        for path in (project / root).rglob("*"):
            if path.is_file() and path.suffix != ".import":
                uri = "res://" + path.relative_to(project).as_posix()
                imports[hashlib.md5(uri.encode()).hexdigest()] = family

    with source.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        version, = struct.unpack_from("<I", data, 4)
        flags, base, cursor = struct.unpack_from("<IQQ", data, 20)
        if data[:4] != b"GDPC" or version != 4 or flags != 2 or base != 112:
            raise ValueError("Unsupported Godot pack header")
        count, = struct.unpack_from("<I", data, cursor)
        cursor += 4
        groups = {"core": []}
        remaining = {"generated/" + directory + "/timeline.json" for directory, family in families.items() if family not in hits}
        for _ in range(count):
            length, = struct.unpack_from("<I", data, cursor)
            name = data[cursor + 4:cursor + 4 + length]
            cursor += 4 + length
            offset, size = struct.unpack_from("<QQ", data, cursor)
            tail = data[cursor + 16:cursor + 36]
            cursor += 36
            path = name.rstrip(b"\0").decode()
            if path == uid_path:
                uid_data = bytes(data[base + offset:base + offset + size])
            remaining.discard(path)
            match = re.fullmatch(r"\.godot/imported/.*-([0-9a-f]{32})\.[^/]+", path)
            parts = path.split("/", 3)
            family = imports.get(match[1]) if match else None
            if len(parts) == 4 and parts[0] == "generated":
                family = families.get("/".join(parts[1:3]))
            groups.setdefault(family or "core", []).append((name, base + offset, size, tail))
        if remaining:
            raise ValueError(f"Missing exported timelines: {sorted(remaining)}")
        if set(groups) != {"core", *(set(families.values()) - hits.keys())}:
            raise ValueError("Missing fighter resources in exported pack")
        merged_uids = None
        if hits:
            from web_family_cache import merge_uids
            merged_uids = merge_uids(uid_data, reuse, hits)
        manifest = {}
        for family, entries in groups.items():
            temp = output / (family + ".tmp")
            with temp.open("wb") as dest:
                dest.write(data[:base])
                directory = bytearray(struct.pack("<I", len(entries)))
                for name, offset, size, tail in entries:
                    dest.write(bytes(-dest.tell() % 16))
                    payload = memoryview(data)[offset:offset + size]
                    if merged_uids is not None and name.rstrip(b"\0") == uid_path.encode():
                        payload = merged_uids
                        size = len(payload)
                        tail = hashlib.md5(payload).digest() + tail[16:]
                    directory.extend(struct.pack("<I", len(name)) + name)
                    directory.extend(struct.pack("<QQ", dest.tell() - base, size) + tail)
                    dest.write(payload)
                    del payload
                dest.write(bytes(-dest.tell() % 16))
                directory_offset = dest.tell()
                dest.write(directory)
                dest.seek(32)
                dest.write(struct.pack("<Q", directory_offset))
            sha = digest(temp)
            filename = f"{family}-{sha}.pck"
            temp.rename(output / filename)
            manifest[family] = {"file": filename, "sha": sha, "size": (output / filename).stat().st_size}
    if plan.get("keys"):
        from web_family_cache import uid_rows, save
        rows = {}
        for path, record in uid_rows(uid_data):
            parts = path.removeprefix("res://generated/").split("/", 2)
            family = families.get("/".join(parts[:2]))
            if family:
                rows.setdefault(family, []).append(record)
        for family, key in plan["keys"].items():
            if family not in hits:
                meta = manifest[family]
                save(Path(plan["cache"]), family, key, output / meta["file"], meta["sha"], rows.get(family, []))
        for family, meta in hits.items():
            (reuse / meta["file"]).replace(output / meta["file"])
            manifest[family] = meta
    return manifest


def prepare(stage, project, reuse=None):
    publish_diagnostics(project, stage)
    manifest = split(stage / "index.pck", project, stage, reuse)
    core = manifest.pop("core")
    (stage / "index.pck").unlink()
    html = stage / "index.html"
    shell = html.read_text()
    config_pattern = r"const GODOT_CONFIG = (\{[^\n]+\});"
    config = json.loads(re.search(config_pattern, shell)[1])
    config["mainPack"] = core["file"]
    config["bvnSingleUseWasm"] = True
    del config["fileSizes"]["index.pck"]
    config["fileSizes"][core["file"]] = core["size"]
    engine_files = sorted(p for p in stage.glob("index.*") if p.suffix in {".js", ".wasm"})
    fingerprint = hashlib.sha256("".join(p.name + digest(p) for p in engine_files).encode()).hexdigest()
    executable = "engine-" + fingerprint
    config["executable"] = executable
    config["fileSizes"][executable + ".wasm"] = config["fileSizes"].pop("index.wasm")
    for path in engine_files:
        path.rename(stage / path.name.replace("index", executable, 1))
    shell = shell.replace('src="index.js"', f'src="{executable}.js"')
    shell = re.sub(config_pattern, lambda _: "const GODOT_CONFIG = " + json.dumps(config) + ";", shell)
    marker = "/* BVN_PACK_RUNTIME */"
    if shell.count(marker) != 1:
        raise ValueError("Missing pack runtime marker")
    host = os.environ.get("VERCEL_URL", "")
    if host and not re.fullmatch(r"[\w.-]+", host):
        raise ValueError("Invalid deployment hostname")
    runtime = (project / "web/battle_packs.js").read_text()
    owners = {path.split("/")[1]: owner for path, owner in family_directories(project).items()}
    settings = {"owners": owners, "packs": manifest, "origin": "https://" + host if host else ""}
    html.write_text(shell.replace(marker, "const battlePackConfig = " + json.dumps(settings) + ";\n" + runtime))
    print("Progressive pack bytes:", {"core": core["size"], **{k: v["size"] for k, v in manifest.items()}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", type=Path)
    parser.add_argument("project", type=Path)
    parser.add_argument("--reuse", type=Path)
    args = parser.parse_args()
    prepare(args.stage, args.project, args.reuse)
