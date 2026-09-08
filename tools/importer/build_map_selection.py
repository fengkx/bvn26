# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pillow==12.3.0",
# ]
# ///
"""Compile the original map menu geometry, navigation and raster presentation.

The temporary SWF freezes each thumbnail's bg.gotoAndStop(_name) and txt.text
assignments for JPEXS rasterization. It is never a production dependency.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageFilter
from extract_timeline_geometry import extract_frames, file_sha256


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build(workspace: Path, temporary: Path, output: Path, jar: Path) -> None:
    temporary.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    xml = workspace / "main.xml"
    report = json.loads((workspace / "export-report.json").read_text())
    if report["source"]["sha256"] != file_sha256(Path("game/main.swf")):
        raise ValueError("Export workspace does not match locked source SWF")
    root = ET.parse(xml).getroot()
    tags = root.find("tags")
    sprites = {
        int(x.get("spriteId")): x for x in tags if x.get("type") == "DefineSpriteTag"
    }
    scripts = {
        s["path"]: s["source"]
        for s in json.loads(Path("scripts/main.json").read_text())["scripts"]
    }
    controller = scripts["DefineSprite_1505/frame_1/DoAction.as"]
    assert "init(2);" in controller and "updateXY(1,1,0)" in controller
    assert "var p2enable = false;" in controller
    repeat = int(re.search(r'czint" \+ player\] < (\d+)', controller)[1])
    delay = int(
        re.search(r"setTimeout\(function\(\).*?\}\s*,\s*(\d+)\);", controller, re.S)[1]
    )
    outer = extract_frames(xml, None)["frames"][45]["display_list"]
    outer_map = next(p for p in outer if p.get("name") == "xure")["matrix"]
    menu_timeline = extract_frames(xml, 1506)
    frames = [f for f in menu_timeline["frames"] if 35 <= f["frame"] <= 50]
    placement = next(p for p in frames[0]["display_list"] if p.get("name") == "xrmc")[
        "matrix"
    ]
    cards = extract_frames(xml, 1505)["frames"][0]["display_list"]
    backgrounds = extract_frames(xml, 1501)
    background_frames = {
        label: f for f in backgrounds["frames"] for label in f["labels"]
    }
    bg_tags = list(sprites[1501].find("subTags"))
    # Each labelled map background is one shape, with no nested action to execute.
    card_template = sprites[1504]
    text_template = next(x for x in tags if x.get("characterID") == "1503")
    exported_ids = []
    label_ids = []
    entries = []
    for index, card in enumerate(cards):
        name = card["name"]
        sprite_id = 3000 + index * 3
        text_id = sprite_id + 1
        bg_id = sprite_id + 2
        text = copy.deepcopy(text_template)
        text.set("characterID", str(text_id))
        text.set("html", "false")
        text.set("initialText", name)
        bg = copy.deepcopy(sprites[1501])
        bg.set("spriteId", str(bg_id))
        bg.set("frameCount", "1")
        subtags = bg.find("subTags")
        subtags.clear()
        bg_shape = background_frames[name]["display_list"][0]["character_id"]
        place = copy.deepcopy(next(x for x in bg_tags if x.get("characterId")))
        place.set("characterId", str(bg_shape))
        subtags.append(place)
        subtags.append(ET.Element("item", {"type": "ShowFrameTag"}))
        symbol = copy.deepcopy(card_template)
        symbol.set("spriteId", str(sprite_id))
        for child in list(symbol.find("subTags")):
            if child.get("type") == "DoActionTag":
                symbol.find("subTags").remove(child)
            elif child.get("characterId") == "1501":
                child.set("characterId", str(bg_id))
            elif child.get("characterId") == "1503":
                symbol.find("subTags").remove(child)
        label_id = 5000 + index
        label_symbol = ET.Element(
            "item",
            {"type": "DefineSpriteTag", "spriteId": str(label_id), "frameCount": "1"},
        )
        children = ET.SubElement(label_symbol, "subTags")
        ET.SubElement(
            children,
            "item",
            {
                "type": "PlaceObject2Tag",
                "depth": "1",
                "characterId": str(text_id),
                "placeFlagHasCharacter": "true",
                "placeFlagMove": "false",
            },
        )
        ET.SubElement(children, "item", {"type": "ShowFrameTag"})
        tags.extend([text, bg, symbol, label_symbol])
        exported_ids.append(sprite_id)
        label_ids.append(label_id)
        m = card["matrix"]
        entries.append(
            {
                "id": name,
                "grid": [int(m["translateX"] / 600), int(m["translateY"] / 600)],
                "position": [
                    (
                        outer_map["translateX"]
                        + placement["translateX"]
                        + m["translateX"]
                    )
                    / 20,
                    (
                        outer_map["translateY"]
                        + placement["translateY"]
                        + m["translateY"]
                    )
                    / 20,
                ],
                "texture": f"card_{index}.png",
            }
        )
    footer_ids = []
    for index, name in enumerate([entry["id"] for entry in entries] + ["魂"]):
        sprite_id = 4000 + index * 2
        text_id = sprite_id + 1
        text = copy.deepcopy(next(x for x in tags if x.get("characterID") == "670"))
        text.set("characterID", str(text_id))
        text.set("hasText", "true")
        text.set("initialText", name)
        symbol = ET.Element(
            "item",
            {"type": "DefineSpriteTag", "spriteId": str(sprite_id), "frameCount": "1"},
        )
        children = ET.SubElement(symbol, "subTags")
        ET.SubElement(
            children,
            "item",
            {
                "type": "PlaceObject2Tag",
                "depth": "1",
                "characterId": str(text_id),
                "placeFlagHasCharacter": "true",
                "placeFlagMove": "false",
            },
        )
        ET.SubElement(children, "item", {"type": "ShowFrameTag"})
        tags.extend([text, symbol])
        footer_ids.append(sprite_id)
    asset_link = temporary / "main_assets"
    if not asset_link.exists():
        asset_link.symlink_to(
            (workspace / "main_assets").resolve(), target_is_directory=True
        )
    modified_xml = temporary / "cards.xml"
    ET.ElementTree(root).write(modified_xml, encoding="utf-8", xml_declaration=True)
    derived_swf = temporary / "cards.swf"

    def run(*args: str) -> None:
        subprocess.run(
            ["java", "-Djava.awt.headless=true", "-jar", str(jar), *map(str, args)],
            check=True,
        )

    run("-xml2swf", modified_xml, derived_swf)
    run(
        "-zoom",
        "2",
        "-selectid",
        ",".join(map(str, exported_ids + footer_ids + label_ids)),
        "-export",
        "sprite",
        temporary / "raster",
        derived_swf,
    )
    run("-selectid", "1276", "-export", "sprite", temporary / "raster", "game/main.swf")
    run(
        "-selectid",
        "1478,668",
        "-format",
        "shape:png",
        "-export",
        "shape",
        temporary / "raster",
        "game/main.swf",
    )
    for index, sprite_id in enumerate(exported_ids):
        with Image.open(
            temporary / "raster" / f"DefineSprite_{sprite_id}" / "1.png"
        ) as image:
            card_image = image.crop(image.getbbox()).convert("RGBA")
        with Image.open(
            temporary / "raster" / f"DefineSprite_{label_ids[index]}" / "1.png"
        ) as image:
            label = image.crop(image.getbbox()).convert("RGBA")
        # JPEXS composites this source DROPSHADOWFILTER over its text. Compose
        # the original white glyph above the shadow, as Flash compositeSource does.
        glyphs = Image.new("RGBA", card_image.size)
        glyphs.alpha_composite(
            label,
            (card_image.width - label.width - 6, card_image.height - label.height - 4),
        )
        alpha = (
            glyphs.getchannel("A")
            .filter(ImageFilter.GaussianBlur(3.0))
            .point(lambda value: min(255, value * 3))
        )
        alpha = alpha.transform(
            alpha.size,
            Image.Transform.AFFINE,
            (1, 0, -1.4142, 0, 1, -1.4142),
            resample=Image.Resampling.BILINEAR,
        )
        shadow = Image.new("RGBA", card_image.size, (0, 0, 0, 0))
        shadow.putalpha(alpha)
        card_image.alpha_composite(shadow)
        card_image.alpha_composite(glyphs)
        card_image.save(output / f"card_{index}.png")
    for index, sprite_id in enumerate(footer_ids):
        with Image.open(
            temporary / "raster" / f"DefineSprite_{sprite_id}" / "1.png"
        ) as image:
            image.crop(image.getbbox()).save(output / f"name_{index}.png")
    for frame in range(1, 5):
        shutil.copyfile(
            temporary / "raster" / "DefineSprite_1276" / f"{frame}.png",
            output / f"background_{frame}.png",
        )
    for id, name in [(1478, "wipe"), (668, "footer")]:
        with Image.open(temporary / "raster" / f"{id}.png") as image:
            image.crop(image.getbbox()).save(output / f"{name}.png")
    # Rasterized source text avoids shipping a substitute font for Flash device text.
    # Use the thumbnail's right-aligned name for the 30 ms typing footer too.
    for index in range(len(entries)):
        with Image.open(output / f"card_{index}.png") as image:
            entries[index]["texture_size"] = list(image.size)
    sound_names = {}
    for key in ["keysound1", "keysound2"]:
        source = (
            scripts["frame_8/DoAction.as"]
            if key in scripts.get("frame_8/DoAction.as", "")
            else scripts["frame_7/DoAction.as"]
        )
        match = re.search(rf'{key}\.attachSound\("([^"]+)"\)', source)
        if match:
            name = match[1]
            for item in tags:
                if item.get("type") == "ExportAssetsTag":
                    ids = [e.text for e in item.find("tags")]
                    names = [e.text for e in item.find("names")]
                    if name in names:
                        sound_id = ids[names.index(name)]
                        sound = next(
                            p
                            for p in (workspace / "main_assets" / "sounds").glob(
                                "*.mp3"
                            )
                            if p.name == f"{sound_id}.mp3"
                            or p.name.startswith(f"{sound_id}_")
                        )
                        shutil.copyfile(sound, output / f"{key}.mp3")
                        sound_names[key] = f"{key}.mp3"
    border = next(x for x in tags if x.get("shapeId") == "1502").find("shapeBounds")
    card_rect = [
        int(border.get("Xmin")) / 20,
        int(border.get("Ymin")) / 20,
        (int(border.get("Xmax")) - int(border.get("Xmin"))) / 20,
        (int(border.get("Ymax")) - int(border.get("Ymin"))) / 20,
    ]
    spec = {
        "source_sha256": file_sha256(Path("game/main.swf")),
        "controller_path": "DefineSprite_1505/frame_1/DoAction.as",
        "raster_scale": 2,
        "cards": entries,
        "repeat_frames": repeat,
        "confirm_delay_ms": delay,
        "initial_grid": [1, 0],
        "unselected_alpha": 0.5,
        "selected_alpha": 1.0,
        "entry_frame": 35,
        "stop_frame": 50,
        "card_rect": card_rect,
        "footer_position": [0, 381.5],
        "footer_name_position": [7.5, 385.85],
        "typing_interval_ms": 30,
        "transition_frames": frames,
        "outer_matrix": outer_map,
        "sounds": sound_names,
    }
    write_json(output / "presentation.json", spec)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--temporary", type=Path, required=True)
    p.add_argument(
        "--output", type=Path, default=Path("godot/generated/main/map_selection")
    )
    p.add_argument("--ffdec-jar", type=Path, required=True)
    a = p.parse_args()
    build(a.workspace, a.temporary, a.output, a.ffdec_jar)
