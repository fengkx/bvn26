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
import shutil
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
        if name == "initCtrl":
            brace = body.index("{") + 1
            body = body[:brace] + '\n_root.aiEvent("initCtrl",String(this));\n' + body[brace:]
        if name == "randAI":
            body = body[:-1] + '\n_root.aiEvent("sample",String(this)+","+attran+","+defran+","+goran+","+jumpran+","+bisharan);\n}'
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


def build(ffdec: Path, output: Path, run_id: str, frames: int) -> dict:
    if output.exists():
        raise ValueError("Use a fresh output directory; previous reference runs must remain intact")
    output.mkdir(parents=True)
    game = output / "game"
    game.mkdir()
    (game / "fighter").mkdir()
    (game / "fighter/fz").mkdir()
    # Copy only the assets selected by bootstrap; music stays read-only input.
    for name in ("kon", "woailuo"):
        shutil.copy2(ROOT / f"game/fighter/fz/{name}.swf", game / f"fighter/fz/{name}.swf")
    (game / "music").symlink_to(ROOT / "game/music", target_is_directory=True)
    changes = []
    sources = {}
    for name in ("main", "fighter/minren", "fighter/yihu"):
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
            if name == "main" and script["path"] == "frame_1/DoAction.as":
                updated = re.sub(r"function goLink\([^)]*\)\s*\{.*?^\}", "function goLink(url)\n{\n}", updated, flags=re.M | re.S)
                updated += '\ngotoAndPlay(6);\n'
            if name == "main" and script["path"] == "frame_10/DoAction.as":
                updated = (Path(__file__).parent / "as2/ai_reference/bootstrap.as").read_text()
                updated = updated.replace("__RUN_ID__", run_id).replace("__FRAMES__", str(frames))
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
                          "AI": 5, "stage": "现世", "p1sf": "我爱罗", "p2sf": "魂"},
        "sources_sha256": sources, "ffdec_sha256": sha(ffdec),
        "outputs_sha256": {p.relative_to(output).as_posix(): sha(p) for p in game.rglob("*.swf")},
        "instrumentation_sha256": sha(output / "instrumentation.diff"),
    }
    (output / "build.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--frames", type=int, default=600)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id) or args.frames < 1:
        parser.error("Use an alphanumeric run ID and a positive frame count")
    print(json.dumps(build(args.ffdec.resolve(), args.output.resolve(), args.run_id, args.frames), ensure_ascii=False))


if __name__ == "__main__":
    main()
