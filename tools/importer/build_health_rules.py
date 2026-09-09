"""Extract the gameplay prefix of the authored health HUD callback."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def build() -> dict:
    bundle = json.loads((ROOT / "scripts/main.json").read_text())
    assert hashlib.sha256((ROOT / "game/main.swf").read_bytes()).hexdigest() == bundle["swf_sha256"]
    source_path = "DefineSprite_1814/frame_1/DoAction.as"
    source = next(s["source"] for s in bundle["scripts"] if s["path"] == source_path)
    prefix = source.split("onEnterFrame = function()", 1)[1].split("   var _loc2_", 1)[0]
    compact = re.sub(r"\s+", "", prefix)
    expected = "{" + "".join(f"p{i}hp=_root.game.p{i}.mc.hp/_root.maxhp*100;" for i in (1, 2))
    expected += "p1xt.bar._xscale=p1hp;p2xt.bar._xscale=p2hp;"
    expected += "if(p1hp<=0||p2hp<=0){returnundefined;}"
    rules = []
    for slot in (1, 2):
        match = re.search(rf"if\(p{slot}xt\.bar\._xscale < (\d+)\)\s*\{{\s*p{slot}xt\.kk\.gotoAndStop\(2\);\s*_root\.game\.p{slot}\.mc\.ql \+= ([\d.]+);\s*\}}", prefix)
        assert match, f"Missing low-health rule for p{slot}"
        threshold, delta = match.groups()
        expected += f"if(p{slot}xt.bar._xscale<{threshold}){{p{slot}xt.kk.gotoAndStop(2);_root.game.p{slot}.mc.ql+={delta};}}"
        rules.append({"slot": slot, "percent_below": float(threshold), "energy_delta": float(delta)})
    assert compact == expected, "Health gameplay prefix changed; review all conditions and ordering"
    return {"format": "bvn26-health-rules-v1", "source_path": source_path,
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "source_swf_sha256": bundle["swf_sha256"], "source_prefix": prefix,
            "percent_scale": 100, "return_if_any_percent_at_most": 0,
            "rules": rules,
            "limits": ["Only the gameplay prefix is compiled; HUD warning and trail visuals use a separate presentation implementation."]}


if __name__ == "__main__":
    output = ROOT / "godot/generated/main/health/rules.json"
    output.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n")
