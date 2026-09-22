"""Aggregate Lee callback markers from every archived native capture.

This deliberately reads both AIREF pipe captures and JSONL captures. A capture
without an unambiguous Lee slot is an error; it is never silently counted as a
zero-marker run.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def _index_slots(index: dict) -> dict[str, str]:
    result = {}

    def walk(value):
        if isinstance(value, dict):
            path = value.get("raw_capture_path") or value.get("events_path")
            slot = value.get("lee_slot")
            if isinstance(path, str) and slot in {"p1", "p2"}:
                result[path] = slot
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(index)
    return result


def _build_slot(path: Path, root: Path) -> str | None:
    for parent in [path.parent, *path.parents]:
        if parent == root.parent:
            break
        build = parent / "build.json"
        if not build.exists():
            continue
        try:
            data = json.loads(build.read_text())
            move = data.get("move_case", data)
            fighters = move.get("fighters", {})
            for slot in ("p1", "p2"):
                if str(fighters.get(slot, "")).lower() == "lee":
                    return slot
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _legacy_slot(path: Path) -> str | None:
    """Slot overrides for role-owned observer captures without build.json."""
    name = str(path)
    if "lee-callback-observer-recovery-r01" in name:
        return "ignore"
    if "lee-callback-observer-hp1" in name or "lee-clip-observer-recovery" in name or "lee-timer-hp1" in name:
        return "p2"
    if any(token in name for token in ("lee-callback-", "lee-callback-exact-", "lee-timer-kill", "lee-callback-observer-kill")):
        return "p1"
    return None


def _is_capture(path: Path) -> bool:
    if path.name in {"events.jsonl", "capture.jsonl"}:
        return True
    if path.suffix:
        return False
    try:
        return any(line.startswith("AIREF|") for line in path.open(errors="ignore"))
    except OSError:
        return False


def _parse(path: Path) -> tuple[dict[str, set[int]], int]:
    frames: dict[str, set[int]] = defaultdict(set)
    errors = 0
    try:
        for line in path.read_text(errors="strict").splitlines():
            if line.startswith("AIREF|"):
                columns = line.split("|", 7)
                if len(columns) != 8 or columns[6] != "body_boundary":
                    continue
                payload = columns[7].split(",")
                if len(payload) < 2:
                    errors += 1
                    continue
                frames[payload[0]].add(int(payload[1]))
            elif line.lstrip().startswith("{"):
                event = json.loads(line)
                if event.get("kind") != "body_boundary":
                    continue
                payload = str(event.get("value", "")).split(",")
                if len(payload) < 2:
                    errors += 1
                    continue
                frames[payload[0]].add(int(payload[1]))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        errors += 1
    return frames, errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("evidence/characters/lee/original"))
    parser.add_argument("--inventory", type=Path, default=Path("evidence/characters/lee/source-callback-inventory-r01.json"))
    parser.add_argument("--index", type=Path, default=Path("evidence/characters/lee/callback-exact-r01/exact-marker-index.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, default=Path("evidence/characters/lee/callback-exact-r01/capture-slot-overrides-r01.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    index_slots = _index_slots(json.loads(args.index.read_text()))
    overrides_data = json.loads(args.overrides.read_text())
    overrides = overrides_data.get("slots", {})
    ignored = set(overrides_data.get("ignored", []))
    captures = []
    errors = []
    observed: dict[tuple[str, int], set[str]] = defaultdict(set)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not _is_capture(path):
            continue
        relative = str(path.relative_to(Path.cwd()))
        slot = index_slots.get(relative)
        if slot is None:
            slot = _build_slot(path, root)
        if slot is None:
            slot = overrides.get(relative)
        frames, parse_errors = _parse(path)
        if slot is None:
            # The directory also contains Byakuya/other-character captures.
            # A build that has no Lee fighter is a deliberate non-Lee skip;
            # only an otherwise plausible Lee capture is an error.
            build_found = None
            for parent in [path.parent, *path.parents]:
                candidate = parent / "build.json"
                if candidate.exists():
                    build_found = candidate
                    break
                if parent == root.parent:
                    break
            if relative in ignored:
                continue
            errors.append({"capture": relative, "error": "cannot determine Lee slot"})
            continue
        if parse_errors:
            errors.append({"capture": relative, "error": "malformed body_boundary rows", "count": parse_errors})
        lee_frames = frames.get(slot, set())
        captures.append({"capture": relative, "lee_slot": slot, "marker_count": len(lee_frames), "frames": sorted(lee_frames), "all_slot_frames": {k: sorted(v) for k, v in frames.items()}, "parse_errors": parse_errors})
        for frame in lee_frames:
            observed[(slot, frame)].add(relative)

    entries = json.loads(args.inventory.read_text())["entries"]
    # Acceptance keys include kind, slot and source capture provenance.  A
    # frame number alone is insufficient: Lee has both body and clip records
    # at frame 1098 and multiple fighter slots in the archive.
    native_matched: set[tuple[int, str, str, str]] = set()
    legacy_native_body: set[tuple[int, str]] = set()
    clip_observed: set[tuple[int, str]] = set()
    clip_report = Path("evidence/characters/lee/callback-exact-r01/clip-action-gap-r01.json")
    if clip_report.exists():
        report = json.loads(clip_report.read_text())
        for event in report.get("native_clip_observer_capture", {}).get("observed_schedule_events", []):
            source_path = str(event.get("source_path", ""))
            match = re.search(r"DefineSprite_518/frame_(\d+)/", source_path)
            if match and event.get("phase") in {"enter", "exit"}:
                # The observer path has a ``fighter/lee#`` prefix while the
                # inventory stores the source-relative suffix.  Keep the
                # complete path, but normalize only that transport prefix.
                clip_observed.add((int(match.group(1)), source_path.split("#", 1)[-1]))
    for compare_path in (Path("evidence/characters/lee/callback-exact-r01/compare.json"), Path("evidence/characters/lee/callback-exact-r01/godot-exact-callback-compare-r01.json")):
        compare = json.loads(compare_path.read_text())
        for case in compare.get("cases", []):
            if case.get("callback_sequence_match", False) or set(case.get("matched_fields", [])) >= {"source_frame", "entering", "action", "ql"}:
                events = case.get("source_events", [])
                source_raw = case.get("source_raw")
                slot = next((str(e.get("slot")) for e in case.get("godot_events", []) if e.get("slot") in {"p1", "p2"}), None)
                for event in events:
                    frame = event.get("source_frame", event.get("frame"))
                    if frame is None or not slot:
                        continue
                    # Legacy compare.json predates source_raw path binding and
                    # carries only a source capture hash. Bind it to the
                    # inventory row's own source captures and slot, never to
                    # every row sharing the frame number.
                    if source_raw:
                        native_matched.add((int(frame), "frame_action", slot, str(source_raw)))
                    else:
                        for candidate in entries:
                            if int(candidate["source_frame"]) == int(frame) and candidate["kind"] == "frame_action" and candidate.get("slot") == slot:
                                for capture in candidate.get("source_raw_captures", []):
                                    native_matched.add((int(frame), "frame_action", slot, str(capture)))
                # compare.json predates path binding; retain its accepted
                # body-callback result as a body-only key, never for clips.
                if case.get("callback_sequence_match", False) and slot:
                    for event in events:
                        frame = event.get("source_frame", event.get("frame"))
                        if frame is not None:
                            legacy_native_body.add((int(frame), slot))
    for attempts_path in (
        Path("evidence/characters/lee/callback-exact-r01/native-exact-attempts-r02.json"),
        Path("evidence/characters/lee/callback-exact-r01/native-exact-attempts-r03.json"),
    ):
        if not attempts_path.exists():
            continue
        for attempt in json.loads(attempts_path.read_text()).get("attempts", []):
            if attempt.get("status") not in {"native_exact_observed"}:
                continue
            frame = attempt.get("source_frame")
            slot = attempt.get("slot")
            source_raw = attempt.get("source_raw")
            if frame is not None and slot and source_raw:
                native_matched.add((int(frame), str(attempt.get("kind", "frame_action")), str(slot), str(source_raw)))
    rows = []
    for entry in entries:
        frame = int(entry["source_frame"])
        slots = [slot for slot in ("p1", "p2") if (slot, frame) in observed]
        captures_for_frame = sorted({p for slot in slots for p in observed[(slot, frame)]})
        source_keys = {(frame, entry["kind"], slot, capture) for slot in slots for capture in captures_for_frame}
        if native_matched.intersection(source_keys) or (
            entry["kind"] == "frame_action" and any((frame, slot) in legacy_native_body for slot in slots)
        ):
            status = "native_matched"
        elif entry["kind"] == "clip_action" and any(
            frame == observed_frame and (
                str(entry["source_path"]).endswith(str(source_path))
                or str(source_path).endswith(str(entry["source_path"]))
            )
            for observed_frame, source_path in clip_observed
        ):
            status = "source_only"
        elif frame in {325, 332}:
            status = "normal_input_unreachable"
        elif captures_for_frame:
            status = "source_only"
        else:
            status = "remaining"
        rows.append({**entry, "lee_slots_observed": slots, "source_raw_captures": captures_for_frame, "status": status})
    output = {"schema": "lee-callback-inventory-aggregate-r01", "captures": captures, "capture_count": len(captures), "parse_errors": errors, "entries": rows, "counts": dict(Counter(row["status"] for row in rows))}
    by_key = {(row["source_frame"], row["kind"]): row for row in rows}
    assertions = {
        "frame_320_source_observed": by_key.get((320, "frame_action"), {}).get("status") == "source_only",
        "frame_1083_recovery_p2": by_key.get((1083, "frame_action"), {}).get("lee_slots_observed") == ["p2"],
        "frame_1086_recovery_p2": by_key.get((1086, "frame_action"), {}).get("lee_slots_observed") == ["p2"],
        "frame_1088_clip_observed": by_key.get((1088, "clip_action"), {}).get("status") in {"source_only", "native_matched"},
        "frame_1098_clip_observed": by_key.get((1098, "clip_action"), {}).get("status") in {"source_only", "native_matched"},
        "frame_29_native_comparison": by_key.get((29, "frame_action"), {}).get("status") == "native_matched",
    }
    output["known_case_assertions"] = assertions
    if not all(assertions.values()):
        raise SystemExit("known-case aggregate assertions failed: " + json.dumps(assertions, ensure_ascii=False))
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"captures": len(captures), "parse_errors": len(errors), "counts": output["counts"]}, ensure_ascii=False))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
