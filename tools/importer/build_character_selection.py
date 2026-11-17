"""Extract the shared original fighter/assist selector and its display lists."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from extract_timeline_geometry import extract_frames, file_sha256

ROOT = Path(__file__).resolve().parents[2]


def _runtime_slug(entry: dict, *, helper: bool) -> str | None:
    source = entry.get("fzurl" if helper else "url")
    return Path(source).stem.lower() if source else None


def _artifact_ready(directory: Path, required: tuple[str, ...]) -> bool:
    return all((directory / path).is_file() for path in required)


def build_available(root: Path = ROOT) -> dict[str, dict]:
    """Publish only source catalog entries with complete native artifacts.

    Selection cards remain source-defined in ``selection.json``. This separate
    registry is derived from the same manifest and the generated artifact
    contract, so hand-added cards cannot silently become selectable before
    their runtime/controller files exist. The current main scene uses the
    player controller for both P2-human and P2-CPU dispatch; AI controller
    artifacts remain optional for this selector contract and are checked by
    the dedicated CPU tests where present.
    """
    catalog = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["fighter_catalog"]
    fighter_required = (
        "fighter.json", "timeline.json", "combat.json", "assets.json", "ai.json",
        "hurt_voice.json", "ai_hit_state.gd",
        "player_controller/body.gd", "player_controller/body.json",
        "player_controller/controller.gd", "player_controller/predicates.gd",
    )
    helper_required = ("timeline.json", "combat.json", "assets.json")
    available = {"fighters": {}, "helpers": {}, "forms": {}}
    selection = json.loads((root / "data/menus/character-selection.json").read_text())
    selectable = {card["id"] for phase in selection["phases"]
                  if phase["kind"] == "fighter" for card in phase["cards"]}
    for kind, helper in (("fighters", False), ("helpers", True)):
        base = root / "godot/generated/helpers" if helper else root / "godot/generated/fighters"
        for name, entry in catalog.items():
            slug = _runtime_slug(entry, helper=helper)
            if slug is None:
                continue
            directory = base / slug
            form = int(entry.get("WKframe", 1)) if not helper else 1
            if form > 1:
                if name not in selectable:
                    continue
                graph_path = directory / "form_profiles.json"
                if not graph_path.is_file():
                    continue
                graph = json.loads(graph_path.read_text())
                profile = graph.get("profiles", {}).get(str(form), {})
                form_slug = f"{slug}-{form}"
                expected = f"res://generated/forms/{form_slug}"
                if profile.get("directory") != expected:
                    continue
                directory = root / "godot/generated/forms" / form_slug
            required = helper_required if helper else fighter_required
            if not _artifact_ready(directory, required):
                continue
            if helper:
                model = json.loads((directory / "combat.json").read_text(encoding="utf-8"))
                if model.get("helper_id") != name:
                    continue
            else:
                model = json.loads((directory / "fighter.json").read_text(encoding="utf-8"))
                if model.get("fighter_id") != name or int(model.get("form_frame", 0)) != form:
                    continue
            if form > 1:
                available["forms"][form_slug] = {"base": slug, "frame": form}
                slug = form_slug
            available[kind][name] = slug
    return available


def build(workspace: Path, output: Path) -> dict:
    xml = workspace / "main.xml"
    report = json.loads((workspace / "export-report.json").read_text())
    if report["source"]["sha256"] != file_sha256(ROOT / "game/main.swf"):
        raise ValueError("Workspace is not the locked original")
    record = next(f for f in report["files"] if f["path"] == "main.xml")
    if record["sha256"] != file_sha256(xml):
        raise ValueError("Exported source XML was modified")
    scripts = {s["path"]: s["source"] for s in json.loads((ROOT / "scripts/main.json").read_text())["scripts"]}
    controllers = [scripts[f"DefineSprite_{sid}/frame_1/DoAction.as"] for sid in (1477, 1480, 1505)]
    normalized = [re.sub(r"init\([012]\);", "init(TYPE);", s) for s in controllers]
    if len(set(normalized)) != 1:
        raise ValueError("Original selection controllers no longer share one implementation")
    outer = extract_frames(xml, None)["frames"][45]["display_list"]
    selector = extract_frames(xml, 1506)
    portraits = extract_frames(xml, 1465)
    labels = {label: f["frame"] for f in portraits["frames"] for label in f["labels"]}
    catalog = json.loads((ROOT / "manifest.json").read_text())["fighter_catalog"]
    phases = []
    for kind, sid, entry, stop in (("fighter", 1477, 1, 15), ("helper", 1480, 20, 32)):
        cards = []
        for item in extract_frames(xml, sid)["frames"][0]["display_list"]:
            name = item.get("name", "")
            if name in ("player1", "player2"):
                continue
            if name not in catalog or name not in labels:
                raise ValueError(f"Missing original portrait/catalog: {name}")
            matrix = item["matrix"]
            cards.append({"id": name, "display_name": catalog[name]["name"],
                          "grid": [int(matrix["translateX"] / 600), int(matrix["translateY"] / 600)],
                          "placement": item, "portrait_frame": labels[name],
                          "is_naruto": bool(catalog[name].get("isNaruto", False))})
        phases.append({"kind": kind, "sprite_id": sid, "entry_frame": entry,
                       "stop_frame": stop, "cards": cards})
    source = controllers[0]
    result = {"format": "bvn26-character-selection-v1", "status": "source_extracted_pending_reference",
              "source_swf_sha256": report["source"]["sha256"],
              "controller_paths": [f"DefineSprite_{sid}/frame_1/DoAction.as" for sid in (1477, 1480, 1505)],
              "controller_sha256": [hashlib.sha256(s.encode()).hexdigest() for s in controllers],
              "repeat_frames": int(re.search(r'czint" \+ player\] < (\d+)', source)[1]),
              "confirm_delay_ms": int(re.search(r'setTimeout\(function\(\).*?\}\s*,(\d+)\);', source, re.S)[1]),
              "phases": phases, "outer_display_list": outer,
              "selector_frames": selector["frames"],
              "phase_scripts": [{"path": path, "source": text} for path, text in scripts.items()
                                if path.startswith("DefineSprite_1506/")],
              "mode_source": [{"path": path, "source": text} for path, text in scripts.items()
                              if '_root.gotoAndStop("选人画面")' in text and '_root.modo =' in text],
              "reference_status": "pending"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    runtime = dict(result)
    runtime.pop("mode_source")
    runtime.pop("phase_scripts")
    runtime_output = ROOT / "godot/generated/main/character_selection/selection.json"
    runtime_output.parent.mkdir(parents=True, exist_ok=True)
    runtime_output.write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n")
    (runtime_output.parent / "available.json").write_text(
        json.dumps(build_available(), ensure_ascii=False, indent=2) + "\n"
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data/menus/character-selection.json")
    args = parser.parse_args()
    result = build(args.workspace, args.output)
    print(json.dumps({p["kind"]: len(p["cards"]) for p in result["phases"]}))
