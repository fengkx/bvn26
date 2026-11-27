"""Reuse verified, native Godot fighter packs in the next Web export."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zipfile


def uid_rows(data):
    count, = struct.unpack_from("<I", data)
    offset = 4
    for _ in range(count):
        _, length = struct.unpack_from("<QI", data, offset)
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("Truncated UID cache")
        yield data[offset + 12:end].decode(), bytes(data[offset:end])
        offset = end
    if offset != len(data):
        raise ValueError("Unexpected UID cache length")


def family_keys(project, families, engine):
    preset = (project / "export_presets.cfg").read_bytes()
    settings = (project / "project.godot").read_bytes()
    if ((project / "addons").exists() or b"[editor_plugins]" in settings
            or b'export_filter="all_resources"' not in preset or b'exclude_filter=""' not in preset
            or (project / "override.cfg").exists() or any(project.rglob("*.gdextension"))):
        return {}
    # The resolved template path lives in a new temporary directory on each CI build.
    # Its content hash and the other export options form the stable identity.
    template = re.search(rb'^custom_template/release=("[^\n]*")$', preset, re.M)
    if not template:
        return {}
    path = Path(json.loads(template[1]))
    if not path.is_file():
        return {}
    seed = hashlib.sha256(Path(__file__).read_bytes() + Path(__file__).with_name("split_web_packs.py").read_bytes()
                          + engine.encode() + settings + preset[:template.start(1)] + preset[template.end(1):]
                          + hashlib.sha256(path.read_bytes()).digest())
    hashes = {}
    ineligible = set()
    for directory, family in sorted(families.items()):
        fingerprint = hashes.setdefault(family, seed.copy())
        if not re.fullmatch(r"[a-z0-9_-]+", family) or not re.fullmatch(r"(?:fighters|forms)/[a-z0-9_-]+", directory):
            ineligible.add(family)
            continue
        for entry in sorted((project / "generated" / directory).rglob("*")):
            if not entry.is_file():
                continue
            data = entry.read_bytes()
            if (entry.suffix not in {".json", ".gd", ".uid", ".png", ".wav", ".mp3", ".import"}
                    or entry.suffix == ".gd" and re.search(rb"\bclass_name\b|@tool\b", data)):
                ineligible.add(family)
            if entry.suffix == ".import":
                # Only built-in, single-output imports have no external dependencies.
                remaps = re.findall(rb'^path(?:\.[^=\n]+)?=.*$', data, re.M)
                output = re.fullmatch(rb'path="res://(\.godot/imported/[^"/]+)"', remaps[0]) if len(remaps) == 1 else None
                if not output or not re.search(rb'^importer="(?:texture|wav|mp3)"$', data, re.M):
                    ineligible.add(family)
                    continue
                imported = project / output[1].decode()
                if not imported.is_file():
                    ineligible.add(family)
                    continue
                fingerprint.update(hashlib.sha256(imported.read_bytes()).digest())
            fingerprint.update(entry.relative_to(project).as_posix().encode() + b"\0" + hashlib.sha256(data).digest())
    return {family: fingerprint.hexdigest() for family, fingerprint in hashes.items() if family not in ineligible}


def plan(project, cache, work, engine, families):
    keys = family_keys(project, families, engine)
    work.mkdir(parents=True, exist_ok=True)
    hits = {}
    for family, key in keys.items():
        try:
            with zipfile.ZipFile(cache / (family + ".zip")) as bundle:
                if bundle.comment.decode() != key:
                    continue
                meta = json.loads(bundle.read("meta.json"))
                sha = meta["sha"]
                if not re.fullmatch(r"[0-9a-f]{64}", sha):
                    continue
                dest = work / f"{family}-{sha}.pck"
                with bundle.open("pack") as source, dest.open("wb") as output:
                    shutil.copyfileobj(source, output)
                if hashlib.sha256(dest.read_bytes()).hexdigest() != sha:
                    continue
                uids = bundle.read("uids")
                list(uid_rows(uids))
                (work / (family + ".uids")).write_bytes(uids)
                hits[family] = {"sha": sha, "size": dest.stat().st_size, "file": dest.name}
        except (OSError, EOFError, KeyError, TypeError, ValueError, struct.error, zipfile.BadZipFile):
            continue
    (work / "plan.json").write_text(json.dumps({"cache": str(cache), "keys": keys, "hits": hits}))
    if hits:
        preset = project / "export_presets.cfg"
        filters = ",".join("res://generated/" + d + "/*" for d, family in families.items() if family in hits)
        preset.write_text(preset.read_text().replace('exclude_filter=""', f'exclude_filter="{filters}"', 1))
    print(f"Godot fighter pack cache: {len(hits)} reused, {len(set(families.values())) - len(hits)} to export")


def merge_uids(native, work, hits):
    # Godot filters its UID table to the current export. Reattach the mappings
    # captured alongside each omitted pack so uid:// lookups still resolve.
    rows = list(uid_rows(native))
    for family in hits:
        rows.extend(uid_rows((work / (family + ".uids")).read_bytes()))
    return struct.pack("<I", len(rows)) + b"".join(row for _, row in rows)


def save(cache, family, key, pack, sha, rows):
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=cache, delete=False) as tmp:
        name = Path(tmp.name)
    try:
        with zipfile.ZipFile(name, "w") as bundle:
            bundle.write(pack, "pack")
            bundle.writestr("meta.json", json.dumps({"sha": sha}))
            bundle.writestr("uids", struct.pack("<I", len(rows)) + b"".join(rows))
            bundle.comment = key.encode()
        name.replace(cache / (family + ".zip"))
    finally:
        name.unlink(missing_ok=True)


if __name__ == "__main__":
    import argparse
    from split_web_packs import family_directories

    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("project", "cache", "work"):
        parser.add_argument(arg, type=Path)
    parser.add_argument("engine")
    args = parser.parse_args()
    plan(args.project, args.cache, args.work, args.engine, family_directories(args.project))
