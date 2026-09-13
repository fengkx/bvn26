#!/usr/bin/env python3
"""Build an isolated Rukia move-case SWF with native hit geometry logging."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RUKIA_SHA256 = "c48d47a817dbf1b4fff9b333bb35d89debb64d0635e8d88b4a7d1228208194eb"
FIXTURE = ROOT / "evidence/characters/rukia/move-cases/rukia-218-nornalhit-neutral.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def build(
    ffdec: Path,
    output: Path,
    run_id: str,
    p1_x: float | None = None,
    p2_x: float | None = None,
) -> dict:
    if output.exists():
        raise FileExistsError(f"Output must be a new directory: {output}")
    source = ROOT / "game/fighter/rukia.swf"
    if sha256(source) != EXPECTED_RUKIA_SHA256:
        raise ValueError("Locked Rukia SWF hash mismatch")

    fixture = json.loads(FIXTURE.read_text())
    move_case = FIXTURE
    temporary_case: Path | None = None
    if p1_x is not None or p2_x is not None:
        temporary_case = output.parent / ("." + output.name + ".case-input.json")
        if temporary_case.exists():
            raise FileExistsError(f"Temporary case input already exists: {temporary_case}")
        if p1_x is not None:
            fixture["setup"]["p1"]["x"] = p1_x
        if p2_x is not None:
            fixture["setup"]["p2"]["x"] = p2_x
        temporary_case.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n")
        move_case = temporary_case

    try:
        run([
            sys.executable,
            str(ROOT / "tools/probes/build_ai_reference.py"),
            "--ffdec", str(ffdec.resolve()),
            "--output", str(output.resolve()),
            "--run-id", run_id,
            "--frames", "300",
            "--p1-character", "露其雅",
            "--p2-character", "一护",
            "--move-case", str(move_case),
            "--dynamic-move-case",
        ])
    finally:
        if temporary_case is not None:
            temporary_case.unlink(missing_ok=True)

    if temporary_case is not None:
        (output / "move-case.json").write_text(
            json.dumps(fixture, ensure_ascii=False, indent=2) + "\n"
        )

    report_path = output / "build.json"
    report = json.loads(report_path.read_text())
    if report["sources_sha256"].get("game/fighter/rukia.swf") != EXPECTED_RUKIA_SHA256:
        raise ValueError("Builder did not bind the expected Rukia source hash")
    case_path = output / "case.txt"
    case = case_path.read_text()
    expected_case_id = fixture["id"]
    if f"run_id={run_id}&" not in case or f"case_id={expected_case_id}&" not in case:
        raise ValueError("Dynamic case file does not match the requested run and fixture")

    root_script_path = output / "patches/main/frame_1/DoAction.as"
    root_script_before = root_script_path.read_text()
    root_script = root_script_before
    marker = "function showCommt()"
    if root_script.count(marker) != 1:
        raise ValueError("Expected one root bootstrap insertion point")
    observer = '''_root.aiRukiaGeometry = function()
{
   var a = _root.game.p1.mc.k1atm;
   var d = _root.game.p2.mc.bdmn;
   var ag = a.getBounds(_root.game);
   var dg = d.getBounds(_root.game);
   var al = a.getBounds(a);
   var dl = d.getBounds(d);
   var am = a.transform.concatenatedMatrix;
   var dm = d.transform.concatenatedMatrix;
   var prefix = _root.game.p1.mc._currentframe + "," + _root.game.p2.mc._currentframe + ",";
   _root.aiEvent("rukia_geometry", prefix + "p1," + _root.aiNumber(_root.game.p1._x) + "," + _root.aiNumber(_root.game.p1._y) + "," + _root.aiNumber(_root.game.p1._xscale) + "," + _root.aiNumber(a._x) + "," + _root.aiNumber(a._y) + "," + _root.aiNumber(a._xscale) + "," + _root.aiNumber(a._yscale) + "," + _root.aiNumber(al.xMin) + "," + _root.aiNumber(al.yMin) + "," + _root.aiNumber(al.xMax) + "," + _root.aiNumber(al.yMax) + "," + _root.aiNumber(ag.xMin) + "," + _root.aiNumber(ag.yMin) + "," + _root.aiNumber(ag.xMax) + "," + _root.aiNumber(ag.yMax) + "," + _root.aiNumber(am.tx) + "," + _root.aiNumber(am.ty) + "," + a.hitTest(d));
   _root.aiEvent("rukia_geometry", prefix + "p2," + _root.aiNumber(_root.game.p2._x) + "," + _root.aiNumber(_root.game.p2._y) + "," + _root.aiNumber(_root.game.p2._xscale) + "," + _root.aiNumber(d._x) + "," + _root.aiNumber(d._y) + "," + _root.aiNumber(d._xscale) + "," + _root.aiNumber(d._yscale) + "," + _root.aiNumber(dl.xMin) + "," + _root.aiNumber(dl.yMin) + "," + _root.aiNumber(dl.xMax) + "," + _root.aiNumber(dl.yMax) + "," + _root.aiNumber(dg.xMin) + "," + _root.aiNumber(dg.yMin) + "," + _root.aiNumber(dg.xMax) + "," + _root.aiNumber(dg.yMax) + "," + _root.aiNumber(dm.tx) + "," + _root.aiNumber(dm.ty) + "," + d.hitTest(a));
};

'''
    root_script = root_script.replace(marker, observer + marker, 1)
    root_script_path.write_text(root_script)

    battle_script_path = output / "patches/main/frame_10/DoAction.as"
    battle_script_before = battle_script_path.read_text()
    battle_script = battle_script_before
    call_marker = '      aiState("p2");'
    if battle_script.count(call_marker) != 1:
        raise ValueError("Expected one battle-loop observer insertion point")
    battle_script = battle_script.replace(
        call_marker,
        call_marker + "\n      if(aiFight >= 13 && aiFight <= 16) _root.aiRukiaGeometry();",
        1,
    )
    battle_script_path.write_text(battle_script)

    custom_diff = "".join(
        difflib.unified_diff(
            root_script_before.splitlines(keepends=True),
            root_script.splitlines(keepends=True),
            fromfile="main/frame_1/DoAction.as",
            tofile="geometry-patch/main/frame_1/DoAction.as",
        )
    )
    custom_diff += "".join(
        difflib.unified_diff(
            battle_script_before.splitlines(keepends=True),
            battle_script.splitlines(keepends=True),
            fromfile="main/frame_10/DoAction.as",
            tofile="geometry-patch/main/frame_10/DoAction.as",
        )
    )
    instrumentation_path = output / "instrumentation.diff"
    with instrumentation_path.open("a") as stream:
        stream.write(custom_diff)

    yihu_bundle_path = ROOT / "scripts/fighter/yihu.json"
    yihu_bundle = json.loads(yihu_bundle_path.read_text())
    if report["sources_sha256"].get("scripts/fighter/yihu.json") != sha256(yihu_bundle_path):
        raise ValueError("Builder did not bind the expected Yihu script bundle")
    if yihu_bundle["swf_sha256"] != report["sources_sha256"].get("game/fighter/yihu.swf"):
        raise ValueError("Yihu script bundle and source SWF hashes disagree")
    receiver_path = "DefineSprite_2/frame_1/DoAction.as"
    receiver_scripts = [script for script in yihu_bundle["scripts"] if script["path"] == receiver_path]
    if len(receiver_scripts) != 1:
        raise ValueError("Expected the unique symbol 2 receiver script")
    try:
        from build_ai_reference import instrument
    except ImportError as exc:
        raise RuntimeError("Run this tool from its repository path") from exc
    receiver_source = instrument(
        receiver_scripts[0]["source"], "fighter/yihu#" + receiver_path, True
    )
    hit_test = "if(this.hitTest(_loc4_))"
    if receiver_source.count(hit_test) != 1:
        raise ValueError("Expected one generic receiver attack hitTest site")
    receiver_observer = '''var _aiRukiaHit = this.hitTest(_loc4_);
         if(_root.aiFight >= 13 && _root.aiFight <= 16 && _loc2_ == "k1")
         {
            var rb = this.getBounds(_root.game);
            var ab = _loc4_.getBounds(_root.game);
            var rr = this.getBounds(_root);
            var ar = _loc4_.getBounds(_root);
            var rl = this.getBounds(this);
            var al = _loc4_.getBounds(_loc4_);
            var rm = this.transform.concatenatedMatrix;
            var am = _loc4_.transform.concatenatedMatrix;
            var gm = _root.game.transform.concatenatedMatrix;
            _root.aiEvent("rukia_receiver_test", _root.aiFight + "," + _parent._name + "," + _parent._currentframe + "," + this._name + "," + this._currentframe + "," + _loc2_ + "," + _loc4_._name + "," + _loc4_._currentframe + "," + _aiRukiaHit + "," + _root.aiNumber(this._x) + "," + _root.aiNumber(this._y) + "," + _root.aiNumber(this._xscale) + "," + _root.aiNumber(this._yscale) + "," + _root.aiNumber(_loc4_._x) + "," + _root.aiNumber(_loc4_._y) + "," + _root.aiNumber(_loc4_._xscale) + "," + _root.aiNumber(_loc4_._yscale) + "," + _root.aiNumber(rl.xMin) + "," + _root.aiNumber(rl.yMin) + "," + _root.aiNumber(rl.xMax) + "," + _root.aiNumber(rl.yMax) + "," + _root.aiNumber(al.xMin) + "," + _root.aiNumber(al.yMin) + "," + _root.aiNumber(al.xMax) + "," + _root.aiNumber(al.yMax) + "," + _root.aiNumber(rb.xMin) + "," + _root.aiNumber(rb.yMin) + "," + _root.aiNumber(rb.xMax) + "," + _root.aiNumber(rb.yMax) + "," + _root.aiNumber(ab.xMin) + "," + _root.aiNumber(ab.yMin) + "," + _root.aiNumber(ab.xMax) + "," + _root.aiNumber(ab.yMax) + "," + _root.aiNumber(rr.xMin) + "," + _root.aiNumber(rr.yMin) + "," + _root.aiNumber(rr.xMax) + "," + _root.aiNumber(rr.yMax) + "," + _root.aiNumber(ar.xMin) + "," + _root.aiNumber(ar.yMin) + "," + _root.aiNumber(ar.xMax) + "," + _root.aiNumber(ar.yMax) + "," + _root.aiNumber(rm.a) + "," + _root.aiNumber(rm.b) + "," + _root.aiNumber(rm.c) + "," + _root.aiNumber(rm.d) + "," + _root.aiNumber(rm.tx) + "," + _root.aiNumber(rm.ty) + "," + _root.aiNumber(am.a) + "," + _root.aiNumber(am.b) + "," + _root.aiNumber(am.c) + "," + _root.aiNumber(am.d) + "," + _root.aiNumber(am.tx) + "," + _root.aiNumber(am.ty) + "," + _root.aiNumber(gm.a) + "," + _root.aiNumber(gm.b) + "," + _root.aiNumber(gm.c) + "," + _root.aiNumber(gm.d) + "," + _root.aiNumber(gm.tx) + "," + _root.aiNumber(gm.ty));
         }
         if(_aiRukiaHit)'''
    receiver_source = receiver_source.replace(hit_test, receiver_observer, 1)
    hierarchy_observer = '''         if(_root.aiFight >= 13 && _root.aiFight <= 16 && _loc2_ == "k1")
         {
            var diagRole = 0;
            while(diagRole < 2)
            {
               var diagBase = diagRole == 0 ? this : _loc4_;
               var diagObject = diagBase;
               var diagDepth = 0;
               while(diagObject != undefined && diagDepth < 8)
               {
                  var diagBounds = diagBase.getBounds(diagObject);
                  var diagMatrix = diagObject.transform.matrix;
                  var diagConcat = diagObject.transform.concatenatedMatrix;
                  _root.aiEvent("rukia_hier_bounds", (diagRole == 0 ? "receiver" : "attack") + "," + diagDepth + "," + diagObject._name + "," + diagObject._currentframe + "," + _root.aiNumber(diagObject._x) + "," + _root.aiNumber(diagObject._y) + "," + _root.aiNumber(diagObject._xscale) + "," + _root.aiNumber(diagObject._yscale) + "," + _root.aiNumber(diagBounds.xMin) + "," + _root.aiNumber(diagBounds.yMin) + "," + _root.aiNumber(diagBounds.xMax) + "," + _root.aiNumber(diagBounds.yMax) + "," + _root.aiNumber(diagMatrix.a) + "," + _root.aiNumber(diagMatrix.b) + "," + _root.aiNumber(diagMatrix.c) + "," + _root.aiNumber(diagMatrix.d) + "," + _root.aiNumber(diagMatrix.tx) + "," + _root.aiNumber(diagMatrix.ty) + "," + _root.aiNumber(diagConcat.a) + "," + _root.aiNumber(diagConcat.b) + "," + _root.aiNumber(diagConcat.c) + "," + _root.aiNumber(diagConcat.d) + "," + _root.aiNumber(diagConcat.tx) + "," + _root.aiNumber(diagConcat.ty));
                  diagObject = diagObject._parent;
                  diagDepth++;
               }
               diagRole++;
            }
         }
'''
    hierarchy_marker = "         if(_aiRukiaHit)"
    if receiver_source.count(hierarchy_marker) != 1:
        raise ValueError("Expected one receiver hit branch after geometry observer")
    receiver_source = receiver_source.replace(hierarchy_marker, hierarchy_observer + hierarchy_marker, 1)
    receiver_patch = output / "patches/fighter/yihu" / receiver_path
    receiver_patch.parent.mkdir(parents=True, exist_ok=True)
    receiver_patch.write_text(receiver_source)
    receiver_diff = "".join(
        difflib.unified_diff(
            instrument(receiver_scripts[0]["source"], "fighter/yihu#" + receiver_path, True).splitlines(keepends=True),
            receiver_source.splitlines(keepends=True),
            fromfile="fighter/yihu/" + receiver_path,
            tofile="geometry-patch/fighter/yihu/" + receiver_path,
        )
    )
    with instrumentation_path.open("a") as stream:
        stream.write(receiver_diff)

    main_swf = output / "game/main.swf"
    before_geometry = output / "game/main-before-geometry.swf"
    shutil.copy2(main_swf, before_geometry)
    run([
        "java", "-Djava.awt.headless=true", "-jar", str(ffdec.resolve()),
        "-importScript", str(before_geometry), str(main_swf),
        str(output / "patches/main"),
    ])

    yihu_swf = output / "game/fighter/yihu.swf"
    yihu_before_geometry = output / "game/fighter/yihu-before-geometry.swf"
    shutil.copy2(yihu_swf, yihu_before_geometry)
    run([
        "java", "-Djava.awt.headless=true", "-jar", str(ffdec.resolve()),
        "-importScript", str(yihu_before_geometry), str(yihu_swf),
        str(output / "patches/fighter/yihu"),
    ])

    report["status"] = "instrumented_geometry_diagnostic_not_captured"
    report["geometry_probe"] = {
        "events": ["rukia_geometry", "rukia_receiver_test", "rukia_hier_bounds"],
        "source_change": "temporary importScript patches to main root and Yihu symbol 2 receiver",
        "frames": "fight ticks 13-16; receiver hitTest is evaluated once, then hierarchy bounds and transforms are logged",
        "capture_run_id": run_id,
        "case_run_id": run_id,
        "case_path": str(case_path.resolve()),
        "source_hash_verified": EXPECTED_RUKIA_SHA256,
        "case_setup": fixture["setup"],
        "case_inputs": fixture["inputs"],
    }
    report["outputs_sha256"]["game/main-before-geometry.swf"] = sha256(before_geometry)
    report["outputs_sha256"]["game/main.swf"] = sha256(main_swf)
    report["outputs_sha256"]["game/fighter/yihu-before-geometry.swf"] = sha256(yihu_before_geometry)
    report["outputs_sha256"]["game/fighter/yihu.swf"] = sha256(yihu_swf)
    report["instrumentation_sha256"] = sha256(instrumentation_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--p1-x", type=float)
    parser.add_argument("--p2-x", type=float)
    args = parser.parse_args()
    if not args.run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in args.run_id):
        parser.error("Run ID may contain only letters, numbers, '_' and '-'")
    print(json.dumps(build(args.ffdec, args.output, args.run_id, args.p1_x, args.p2_x), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
