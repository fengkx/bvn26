# M0-02 r05: offline fight-query and timer observers

Offline preparation only. No Flash launch, capture, focus operation or physical input
was performed. M0-02 remains pending; `production_admitted=false`,
`native_parity_proven=false`, `oracle_accepted=false`.

## Source sites and scope

The r03/r04 observer watched only intro `renderSkip` queries. This extension
instruments **39 lexical `_parent.kis(_parent.<key>)` expressions** in
`scripts/fighter/ichigo.json` → `DefineSprite_12/frame_1/DoAction.as`.
Each site/function/line/argument is recorded in `build.json.fight_sites`.
Examples include `moveLeft`, `moveRight`, `holdJ`, `nornalhit`, `jump`,
`defence`, and skill/super predicates. They are in the non-AI branches of the
base-form fight decision helper, not intro/menu code. The unchanged load script
`frame_1/PlaceObject2_274_1/CLIPACTIONRECORD onClipEvent(load).as` binds
`kis = Key.isDown`. The forwarding helper calls **owner.kis(code) once**, preserving
the original receiver, argument and actual return, then logs owner target,
AI/pause flags, source frame, action and game clock. Short-circuit structure and
all original control-flow statements remain intact. No global API is replaced.
Live reachability, native alias identity after loading, and downstream action
consumption remain unproved; no claim covers transformed Ichigo or other fighters.

Also instrumented: `scripts/main.json` →
`DefineSprite_1813/frame_1/DoAction.as`, entry/exit of existing `time` callback.
The source initializes `gametime=maxtime`, uses `setInterval(time,1000)`, and
conditionally decrements while unpaused and both actors are alive; unlimited mode
bypasses this interval. We log the existing callback boundary, actual gametime,
pause flags and two actor snapshots. Its ordinal is **local to this timer**;
r03 camera ordinal and `getTimer()` remain distinct. None is a certified global
ExecutionProfile tick or an exact initial-state boundary.

SOURCE_FIRST: source functions and original stop/goto/interval operations are
retained. Recursive tag auditing preserves every placement/MOVE/removal tag and
frame layout; no lifetime or scheduling equivalence is inferred from that audit.
Tests assert source-call/short-circuit preservation, not guessed game behavior.
Same-input original/instrumented comparison and live callback ordering are absent;
therefore no runtime mechanism is changed and no task is marked complete.

## Build and recheck

From repository root, with the receipt-pinned JPEXS jar (SHA in build.json):

```sh
python3.11 evidence/oracle/native-fight-r05/build_observer.py \
  --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-m002-r05-recheck \
  --run-id m002-r05-offline-20261109
python3.11 -m unittest discover -s evidence/oracle/native-fight-r05 -v
python3.11 evidence/oracle/native-fight-r05/analyze.py
python3.11 evidence/oracle/native-fight-r05/analyze.py --require-oracle
```

Use a fresh output directory. For future live work, rebuild with a **new** tag;
this offline tag must not be reused as fresh capture identity. No capture driver
is invoked by these commands. Future driver integration must accept and recheck
the two changed assets; existing r03 assumptions must not silently admit them.

Build is layered on immutable r03 builder/observer. The retained r03 diff covers
three initial main tags; `extension.diff.gz` covers the extra boot definitions,
timer callback and fighter decision script. Final audit versus locked originals:

- main: `root/547:12`, `root/2012:39/sprite1813/1:12`,
  `root/2106:39/sprite1900/1:12`, `root/2198:39/sprite1991/1:12`.
- ichigo: `root/15:39/sprite12/1:12`.
- All remaining tag payloads/header/topology and **73 other assets** unchanged.

Only temporary copies are compiled. `build.json` pins source/output hashes,
compiler and facility sources. Compiler logs are retained compressed. Temporary
build paths are receipts, not a claim of cross-machine path availability.

## Refusal gates and remaining proof

Both analyzer invocations exit **1** without live receipts. The analyzer verifies
r05 source/build identity, fresh tag, raw-log selection, no foreign observer tag,
append interval, input PID returns and cleanup. Its structural parser demands
known fight sites, a positive P1 non-AI/unpaused query, numeric state, paired
camera callbacks, paired timer ordinals and actor snapshots; it rejects intro-only
queries, mismatched owners, gaps, duplicates, truncation and timer regression.
Synthetic tests exercise these rules; they are not observations.

Even a structurally complete future prefix cannot pass oracle acceptance: the CLI
continues to return 1. Certified initial-state/global clock proof, complete RNG
consumer provenance/replay tape, full exclusive contract-valid state trace,
physical input-to-consumption tick binding, deterministic repeat, and observer
noninterference still require independent evidence and a reviewed acceptance path.
Tag/owner strings are not OS per-write PID attestation. This package does not
replace shared validators or treat local timer pairs as global ticks.

See `checks.json` for actual exits. Current Codex remaining percentage was not
visible in this turn; no credential/session files were inspected.
