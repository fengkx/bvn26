"""Group retained receiver rules across every main fighter, without assuming parity."""
import argparse
import json
from pathlib import Path

from analyze_ai import functions, sha

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence/ai/shared-receiver-rules.json"
NAMES = ("onDefence", "updateDirect", "loseHp", "hitlosehp", "getHitObj")


def build() -> dict:
    groups = {name: {} for name in NAMES}
    bundles = []
    for path in sorted((ROOT / "scripts/fighter").glob("*.json")):
        bundle = json.loads(path.read_text())
        coverage = {name: 0 for name in NAMES}
        for record in bundle["scripts"]:
            found = functions(record["source"])
            for name in NAMES:
                if name not in found:
                    continue
                source = found[name]
                digest = sha(source.encode())
                group = groups[name].setdefault(digest, {"source": source, "occurrences": []})
                group["occurrences"].append({"bundle": path.relative_to(ROOT).as_posix(), "path": record["path"]})
                coverage[name] += 1
        bundles.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path.read_bytes()), "coverage": coverage})
    return {"status": "all_main_fighter_source_groups_not_runtime_acceptance", "bundles": bundles,
            "groups": groups,
            "limits": ["Source duplicates do not prove that every form is reachable or ported.",
                       "Variants are retained separately; migration must bind the matching source rule.",
                       "The health HUD callback is global main.swf behavior, not a fighter-specific rule."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert OUTPUT.read_text() == encoded, "Shared receiver audit is stale"
    else:
        OUTPUT.write_text(encoded)
    print(json.dumps({"bundles": len(result["bundles"]), "groups": {name: len(groups) for name, groups in result["groups"].items()}}))
