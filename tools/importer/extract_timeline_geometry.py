"""Extract ordered frame/display-list evidence from pinned JPEXS XML."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from visual_blend_modes import validate_blend_mode
from visual_filters import compile_filters
from import_guards import finite_numbers, validate_placement, validate_wrapper_fields
from visual_control_guard import ROOT, validate_nested_controls
from bitmap_shape_polygon import adjacent_fill_boundary, bitmap_shape_fill_polygons, bitmap_shape_polygon


SUPPORTED_XML_EXPORTS = {(2, 2), (3, 2)}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar(value: str) -> int | float | str:
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def attributes(element: ET.Element) -> dict[str, int | float | str]:
    return {key: scalar(value) for key, value in sorted(element.attrib.items())}


def placement_delta(tag: ET.Element, source: str = "placement") -> dict[str, Any]:
    validate_placement(tag, source)
    result: dict[str, Any] = {
        "depth": int(tag.attrib["depth"]),
        "move": tag.attrib.get("placeFlagMove") == "true",
    }
    optional_attributes = {
        "characterId": "character_id",
        "name": "name",
        "ratio": "ratio",
        "clipDepth": "clip_depth",
        "blendMode": "blend_mode",
    }
    if "blendMode" in tag.attrib:
        validate_blend_mode(int(tag.attrib["blendMode"]), source)
    for attribute, target in optional_attributes.items():
        if attribute in tag.attrib:
            result[target] = scalar(tag.attrib[attribute])
    for child_name, target in (
        ("matrix", "matrix"),
        ("colorTransform", "color_transform"),
    ):
        child = tag.find(child_name)
        if child is not None:
            result[target] = attributes(child)
    if "bitmapCache" in tag.attrib:
        result["cache_as_bitmap"] = tag.attrib["bitmapCache"] == "1"
    filters = tag.find("surfaceFilterList")
    if filters is not None:
        result["filters"] = compile_filters(filters, source)
    clip_actions = tag.find("clipActions")
    if clip_actions is not None:
        records = []
        for record in clip_actions.findall("./clipActionRecords/item"):
            event_flags = record.find("eventFlags")
            records.append(
                {
                    "events": sorted(
                        key.removeprefix("clipEvent")
                        for key, value in event_flags.attrib.items()
                        if key.startswith("clipEvent") and value == "true"
                    )
                    if event_flags is not None
                    else [],
                    "action_bytes_sha256": sha256_text(record.attrib["actionBytes"]),
                }
            )
        result["clip_actions"] = records
    return result


def character_id(tag: ET.Element) -> int | None:
    for key in ("characterID", "shapeId", "spriteId", "buttonId", "textId", "fontId"):
        if key in tag.attrib:
            return int(tag.attrib[key])
    return None


def sound_info(tag: ET.Element) -> dict[str, Any]:
    """SOUNDINFO on StartSound: envelope levels are 0..32768 volume scales."""
    info = tag.find("soundInfo")
    if info is None:
        return {}
    result: dict[str, Any] = {}
    for attribute, key in (
        ("syncStop", "sync_stop"),
        ("syncNoMultiple", "sync_no_multiple"),
    ):
        if info.attrib.get(attribute) == "true":
            result[key] = True
    for flag, attribute, key in (
        ("hasInPoint", "inPoint", "in_point"),
        ("hasOutPoint", "outPoint", "out_point"),
        ("hasLoops", "loopCount", "loop_count"),
    ):
        if info.attrib.get(flag) == "true":
            result[key] = int(info.attrib[attribute])
    if info.attrib.get("hasEnvelope") == "true":
        result["envelope"] = [
            {
                "pos44": int(record.attrib["pos44"]),
                "left_level": int(record.attrib["leftLevel"]),
                "right_level": int(record.attrib["rightLevel"]),
            }
            for record in info.findall("./envelopeRecords/item")
        ]
    return result


def definition_dependencies(tag: ET.Element) -> set[int]:
    dependencies = set()
    for descendant in tag.iter():
        if "bitmapId" in descendant.attrib:
            bitmap_id = int(descendant.attrib["bitmapId"])
            if bitmap_id != 65535:
                dependencies.add(bitmap_id)
        if (
            descendant.attrib.get("type") in ("PlaceObject2Tag", "PlaceObject3Tag")
            and "characterId" in descendant.attrib
        ):
            dependencies.add(int(descendant.attrib["characterId"]))
    return dependencies


def sprite_timeline_frames(sprite: ET.Element) -> list[dict[str, Any]]:
    """Return child display-list snapshots and events on each authored frame."""
    return build_frames(sprite.findall("./subTags/item"))


def sprite_display_frames(sprite: ET.Element) -> list[list[dict[str, Any]]]:
    """Keep the legacy display-list-only view for callers outside the importer."""
    return [frame["display_list"] for frame in sprite_timeline_frames(sprite)]


def first_frame_display_list(sprite: ET.Element) -> list[dict[str, Any]]:
    frames = sprite_display_frames(sprite)
    return frames[0] if frames else []


def sound_definitions(
    root: ET.Element, frame_groups: list[list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """DefineSound tags reached on the root or a statically reachable child timeline."""
    wanted = {
        int(event["sound_id"])
        for frames in frame_groups
        for frame in frames
        for event in frame.get("events", [])
        if event.get("type") == "start_sound" and "sound_id" in event
    }
    definitions = []
    for tag in root.findall("./tags/item"):
        if tag.attrib.get("type") != "DefineSoundTag":
            continue
        sound_id = int(tag.attrib["soundId"])
        if sound_id not in wanted:
            continue
        definition: dict[str, Any] = {"character_id": sound_id, "type": "DefineSoundTag"}
        if "_externalFile" in tag.attrib:
            definition["external_file"] = tag.attrib["_externalFile"]
        definitions.append(definition)
    return definitions


def referenced_definitions(root: ET.Element, frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {
        placement["character_id"]
        for frame in frames
        for placement in frame["display_list"]
        if "character_id" in placement
    }
    definitions_by_id = {
        item_id: tag
        for tag in root.findall("./tags/item")
        if (item_id := character_id(tag)) is not None
    }
    pending = list(wanted)
    while pending:
        item_id = pending.pop()
        tag = definitions_by_id.get(item_id)
        if tag is None:
            continue
        dependencies = definition_dependencies(tag)
        for dependency in dependencies - wanted:
            wanted.add(dependency)
            pending.append(dependency)

    mask_ids = {int(tag.attrib['characterId']) for tag in root.iter('item')
                if tag.attrib.get('placeFlagHasClipDepth') == 'true'
                and 'characterId' in tag.attrib and int(tag.attrib.get('clipDepth', 0)) > 0}
    definitions = []
    sound_frame_groups = [frames]
    for item_id in sorted(wanted):
        tag = definitions_by_id.get(item_id)
        if tag is None:
            continue
        definition: dict[str, Any] = {
            "character_id": item_id,
            "type": tag.attrib["type"],
        }
        bounds = tag.find("shapeBounds")
        if bounds is not None:
            definition["shape_bounds_twips"] = {
                key: int(bounds.attrib[key]) for key in ("Xmin", "Ymin", "Xmax", "Ymax")
            }
        bitmap_fills = []
        solid_fills = []
        for fill in tag.findall(".//fillStyles/item"):
            fill_style_type = int(fill.attrib.get("fillStyleType", -1))
            if "bitmapId" in fill.attrib:
                bitmap_fill: dict[str, Any] = {
                    "bitmap_id": int(fill.attrib["bitmapId"]),
                    "fill_style_type": fill_style_type,
                }
                matrix = fill.find("bitmapMatrix")
                if matrix is not None:
                    bitmap_fill["matrix"] = attributes(matrix)
                bitmap_fills.append(bitmap_fill)
                continue
            if fill_style_type != 0:
                continue
            color = fill.find("color")
            if color is None:
                continue
            solid: dict[str, Any] = {
                "fill_style_type": 0,
                "red": int(color.attrib.get("red", 0)),
                "green": int(color.attrib.get("green", 0)),
                "blue": int(color.attrib.get("blue", 0)),
            }
            if "alpha" in color.attrib:
                solid["alpha"] = int(color.attrib["alpha"])
            solid_fills.append(solid)
        if bitmap_fills:
            definition["bitmap_fills"] = bitmap_fills
            polygon = bitmap_shape_polygon(tag)
            if polygon is not None:
                definition["bitmap_clip_polygon"] = polygon
            else:
                fill_polygons = bitmap_shape_fill_polygons(tag)
                if fill_polygons is not None and (len(bitmap_fills) > 1 or fill_polygons == [[]]):
                    definition["bitmap_clip_polygons"] = fill_polygons
        if solid_fills:
            definition["solid_fills"] = solid_fills
        if item_id in mask_ids and tag.attrib['type'].startswith('DefineShape'):
            # Mask geometry uses the same directed fill edges, irrespective of
            # paint color. A temporary bitmap style lets the contour compiler
            # reuse its checked edge stitching without approximating the AABB.
            mask_shape = copy.deepcopy(tag)
            for fill in mask_shape.findall('.//fillStyles/item'):
                fill.set('bitmapId', '0')
            # Flash masks use fills only; authored strokes do not expand the mask.
            for record in mask_shape.findall('./shapes/shapeRecords/item'):
                if record.get('type') == 'StyleChangeRecord':
                    record.set('stateLineStyle', 'false')
            contours = bitmap_shape_fill_polygons(mask_shape)
            # Unused styles paint nothing. Adjacent authored fills can share
            # one outer boundary; holes and disjoint regions remain rejected.
            boundaries = [contour for fill in contours for contour in fill] if contours is not None else []
            if len(boundaries) > 1:
                combined = adjacent_fill_boundary(boundaries)
                if combined is not None:
                    boundaries = [combined]
            if len(boundaries) != 1:
                raise ValueError(f'Unsupported clipDepth mask geometry: {item_id}')
            definition['mask_polygon'] = boundaries[0]
        dependencies = definition_dependencies(tag)
        if dependencies:
            definition["referenced_character_ids"] = sorted(dependencies)
        if "frameCount" in tag.attrib:
            definition["frame_count"] = int(tag.attrib["frameCount"])
            sprite_frames = sprite_timeline_frames(tag)
            sound_frame_groups.append(sprite_frames)
            definition["first_frame_display_list"] = (
                sprite_frames[0]["display_list"] if sprite_frames else []
            )
            definition["display_list_frames"] = [
                frame["display_list"] for frame in sprite_frames
            ]
            labels = {
                label: frame["frame"] for frame in sprite_frames for label in frame["labels"]
            }
            if labels:
                definition["frame_labels"] = labels
            definition["display_list_frame_events"] = [
                frame["events"] for frame in sprite_frames
            ]
        if "_externalFile" in tag.attrib:
            definition["external_file"] = tag.attrib["_externalFile"]
        definitions.append(definition)
    definitions.extend(sound_definitions(root, sound_frame_groups))
    definitions.sort(key=lambda item: item["character_id"])
    return definitions


def visual_control_actions(encoded: str) -> list[dict[str, Any]]:
    """Compile self-contained timeline controls; never interpret gameplay bytecode.

    Plain variable initialization and function declarations do not change a
    playhead. Reject branches and calls: a conditional stop must never become
    unconditional, and a called function may change the same timeline.
    """
    data = bytes.fromhex(encoded)
    result = []
    offset = 0
    while offset < len(data):
        opcode = data[offset]
        offset += 1
        if opcode == 0:
            break
        payload = b""
        if opcode >= 0x80:
            if offset + 2 > len(data):
                raise ValueError("Truncated action length")
            size = int.from_bytes(data[offset:offset + 2], "little")
            offset += 2
            payload = data[offset:offset + size]
            offset += size
            if len(payload) != size:
                raise ValueError("Truncated action payload")
        if opcode in (0x06, 0x07):
            result.append({"op": "play" if opcode == 0x06 else "stop"})
        elif opcode == 0x81 and len(payload) == 2:
            result.append({"op": "goto", "frame": int.from_bytes(payload, "little") + 1})
        elif opcode == 0x8c and payload.endswith(b"\0"):
            result.append({"op": "goto", "label": payload[:-1].decode("utf-8")})
        elif opcode in {0x17, 0x1c, 0x1d, 0x3c, 0x41, 0x4c, 0x4d, 0x4e,
                        0x4f, 0x87, 0x88, 0x8e, 0x96, 0x9b}:
            # These are stack/local/property operations or declarations. Function
            # bodies are contained inside this action's payload, not executed.
            continue
        else:
            return []
    return result


def build_frames(tags: list[ET.Element], source: str = "timeline") -> list[dict[str, Any]]:
    display_list: dict[int, dict[str, Any]] = {}
    pending_changes: list[dict[str, Any]] = []
    pending_events: list[dict[str, Any]] = []
    pending_labels: list[str] = []
    frames: list[dict[str, Any]] = []
    for tag in tags:
        tag_type = tag.attrib.get("type", "")
        if tag_type.startswith("PlaceObject"):
            delta = placement_delta(tag, f"{source}/frame_{len(frames) + 1}/depth_{tag.get('depth')}")
            depth = delta["depth"]
            if delta["move"]:
                if depth not in display_list:
                    raise ValueError(f"Move at unoccupied depth {depth}")
                updated = copy.deepcopy(display_list[depth])
                updated.update({key: value for key, value in delta.items() if key != "move"})
                display_list[depth] = updated
            else:
                if "character_id" not in delta:
                    raise ValueError(f"Placement at depth {depth} has no character")
                display_list[depth] = {
                    key: value for key, value in delta.items() if key != "move"
                }
                display_list[depth]["placed_frame"] = len(frames) + 1
            pending_changes.append({"type": "place", **delta})
        elif tag_type in ("RemoveObjectTag", "RemoveObject2Tag"):
            depth = int(tag.attrib["depth"])
            display_list.pop(depth, None)
            pending_changes.append({"type": "remove", "depth": depth})
        elif tag_type == "FrameLabelTag":
            pending_labels.append(tag.attrib["name"])
        elif tag_type == "StartSoundTag":
            pending_events.append(
                {
                    "type": "start_sound",
                    "sound_id": int(tag.attrib["soundId"]),
                    **sound_info(tag),
                }
            )
        elif tag_type == "DoActionTag":
            pending_events.append(
                {
                    "type": "action_bytecode",
                    "sha256": sha256_text(tag.attrib["actionBytes"]),
                    **({"visual_controls": controls} if (controls := visual_control_actions(
                        tag.attrib["actionBytes"])) else {}),
                }
            )
        elif tag_type == "ShowFrameTag":
            frames.append(
                {
                    "frame": len(frames) + 1,
                    "labels": pending_labels,
                    "changes": pending_changes,
                    "events": pending_events,
                    "display_list": [display_list[key] for key in sorted(display_list)],
                }
            )
            pending_labels = []
            pending_changes = []
            pending_events = []
    return frames


def extract_wrapper_placement(
    root: ET.Element, sprite_id: int, source: str = "timeline"
) -> dict[str, Any] | None:
    """Root PlaceObject that mounts the extracted sprite, usually named `mc`.

    Fighter `_x/_y` is the player wrapper. Visuals and `bdmn` live inside `mc`,
    whose matrix is not part of the inner DefineSprite timeline.
    """
    frame = 1
    for tag in root.findall("./tags/item"):
        tag_type = tag.attrib.get("type", "")
        if tag_type == "ShowFrameTag":
            frame += 1
            continue
        if not tag_type.startswith("PlaceObject"):
            continue
        location = f"{source}/root/frame_{frame}/depth_{tag.get('depth')}"
        if tag_type not in ("PlaceObject2Tag", "PlaceObject3Tag"):
            validate_placement(tag, location)
        if int(tag.attrib.get("characterId", -1)) != sprite_id:
            continue
        delta = placement_delta(tag, location)
        validate_wrapper_fields(delta, location)
        wrapper: dict[str, Any] = {
            "name": str(delta.get("name", "")),
            "character_id": sprite_id,
            "root_frame": frame,
            "depth": int(delta["depth"]),
        }
        # The selected wrapper mounts a DefineSprite, so ratio is metadata,
        # not a request to interpolate a morph shape. Preserve it for auditing.
        for key in ("matrix", "blend_mode", "ratio", "filters"):
            if key in delta:
                wrapper[key] = delta[key]
        return wrapper
    return None


def extract_frames(xml_path: Path, sprite_id: int | None = None, *, wrapper_siblings: bool = False) -> dict[str, Any]:
    root = ET.parse(xml_path).getroot()
    xml_version = (
        int(root.attrib["_xmlExportMajor"]),
        int(root.attrib["_xmlExportMinor"]),
    )
    if xml_version not in SUPPORTED_XML_EXPORTS:
        raise ValueError(f"Unsupported JPEXS XML export version: {xml_version}")

    if sprite_id is None:
        frames = build_frames(root.findall("./tags/item"), str(xml_path))
        declared_frames = int(root.attrib.get("frameCount", 0)) or len(frames)
        result_sprite_id = 0
    else:
        sprite = next(
            (
                item
                for item in root.findall("./tags/item")
                if item.attrib.get("type") == "DefineSpriteTag"
                and int(item.attrib["spriteId"]) == sprite_id
            ),
            None,
        )
        if sprite is None:
            raise ValueError(f"Sprite {sprite_id} not found in {xml_path}")
        frames = build_frames(sprite.findall("./subTags/item"), f"{xml_path}/DefineSprite_{sprite_id}")
        declared_frames = int(sprite.attrib["frameCount"])
        result_sprite_id = sprite_id

    if len(frames) != declared_frames:
        raise ValueError(f"Expected {declared_frames} frames, extracted {len(frames)}")
    result = {
        "format": "bvn26-timeline-geometry-v1",
        "source_xml": {"name": xml_path.name, "sha256": file_sha256(xml_path)},
        "xml_export": {"major": xml_version[0], "minor": xml_version[1]},
        "sprite_id": result_sprite_id,
        "frame_count": declared_frames,
        "frames": frames,
    }
    if sprite_id is None:
        result["timeline"] = "root"
    else:
        wrapper = extract_wrapper_placement(root, sprite_id, str(xml_path))
        if wrapper is not None:
            result["wrapper"] = wrapper
    result["definitions"] = referenced_definitions(root, frames)
    if wrapper_siblings and result.get("wrapper"):
        wrapper = result["wrapper"]
        parent = build_frames(root.findall("./tags/item"), str(xml_path) + '/root')
        siblings = [p for p in parent[wrapper['root_frame'] - 1]['display_list']
                    if p['depth'] != wrapper['depth']]
        for placement in siblings:
            if placement['depth'] <= wrapper['depth'] or placement.get('clip_actions'):
                raise ValueError('Unsupported wrapper sibling order or callback')
            if placement['placed_frame'] != wrapper['root_frame']:
                raise ValueError('Retained wrapper sibling needs an earlier placement clock')
        if siblings:
            definitions = referenced_definitions(root, [{'display_list': siblings}])
            for definition in definitions:
                for events in definition.get('display_list_frame_events', []):
                    if events:
                        raise ValueError('Wrapper sibling frame actions/sounds require a source consumer')
                for children in definition.get('display_list_frames', []):
                    if any(p.get('clip_actions') for p in children):
                        raise ValueError('Wrapper sibling child callbacks require a source consumer')
            result['wrapper_siblings'] = siblings
            merged = {d['character_id']: d for d in result['definitions'] + definitions}
            result['definitions'] = [merged[key] for key in sorted(merged)]
    finite_numbers(result, str(xml_path))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xml", type=Path)
    parser.add_argument("--sprite-id", type=int)
    parser.add_argument("--root", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frame", type=int, action="append", dest="frames")
    parser.add_argument("--ranges-from", type=Path)
    parser.add_argument("--source-swf", type=Path)
    args = parser.parse_args()
    if args.root == (args.sprite_id is not None):
        parser.error("exactly one of --root or --sprite-id is required")
    result = extract_frames(args.xml, None if args.root else args.sprite_id)
    wanted = set(args.frames or [])
    if args.ranges_from:
        ranges = json.loads(args.ranges_from.read_text(encoding="utf-8"))["actions"]
        for group in ranges.values():
            for span in group.values():
                wanted.update(range(span["start_frame"], span["end_frame"] + 1))
    if wanted:
        result["frames"] = [frame for frame in result["frames"] if frame["frame"] in wanted]
        root = ET.parse(args.xml).getroot()
        result["definitions"] = referenced_definitions(root, result["frames"])
    if args.source_swf:
        result["source_swf"] = {
            "path": args.source_swf.as_posix(),
            "sha256": file_sha256(args.source_swf),
        }
    if args.source_swf:
        bundle_path = ROOT / args.source_swf.as_posix().replace("game/", "scripts/").replace(".swf", ".json")
        validate_nested_controls(result, json.loads(bundle_path.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sprite_id": result["sprite_id"], "frames": len(result["frames"])}))


if __name__ == "__main__":
    main()
