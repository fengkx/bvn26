# M0-02 r24: four-prefix capture adapter (offline)

Base `afd96ae169707e85a8a873d8dc07c211aeddb4d8` (#267 squash), checked out on a new branch without rewriting published history. Historical packages and local untracked b97e/c62f failed receipts remain immutable/uncommitted. **No Flash launch, physical input, Computer Use or live capture in this slice.** Official remaining UNKNOWN.

## Prepared adapter

`capture_observer.py` adapts the retained r22 physical movie-PID AX/CG/System Events path to a receipt-matched **r23** build. `channels.py` is shared by capture and analysis, pins the r23 builder hash, exact frame174 source site and seven-DoAction scope, and requires all four prefixes to be absent before launch:

- `M002|<fresh-tag>|`
- `M002SIDE|<fresh-tag>,`
- `M002LITERAL|<fresh-tag>|`
- `M002TARGET|<fresh-tag>|`

The original physical tape, lock, pinned player/assets/config, unique movie PID/window ownership, focus checks and owned cleanup remain. No CUA app-string binding or permission/grant request was added. The driver refuses stale prelaunch tags before launching, retains the complete raw flashlog in combined.log, records target counts alongside the other three channel counts, and rejects foreign tags in any channel. Raw files are retained before postcapture channel validation; rejection still reaches owned cleanup. Driver exit1 is intentional evidence-only behavior.

`analyze.py` requires exact build/session equality, r23 source-site/builder/scope, receipt channel counts, adapter and shared helper hashes, all prior source/player/input/focus/cleanup/copy checks, four-prefix freshness/foreign refusal, and **combined.log byte-identical to flashlog.after.log**. Changed order, removed target lines, changed bytes, nonappend baseline and mismatched root selection fail closed. Arbitrary bytes and unknown lines are preserved, not normalized away.

The r23 target parser reports only observed body owner/frame174. Repeated visits remain separate observations; wrong owner/frame/site and malformed/foreign target markers are refused. Target lines remain in combined order as barriers to inherited adjacency-based continuation joins. They are not filtered out to manufacture a literal-after match. `initiating_call_join_proven` and `helper_lifetime_proven` stay false; target occurrence does not prove original-helper continuation, liveness, native return or causal call association.

## Build and evidence boundaries

The retained build.json is the **offline r23 build receipt**, an expected shape, not a new live run. A later reviewed live package must retain its own fresh r23 build.json and use that same receipt for capture and analysis. Historical r22/r21 sessions cannot be relabeled as r23; tests reject them before host/provenance reads. No new SWF instrumentation or compile is required for this adapter-only slice; r23's independently compiled target observer is unchanged.

No run-01 exists here. Both CLI modes exit1 with `Refused: no live receipt; r24 four-prefix capture adapted but not live-proved`. The unchanged r05 full-prefix gate remains in the analyzer; a targeted immutable-e84a replay still refuses `Incomplete actor state at clock boundary`. No early HP/readiness row is trimmed or filled. Synthetic four-prefix payloads are tests only, not observations.

All five flags remain false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending. Full initial state/global scheduling, calibrated OS input join, full RNG/trace, repeat and noninterference remain unproved.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r24 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r24/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r24/analyze.py --require-oracle
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

Six retained binding tests plus ten targeted tests cover four-prefix freshness/foreign tags, byte identity/order, append/root selection, target shape/owner/frame, r23 receipt refusal, target interleaving barriers and historical structural refusal. Tests call pure gates and fixture replay; they never launch the capture driver. Actual exits are in checks.json.

## Next step after independent review/merge

A later authorized bounded live must build a fresh r23 temp copy/tag, retain its build receipt, run this four-prefix physical-PID adapter using the existing approved per-command host path, and analyze the complete raw logs. Test whether body-frame174 output appears while original helper after channels stay silent. A positive target observation proves body source execution/output only; silence leaves reachability/output unresolved. Neither result alone diagnoses the old silence or grants admission. No live is authorized or performed by this offline preparation, and no new live should precede review/merge.
