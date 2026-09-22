#!/usr/bin/env python3
"""Build an isolated Byakuya SWF AVM goto experiment.

The source bundle is copied to a temporary patch and imported into a copied
Byakuya.swf.  The injected code records frame/child identity and executes a
single synchronous A->B->A goto sequence.  It is intentionally not a gameplay
capture and must never be used as natural-input parity evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SWF = ROOT / "game/fighter/Byakuya.swf"
SOURCE_BUNDLE = ROOT / "scripts/fighter/Byakuya.json"
MAIN_SWF = ROOT / "game/main.swf"
MAIN_BUNDLE = ROOT / "scripts/main.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_run_id(value: str) -> None:
    if not re.fullmatch(r"byakuya-avm-goto-[A-Za-z0-9_-]+", value):
        raise ValueError("run_id must match byakuya-avm-goto-<unique-token>")


def observer(run_id: str) -> str:
    # The sequence is intentionally explicit and synchronous. It tests AVM
    # call ordering and object identity only; it does not claim natural parity.
    prefix = f"AIREF|{run_id}|goto|"
    return f'''\n_root.__byakuyaGotoIdentity = function(clip, tag) {{
    var m = clip.mian;
    var j = clip.jiao;
    var b = clip.bdmn;
    if (m != undefined) m.__byakuya_probe_sentinel = "mian:" + tag;
    if (j != undefined) j.__byakuya_probe_sentinel = "jiao:" + tag;
    if (b != undefined) b.__byakuya_probe_sentinel = "bdmn:" + tag;
    _root.aiEvent("{prefix}identity|" + tag + "|frame=" + String(clip._currentframe) +
        "|m_same=" + String(m === _root.__byakuya_mian_ref) +
        "|j_same=" + String(j === _root.__byakuya_jiao_ref) +
        "|b_same=" + String(b === _root.__byakuya_bdmn_ref) +
        "|m_sentinel=" + String(m == undefined ? undefined : m.__byakuya_probe_sentinel) +
        "|j_sentinel=" + String(j == undefined ? undefined : j.__byakuya_probe_sentinel) +
        "|b_sentinel=" + String(b == undefined ? undefined : b.__byakuya_probe_sentinel));
}};
_root.__byakuya_mian_ref = this.mian;
_root.__byakuya_jiao_ref = this.jiao;
_root.__byakuya_bdmn_ref = this.bdmn;
_root.aiEvent("{prefix}identity|initial|frame=" + String(this._currentframe) +
    "|m_same=true|j_same=true|b_same=true|m_sentinel=" + String(this.mian == undefined ? undefined : this.mian.__byakuya_probe_sentinel) +
    "|j_sentinel=" + String(this.jiao == undefined ? undefined : this.jiao.__byakuya_probe_sentinel) +
    "|b_sentinel=" + String(this.bdmn == undefined ? undefined : this.bdmn.__byakuya_probe_sentinel));
_root.aiEvent("{prefix}entry|label=招换|start=814|script=819|" + String(_currentframe));
_root.aiEvent("{prefix}before|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
if (_root.__byakuyaGotoProbeDone != true) {{
    _root.__byakuyaGotoProbeDone = true;
    _root.aiEvent("{prefix}A0|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("{prefix}B0|" + String(_currentframe));
    this.gotoAndStop("招换");
    _root.aiEvent("{prefix}A1|" + String(_currentframe));
    _root.__byakuyaGotoIdentity(this, "sync_after_A1");
    this.gotoAndStop("站立");
    _root.aiEvent("{prefix}repeat_A|" + String(_currentframe));
    this.gotoAndStop("招换");
    _root.__byakuyaGotoIdentity(this, "sync_repeat_B0");
    this.gotoAndStop("招换");
    _root.__byakuyaGotoIdentity(this, "sync_repeat_B1");
    this.gotoAndStop("站立");
    _root.__byakuyaGotoIdentity(this, "sync_final_A");
    _root.aiEvent("{prefix}after|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
}}
if (_root.__byakuyaCrossTickProbeInstalled != true) {{
    _root.__byakuyaCrossTickProbeInstalled = true;
    _root.__byakuyaCrossTickProbePhase = 0;
    this.onEnterFrame = function() {{
        if (_root.__byakuyaCrossTickProbePhase == 0) {{
            _root.__byakuyaCrossTickProbePhase = 1;
            this.gotoAndStop("站立");
            _root.__byakuyaGotoIdentity(this, "cross_tick_A");
            _root.aiEvent("{prefix}cross_tick_A|" + String(_currentframe));
        }} else if (_root.__byakuyaCrossTickProbePhase == 1) {{
            _root.__byakuyaCrossTickProbePhase = 2;
            this.gotoAndStop("招换");
            _root.__byakuyaGotoIdentity(this, "cross_tick_B");
            _root.aiEvent("{prefix}cross_tick_B|" + String(_currentframe));
        }} else if (_root.__byakuyaCrossTickProbePhase == 2) {{
            _root.__byakuyaCrossTickProbePhase = 3;
            this.gotoAndStop("站立");
            _root.__byakuyaGotoIdentity(this, "cross_tick_A2");
            _root.aiEvent("{prefix}cross_tick_A2|" + String(_currentframe));
            _root.aiGotoDone();
            this.onEnterFrame = null;
        }}
    }};
}}
'''


def build(ffdec: Path, output: Path, run_id: str) -> dict:
    require_run_id(run_id)
    prefix = f"AIREF|{run_id}|goto|"
    if output.exists():
        raise ValueError(f"refusing to overwrite existing output: {output}")
    bundle = json.loads(SOURCE_BUNDLE.read_text(encoding="utf-8"))
    scripts = {item["path"]: item["source"] for item in bundle["scripts"]}
    target = "DefineSprite_631/frame_819/DoAction.as"
    if target not in scripts:
        raise ValueError(f"missing source patch target: {target}")
    output.mkdir(parents=True)
    patch = output / "patch/scripts" / target
    patch.parent.mkdir(parents=True)
    patch.write_text(scripts[target].rstrip() + observer(run_id), encoding="utf-8")
    # Mark the two source frame scripts used by the controlled re-entry. This
    # is an observation of actual frame-script execution, not a synthetic
    # expected sequence.
    for frame in ("1", "8", "844"):
        frame_target = f"DefineSprite_631/frame_{frame}/DoAction.as"
        if frame_target in scripts:
            frame_patch = output / "patch/scripts" / frame_target
            frame_patch.parent.mkdir(parents=True, exist_ok=True)
            frame_patch.write_text(
                scripts[frame_target].rstrip()
                + f'\n_root.aiEvent("{prefix}frame_script|{frame}|" + String(this._currentframe));\n',
                encoding="utf-8",
            )
    main_patch = output / "patch-main/frame_1/DoAction.as"
    main_source = next(
        item["source"] for item in json.loads(MAIN_BUNDLE.read_text(encoding="utf-8"))["scripts"]
        if item["path"] == "frame_1/DoAction.as"
    )
    main_patch.parent.mkdir(parents=True)
    main_patch.write_text(main_source.rstrip() + f'''\n_root.__byakuyaGotoTraceSeq = 0;
_root.aiEvent = function(value) {{
    trace("AIREF|{run_id}|" + (++_root.__byakuyaGotoTraceSeq) + "|" + getTimer() + "|0|0|event|" + value);
}};
_root.aiGotoDone = function() {{
    trace("AIREF|{run_id}|" + (++_root.__byakuyaGotoTraceSeq) + "|" + getTimer() + "|0|0|done|goto_complete");
}};
''', encoding="utf-8")
    game = output / "game"
    (game / "fighter").mkdir(parents=True)
    (game / "music").mkdir(parents=True)
    shutil.copy2(MAIN_SWF, game / "main.swf")
    # Preserve all runtime assets while replacing only the temporary Byakuya SWF.
    for item in (ROOT / "game/fighter").iterdir():
        if item.name == "Byakuya.swf":
            continue
        dest = game / "fighter" / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    for item in (ROOT / "game/music").iterdir():
        dest = game / "music" / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    main_result = subprocess.run(
        ["java", "-Djava.awt.headless=true", "-jar", str(ffdec), "-importScript",
         str(MAIN_SWF), str(game / "main.swf"), str(output / "patch-main")],
        check=True, capture_output=True, text=True,
    )
    result = subprocess.run(
        ["java", "-Djava.awt.headless=true", "-jar", str(ffdec), "-importScript",
         str(SOURCE_SWF), str(game / "fighter/Byakuya.swf"), str(output / "patch")],
        check=True, capture_output=True, text=True,
    )
    metadata = {
        "format": "bvn26-byakuya-avm-goto-build-v1",
        "status": "built_not_run",
        "scope": "isolated AVM source goto ordering experiment; not natural-input parity",
        "run_id": run_id,
        "source_swf": str(SOURCE_SWF.relative_to(ROOT)),
        "source_swf_sha256": sha(SOURCE_SWF),
        "source_scripts": str(SOURCE_BUNDLE.relative_to(ROOT)),
        "source_scripts_sha256": sha(SOURCE_BUNDLE),
        "main_swf": str(game / "main.swf"),
        "fighter_swf": str(game / "fighter/Byakuya.swf"),
        "patch_target": target,
        "patched_script_sha256": sha(patch),
        "experiment": "招换 label entry 814 reaches frame-819 DoAction; records synchronous A->B->A and a separate onEnterFrame cross-display A->B->A sequence",
        "input": "original game input; injected sequence is controlled and behavior-changing",
        "capture_lock": "/tmp/bvn-native-flash-capture.lock",
        "ffdec": str(ffdec),
    }
    (output / "build.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    (output / "ffdec.stdout.txt").write_text(result.stdout or "")
    (output / "ffdec.stderr.txt").write_text(result.stderr or "")
    (output / "ffdec-main.stdout.txt").write_text(main_result.stdout or "")
    (output / "ffdec-main.stderr.txt").write_text(main_result.stderr or "")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffdec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    metadata = build(args.ffdec.resolve(), args.output.resolve(), args.run_id)
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
