"""Source-pinned, opt-in helper initialization observations for future copies."""
from __future__ import annotations

import hashlib

KINDS = ("helper_init_request", "helper_init_load_complete", "helper_init_frame_tail")

SITES = {
    ("main", "DefineSprite_1900/frame_1/DoAction.as"): "cb217a4711cd07059b39bf671e4382b352f9f26944b7236141c9da0c237ee27b",
    ("fighter/fz/woailuo", "frame_1/DoAction.as"): "cbafff39ffe1fc02257bcfcb33c6e6db8abe6db739aaa8dd769103fe93b3c9b9",
    ("fighter/fz/kon", "frame_1/DoAction.as"): "c6ff0865c88f6cdf9f995184cf3b1abcc801500369a5dadc6799496c2af3c0c4",
}


def configuration(p1: str | None, p2: str | None) -> dict:
    if p1 not in ("我爱罗", "woailuo") or p2 not in ("魂", "kon"):
        raise ValueError("Helper init observation requires explicit P1 Gaara and P2 Kon")
    return {"format": "helper-source-init-v1", "slots": {
        "p1": {"selection": "我爱罗", "asset": "woailuo", "target": "/game/p1fz"},
        "p2": {"selection": "魂", "asset": "kon", "target": "/game/p2fz"}},
        "scope": "request_then_load_complete_callback_then_source_frame1_tail_before_ready",
        "native_initialization_complete": False, "noninterference_proven": False,
        "source_sha256": {name + "#" + path: digest for (name, path), digest in SITES.items()},
        "columns": {
            "helper_init_request": ["slot", "selection", "resolved_url", "target"],
            "helper_init_load_complete": ["slot", "target", "loaded_url"],
            "helper_init_frame_tail": ["slot", "source_asset", "target", "loaded_url", "frame", "inited", "attacking"]}}


def _slot(target: str) -> str:
    return f'({target} === _root.game.p1fz ? "p1" : ({target} === _root.game.p2fz ? "p2" : "unknown"))'


def instrument(original: str, updated: str, bundle: str, path: str) -> str:
    key = (bundle, path)
    if key not in SITES:
        return updated
    if hashlib.sha256(original.encode()).hexdigest() != SITES[key]:
        raise ValueError(f"Helper initialization source changed: {key}")
    if 'aiEvent("helper_init_' in updated:
        raise ValueError("Helper initialization observer already installed")
    if bundle == "main":
        call = '_this._loader.loadClip(_root.fzDir + _loc3_.fzurl,_root.game[pr + "fz"]);'
        callback = 'LO.onLoadComplete = function(target)\r\n{'
        # Other builder passes may normalize line endings, but not source logic.
        if callback not in updated:
            callback = callback.replace('\r\n', '\n')
        if updated.count(call) != 1 or updated.count(callback) != 1:
            raise ValueError("Missing unique helper request/completion source anchor")
        request = '_root.aiEvent("helper_init_request", pr + "," + _root[pr + "sf"] + "," + _root.fzDir + _loc3_.fzurl + "," + _root.game[pr + "fz"]._target);\n   '
        complete = ('\n   if(target === _root.game.p1fz || target === _root.game.p2fz)\n   {\n'
                    '      _root.aiEvent("helper_init_load_complete", ' + _slot('target') +
                    ' + "," + target._target + "," + target._url);\n   }')
        return updated.replace(call, request + call).replace(callback, callback + complete)
    asset = bundle.rsplit('/', 1)[-1]
    return updated + ('\n_root.aiEvent("helper_init_frame_tail", ' + _slot('this') +
                      ' + ",' + asset + '," + this._target + "," + this._url + "," + _currentframe + "," + inited + "," + attacking);\n')


def analyze(events: list[dict], config: dict, run_id: str) -> dict:
    """Require one complete pre-Ready chain per slot; never synthesize old events."""
    result = {"status": "refused", "source_frame_initialization_observed": False,
              "native_initialization_complete": False, "production_admitted": False,
              "native_parity_proven": False, "oracle_accepted": False,
              "certified_global_tick": False, "os_input_join_proven": False}
    try:
        if config != configuration("我爱罗", "魂") or not run_id or not events:
            raise ValueError("unqualified_observation_configuration")
        for index, event in enumerate(events, 1):
            if event.get("run_id") != run_id or type(event.get("sequence")) is not int or event["sequence"] != index:
                raise ValueError("foreign_or_noncontiguous_capture")
        ready = [e for e in events if e.get("kind") == "ready"]
        if len(ready) != 1:
            raise ValueError("missing_or_duplicate_ready")
        chains = {slot: {} for slot in config["slots"]}
        for event in events:
            kind = event.get("kind", "")
            if not kind.startswith("helper_init_") or event["sequence"] >= ready[0]["sequence"]:
                continue
            if kind not in config["columns"] or not isinstance(event.get("value"), str):
                raise ValueError("unknown_or_malformed_observation")
            parts = event["value"].split(',')
            if len(parts) != len(config["columns"][kind]) or parts[0] not in chains:
                raise ValueError("malformed_or_unknown_helper")
            slot = parts[0]
            if kind in chains[slot]:
                raise ValueError("duplicate_pre_ready_observation")
            chains[slot][kind] = (event["sequence"], parts)
        for slot, expected in config["slots"].items():
            chain = chains[slot]
            if set(chain) != set(config["columns"]):
                raise ValueError("incomplete_helper_initialization")
            request, complete, tail = [chain[k] for k in KINDS]
            if not request[0] < complete[0] < tail[0]:
                raise ValueError("unproved_initialization_order")
            r, c, t = request[1], complete[1], tail[1]
            if (r[1] != expected["selection"] or r[3] != expected["target"]
                    or c[1] != expected["target"] or t[2] != expected["target"]
                    or not r[2].endswith('/' + expected["asset"] + '.swf')
                    or c[2] != r[2] or t[3] != r[2] or t[1] != expected["asset"]
                    or t[4:] != ["1", "true", "false"]):
                raise ValueError("helper_identity_or_initial_state_mismatch")
        result.update(status="source_init_chain_observed", source_frame_initialization_observed=True,
                      chains=chains)
    except (ValueError, KeyError, TypeError) as error:
        result["reason"] = str(error)
    return result


def main() -> int:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build = json.loads(args.build.read_text())
    events = [json.loads(line) for line in args.events.read_text().splitlines() if line.strip()]
    result = analyze(events, build.get("helper_init_observer"), build.get("run_id", ""))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "reason": result.get("reason")}, ensure_ascii=False))
    return 0 if result["source_frame_initialization_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
