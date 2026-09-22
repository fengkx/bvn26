"""Compare archived Godot Lee callback attempts with same-fixture source rows.

This is deliberately conservative: a callback-shaped Godot log is not a
match until its source capture, slot, kind and four requested fields agree.
Clip callbacks are kept separate from body frame actions and are never
promoted by a frame-number-only lookup.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from collect_ai_reference import decode_number


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/characters/lee"
INVENTORY = EVIDENCE / "callback-exact-r01/pending-inventory-current-r02.json"
LOG_DIR = EVIDENCE / "godot/callback-exact-r03-attempts"
OUT = EVIDENCE / "callback-exact-r01/native-exact-attempts-r03.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_events(path: Path, slot: str, frame: int) -> list[dict]:
    out = []
    paths = [path] if path.is_file() else list(path.rglob("events.jsonl"))
    if path.is_file() and path.name.endswith("events.jsonl"):
        paths = [path]
    for p in paths:
        if not p.is_file():
            continue
        for line in p.read_text(errors="ignore").splitlines():
            if line.startswith("AIREF|"):
                cols = line.split("|", 7)
                if len(cols) != 8 or cols[6] != "body_boundary":
                    continue
                val = cols[7]
                # AIREF columns are sequence|time_ms|display_tick|fight_tick;
                # time is cols[3], display is cols[4], fight is cols[5].
                tick = int(cols[5])
                disp = int(cols[4])
                time_ms = int(cols[3])
            elif line.lstrip().startswith("{"):
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("kind") != "body_boundary":
                    continue
                val = str(ev.get("value", ""))
                tick = ev.get("fight_tick")
                disp = ev.get("display_tick")
                time_ms = ev.get("time_ms")
            else:
                continue
            fields = val.split(",")
            if len(fields) < 7 or fields[0] != slot:
                continue
            try:
                if int(fields[1]) != frame:
                    continue
                ql = decode_number(fields[6])
                out.append({
                    "source_frame": frame,
                    "entering": fields[2] == "true",
                    "action": float(fields[4]) if fields[4] not in {"undefined", ""} else None,
                    "ql": ql,
                    "fight_tick": tick,
                    "display_tick": disp,
                    "time_ms": time_ms,
                    "raw": val,
                    "source_file": str(p.relative_to(ROOT)),
                })
            except (ValueError, TypeError):
                continue
    return out


def native_events(path: Path) -> list[dict]:
    out = []
    pat = re.compile(r"LEE_EXACT_CALLBACK (\{.*\})")
    for line in path.read_text(errors="ignore").splitlines():
        m = pat.search(line)
        if not m:
            continue
        try:
            out.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            continue
    return out


def resolve_source(relpaths: list[str], slot: str, frame: int) -> tuple[str | None, list[dict]]:
    for rel in relpaths:
        p = ROOT / rel
        rows = source_events(p, slot, frame)
        if rows:
            return rel, rows
    return None, []


def main() -> None:
    inventory = json.loads(INVENTORY.read_text())["entries"]
    by_frame = {(int(e["source_frame"]), e["kind"], e["slot"]): e for e in inventory}
    rows = []
    for log in sorted(Path(str(LOG_DIR)).glob("*.log")):
        m = re.search(r"target(\d+)(?:\.log)?$", log.name)
        if not m:
            continue
        frame = int(m.group(1))
        events = native_events(log)
        slots = sorted({str(e.get("slot")) for e in events if e.get("slot") in {"p1", "p2"}})
        slot = slots[0] if len(slots) == 1 else None
        entry = by_frame.get((frame, "frame_action", slot)) if slot else None
        item = {
            "fixture_log": str(log.relative_to(ROOT)),
            "log_sha256": sha(log),
            "source_frame": frame,
            "native_events": events,
            "slot": slot,
            "kind": "frame_action",
            "status": "native_observed" if events else "native_not_reached",
            "matched_fields": [],
            "differences": [],
        }
        if entry is None and slot:
            # A probe can emit a callback for a source row outside the 49-row
            # inventory; keep it observable but never promote it.
            item["status"] = "invalid_inventory_key"
            item["differences"].append("no matching frame_action inventory row for slot")
        elif entry and events:
            source_rel, src = resolve_source(entry.get("source_raw_captures", []), slot, frame)
            item["source_raw"] = source_rel
            if source_rel:
                item["source_raw_sha256"] = sha(ROOT / source_rel)
            # Compare only the requested four fields, preserving entry order.
            keys = ("source_frame", "entering", "action", "ql")
            n = min(len(src), len(events))
            for i in range(n):
                for key in keys:
                    sv = frame if key == "source_frame" else src[i].get(key)
                    nv = events[i].get("source_frame") if key == "source_frame" else events[i].get(key)
                    if isinstance(sv, float) or isinstance(nv, float):
                        equal = sv is not None and nv is not None and abs(float(sv) - float(nv)) < 1e-6
                    else:
                        equal = sv == nv
                    if not equal:
                        item["differences"].append({"index": i, "field": key, "source": sv, "native": nv})
                    elif key not in item["matched_fields"]:
                        item["matched_fields"].append(key)
            if len(src) != len(events):
                item["differences"].append({"field": "event_count", "source": len(src), "native": len(events)})
            if source_rel and not item["differences"] and set(item["matched_fields"]) == set(keys):
                item["status"] = "native_exact_observed"
            elif not source_rel:
                item["status"] = "native_observed_source_unresolved"
            else:
                item["status"] = "native_diverged"
        rows.append(item)
    out = {
        "schema": "lee-exact-callback-native-attempts-r03",
        "scope": "Existing Godot target-filter logs only; no Flash capture and no production runtime changes.",
        "comparison_fields": ["source_frame", "entering", "action", "ql"],
        "ql_decoder": "tools/probes/collect_ai_reference.py:decode_number",
        "runtime_provenance": {"status": "not embedded in target-filter logs; do not promote to full parity"},
        "attempts": rows,
        "counts": {},
    }
    from collections import Counter
    out["counts"] = dict(Counter(r["status"] for r in rows))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"attempts": len(rows), "counts": out["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
