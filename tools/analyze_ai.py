"""Build static AI evidence from retained scripts and existing slice timelines.

This is a source index, not an AS2 compiler or a runtime equivalence test.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "evidence/ai/source-audit.json"
FUNCTION = re.compile(r"^function (\w+)\([^\n]*\)\r?\n\{\r?\n.*?^\}", re.M | re.S)
CORE_FUNCTIONS = {
    "randAI", "initCtrl", "hurtSkill", "doHurtSkill", "dash", "doDashX",
    "onDashing", "zhaoHuan", "doZhaoHuan", "beidax", "doWanKai",
}


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def functions(source: str) -> dict[str, str]:
    # Pinned JPEXS exports put named top-level functions at column zero.
    return {m[1]: m[0] for m in FUNCTION.finditer(source)}


def ref(path: Path, script: dict) -> dict:
    return {
        "bundle": path.relative_to(ROOT).as_posix(),
        "path": script["path"],
        "source_sha256": sha(script["source"].encode()),
    }


def build() -> dict:
    inputs = {}
    controllers = {}
    core = {}
    difficulty = []
    random_sites = []
    main_links = []
    bundles = {}
    for path in sorted((ROOT / "scripts").rglob("*.json")):
        data = json.loads(path.read_text())
        relative = path.relative_to(ROOT).as_posix()
        bundles[relative] = data
        inputs[relative] = sha(path.read_bytes())
        assert sha((ROOT / data["game_file"]).read_bytes()) == data["swf_sha256"]
        for script in data["scripts"]:
            source = script["source"]
            origin = ref(path, script)
            is_controller = "function moveLeft()" in source and "function defence()" in source
            if is_controller:
                controllers.setdefault(source, []).append(origin)
            if not is_controller and path.parent == ROOT / "scripts/fighter":
                for name, body in functions(source).items():
                    if name in CORE_FUNCTIONS:
                        core.setdefault(name, {}).setdefault(body, []).append(origin)
            for line, text in enumerate(source.splitlines(), 1):
                if re.search(r"\b_root\.AI\b|\bAI\s*=", text):
                    difficulty.append({**origin, "line": line, "text": text.strip()})
                if re.search(r"Math\.random\s*\(|(?<![\w.])random\s*\(", text):
                    random_sites.append({**origin, "line": line, "text": text.strip()})
            if relative == "scripts/main.json" and re.search(
                r"p[12]cpu|airanset|initCtrl\(|function pauseGame|clearint", source
            ):
                main_links.append(origin)

    base_source = next(
        s["source"] for s in bundles["scripts/fighter/minren.json"]["scripts"]
        if s["path"] == "DefineSprite_16/frame_1/DoAction.as"
    )
    base_functions = functions(base_source)
    groups = []
    for source, origins in sorted(controllers.items(), key=lambda item: (-len(item[1]), item[1][0]["bundle"], item[1][0]["path"])):
        funcs = functions(source)
        groups.append({
            "source_sha256": sha(source.encode()),
            "occurrences": origins,
            "changed_functions_from_minren": [n for n, s in funcs.items() if s != base_functions.get(n)],
            "missing_functions_from_minren": sorted(base_functions.keys() - funcs.keys()),
            "diff_from_minren": list(difflib.unified_diff(
                base_source.splitlines(), source.splitlines(),
                fromfile="minren/DefineSprite_16", tofile=origins[0]["bundle"] + "#" + origins[0]["path"], n=2,
            )),
        })

    slices = {}
    for name in ("minren", "yihu"):
        path = ROOT / f"data/slices/{name}-base.timeline.json"
        inputs[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
        timeline = json.loads(path.read_text())
        assert sha((ROOT / timeline["source_swf"]["path"]).read_bytes()) == timeline["source_swf"]["sha256"]
        scripts = bundles[f"scripts/fighter/{name}.json"]["scripts"]
        sprite = timeline["sprite_id"]
        prefix = f"DefineSprite_{sprite}/"
        ai = next(p for p in timeline["frames"][0]["display_list"] if p.get("name") == "AImain")
        definition = next(d for d in timeline["definitions"] if d["character_id"] == ai["character_id"])
        hooks = []
        for script in scripts:
            match = re.fullmatch(prefix + r"frame_(\d+)/PlaceObject\d+_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\)\.as", script["path"])
            if not match or int(match[2]) != 16:
                continue
            frame, character, depth = map(int, match.groups())
            membership = [
                f["frame"] for f in timeline["frames"]
                if any(p.get("depth") == depth and p.get("character_id") == character
                       and p.get("placed_frame") == frame for p in f["display_list"])
            ]
            hooks.append({
                "path": script["path"], "source": script["source"],
                "placement_frame": frame, "depth": depth,
                "linear_display_membership_frames": membership,
                "note": "Static display membership, not executed callback ticks or reachability.",
            })
        # Include every source path and explicit empty frames for the base timeline.
        frame_sources = {str(f["frame"]): [] for f in timeline["frames"]}
        for script in scripts:
            match = re.match(prefix + r"frame_(\d+)/", script["path"])
            if match:
                frame_sources[match[1]].append(script["path"])
        slices[name] = {
            "timeline": path.relative_to(ROOT).as_posix(), "sprite_id": sprite,
            "source_swf": timeline["source_swf"],
            "source_xml": timeline["source_xml"], "wrapper": timeline["wrapper"],
            "ai_placement": ai, "ai_definition": definition,
            "referenced_sensor_names": sorted(set(re.findall(r"AImain\.(\w+)\.hitTest", base_source))),
            "placed_sensor_names": sorted(p["name"] for p in definition["display_list_frames"][1]),
            "controller_hooks": sorted(hooks, key=lambda h: (h["placement_frame"], h["depth"])),
            "frame_source_index": frame_sources,
        }
    return {
        "status": "static_analysis_only",
        "scope": "All retained script bundles; geometry and callback membership only for two existing base slices.",
        "inputs_sha256": inputs,
        "counts": {
            "script_bundles": len(bundles),
            "fighter_bundles": sum(Path(p).parent.as_posix() == "scripts/fighter" for p in bundles),
            "controller_scripts": sum(len(v) for v in controllers.values()),
            "exact_controller_variants": len(groups),
            "randAI_definitions": sum(len(v) for v in core["randAI"].values()),
            "random_source_lines": len(random_sites),
        },
        "controller_groups": groups,
        "core_function_groups": {
            name: [{"function_sha256": sha(body.encode()), "source": body, "occurrences": origins}
                   for body, origins in variants.items()]
            for name, variants in sorted(core.items())
        },
        "difficulty_references": difficulty,
        "random_source_lines": random_sites,
        "main_lifecycle_sources": main_links,
        "base_slices": slices,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed audit is stale")
    args = parser.parse_args()
    report = build()
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != encoded:
            print("AI source audit is stale; run python3 tools/analyze_ai.py")
            return 1
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(encoded)
    print(json.dumps(report["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
