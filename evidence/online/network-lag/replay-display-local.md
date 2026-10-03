# Replay presentation and online combo display — local evidence

Implemented 2026-10-03 at the user's request. Replay presentation batching is
on by default; online matches suppress combo-number drawing automatically.
Diagnostics remain enabled. Fighter hit counters, damage, authored HUD clocks,
input/random tapes and audio observations are unchanged. Leaving online mode
restores the presentation policy and previous visibility.

## Source-first scope

1. Per-frame scripts: `scripts/main.json`,
   `DefineSprite_1833/frame_11/DoAction.as` reads the opponent's `mc.hits` and calls
   `sz.changeNum(hits)`. The implementation still advances this logical state.
2. Placement/MOVE: source display lists and retained nested clocks remain intact.
   Only derived Sprite2D/Polygon2D materialization is deferred. Collision bounds
   continue to use source data. New placement lifetimes are unchanged.
3. Label exit: `DefineSprite_1833/frame_50/DoAction.as` returns to frame 1;
   no label, stop, or fallthrough behavior changes.
4. Invariants: source `p1hits.pn=2` / `p2hits.pn=1`, fighter hit accounting and
   authored board state remain intact. Shadow BitmapData-style captures force
   the current actor to materialize before copying its pose. Retired nodes are
   weakly referenced and omitted from the final flush.
5. Same-input comparison: existing PvP and training timer golden comparisons
   each match 602 original states. New tests compare every raw checkpoint graph
   across eager/deferred rendering (330 frames per roster), final visual
   structure, current-pose shadows and diagnostic event payloads. This is local
   regression evidence, not a new original Flash visual-parity acceptance.

Hiding online combo numbers is an explicit user-authorized presentation change,
not a claim of original visual parity. References: `docs/HIT_RECEIVE_SOP.md`
and the existing compiled combo timeline. No source input or golden was edited.

## Implementation and validation

`TimelinePreview` keeps source clocks and sound observations on every replayed
frame, queues drawing work in `BattleCheckpoint`, and flushes at `end_replay`.
Immutable shader programs are now shared static caches, with per-material
uniforms preserved. Previously their lazy creation leaked into per-instance
checkpoint state; the new cache boundary changes graph encoding and requires
matching new compatibility fingerprints on both peers.

Two rosters each passed 330 complete-state comparisons and 385 final visual
comparisons, plus shadow pose and diagnostic-event equality. The additional
sparse/stride-two field-roster correction test compared 1,524 retained graphs.
The online pair test passed correction, pause, recovery, timeout, KO/result and
new-epoch cases with sparse/stride-two enabled. The default 12-test suite also
passed, including 11 fighters, 4 helpers and 10 maps, round transitions, immutable
caches, start cancellation and terminal service handling. Logs are retained;
the pair fixture asserts diagnostics remain enabled with the combo HUD hidden.

## Timing and limits

[Machine-readable evidence](replay-display-local.json) records sequential ABBA
native runs of the unchanged delayed-input workload, using
`rollback_delayed_input_profile.gd --batch` with/without `--eager-display` and
with/without `--field-roster` (see recorded command per run).

| Roster | Eager wall time (ms) | Deferred wall time (ms) | Deferred requests / actual flushes |
|---|---|---|---|
| Default | 5156.430, 5169.840 | 5152.833, 5098.953 | 512 / 80 |
| Field | 5595.826, 5597.170 | 5551.943, 5675.163 | 523 / 86 |

Actual replay materializations fall about 84%; total wall-time improvement is
small and inconsistent. Snapshot encoding remains a large cost. These numbers
are not browser FPS and do not establish that CPU-bound stalls are resolved.
`rebuild_count/us` measures restore refresh requests; the new
`display_deferred_count` and `display_flush_count/us` separately record queued
requests and actual flushes. No acceptance threshold or baseline was relaxed.

Reproduce with Godot 4.7.2, headless, `--max-fps 60`, `--path godot`, and
`-s res://tests/replay_display_smoke.gd` (also `-- --field-roster`), plus the
commands recorded in the JSON. `tools/test_shared_modes.py --godot <binary>`
checks the original tapes. Temporary logs remain outside source under
`/private/tmp/bvn-replay-display`; the JSON records their hashes.

No Web export, deployment or paired Web/TURN acceptance was performed for this
change. Existing NET gates and `plan/tasks.json` remain pending.

Repository verification, handoff checks, contract validation, manifest check
and `git diff --check` passed. Locked `game/` and `scripts/` inputs are unchanged.
Build fingerprint: `adbd0c319db4c82c790c6aacbcc7e15767fac0ea305b476e708502f64f62fa15`.
