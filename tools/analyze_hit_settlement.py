"""Index receipt and settlement source separately; never infer a tick delay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_ai import functions, sha
from importer.compile_hit_receive import (
    compile_on_be_hit_frames,
    compile_on_defence_frames,
)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "evidence/ai/hit-settlement-source.json"


def build() -> dict:
    result = {"status": "static_source_index_not_runtime_acceptance", "fighters": {}}
    for name, sprite in (("minren", 764), ("yihu", 638)):
        path = ROOT / f"scripts/fighter/{name}.json"
        bundle = json.loads(path.read_text())
        scripts = {item["path"]: item["source"] for item in bundle["scripts"]}
        entries = {}
        for owner, names in (
            (2, ("beida", "fangyu")),
            (sprite, ("onBeHit0", "onBeHit", "hitlosehp", "onDefence")),
        ):
            source_path = f"DefineSprite_{owner}/frame_1/DoAction.as"
            found = functions(scripts[source_path])
            for function in names:
                source = found[function]
                entries[function] = {
                    "source_path": source_path,
                    "source_sha256": sha(source.encode()),
                    "source": source,
                }
        calls = []
        for event in compile_on_be_hit_frames(bundle) + compile_on_defence_frames(bundle):
            if event["sprite_id"] != sprite:
                continue
            source_path = event["source_path"]
            previous = f"DefineSprite_{sprite}/frame_{event['frame'] - 1}/DoAction.as"
            calls.append({
                **event,
                "source": scripts[source_path],
                "preceding_frame_source": scripts.get(previous),
                "preceding_frame_path": previous,
            })
        result["fighters"][name] = {
            "bundle": path.relative_to(ROOT).as_posix(),
            "bundle_sha256": sha(path.read_bytes()),
            "sprite_id": sprite,
            "functions": entries,
            "settlement_calls": sorted(calls, key=lambda event: event["frame"]),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if OUTPUT.read_text() != output:
            raise SystemExit("Hit settlement source index is stale")
    else:
        OUTPUT.write_text(output)
    print("HIT_SETTLEMENT_SOURCE_OK")


if __name__ == "__main__":
    main()
