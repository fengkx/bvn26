"""Create an isolated, instrumented single-player project; never edit production runtime."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "tools/g0"
BUTTONS = ("up", "down", "left", "right", "attack", "jump", "dash", "ranged", "special", "summon")


def wrap(source: str, name: str, kind: str, arguments: str = "") -> str:
    pattern = rf"^func {name}\((.*)\) -> void:\n"
    matches = list(re.finditer(pattern, source, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError(f"Expected one void method: {name}")
    match = matches[0]
    signature = match.group(0)
    wrapper = (signature + '\tpreload("res://g0/timing.gd").begin("' + kind + '")\n'
               + f"\t_g0_original{name}({arguments})\n"
               + '\tpreload("res://g0/timing.gd").end()\n\n\n'
               + signature.replace(f"func {name}(", f"func _g0_original{name}("))
    return source[:match.start()] + wrapper + source[match.end():]


def workload() -> list[dict]:
    rows = []
    for tick in range(1, 901):
        players = {slot: dict.fromkeys(BUTTONS, False) for slot in ("p1", "p2")}
        # Fixed sampled inputs, with an idle opponent; initial energy is frozen by the fixture.
        for start, stop, buttons in ((165, 190, ["right"]), (195, 200, ["attack"]),
                                     (235, 237, ["ranged"]), (300, 302, ["summon"]),
                                     (450, 452, ["down", "special"]), (600, 602, ["special"]),
                                     (750, 752, ["summon"])):
            if start <= tick < stop:
                for button in buttons: players["p1"][button] = True
        rows.append({"tick": tick, "segment": "warmup" if tick < 165 else "normal" if tick < 300 else "heavy_candidate", "players": players})
    return rows


def prepare(destination: Path) -> dict:
    destination = destination.resolve()
    if destination.exists() or destination.is_relative_to(ROOT) or str(destination).startswith(("/tmp/", "/private/tmp/")):
        raise ValueError("Use a new external non-/tmp staging directory")
    shutil.copytree(ROOT / "godot", destination, ignore=shutil.ignore_patterns(".godot"))
    shutil.copytree(ASSETS, destination / "g0")
    inventory = []
    for path in sorted(destination.rglob("*.gd")):
        if "tests" in path.parts or "g0" in path.parts: continue
        source = path.read_text()
        methods = []
        if path.name == "main.gd": methods.append(("_advance_fight", "advance", "recorded_events, root_observer, event_supplier"))
        if path.name == "timeline_preview.gd": methods.append(("materialize_display", "materialize", ""))
        if re.search(r"^func _draw\(\) -> void:", source, re.MULTILINE): methods.append(("_draw", "draw", ""))
        for name, kind, arguments in methods:
            source = wrap(source, name, kind, arguments)
            inventory.append({"file": str(path.relative_to(destination)), "method": name, "kind": kind})
        if methods: path.write_text(source)
    (destination / "g0/tape.json").write_text(json.dumps(workload(), ensure_ascii=False))
    (destination / "g0/main.tscn").write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://g0/workload.gd" id="1"]\n[node name="G0" type="Node"]\nscript = ExtResource("1")\n')
    project = destination / "project.godot"
    project.write_text(project.read_text().replace('run/main_scene="res://render_surface.tscn"', 'run/main_scene="res://g0/main.tscn"').replace('window_width_override=900', 'window_width_override=600').replace('window_height_override=600', 'window_height_override=400'))
    preset = destination / "export_presets.cfg"
    preset.write_text(preset.read_text().replace('res://web/shell.html', 'res://g0/shell.html'))
    files = {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(destination.rglob("*")) if p.is_file()}
    identity = {"source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
                "files": files, "instrumented_methods": inventory, "g0_passed": False}
    (destination / "g0/identity.json").write_text(json.dumps(identity, indent=2))
    return identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    identity = prepare(args.stage)
    print(json.dumps({"stage": str(args.stage), "instrumented_methods": identity["instrumented_methods"]}))


if __name__ == "__main__": main()
