"""Retain Jinye's source placement graph without admitting its affine bitmap renderer."""
import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zlib

from PIL import Image

from tools.probes.build_bound_bitmap_component import ROOT, source_tags


def timeline(sprite):
    frame = 1
    live = {}
    frames, events, metadata = [], [], []
    for tag in sprite.find("subTags"):
        kind = tag.get("type")
        if kind == "ShowFrameTag":
            frames.append({"frame": frame, "placements": [dict(live[d]) for d in sorted(live)]})
            frame += 1
        elif kind == "PlaceObject2Tag":
            depth = int(tag.get("depth"))
            flags = {key: value for key, value in tag.attrib.items() if key.startswith("placeFlag")}
            permitted = {"placeFlagHasCharacter", "placeFlagHasMatrix", "placeFlagMove"}
            if any(value == "true" and key not in permitted for key, value in flags.items()):
                raise ValueError(f"DefineSprite_58/frame_{frame}/depth_{depth}: unhandled placement flag")
            if tag.get("placeFlagHasMatrix") != "true" or len(tag) != 1 or tag[0].tag != "matrix":
                raise ValueError(f"DefineSprite_58/frame_{frame}/depth_{depth}: unhandled placement payload")
            moving = tag.get("placeFlagMove") == "true"
            has_character = tag.get("placeFlagHasCharacter") == "true"
            if moving != (depth in live) or not moving and not has_character:
                raise ValueError(f"DefineSprite_58/frame_{frame}/depth_{depth}: inconsistent lifetime")
            character = int(tag.get("characterId")) if has_character else live[depth]["character_id"]
            if character not in (56, 57):
                raise ValueError(f"DefineSprite_58/frame_{frame}/depth_{depth}: unhandled character {character}")
            live[depth] = {"depth": depth, "character_id": character, "matrix": dict(tag[0].attrib)}
            events.append({"frame": frame, "depth": depth,
                           "operation": "replace" if moving and has_character else "move" if moving else "place",
                           "attributes": dict(tag.attrib), "matrix": dict(tag[0].attrib)})
        elif kind == "RemoveObject2Tag":
            depth = int(tag.get("depth"))
            if depth not in live:
                raise ValueError(f"DefineSprite_58/frame_{frame}/depth_{depth}: remove absent depth")
            del live[depth]
            events.append({"frame": frame, "depth": depth, "operation": "remove", "attributes": dict(tag.attrib)})
        elif kind == "SoundStreamHead2Tag":
            metadata.append({"frame": frame, "attributes": dict(tag.attrib)})
        else:
            raise ValueError(f"DefineSprite_58/frame_{frame}: unhandled tag {kind}")
    assert len(frames) == int(sprite.get("frameCount")) == 21 and not live
    return {"frames": frames, "events": events, "stream_metadata": metadata}


def inventory(xml):
    case = json.loads((ROOT / "evidence/importer-loud-fail/r32/components/jinye/cases.json").read_text())[0]
    source = ROOT / case["source"]["path"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == case["source"]["sha256"]
    tags = ET.parse(xml).getroot().find("tags")
    sprite = next(tag for tag in tags if tag.get("spriteId") == "58")
    root_frame = 1
    placements = []
    for tag in tags:
        if tag.get("type") == "ShowFrameTag":
            root_frame += 1
        if tag.get("characterId") == "58":
            placements.append({"frame": root_frame, "xml": ET.tostring(tag, encoding="unicode")})
    assert len(placements) == 1 and placements[0]["frame"] == 41
    raw = {struct.unpack_from("<H", payload)[0]: (code, payload, data)
           for code, payload, data in source_tags(source) if code in (2, 35, 39)}
    code, payload, _ = raw[55]
    assert code == 35
    jpeg_size = struct.unpack_from("<I", payload, 2)[0]
    jpeg = payload[6:6 + jpeg_size]
    alpha = zlib.decompress(payload[6 + jpeg_size:])
    image = Image.open(BytesIO(jpeg))
    assert len(alpha) == image.width * image.height
    shapes = []
    for identifier in (56, 57):
        shape = next(tag for tag in tags if tag.get("shapeId") == str(identifier))
        fills = list(shape.find("shapes/fillStyles/fillStyles"))
        records = list(shape.find("shapes/shapeRecords"))
        assert len(fills) == 2 and fills[1].get("bitmapId") == "55" and fills[1].get("fillStyleType") == "65"
        assert records[0].get("fillStyle1") == "2"
        shapes.append({"id": identifier, "xml": ET.tostring(shape, encoding="unicode"),
                       "active_fill": 2, "fill_type": 65, "bitmap": 55,
                       "bitmap_matrix": dict(fills[1][0].attrib),
                       "mask_records": [dict(record.attrib) for record in records]})
    graph = timeline(sprite)
    return {"source": case["source"], "case": case, "root_placements": placements,
            "raw_tag_sha256": {str(i): hashlib.sha256(raw[i][2]).hexdigest() for i in (55, 56, 57, 58)},
            "sprite_xml": ET.tostring(sprite, encoding="unicode"), "graph": graph, "shapes": shapes,
            "bitmap": {"id": 55, "tag": 35, "width": image.width, "height": image.height,
                       "jpeg_sha256": hashlib.sha256(jpeg).hexdigest(), "jpeg_bytes": len(jpeg),
                       "alpha_sha256": hashlib.sha256(alpha).hexdigest(), "alpha_bytes": len(alpha),
                       "alpha_histogram": dict(sorted(Counter(alpha).items()))},
            "required_unproven_rendering": ["JPEG3 bitmap55 decode", "affine clipped smoothed bitmap fill65",
                                            "quadrilateral coverage", "11 overlapping depth compositions",
                                            "animated cache bounds and replacement at frames10/20"],
            "stream_metadata_semantics_admitted": False,
            "ratio_consumption_proved": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.xml)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print({"frames": len(result["graph"]["frames"]), "events": len(result["graph"]["events"]),
           "bitmap": result["bitmap"], "production_admitted": False})
