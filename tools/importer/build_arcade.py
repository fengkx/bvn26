"""Build Single Play routes and native presentation clips from the locked main movie."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops

from materialize_stage_music import selection_steps

OUT = Path("godot/generated/main/arcade")
AVAILABLE = Path("godot/generated/main/character_selection/available.json")
MUSIC = Path("godot/generated/stages/catalog/music")
SCENES = {"tutorial": 1267, "continue": 2050, "gameover": 2055, "ending": 2075}


def write_json(path, value):
    if "changes" in value:
        # Keep a line per source frame even in long, densely packed clips.
        rows = [f'    "{frame}": ' + json.dumps(rects, separators=(",", ":"))
                for frame, rects in value["changes"].items()]
        path.write_text('{\n' + '  "pages": ' + json.dumps(value["pages"])
                        + ',\n  "changes": {\n' + ',\n'.join(rows) + '\n  }\n}\n')
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def compile_routes(manifest, available, source):
    def array(name):
        return json.loads(re.search(rf'var {name} = (\[.*?\]);', source)[1])

    catalog = manifest["fighter_catalog"]
    last = int(re.search(r'_root.totalstage = (\d+);', source)[1])
    boss = re.search(r'var bossStage = "(.*?)";', source)[1]
    routes, encounters, hidden = {}, {}, {}
    music = set()
    for player in available["fighters"]:
        actor = catalog[player]
        first = array("narutoStages" if actor.get("isNaruto") else "bleachStages")
        rivals = actor.get("vs") or array("bleachElseStages" if actor.get("isNaruto") else "narutoElseStages")
        route = first + rivals + [boss]
        assert len(route) == last + 1
        routes[player] = []
        for stage, foe in enumerate(route):
            data = catalog[foe]
            arena = data.get("map") or array("narutoStageMaps" if data.get("isNaruto") else "bleachStageMaps")[stage]
            key = f"{foe}/{arena}"
            routes[player].append(key)
            steps, _ = selection_steps(manifest, foe, arena)
            music.update(step["file"] for step in steps)
            assert data["fz"] in available["helpers"]
            encounters[key] = {"fighter": foe, "helper": data["fz"], "map": arena, "music": steps}
            if foe not in available["fighters"]:
                base = Path(data["url"]).stem.lower()
                resource = f'{base}-{data["WKframe"]}'
                assert Path("godot/generated/forms", resource, "player_controller/controller.json").is_file()
                hidden[foe] = {"id": resource, "base": base, "frame": data["WKframe"], "portrait": data["clone_of"]}
    for filename in music:
        if not (MUSIC / filename).is_file():
            shutil.copyfile(Path("game/music", filename), MUSIC / filename)
    return {"routes": routes, "encounters": encounters, "forms": hidden,
            "quotes": {p: catalog[p].get("says", []) for p in routes}}


def pack_frames(folder, length):
    # A keyframe at the tutorial skip label lets the player jump there directly.
    # Store only changed pixels; stopped timelines require no image uploads.
    pages = []
    changes = {}
    page = Image.new("RGB", (600, 800))
    x = y = row = 0
    previous = None

    def flush():
        # The player composites patches on the CPU and uploads only the canvas.
        crop = page.crop((0, 0, page.width, y + row))
        name = f"{folder.name}-{len(pages)}.bvnwebp"
        crop.save(OUT / name, format="WEBP", lossless=True, method=2)
        pages.append(name)

    for frame in range(1, length + 1):
        with Image.open(folder / f"{frame}.png") as png:
            image = png.convert("RGB")
        bounds = (0, 0, *image.size) if previous is None or (folder.name == "tutorial" and frame == 1249) else ImageChops.difference(image, previous).getbbox()
        previous = image
        if bounds is None:
            continue
        patch = image.crop(bounds)
        w, h = patch.size
        if x + w > page.width:
            x, y, row = 0, y + row, 0
        if y + h > page.height:
            flush()
            page = Image.new("RGB", page.size)
            x = y = row = 0
        page.paste(patch, (x, y))
        changes[str(frame)] = [[len(pages), x, y, w, h, bounds[0], bounds[1]]]
        x += w
        row = max(row, h)
    flush()
    write_json(OUT / (folder.name + ".json"), {"pages": pages, "changes": changes})


def pack_victories(workspace, players):
    # Group shared tiles by frame so a winner decodes each required page only once.
    size = 50
    columns = 12
    capacity = columns * 8
    clips = {p: {"pages": [], "changes": {}} for p in players}
    previous = {p: {} for p in clips}
    for frame in range(1, 25):
        uses = Counter()
        patches = {}
        for player in clips:
            patches[player] = []
            with Image.open(workspace / "frames" / f"win-{player}" / f"{frame}.png") as png:
                image = png.convert("RGB")
            for y in range(0, image.height, size):
                for x in range(0, image.width, size):
                    tile = image.crop((x, y, x + size, y + size)).tobytes()
                    if previous[player].get((x, y)) == tile:
                        continue
                    previous[player][x, y] = tile
                    uses[tile] += 1
                    patches[player].append((tile, x, y))

        positions = {}
        ordered = [tile for tile, _ in uses.most_common()]
        for start in range(0, len(ordered), capacity):
            tiles = ordered[start:start + capacity]
            page = Image.new("RGB", (columns * size, ((len(tiles) + columns - 1) // columns) * size))
            name = f"victory-{frame}-{start // capacity}.bvnwebp"
            for index, tile in enumerate(tiles):
                left, top = index % columns * size, index // columns * size
                page.paste(Image.frombytes("RGB", (size, size), tile), (left, top))
                positions[tile] = (name, left, top)
            page.save(OUT / name, format="WEBP", lossless=True, method=2)

        for player, updates in patches.items():
            clip = clips[player]
            rects = []
            for tile, x, y in updates:
                name, left, top = positions[tile]
                if name not in clip["pages"]:
                    clip["pages"].append(name)
                rects.append([clip["pages"].index(name), left, top, size, size, x, y])
            if rects:
                # Tiles never overlap, so page order preserves the frame.
                clip["changes"][str(frame)] = sorted(rects, key=lambda rect: rect[0])
    for player, clip in clips.items():
        write_json(OUT / f"win-{player}.json", clip)


def build(jar, xml, workspace):
    bundle = json.loads(Path("scripts/main.json").read_text())
    assert hashlib.sha256(Path("game/main.swf").read_bytes()).hexdigest() == bundle["swf_sha256"]
    available = json.loads(AVAILABLE.read_text())
    setup = next(s["source"] for s in bundle["scripts"] if s["path"] == "frame_7/DoAction.as")
    OUT.mkdir(parents=True, exist_ok=True)
    spec = compile_routes(json.loads(Path("manifest.json").read_text()), available, setup)
    tags = ET.parse(xml).getroot().find("tags")
    workspace.mkdir(parents=True, exist_ok=True)
    names = workspace / "portraits.tsv"
    names.write_text("".join(f"{name}\t{id_}\n" for name, id_ in available["fighters"].items()))
    java = ["java", "-Xmx1400m", "-Djava.awt.headless=true"]
    subprocess.run(java + ["-cp", str(jar), str(Path(__file__).with_name("ArcadeFrames.java")),
                           "game/main.swf", str(workspace / "frames"), str(names)], check=True)
    package(jar, workspace, available, spec, tags)


def package(jar, workspace, available, spec, tags):
    java = ["java", "-Djava.awt.headless=true"]
    sounds = set()
    spec["screens"] = {}
    for name, sprite in SCENES.items():
        tag = next(t for t in tags if t.get("spriteId") == str(sprite))
        frame = 1
        cues = {}
        for item in tag.find("subTags"):
            if item.get("type") == "ShowFrameTag":
                frame += 1
            elif item.get("type") == "StartSoundTag":
                sound = item.get("soundId")
                sounds.add(sound)
                cues.setdefault(str(frame), []).append([sound, item[0].get("hasLoops") == "true"])
        spec["screens"][name] = {"length": int(tag.get("frameCount")), "sounds": cues}
    subprocess.run(java + ["-jar", str(jar), "-selectid", ",".join(sorted(sounds)), "-export",
                           "sound", str(workspace / "sounds"), "game/main.swf"], check=True, stdout=subprocess.DEVNULL)
    for sound in sounds:
        shutil.copyfile(workspace / "sounds" / f"{sound}.mp3", OUT / f"{sound}.mp3")
    for name in SCENES:
        length = spec["screens"][name]["length"]
        frames = workspace / "frames" / name
        pack_frames(frames, length)
    pack_victories(workspace, available["fighters"].values())
    write_json(OUT / "campaign.json", spec)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for arg in ("ffdec", "xml", "workspace"):
        parser.add_argument("--" + arg, required=True, type=Path)
    args = parser.parse_args()
    build(args.ffdec, args.xml, args.workspace)
