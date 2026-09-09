"""Instrument a separate native-player game copy for the fixed VS COM slice.

The source game and script bundles are never edited. This captures the original
RNG; it does not substitute a seeded generator or schedule AI on display frames.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PREDICATES = {
    "moveLeft", "moveRight", "airhit", "airMagichit", "holdJ", "holdU",
    "nornalhit", "combohitAI", "magichit1", "magichit2", "magichit3",
    "skill1", "skill2", "jump", "jumpDown", "rush", "hide", "defence",
    "standup", "zhaoHuan", "bisha", "bishaUP", "bishaAir", "bishaSuper",
    "hurtSkill", "dash", "wankai",
}
FUNCTION = re.compile(r"^function (\w+)\([^\n]*\)\r?\n\{\r?\n.*?^\}", re.M | re.S)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def instrument(source: str, origin: str, fighter: bool) -> str:
    def function_patch(match: re.Match) -> str:
        name, body = match[1], match[0]
        if name in PREDICATES:
            body = re.sub(
                r"\breturn ([^;\n]+);",
                lambda ret: "return _root.aiPredicate(" + quoted(name) + ",this,(" + ret[1] + "));",
                body,
            )
        if name == "hurtVoice":
            clock_index = 0
            def clock_patch(call: re.Match) -> str:
                nonlocal clock_index
                clock_index += 1
                return "_root.aiTimer(" + quoted(origin + "#hurtVoice:getTimer:" + str(clock_index)) + ")"
            body = re.sub(r"getTimer\(\)", clock_patch, body)
            if clock_index != 4:
                raise ValueError("Unexpected hurtVoice clock sites: " + origin)
        if name == "initCtrl":
            brace = body.index("{") + 1
            body = body[:brace] + '\n_root.aiEvent("initCtrl",String(this));\n' + body[brace:]
        if name == "randAI":
            fields = '+","+'.join('_root.aiNumber(' + field + ')' for field in ('attran', 'defran', 'goran', 'jumpran', 'bisharan'))
            body = body[:-1] + '\n_root.aiEvent("sample",String(this)+","+' + fields + ');\n}'
        return body

    if fighter:
        source = FUNCTION.sub(function_patch, source)
    # Label every lexical call without changing the number or order of draws.
    index = 0
    def random_patch(match: re.Match) -> str:
        nonlocal index
        index += 1
        return "_root.aiRandom(" + quoted(origin + ":" + str(index)) + ")"
    return re.sub(r"Math\.random\(\)", random_patch, source)


def build(ffdec: Path, output: Path, run_id: str, frames: int, frame_order_probe: bool = False, body_boundaries: bool = False, recovery_order_probe: bool = False, recovery_walk_first: bool = False, match_flow: bool = False, helper_probe: str | None = None) -> dict:
    if output.exists():
        raise ValueError("Use a fresh output directory; previous reference runs must remain intact")
    output.mkdir(parents=True)
    game = output / "game"
    game.mkdir()
    (game / "fighter").mkdir()
    (game / "fighter/fz").mkdir()
    # Only selected assets are materialized; music stays read-only input.
    (game / "music").symlink_to(ROOT / "game/music", target_is_directory=True)
    changes = []
    sources = {}
    bootstrap = (Path(__file__).parent / "as2/ai_reference/bootstrap.as").read_text()
    bootstrap = (Path(__file__).parent / "as2/ai_reference/number.as").read_text() + bootstrap
    bootstrap = bootstrap.replace("__RUN_ID__", run_id).replace("__FRAMES__", str(frames))
    bootstrap = bootstrap.replace("__GAME_URI__", game.as_uri())
    if helper_probe:
        helper_name = {"woailuo": "我爱罗", "kon": "魂"}[helper_probe]
        bootstrap = bootstrap.replace('p1sf = "我爱罗";', 'p1sf = ' + quoted(helper_name) + ';')
        bootstrap = re.sub(r'   if\(aiFight >= \d+ && aiFight < \d+\) aiHeld\[\w\] = true;\n', '', bootstrap)
        fixture = (Path(__file__).parent / "as2/ai_reference/helper.as").read_text()
        fixture = fixture.replace("__TARGET_X__", "340" if helper_probe == "kon" else "420")
        fixture = fixture.replace("__TARGET_ENERGY__", "200" if helper_probe == "kon" else "0")
        bootstrap = bootstrap.replace('   aiHeld = {};', fixture + '\n   aiHeld = {};\n   if(aiFight >= 10 && aiFight < 15) aiHeld[o] = true;')
    if match_flow:
        bootstrap = (Path(__file__).parent / "as2/ai_reference/match_flow.as").read_text() + bootstrap
        bootstrap = bootstrap.replace('   aiHeld = {};', '   _root.aiMatch("root");\n   aiHeld = {};', 1)
    if frame_order_probe:
        bootstrap = bootstrap.replace('   aiHeld = {};', '''   if(aiFight == 1)
   {
      aiEvent("fixture", "frame-order: p2 goto389, action1, rootpause");
      _root.game.p2.mc.gotoAndPlay(389);
      _root.game.p2.mc.动作 = 1;
      _root.zhanting = true;
   }
   aiHeld = {};''')
    if recovery_order_probe:
        bootstrap = bootstrap.replace('   aiHeld = {};', """   if(aiFight == 1)
   {
      aiEvent("fixture", "recovery-order: p1 goto1064 x330; p2 goto10 x351; fixed samples; cancel AI interval");
      clearInterval(_root.airanset);
      _root.game.p1._x = 330;
      _root.game.p1._xscale = 100;
      _root.game.p1.mc.动作 = -1;
      _root.game.p1.mc.sw = false;
      _root.game.p1.mc.gotoAndPlay(1064);
      _root.game.p2._x = 351;
      _root.game.p2._xscale = -100;
      _root.game.p2.mc.goran = 60;
      _root.game.p2.mc.attran = 400;
      _root.game.p2.mc.defran = 400;
      _root.game.p2.mc.jumpran = 400;
      _root.game.p2.mc.bisharan = 400;
      _root.game.p2.mc.gotoAndPlay(10);
      _root.zhanting = false;
   }
   aiHeld = {};""")
        bootstrap = """_root.aiRecoveryOrder = function(site)
{
   if(_root.aiFight < 1) return;
   var a = _root.game.p1;
   var b = _root.game.p2;
   _root.aiEvent("recovery_order", site + "," + a.mc._currentframe + "," + b.mc._currentframe + "," + a._x + "," + b._x + "," + a.getDepth() + "," + b.getDepth());
};
""" + bootstrap
    if body_boundaries:
        bootstrap = '''_root.aiBodyBoundary = function(m, slot, sourceFrame, entering)
{
   _root.aiEvent("body_boundary",slot + "," + sourceFrame + "," + entering + "," + m._currentframe + "," + m.动作 + "," + _root.aiNumber(m.hp) + "," + _root.aiNumber(m.ql) + "," + m.sw + "," + m.touch + "," + m.touchFloor + "," + m.hits + "," + _root.zhanting + "," + m.hstm + "," + m.hurtSkling);
};
''' + bootstrap
    if recovery_walk_first:
        if not recovery_order_probe:
            raise ValueError("Recovery creation-order variant requires recovery-order probe")
        bootstrap = bootstrap.replace('      _root.game.p1.mc.gotoAndPlay(1064);', '      _root.game.p2.mc.gotoAndPlay(10);\n      _root.game.p1.mc.gotoAndPlay(1064);', 1)
        needle = '      _root.game.p2.mc.bisharan = 400;\n      _root.game.p2.mc.gotoAndPlay(10);'
        bootstrap = bootstrap.replace(needle, '      _root.game.p2.mc.bisharan = 400;')
        bootstrap = bootstrap.replace('fixed samples; cancel AI interval', 'fixed samples; cancel AI interval; walking instance created first')
    hooks, battle = bootstrap.split("_root.aiHeld = {};", 1)
    battle = "_root.aiHeld = {};" + battle
    for name in ("main", "fighter/minren", "fighter/yihu", "fighter/fz/kon", "fighter/fz/woailuo"):
        bundle_path = ROOT / f"scripts/{name}.json"
        bundle = json.loads(bundle_path.read_text())
        input_swf = ROOT / bundle["game_file"]
        if sha(input_swf) != bundle["swf_sha256"]:
            raise ValueError(f"Source hash mismatch: {input_swf}")
        sources[bundle["game_file"]] = sha(input_swf)
        sources[f"scripts/{name}.json"] = sha(bundle_path)
        patch = output / "patches" / name
        for script in bundle["scripts"]:
            original = script["source"]
            updated = instrument(original, name + "#" + script["path"], name != "main")
            if match_flow and name == "main":
                if script["path"] == "DefineSprite_1813/frame_1/DoAction.as":
                    updated = '_root.aiMatch("timer_load");\n' + updated
                    updated, count = re.subn(r'(time = function\(\)\s*\{)',
                        lambda m: m[1] + '\n_root.aiMatch("timer_enter");', updated)
                    if count != 1:
                        raise ValueError("Missing unique countdown callback")
                    needle = '   个.gotoAndStop(gs + 1);'
                    if updated.count(needle) != 1:
                        raise ValueError("Missing countdown callback end")
                    updated = updated.replace(needle, needle + '\n_root.aiMatch("timer_exit");')
                if re.fullmatch(r'DefineSprite_(1848|1858)/frame_\d+/DoAction.as', script["path"]):
                    site = quoted(script["path"])
                    updated = '_root.aiMatch(' + site + ');\n' + updated
                    updated = re.sub(r'(nextfight = function\(\)\s*\{)',
                        lambda m: m[1] + '\n_root.aiMatch("nextfight_enter");', updated)
            if name in ("fighter/minren", "fighter/yihu") and "onClipEvent(load)" in original:
                # Key.isDown itself is read-only in FP32. Bind the source's
                # per-body alias to the recorded input function instead.
                updated = updated.replace("var kis = Key.isDown;", "var kis = _root.aiKeyDown;")
            if name == "main" and script["path"] == "DefineSprite_1991/frame_1/DoAction.as":
                for signature, event, value in (
                    ("kaichang()", "intro_poll", "curStep"),
                    ("goStep(step)", "intro_step", "step"),
                ):
                    pattern = r'(function ' + re.escape(signature) + r'\s*\{)'
                    updated, count = re.subn(pattern, lambda match: match[1] +
                        '\n   _root.aiEvent("' + event + '",' + value + ');', updated)
                    if count != 1:
                        raise ValueError("Missing unique intro function: " + signature)
                needle = '_root.game.p2.mc.gotoAndPlay("开场");'
                poll_hook = '_root.aiEvent("intro_poll",curStep);'
                updated = updated.replace(poll_hook, poll_hook +
                    '\n_root.aiEvent("intro_poll_state",curStep + "," + _root.p2loaded + "," + ' +
                    '_root.game.p1.mc.kcplayed + "," + _root.game.p2.mc.kcplayed + "," + ' +
                    '_root.game.p1.mc._currentframe + "," + _root.game.p2.mc._currentframe);')
                if updated.count(needle) != 1:
                    raise ValueError("Missing unique P2 intro goto")
                updated = updated.replace(needle,
                    '_root.aiEvent("intro_goto_before",_root.game.p2.mc._currentframe);\n' + needle +
                    '\n_root.aiEvent("intro_goto_return",_root.game.p2.mc._currentframe);')
            if name == "fighter/yihu":
                frame_match = re.fullmatch(r'DefineSprite_638/frame_(1|8|822|823|883)/DoAction.as', script['path'])
                if frame_match:
                    frame = frame_match[1]
                    updated = ('_root.aiEvent("intro_body_enter","' + frame + '," + _currentframe);\n' +
                               updated + '\n_root.aiEvent("intro_body_exit","' + frame + '," + _currentframe);\n')
            if name == "fighter/yihu" and script["path"] in (
                "DefineSprite_638/frame_1/DoAction.as",
                "DefineSprite_638/frame_390/DoAction.as",
            ):
                source_frame = script["path"].split("/")[1].removeprefix("frame_")
                value = '"' + source_frame + '," + _currentframe + "," + 动作 + "," + ql + "," + sw'
                updated = ('_root.aiEvent("frame_state_enter",' + value + ');\n' + updated +
                           '\n_root.aiEvent("frame_state_exit",' + value + ');\n')
            if body_boundaries and name in ("fighter/minren", "fighter/yihu"):
                sprite, slot = (764, "p1") if name == "fighter/minren" else (638, "p2")
                boundary_frame = re.fullmatch(rf'DefineSprite_{sprite}/frame_(\d+)/DoAction.as', script["path"])
                if boundary_frame:
                    prefix = '_root.aiBodyBoundary(this,"' + slot + '",' + boundary_frame[1] + ','
                    updated = prefix + 'true);\n' + updated + '\n' + prefix + 'false);\n'
            if recovery_order_probe:
                if name == "fighter/yihu" and script["path"] == "DefineSprite_16/frame_1/DoAction.as":
                    updated, count = re.subn(r'(function moveLeft\(\)\s*\{)',
                        lambda match: match[1] + '\n_root.aiRecoveryOrder("moveLeft");', updated)
                    if count != 1:
                        raise ValueError("Missing moveLeft recovery probe site")
                if name == "fighter/minren" and script["path"].startswith("DefineSprite_764/frame_1064/") and "onClipEvent(enterFrame)" in updated:
                    updated = updated.replace("onClipEvent(enterFrame){", 'onClipEvent(enterFrame){\n_root.aiRecoveryOrder("recovery-enter");', 1)
                    end = updated.rfind("}")
                    updated = updated[:end] + '_root.aiRecoveryOrder("recovery-exit");\n' + updated[end:]
            if name == "main" and script["path"] == "frame_1/DoAction.as":
                updated = re.sub(r"function goLink\([^)]*\)\s*\{.*?^\}", "function goLink(url)\n{\n}", updated, flags=re.M | re.S)
                updated = hooks + updated + '\ngotoAndPlay(6);\n'
            if name == "main" and script["path"] == "frame_10/DoAction.as":
                updated = battle
            if updated == original:
                continue
            target = patch / script["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(updated)
            changes.extend(difflib.unified_diff(original.splitlines(True), updated.splitlines(True),
                                               fromfile=name + "/" + script["path"], tofile=str(target)))
        log = output / (name.replace("/", "-") + "-build.log")
        with log.open("w") as stream:
            subprocess.run(["java", "-Djava.awt.headless=true", "-jar", str(ffdec),
                            "-importScript", str(input_swf), str(game / (name + ".swf")), str(patch)],
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
    (output / "instrumentation.diff").write_text("".join(changes))
    report = {
        "run_id": run_id, "status": "built_not_run", "frames_after_ready": frames,
        "configuration": {"modo": 2, "p1": "鸣人", "p2": "一护", "p2cpu": True,
                          "AI": 5, "stage": "现世", "p1sf": "魂" if helper_probe == "kon" else "我爱罗", "p2sf": "魂"},
        "sources_sha256": sources, "ffdec_sha256": sha(ffdec),
        "outputs_sha256": {p.relative_to(output).as_posix(): sha(p) for p in game.rglob("*.swf")},
        "instrumentation_sha256": sha(output / "instrumentation.diff"),
        "frame_order_probe": frame_order_probe,
        "body_boundaries": body_boundaries,
        "recovery_order_probe": recovery_order_probe,
        "recovery_walk_first": recovery_walk_first,
        "match_flow": match_flow,
        "helper_probe": helper_probe,
        "input_injection": "body_kis_alias_with_per_read_trace",
        "number_encoding": "binary53_for_random_samples_hp_ql_and_state_geometry",
        "capture_scope": "Math.random in selected bundles and getTimer in hurtVoice; random(n) is not wrapped",
    }
    (output / "build.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--frames", type=int, default=600)
    parser.add_argument("--frame-order-probe", action="store_true")
    parser.add_argument("--body-boundaries", action="store_true")
    parser.add_argument("--recovery-order-probe", action="store_true")
    parser.add_argument("--recovery-walk-first", action="store_true")
    parser.add_argument("--match-flow", action="store_true")
    parser.add_argument("--helper-probe", choices=["woailuo", "kon"])
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id) or args.frames < 1:
        parser.error("Use an alphanumeric run ID and a positive frame count")
    print(json.dumps(build(args.ffdec.resolve(), args.output.resolve(), args.run_id, args.frames, args.frame_order_probe, args.body_boundaries, args.recovery_order_probe, args.recovery_walk_first, args.match_flow, args.helper_probe), ensure_ascii=False))


if __name__ == "__main__":
    main()
