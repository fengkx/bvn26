"""Compile the retained shared hurtVoice branch and verify missing linkages."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from analyze_ai import functions, sha
from inspect_swf import inspect


def build(fighters: list[str] | None = None) -> None:
    names = ["voice_hurt1", "voice_hurt2", "voice_die"]
    inputs = {}
    for path in sorted((ROOT / "game").rglob("*.swf")):
        swf = inspect(path)
        inputs[path.relative_to(ROOT).as_posix()] = swf["sha256"]
        if any(item["name"] in names for item in swf["exports"]):
            raise ValueError("Voice linkage now exists; materialize it before compiling")
    main = json.loads((ROOT / "scripts/main.json").read_text())
    main_source = next(s["source"] for s in main["scripts"] if s["path"] == "frame_8/DoAction.as")
    selector = functions(main_source)["getRandInArray"]
    selector_offset = main_source.index(selector) + selector.index("Math.random()")
    selector_index = main_source[:selector_offset].count("Math.random()") + 1
    for name in fighters or ["minren", "yihu"]:
        sprite = json.loads((ROOT / f"data/slices/{name}-base.timeline.json").read_text())["sprite_id"]
        bundle = json.loads((ROOT / f"scripts/fighter/{name}.json").read_text())
        path = f"DefineSprite_{sprite}/frame_1/DoAction.as"
        source = next(s["source"] for s in bundle["scripts"] if s["path"] == path)
        voice = functions(source)["hurtVoice"]
        hit = functions(source)["onBeHit"]
        threshold = re.search(r"jhp <= (\d+) \? ([\d.]+) : ([\d.]+)", hit)
        flying_probability = re.search(r"var _loc4_ = ([\d.]+);", hit)
        if sha(voice.encode()) != "dbd7fad57954ea4dbe79ba614ec8215b6613aa83d7e8f9b5201db69e251caedb":
            raise ValueError("Unsupported hurtVoice control flow")
        offset = source.index(voice) + voice.index("Math.random()")
        ordinal = source[:offset].count("Math.random()") + 1
        if len(re.findall(r'getTimer\(\)', voice)) != 4:
            raise ValueError("Unexpected hurtVoice clock sites")
        clock_sites = {key: f"fighter/{name}#{path}#hurtVoice:getTimer:{i + 1}"
                       for i, key in enumerate(("death_check", "death_write", "hurt_check", "hurt_write"))}
        spec = {"clock_sites": clock_sites,
            "source_path": path, "source_sha256": sha(voice.encode()),
            "source": voice, "selector_source": selector,
            "probability_site": f"fighter/{name}#{path}:{ordinal}",
            "selector_site": f"main#frame_8/DoAction.as:{selector_index}",
            "death_cooldown_ms": int(re.search(r"_dievoicen < (\d+)", voice)[1]),
            "hurt_cooldown_ms": int(re.search(r"_lastvoice < (\d+)", voice)[1]),
            "damage_threshold": int(threshold[1]),
            "low_damage_probability": float(threshold[2]),
            "high_damage_probability": float(threshold[3]),
            "flying_probability": float(flying_probability[1]),
            "hurt_linkages": names[:2], "death_linkage": names[2],
            "linkages_absent_in": inputs,
        }
        (ROOT / f"godot/generated/fighters/{name}/hurt_voice.json").write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fighters", nargs="*")
    build(parser.parse_args().fighters)
