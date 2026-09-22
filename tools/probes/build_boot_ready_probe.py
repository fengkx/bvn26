"""Build a source-preserving title/menu/intro trace probe.

The probe appends trace statements to the locked source's existing root,
selection, and intro actions.  It does not replace input handling, select a
fighter, start a mode, or force a pause.  A human/native UI driver must still
perform the title -> menu -> selection -> map input sequence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRACE_SITES = {
    "frame_1/DoAction.as": 'trace("BOOT_REF|root_frame_1|" + _currentframe);',
    "frame_10/DoAction.as": 'trace("BOOT_REF|root_frame_10|" + _currentframe);',
    "frame_46/DoAction.as": (
        'trace("BOOT_REF|selection|" + _root.modo + "|" + _root.p1selt + "|" + '
        '_root.p2selt + "|" + _root.p1sf + "|" + _root.p2sf);'
    ),
    "frame_56/DoAction.as": (
        'trace("BOOT_REF|battle_entry|" + _root.modo + "|" + _root.p1selt + "|" + '
        '_root.p2selt + "|" + _root.p1sf + "|" + _root.p2sf);'
    ),
    "DefineSprite_1989/frame_1/DoAction_2.as": (
        'trace("BOOT_REF|intro_load|" + _root.p1selt + "|" + _root.p2selt + "|" + '
        '_root.p1sf + "|" + _root.p2sf + "|" + _root.p2loaded);'
    ),
    "DefineSprite_1991/frame_1/DoAction.as": (
        'trace("BOOT_REF|intro_poll|" + _root.p1selt + "|" + _root.p2selt + "|" + '
        '_root.p2loaded + "|" + _root.game.p1.mc.kcplayed + "|" + '
        '_root.game.p2.mc.kcplayed);'
    ),
}
TRACE_VALUES = {
    "frame_1/DoAction.as": "root_frame_1",
    "frame_10/DoAction.as": "root_frame_10",
    "frame_46/DoAction.as": "selection",
    "frame_56/DoAction.as": "battle_entry",
    "DefineSprite_1989/frame_1/DoAction_2.as": "intro_load",
    "DefineSprite_1991/frame_1/DoAction.as": "intro_poll",
}


def _event(run_id: str, value: str, *, done: bool = False) -> str:
    kind = "done" if done else "boot"
    return (f'trace("AIREF|{run_id}|" + (++_root.__bootSeq) + "|" + getTimer() '
            f'+ "|0|0|{kind}|{value}");')


def _event_expr(run_id: str, expression: str, *, done: bool = False) -> str:
    kind = "done" if done else "boot"
    return (f'trace("AIREF|{run_id}|" + (++_root.__bootSeq) + "|" + getTimer() '
            f'+ "|0|0|{kind}|" + ({expression}));')


def _ready_observer(run_id: str) -> str:
    return (
        f'_root.__bootReadyCount = (_root.__bootReadyCount == undefined ? 0 : _root.__bootReadyCount) + 1;\n'
        f'_root.__bootReadyFrame = _root.__bootFrame;\n'
        f'{_event(run_id, "ready_begin", done=False)}\n'
    )


def _frame_observer(run_id: str) -> str:
    input_event = _event_expr(run_id, '"input:" + Key.isDown(_root.w) + "," + Key.isDown(_root.s) + "," + Key.isDown(_root.a) + "," + Key.isDown(_root.d) + "," + Key.isDown(_root.j) + "," + Key.isDown(_root.k) + "," + Key.isDown(_root.l) + "," + Key.isDown(_root.u) + "," + Key.isDown(_root.i) + "," + Key.isDown(_root.o) + "," + Key.isDown(_root.上箭) + "," + Key.isDown(_root.下箭) + "," + Key.isDown(_root.左箭) + "," + Key.isDown(_root.右箭) + "," + Key.isDown(_root.N1) + "," + Key.isDown(_root.N2) + "," + Key.isDown(_root.N3) + "," + Key.isDown(_root.N4) + "," + Key.isDown(_root.N5) + "," + Key.isDown(_root.N6)')
    return (
        '_root.__bootFrame = (_root.__bootFrame == undefined ? 0 : _root.__bootFrame) + 1;\n'
        '_root.__bootRounds = (_root.__bootRounds == undefined ? _root.rounds : _root.__bootRounds);\n'
        'if (_root.rounds != _root.__bootRounds) {\n'
        '   _root.__bootRounds = _root.rounds;\n'
        f'   {_event(run_id, "next_round", done=False)}\n'
        '}\n'
        + input_event + '\n'
        'if (_root.__bootReadyCount > 0 && _root.zhanting == false && _root.__bootRunning != true) {\n'
        '   _root.__bootRunning = true;\n'
        '   _root.__bootRunningCount = (_root.__bootRunningCount == undefined ? 0 : _root.__bootRunningCount) + 1;\n'
        '   _root.__bootRunningFrame = _root.__bootFrame;\n'
        f'   {_event(run_id, "game_running", done=False)}\n'
        '}\n'
        'if (_root.zhanting == true) { _root.__bootRunning = false; }\n'
        'if (_root.__bootRunningCount > 0 && _root.__bootDone != true &&\n'
        '    (_root.__bootRunningCount >= 2 || _root.__bootFrame - _root.__bootRunningFrame >= 900)) {\n'
        '   _root.__bootDone = true;\n'
        f'   {_event(run_id, "ready_horizon", done=True)}\n'
        '}\n'
    )


def build(ffdec: Path, output: Path, run_id: str) -> dict:
    if output.exists():
        raise ValueError(f"Refusing to overwrite probe directory: {output}")
    source = ROOT / "scripts/main.json"
    main_swf = ROOT / "game/main.swf"
    scripts = json.loads(source.read_text(encoding="utf-8"))["scripts"]
    by_path = {item["path"]: item["source"] for item in scripts}
    missing = sorted(set(TRACE_SITES) - set(by_path))
    if missing:
        raise ValueError("Source trace sites missing: " + ", ".join(missing))

    patch = output / "patch/scripts"
    patch.mkdir(parents=True)
    if not run_id or any(c in run_id for c in "|\r\n"):
        raise ValueError("run_id must be a non-empty trace-safe token")
    for path in TRACE_SITES:
        # Keep authored source byte-for-byte except for the explicit observer.
        patched = by_path[path].rstrip() + "\n_root.__bootSeq = _root.__bootSeq == undefined ? 0 : _root.__bootSeq;\n"
        if path == "DefineSprite_1991/frame_1/DoAction.as":
            patched = patched.replace('_root.ready.play();',
                                      '_root.ready.play();\n' + _ready_observer(run_id), 1)
            frame_observer = 'onEnterFrame = function()\n{\n' + _frame_observer(run_id)
            patched = patched.replace('onEnterFrame = function()\r\n{', frame_observer.replace('\n', '\r\n'), 1)
            patched = patched.replace('onEnterFrame = function()\n{', frame_observer, 1)
            patched += "\n" + _event(run_id, TRACE_VALUES[path])
        else:
            patched += _event(run_id, TRACE_VALUES[path])
        patched += "\n"
        target = patch / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(patched, encoding="utf-8")

    game_dir = output / "game"
    game_dir.mkdir(parents=True, exist_ok=True)
    for asset_dir in ("fighter", "music"):
        (game_dir / asset_dir).symlink_to(ROOT / "game" / asset_dir,
                                          target_is_directory=True)
    result = subprocess.run(
        ["java", "-Djava.awt.headless=true", "-jar", str(ffdec), "-importScript",
         str(main_swf), str(game_dir / "main.swf"), str(output / "patch")],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = {
        "kind": "source-preserving-boot-ready-probe",
        "run_id": run_id,
        "scope": "title/menu/selection/intro/ready/game-running/next-round trace; bounded horizon",
        "observer_lifecycle": "DefineSprite_1991 onEnterFrame remains source camera/wall controller after goStep(4); source clears kcint but does not remove the clip",
        "input_handling": "original",
        "selection": "original",
        "mode_start": "original",
        "forced_pause": False,
        "source_main_sha256": hashlib.sha256(main_swf.read_bytes()).hexdigest(),
        "source_scripts_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "trace_sites": sorted(TRACE_SITES),
        "output": str(game_dir / "main.swf"),
        "ffdec": str(ffdec),
    }
    (output / "build.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    (output / "ffdec.stdout.txt").write_text(result.stdout or "")
    (output / "ffdec.stderr.txt").write_text(result.stderr or "")
    print(json.dumps(metadata, ensure_ascii=False))
    return metadata


def validate(output: Path) -> None:
    """Check the shared native-capture contract without launching Flash."""
    metadata_path = output / "build.json"
    main = output / "game/main.swf"
    if not metadata_path.is_file() or not main.is_file():
        raise ValueError("boot build must contain build.json and game/main.swf")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    run_id = metadata.get("run_id")
    if not isinstance(run_id, str) or not run_id or any(c in run_id for c in "|\r\n"):
        raise ValueError("build.json has no capture-safe run_id")
    for asset_dir in ("fighter", "music"):
        if not (output / "game" / asset_dir).is_dir():
            raise ValueError(f"missing relative runtime asset directory: game/{asset_dir}")
    patch_text = "\n".join(p.read_text(encoding="utf-8") for p in (output / "patch/scripts").rglob("*.as"))
    prefix = f'AIREF|{run_id}|'
    intro_patch = (output / "patch/scripts/DefineSprite_1991/frame_1/DoAction.as").read_text(encoding="utf-8")
    if prefix not in patch_text or f"|done|ready_horizon" not in patch_text:
        raise ValueError("patch does not contain AIREF sequence and done protocol")
    if (intro_patch.count("__bootFrame") < 2 or intro_patch.count("__bootReadyCount") < 2
            or "_root.gamePlayers" not in intro_patch or "clearInterval(_root.kcint)" not in intro_patch
            or "removeMovieClip" in intro_patch):
        raise ValueError("observer lifecycle proof is incomplete or replaces the source controller")
    if metadata.get("input_handling") != "original" or metadata.get("forced_pause"):
        raise ValueError("boot probe must preserve input and pause semantics")
    print("BOOT_READY_CAPTURE_CONTRACT_OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id",
                        help="Unique token used by the AIREF capture protocol")
    parser.add_argument("--validate", action="store_true",
                        help="Validate an existing output instead of building it")
    args = parser.parse_args()
    if args.validate:
        validate(args.output.resolve())
    else:
        if not args.ffdec or not args.run_id:
            parser.error("--ffdec and --run-id are required when building")
        build(args.ffdec.resolve(), args.output.resolve(), args.run_id)


if __name__ == "__main__":
    main()
