"""Build source-first evidence for Byakuya's base timeline.

This is deliberately a source inventory. It does not assert original-player
parity or enable the deferred Bankai timeline.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from inspect_swf import inspect  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spans(labels: list[dict], end: int) -> dict[str, dict[str, int]]:
    result = {}
    for i, item in enumerate(labels):
        next_frame = labels[i + 1]["frame"] if i + 1 < len(labels) else end + 1
        result[item["label"]] = {"start_frame": item["frame"], "end_frame": next_frame - 1}
    return result


def main() -> None:
    swf = ROOT / "game/fighter/Byakuya.swf"
    bundle_path = ROOT / "scripts/fighter/Byakuya.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    info = inspect(swf)
    timeline = next(item for item in info["timelines"] if item["name"] == "sprite_631")
    scripts = bundle["scripts"]
    by_path = {item["path"]: item for item in scripts}
    frame_scripts = []
    prefix = "DefineSprite_631/"
    for item in scripts:
        if not item["path"].startswith(prefix):
            continue
        match = re.match(r"DefineSprite_631/frame_(\d+)/", item["path"])
        if match:
            frame_scripts.append({"frame": int(match[1]), "path": item["path"],
                                  "sha256": hashlib.sha256(item["source"].encode()).hexdigest()})
    frame_scripts.sort(key=lambda item: (item["frame"], item["path"]))
    controller_paths = [item["path"] for item in scripts
                        if item["path"].startswith("DefineSprite_631/frame_1/PlaceObject")]
    # The root placement owns the load callback; the selected body timeline
    # only exposes enterFrame callbacks for that placed instance.
    load_path = "frame_1/PlaceObject2_631_1/CLIPACTIONRECORD onClipEvent(load).as"
    load_source = by_path[load_path]["source"]
    speed = re.search(r"var spd = (-?\d+(?:\.\d+)?);", load_source)
    jump = re.search(r"var jumpPower = (-?\d+(?:\.\d+)?);", load_source)
    result = {
        "format": "bvn26-byakuya-source-audit-v1",
        "status": "source_inventory_not_behavior_acceptance",
        "scope": {"fighter_id": "白哉", "form": "base", "root_sprite": 631,
                  "excluded_label": "万解", "excluded_start_frame": 1105},
        "sources": {
            "swf": {"path": "game/fighter/Byakuya.swf", "sha256": info["sha256"]},
            "script_bundle": {"path": "scripts/fighter/Byakuya.json", "sha256": sha256(bundle_path)},
        },
        "root_placements": [{"frame": 1, "depth": 1, "character_id": 631},
                            {"frame": 2, "depth": 1, "character_id": 1052}],
        "timeline": {"name": timeline["name"], "declared_frames": timeline["declared_frames"],
                      "labels": timeline["labels"], "spans": spans(timeline["labels"], timeline["declared_frames"])},
        "frame_scripts": frame_scripts,
        "base_controller": {"load_path": load_path,
                            "speed_per_tick": float(speed[1]) if speed else None,
                            "jump_power": float(jump[1]) if jump else None,
                            "controller_candidates_at_frame_1": controller_paths},
        "nested_controller_placements": [
            {"frame": int(match[1]), "character_id": int(match[2]), "depth": int(match[3]),
             "path": item["path"],
             "source_sha256": hashlib.sha256(item["source"].encode()).hexdigest()}
            for item in scripts
            if (match := re.match(
                r"DefineSprite_631/frame_(\d+)/PlaceObject[23]_(\d+)_(\d+)/CLIPACTIONRECORD onClipEvent\(enterFrame\)\.as$",
                item["path"],
            ))
        ],
        "special_frame_scripts": [
            {"frame": int(match[1]), "path": item["path"],
             "source_sha256": hashlib.sha256(item["source"].encode()).hexdigest(),
             "source": item["source"]}
            for item in scripts
            if (match := re.match(r"DefineSprite_631/frame_(\d+)/DoAction\.as$", item["path"]))
            and 454 <= int(match[1]) <= 700
        ],
        "source_first": {
            "q1_frame_scripts": "Every source script under DefineSprite_631 is listed with frame and source hash; the complete source remains in the locked bundle.",
            "q2_placements": "Frame 1 places sprite 631 at depth 1; frame 2 replaces it with sprite 1052. The base body uses character 16 at depth 31, while later action placements include character 69 and other clips at distinct frames/depths. The complete callback placement inventory is retained above; a new placement does not inherit instance state.",
            "q3_exits": "The source labels and all frame scripts are retained. Label end is not treated as an implicit return. The first special label is one frame (454), while its source energy write is frame 455; the compiler must preserve this boundary instead of assigning the write by proximity.",
            "q4_invariants": ["Base form uses sprite 631 only.", "Bankai label begins at frame 1105 and remains disabled.", "Movement constants are read from the frame-1 placed controller load callback.", "Controller candidates from future placements must not be merged into the base controller."],
            "q5_same_input": "Not available yet: no serialized original-player same-input trace exists for Byakuya. This audit therefore cannot claim parity acceptance."
        },
    }
    output = ROOT / "evidence/characters/byakuya/source-audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "labels": len(timeline["labels"]),
                      "frame_scripts": len(frame_scripts), "sha256": info["sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
