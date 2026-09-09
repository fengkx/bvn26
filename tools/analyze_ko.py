"""Index retained KO scripts and SWF frame labels without running the movie."""
from pathlib import Path
import hashlib
import json
import re

from inspect_swf import inspect

ROOT = Path(__file__).resolve().parents[1]


def build() -> dict:
    path = ROOT / "scripts/main.json"
    bundle = json.loads(path.read_text())
    swf = inspect(ROOT / "game/main.swf")
    source_hash = hashlib.sha256((ROOT / "game/main.swf").read_bytes()).hexdigest()
    assert bundle["swf_sha256"] == source_hash
    records = bundle["scripts"]
    start = [s for s in records if s["source"].strip() == "_root.KOstart();"]
    assert len(start) == 1
    symbol = int(re.match(r"DefineSprite_(\d+)/", start[0]["path"])[1])
    timeline = next(t for t in swf["timelines"] if t["name"] == f"sprite_{symbol}")
    source = next(s["source"] for s in records if s["path"] == "frame_8/DoAction.as")
    functions = {}
    for name in ("KOplay", "KOstart", "KOend", "pauseGame", "resumeGame", "resumeGame2", "stopMc", "playMc"):
        match = re.search(r"^function " + name + r"\([^\n]*\n\{.*?^\}", source, re.M | re.S)
        assert match, name
        functions[name] = {"path": "frame_8/DoAction.as#" + name, "source": match[0],
                           "sha256": hashlib.sha256(match[0].encode()).hexdigest()}
    frames = {}
    for script in records:
        match = re.fullmatch(rf"DefineSprite_{symbol}/frame_(\d+)/DoAction.as", script["path"])
        if match:
            frames[int(match[1])] = {**script, "sha256": hashlib.sha256(script["source"].encode()).hexdigest()}
    assert set(frames) == {event["frame"] for event in timeline["actions"] if event["tag"] == 12}
    assert timeline["declared_frames"] == timeline["show_frames"]
    return {"status": "source_inventory_not_runtime_acceptance", "source_swf_sha256": source_hash,
            "bundle_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "timeline": timeline,
            "functions": functions, "frame_scripts": frames,
            "frames_without_root_doaction": [frame for frame in range(1, timeline["show_frames"] + 1) if frame not in frames],
            "limits": ["Root KO instance placement and child ClipActions require full display-list audit.",
                       "Round transitions, win counters and nextfight interval are not implemented by this inventory."]}


if __name__ == "__main__":
    output = ROOT / "evidence/ai/ko-source.json"
    output.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
