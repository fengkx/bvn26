# r12: offline source-local startFight and menu outcome observers

Based on master dc291085a3f5bb96f5d28803e0cfb006d34de05a (#254).
Offline only: no Flash launch, capture or input. Official remaining UNKNOWN;
not claiming above floor. production_admitted=false, native_parity_proven=false,
oracle_accepted=false. M0-02 remains pending.

## Narrow source gap and correction

r11's first unpaused, HP-complete, p2loaded camera entry is not a source-local
startFight boundary. Locked `scripts/main.json:frame_8/DoAction.as` defines
startFight with three operations: clear zhanting, clear readying, call
`_root.setMenuEnable(true)`. The actual setMenuEnable body writes `_menuEnabled=v`
and hides game_menu only when v is false. Enabling is **not** showing the menu.
These state writes were not observed by the historical r09 trace.

This package instruments only these two exact existing function bodies in the
independent r08 copy. Missing/duplicate bodies fail closed. The original source
statements and call/assignment counts are preserved; removing the six inserted
marker snippets reconstructs the inherited frame8 source exactly in tests.
No call is replaced, no result is manufactured, no return/goto/frame is inserted,
and no global Key/Math API is changed.

| Event | Position and fields |
|---|---|
| startfight-entry | Before original writes; zhanting, readying, lexical _menuEnabled, gamePaused, p2loaded, root frame; immediate P1/P2 actor snapshots |
| startfight-state-written | After original readying=false and before menu call; same state tuple |
| menu-write-before | Inside existing setMenuEnable; v, lexical _menuEnabled, game_menu._visible before original assignment |
| menu-write-after | Immediately after the original assignment; same tuple |
| menu-exit | At original function's normal end, after original optional hide branch; same tuple |
| startfight-exit | At original function's normal end, after menu call returns; state tuple and immediate actor snapshots |

`escape` retains undefined/boolean field values as text rather than filling them.
Actor snapshots use the inherited full-precision encoder. Menu markers apply to
all actual invocations of that function, including later pause/KO calls; they are
not automatically attributed to startFight. A later live parser must establish
an unambiguous invocation interval. Missing exit is not a synthetic normal return.
The recorded normal end is a source-body marker, not native dispatcher/unwind proof.
Extra observation reads/traces still require noninterference validation.

## Independent build and byte audit

The immutable r08 builder prepares the temporary copy, then this builder imports
only patched `frame_8/DoAction.as`. Relative to r08, only **root/637:12** changes.
Relative to locked originals, the inherited six DoAction set remains:
main root547, root637, sprite1813, sprite1900, sprite1991; yihu sprite16.
All other tag payloads/header/topology and73 other assets are unchanged.
The corrected yihu39 native-alias query sites, decision-installed, loader,
chushi and timer markers are retained. No historical files are edited.

build.json pins output/source hashes and this builder. r08-build.json and
r07-build.json pin parent layers; inherited facility/marker-builder fields refer
to those historical builders, while startfight_builder_sha256 identifies r12.
Four compressed diff layers and compiler logs are retained. All compiled SWFs
are in receipt-pinned temporary directories, not committed assets.

```sh
python3.11 evidence/oracle/native-fight-r12/build_observer.py \
  --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-m002-r12-recheck \
  --run-id m002-r12-offline-recheck
python3.11 -m unittest discover -s evidence/oracle/native-fight-r12 -v
python3.11 evidence/oracle/native-fight-r12/analyze.py
python3.11 evidence/oracle/native-fight-r12/analyze.py --require-oracle
```

## Refusal and tests

Both analysis modes exit1. The immutable r09 replay has zero new startFight/menu
markers and still fails unchanged r05 structural validation with
`Incomplete actor state at clock boundary`. Hashes pin the raw input. No early
state is dropped or rewritten. The new shape-only function checks the six-event
order and actual written/returned state fields; synthetic positive fixtures remain
oracle_accepted=false and certified_global_tick=false. It is not a live admission
adapter and does not claim receipt provenance, actor completeness, invocation
identity or deterministic execution from an event list alone.

Tests reject missing/duplicate source bodies, marker collisions, absent/reordered/
duplicated return sequences, and mismatched menu/readying outcomes. See checks.json
for actual build/test/project verification and nonzero gate results.

## Next live requirement, not executed here

Existing captures cannot retrospectively prove the missing source-local events.
A future authorized run must use a new tag and recheck main+yihu copy hashes, then
retain the entire exact-PID physical-input run from boot. Match the actual
startFight entry/state-written/menu assignment/menu normal-return/startFight
normal-return sequence to actor snapshots and the timer/camera sequence, preserving
every early undefined HP row. Verify readying and _menuEnabled outcomes without
calling menu visibility equivalent to enabled state. Reject missing, nested or
ambiguous invocation joins; do not synthesize them from an unpaused camera sample.

That live observation is needed to validate these markers; offline work is complete
without launching Flash. It would still not certify global scheduler ticks,
physical-input downstream consumption, complete RNG tape, exclusive full trace,
deterministic repeat or original/instrumented noninterference. SOURCE_FIRST same-
input comparison is outstanding, so no mechanism/parity/admission is claimed.
