"""Insert independent source-frame markers after StartSound tags in an isolated SWF."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_minimal_swf import build as build_minimal_swf  # noqa: E402


WIDTH_ONLY_ATTRIBUTES = {"nScaleBits", "moveBits"}
FFDEC_HOME = Path("/private/tmp/ffdec-startsound-home")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_ffdec(ffdec: Path, *arguments: str) -> None:
    subprocess.run([
        "java", "-Djava.awt.headless=true", f"-Duser.home={FFDEC_HOME}",
        "-jar", str(ffdec), "-config", "parallelSpeedUp=false", *arguments,
    ], check=True, capture_output=True, text=True)


def _sprite_subtags(root: ET.Element, sprite_id: int) -> ET.Element:
    tags = root.find("tags")
    if tags is None:
        raise ValueError("SWF XML is missing the top-level tag list")
    sprite = next((tag for tag in tags
                   if tag.get("type") == "DefineSpriteTag"
                   and tag.get("spriteId") == str(sprite_id)), None)
    if sprite is None:
        raise ValueError(f"Source SWF has no DefineSpriteTag {sprite_id}")
    sub_tags = sprite.find("subTags")
    if sub_tags is None:
        raise ValueError(f"Source sprite {sprite_id} has no subTags")
    return sub_tags


def build_sound_asset_index(source_assets_xml: Path, asset_root: Path) -> dict[str, dict]:
    root = ET.parse(source_assets_xml).getroot()
    index = {}
    for tag in root.iter():
        if tag.get("type") != "DefineSoundTag":
            continue
        sound_id = tag.get("soundId")
        external = tag.get("_externalFile")
        if sound_id is None or external is None:
            continue
        path = (asset_root / external).resolve()
        path.relative_to(asset_root.resolve())
        if not path.is_file():
            raise FileNotFoundError(f"Missing original sound asset: {path}")
        index[sound_id] = {
            "path": path,
            "relative_path": path.relative_to(asset_root.resolve()).as_posix(),
            "sha256": sha256(path),
        }
    return index


def _sound_asset_for_tag(tag: ET.Element, xml_path: Path, asset_root: Path,
                         source_sound_assets: dict[str, dict]) -> dict:
    external = tag.get("_externalFile")
    sound_id = tag.get("soundId")
    if external is not None:
        path = (xml_path.parent / external).resolve()
        path.relative_to(asset_root.resolve())
        if not path.is_file():
            raise FileNotFoundError(f"Missing extracted sound asset: {path}")
        return {"path": path, "relative_path": path.relative_to(asset_root.resolve()).as_posix(),
                "sha256": sha256(path)}
    source = source_sound_assets.get(sound_id)
    if source is None:
        raise ValueError(f"No original sound asset mapping for soundId={sound_id}")
    raw_data = tag.get("soundData")
    if raw_data is None:
        raise ValueError(f"DefineSoundTag {sound_id} has neither external file nor soundData")
    sound_data = bytes.fromhex(raw_data)
    source_bytes = source["path"].read_bytes()
    sound_format = int(tag.get("soundFormat", "-1"))
    # SWF MP3 SoundData starts with a two-byte seek-sample header; the remaining
    # bytes are the original MP3 file. Other formats must match their asset bytes.
    payload = sound_data[2:] if sound_format == 2 else sound_data
    if payload != source_bytes:
        raise ValueError(f"Embedded soundId={sound_id} differs from its original asset")
    return source


def collect_tags(xml_path: Path, asset_root: Path, sprite_id: int,
                 source_sound_assets: dict[str, dict] | None = None) -> list[dict]:
    root = ET.parse(xml_path).getroot()
    top_tags = root.find("tags")
    if top_tags is None:
        raise ValueError("SWF XML is missing the top-level tag list")
    sound_assets = {
        tag.get("soundId"): tag
        for tag in top_tags if tag.get("type") == "DefineSoundTag"
    }
    sub_tags = list(_sprite_subtags(root, sprite_id))
    result = []
    frame = 1
    frame_ordinals: dict[int, int] = {}
    for tag_index, tag in enumerate(sub_tags):
        tag_type = tag.get("type")
        if tag_type == "ShowFrameTag":
            frame += 1
            continue
        if tag_type == "StartSound2Tag":
            raise ValueError("StartSound2Tag is not supported by this observer")
        if tag_type != "StartSoundTag":
            continue
        sound_id = tag.get("soundId")
        if sound_id is None or sound_id not in sound_assets:
            raise ValueError(f"StartSoundTag has no DefineSoundTag asset: sprite {sprite_id}, frame {frame}")
        asset = _sound_asset_for_tag(sound_assets[sound_id], xml_path, asset_root,
                                     source_sound_assets or {})
        frame_ordinal = frame_ordinals.get(frame, 0)
        frame_ordinals[frame] = frame_ordinal + 1
        info = tag.find("soundInfo")
        if info is None:
            raise ValueError(f"StartSoundTag has no SOUNDINFO: sprite {sprite_id}, frame {frame}")
        sound_info = {
            "attributes": dict(info.attrib),
            "envelope": [dict(item.attrib) for item in info.iter("item")],
        }
        result.append({
            "sprite_id": sprite_id,
            "frame": frame,
            "tag_index": tag_index,
            "frame_ordinal": frame_ordinal,
            "sound_id": int(sound_id),
            "sound_info": sound_info,
            "asset_path": asset["relative_path"],
            "asset_sha256": asset["sha256"],
        })
    if not result:
        raise ValueError(f"No StartSoundTag found in source sprite {sprite_id}")
    return result


def marker_script(tag: dict, run_id: str, position_observer_frame: int | None = None,
                  position_observer_ms: int = 2600, position_interval_ms: int = 25) -> str:
    payload = "|".join((
        run_id, f"sprite{tag['sprite_id']}", str(tag["frame"]),
        str(tag["tag_index"]), str(tag["frame_ordinal"]), str(tag["sound_id"]),
    ))
    script = (
        '_root.aiEvent("source_sound_tag_frame", '
        f'{json.dumps(payload)} + "|" + String(this._name) + "|" + _currentframe);\n'
    )
    if tag["frame"] == position_observer_frame:
        script += (
            'var __aiSoundPositionProbe = new Sound(this);\n'
            'var __aiSoundPositionStarted = getTimer();\n'
            'var __aiSoundPositionTimer = setInterval(function()\n'
            '{\n'
            '   var elapsed = getTimer() - __aiSoundPositionStarted;\n'
            '   _root.aiEvent("source_sound_position", '
            f'{json.dumps(payload)} + "|" + elapsed + "|" + '
            'String(__aiSoundPositionProbe.position) + "|" + '
            'String(__aiSoundPositionProbe.duration));\n'
            f'   if(elapsed >= {int(position_observer_ms)}) clearInterval(__aiSoundPositionTimer);\n'
            f'}}, {int(position_interval_ms)});\n'
        )
    return script


def insert_markers(root: ET.Element, sprite_id: int, tags: list[dict], action_bytes: dict[str, str]) -> None:
    """Insert a new DoActionTag immediately after each source StartSoundTag."""
    subtags = _sprite_subtags(root, sprite_id)
    by_index = {tag["tag_index"]: tag for tag in tags}
    source = list(subtags)
    if any(index >= len(source) or source[index].get("type") != "StartSoundTag" for index in by_index):
        raise ValueError("Source sound-tag index changed before instrumentation")
    for index in sorted(by_index, reverse=True):
        tag = by_index[index]
        key = f"{tag['frame']}:{tag['frame_ordinal']}"
        if key not in action_bytes:
            raise ValueError(f"No compiled marker action for source sound tag {key}")
        marker = ET.Element("item", {"type": "DoActionTag", "actionBytes": action_bytes[key]})
        subtags.insert(index + 1, marker)


def strip_markers(root: ET.Element, sprite_id: int, tags: list[dict], action_bytes: dict[str, str]) -> None:
    subtags = _sprite_subtags(root, sprite_id)
    by_index = {tag["tag_index"]: tag for tag in tags}
    for index in sorted(by_index, reverse=True):
        tag = by_index[index]
        key = f"{tag['frame']}:{tag['frame_ordinal']}"
        prior_markers = sum(1 for prior in by_index if prior < index)
        position = index + 1 + prior_markers
        if position >= len(subtags):
            raise ValueError("Inserted marker tag is missing")
        marker = subtags[position]
        if marker.get("type") != "DoActionTag" or marker.get("actionBytes") != action_bytes.get(key):
            raise ValueError(f"Inserted marker is not immediately after source sound tag {key}")
        subtags.remove(marker)


def normalize_xml(element: ET.Element) -> tuple:
    attributes = tuple(sorted(
        (key, value) for key, value in element.attrib.items()
        if key not in WIDTH_ONLY_ATTRIBUTES
    ))
    return (
        element.tag,
        attributes,
        (element.text or "").strip(),
        tuple(normalize_xml(child) for child in element),
    )


def copy_external_assets(root: ET.Element, source_xml: Path, asset_root: Path, destination: Path) -> dict[str, str]:
    hashes = {}
    for element in root.iter():
        external = element.get("_externalFile")
        if external is None:
            continue
        source = (asset_root / external).resolve()
        source.relative_to(asset_root.resolve())
        if not source.is_file():
            raise FileNotFoundError(f"Missing external SWF asset: {source}")
        target = destination / external
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[external] = sha256(source)
    return hashes


def compile_marker_actions(ffdec: Path, tags: list[dict], run_id: str, temporary: Path,
                           position_observer_frame: int | None = None,
                           position_observer_ms: int = 2600,
                           position_interval_ms: int = 25) -> dict[str, str]:
    swf = temporary / "marker-source.swf"
    compiled = temporary / "marker-compiled.swf"
    scripts_root = temporary / "marker-scripts"
    swf.write_bytes(build_minimal_swf(len(tags)))
    for ordinal, tag in enumerate(tags, 1):
        frame = scripts_root / f"frame_{ordinal}"
        frame.mkdir(parents=True)
        (frame / "DoAction.as").write_text(marker_script(
            tag, run_id, position_observer_frame, position_observer_ms,
            position_interval_ms))
    run_ffdec(ffdec, "-importScript", str(swf), str(compiled), str(scripts_root))
    compiled_xml = temporary / "marker-compiled.xml"
    run_ffdec(ffdec, "-swf2xml", str(compiled), str(compiled_xml))
    compiled_root = ET.parse(compiled_xml).getroot()
    frames = [item for item in compiled_root.find("tags") if item.get("type") == "DoActionTag"]
    if len(frames) != len(tags):
        raise ValueError(f"FFDec returned {len(frames)} marker action tags for {len(tags)} markers")
    return {
        f"{tag['frame']}:{tag['frame_ordinal']}": frame.get("actionBytes")
        for tag, frame in zip(tags, frames, strict=True)
    }


def _export_scripts(ffdec: Path, swf: Path, destination: Path) -> Path:
    run_ffdec(ffdec, "-export", "script", str(destination), str(swf))
    return destination / "scripts"


def bitmap_semantics(root: ET.Element) -> dict:
    digest = hashlib.sha256()
    counts: dict[str, int] = {}
    for tag in root.iter():
        tag_type = tag.get("type", "")
        if not tag_type.startswith("DefineBits"):
            continue
        counts[tag_type] = counts.get(tag_type, 0) + 1
        digest.update(tag_type.encode("utf-8") + b"\0")
        digest.update((tag.get("characterID") or "").encode("ascii") + b"\0")
        for field in ("imageData", "bitmapAlphaData"):
            value = tag.get(field)
            if value is not None:
                raw = bytes.fromhex(value)
                digest.update(field.encode("ascii") + b"\0" + hashlib.sha256(raw).digest())
    return {"tag_counts": counts, "image_and_alpha_payloads_sha256": digest.hexdigest()}


def instrument(ffdec: Path, base_swf: Path, output_swf: Path, asset_root: Path,
               source_assets_xml: Path, run_id: str, sprite_id: int,
               position_observer_frame: int | None = None,
               position_observer_ms: int = 2600,
               position_interval_ms: int = 25) -> dict:
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in run_id):
        raise ValueError("run_id must contain only letters, digits, underscores, and hyphens")
    if output_swf.exists():
        raise FileExistsError(f"Refusing to overwrite instrumented SWF: {output_swf}")
    FFDEC_HOME.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="start-sound-xml-") as temp_name:
        temporary = Path(temp_name)
        source_xml = temporary / "source.xml"
        run_ffdec(ffdec, "-swf2xml", str(base_swf), str(source_xml))
        source_root = ET.parse(source_xml).getroot()
        source_sound_assets = build_sound_asset_index(source_assets_xml, asset_root)
        external_hashes = copy_external_assets(source_root, source_xml, asset_root, temporary)
        tags = collect_tags(source_xml, temporary, sprite_id, source_sound_assets)
        image_semantics = bitmap_semantics(source_root)
        if position_observer_ms <= 0 or position_interval_ms <= 0:
            raise ValueError("Sound position observer durations must be positive")
        if position_observer_frame is not None and not any(
                tag["frame"] == position_observer_frame for tag in tags):
            raise ValueError("Sound position observer frame has no StartSound marker")
        action_bytes = compile_marker_actions(
            ffdec, tags, run_id, temporary, position_observer_frame,
            position_observer_ms, position_interval_ms)

        edited_root = ET.parse(source_xml).getroot()
        insert_markers(edited_root, sprite_id, tags, action_bytes)
        edited_xml = temporary / "instrumented.xml"
        ET.ElementTree(edited_root).write(edited_xml, encoding="utf-8", xml_declaration=True)
        output_swf.parent.mkdir(parents=True, exist_ok=True)
        run_ffdec(ffdec, "-xml2swf", str(edited_xml), str(output_swf))

        output_xml = temporary / "roundtrip.xml"
        run_ffdec(ffdec, "-swf2xml", str(output_swf), str(output_xml))
        output_root = ET.parse(output_xml).getroot()
        strip_markers(output_root, sprite_id, tags, action_bytes)
        if normalize_xml(source_root) != normalize_xml(output_root):
            raise ValueError("XML roundtrip changed source tag semantics after removing marker tags")
        if image_semantics != bitmap_semantics(output_root):
            raise ValueError("XML roundtrip changed image or alpha payloads")
        for external, expected_hash in external_hashes.items():
            if sha256(temporary / external) != expected_hash:
                raise ValueError(f"External asset changed during XML roundtrip: {external}")

        source_scripts = _export_scripts(ffdec, base_swf, temporary / "source-export")
        output_scripts = _export_scripts(ffdec, output_swf, temporary / "roundtrip-export")
        script_count = 0
        for source in source_scripts.rglob("*.as"):
            relative = source.relative_to(source_scripts)
            exported = output_scripts / relative
            if not exported.is_file() or source.read_bytes() != exported.read_bytes():
                raise ValueError(f"Original ActionScript changed during instrumentation: {relative}")
            script_count += 1
        source_paths = {path.relative_to(source_scripts) for path in source_scripts.rglob("*.as")}
        output_paths = {path.relative_to(output_scripts) for path in output_scripts.rglob("*.as")}
        if output_paths - source_paths and len(output_paths - source_paths) != len(tags):
            raise ValueError("Unexpected number of newly exported marker action scripts")

    return {
        "format": "source-start-sound-tag-instrumentation-v2",
        "run_id": run_id,
        "sprite_id": sprite_id,
        "scope": "Independent DoActionTag inserted immediately after each StartSoundTag; source behavior preservation validated; tag arrival is not proof of audible output",
        "position_observer": ({"frame": position_observer_frame,
                               "duration_ms": position_observer_ms,
                               "interval_ms": position_interval_ms,
                               "reads_only": ["Sound.position", "Sound.duration"],
                               "starts_or_stops_sound": False,
                               "sets_onSoundComplete": False}
                              if position_observer_frame is not None else None),
        "source_swf_sha256": sha256(base_swf),
        "instrumented_swf_sha256": sha256(output_swf),
        "ffdec_sha256": sha256(ffdec),
        "tag_count": len(tags),
        "marker_action_count": len(action_bytes),
        "preserved_source_script_count": script_count,
        "external_asset_count": len(external_hashes),
        "external_assets_sha256": external_hashes,
        "original_sound_asset_count": len(source_sound_assets),
        "bitmap_semantics": image_semantics,
        "roundtrip_semantics": "exact normalized XML equality after marker removal; only nScaleBits and moveBits encoding-width fields ignored",
        "tags": tags,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", required=True, type=Path)
    parser.add_argument("--base-swf", required=True, type=Path)
    parser.add_argument("--output-swf", required=True, type=Path)
    parser.add_argument("--asset-root", required=True, type=Path,
                        help="Root containing the source XML's external assets")
    parser.add_argument("--source-assets-xml", required=True, type=Path,
                        help="Original FFDec XML with externalized audio assets")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sprite-id", required=True, type=int)
    parser.add_argument("--position-observer-frame", type=int,
                        help="Read Sound.position/duration from this frame's target clip after its StartSound tag")
    parser.add_argument("--position-observer-ms", type=int, default=2600)
    parser.add_argument("--position-interval-ms", type=int, default=25)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report = instrument(args.ffdec, args.base_swf, args.output_swf, args.asset_root,
                        args.source_assets_xml, args.run_id, args.sprite_id,
                        args.position_observer_frame, args.position_observer_ms,
                        args.position_interval_ms)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"run_id": report["run_id"], "tag_count": report["tag_count"],
                      "marker_action_count": report["marker_action_count"],
                      "instrumented_swf_sha256": report["instrumented_swf_sha256"]}))


if __name__ == "__main__":
    main()
