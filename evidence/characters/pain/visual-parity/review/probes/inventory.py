import os
import json, collections
from pathlib import Path

rows = []
for path in sorted(Path("godot/generated").rglob("timeline.json")):
    d = json.loads(path.read_text())
    defs = {x["character_id"]: x for x in d["definitions"]}
    key = str(path.parent).removeprefix("godot/generated/").replace("/", "-")
    for x in d["definitions"]:
        es = [
            {"frame": i + 1, "controls": e["visual_controls"]}
            for i, ev in enumerate(x.get("display_list_frame_events", []))
            for e in ev
            if e.get("visual_controls")
        ]
        if es or (x.get("type") == "DefineSpriteTag" and x.get("frame_count", 1) > 1):
            rows.append(
                {
                    "id": key + "-clock-" + str(x["character_id"]),
                    "kind": "clock",
                    "timeline": str(path),
                    "source": d.get("source_swf", {"path": "game/main.swf"}),
                    "symbol": x["character_id"],
                    "frame_count": x["frame_count"],
                    "controls": es,
                }
            )
    owners = [(d["sprite_id"], [f["display_list"] for f in d["frames"]])] + [
        (x["character_id"], x["display_list_frames"])
        for x in d["definitions"]
        if x.get("display_list_frames")
    ]
    seen = {}
    for owner, frames in owners:
        for frame, ps in enumerate(frames, 1):
            for p in ps:
                if p.get("blend_mode", 1) in (0, 1):
                    continue
                ident = (
                    owner,
                    p["depth"],
                    p["character_id"],
                    p.get("placed_frame", 1),
                    p["blend_mode"],
                )
                if ident in seen:
                    seen[ident]["last_frame"] = frame
                    continue
                row = {
                    "id": key + "-blend-" + "-".join(map(str, ident)),
                    "kind": "blend",
                    "timeline": str(path),
                    "source": d.get("source_swf", {"path": "game/main.swf"}),
                    "owner": owner,
                    "source_frame": frame,
                    "last_frame": frame,
                    "placement": p,
                    "symbol": p["character_id"],
                    "frame_count": defs[p["character_id"]].get("frame_count", 1),
                }
                seen[ident] = row
                rows.append(row)
Path(
    os.path.join(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "inventory.json")
).write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
print(collections.Counter(r["kind"] for r in rows))
print(
    collections.Counter(
        r["placement"]["blend_mode"] for r in rows if r["kind"] == "blend"
    )
)
