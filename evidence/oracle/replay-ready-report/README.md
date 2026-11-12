# Identity-checked r13 Ready and actual-state reporting

Base `5000ae8745661edd94770dc4b592a82022bc16a8`. Offline test-runner reporting
only; no gameplay scheduler, validator, locked input, historical package or tape
changed. No Flash/live/FDB/connection experiment. All five flags remain false:
production_admitted, native_parity_proven, oracle_accepted, certified_global_tick,
os_input_join_proven. M0-02 pending. Weekly quota UNKNOWN.

## Binding and observation

The existing intro_continuous_reference runner now retains actual/expected state
values alongside differences. The explicit fourth argument `r13-report` enables
a narrow receipt profile; it is not a generic roster guesser. It requires the
exact r13 events and adjacent build.json hashes, then rechecks every locked
source hash from that pinned build. Before replay advances, runtime fighter slot
and model identities (Naruto/minren, Ichigo/yihu), model source hashes, helpers,
mode, AI, CPU assignment and stage must match. Runtime setup and fighter-model
hashes are retained. Hash qualification is not independent native binding or
proof of generated-model semantic correctness.

Wrong event/build identities write `identity_refused`, an empty checkpoint and
exit 1 before main scene initialization. Runtime identity failures stop before
replay, clean the scene, write the refusal and exit 1. The previous Ichigo/Byakuya
runner is neither used nor modified. Legacy modes remain available; they do not
claim this qualification or supply a qualified checkpoint.

Source anchors: immutable r13 instrumentation.diff root onEnterFrame increments
aiDisplay and emits ready when p2loaded, _menuEnabled and !zhanting hold; its
ready is sequence2466/display484, followed by the state rows. Existing main.gd
runs battle_intro.run_frame_actions immediately before the root-observer hook
and before deferred target scripts. At that hook, this reporting mode records
the first observed inactive intro. It reads actor fields, positions, frames,
actual random/clock cursors, queued frame counts and **all existing helper
objects**. It does not initialize, restore, fill or rewrite any state. The
relative fight_tick=0 names that first observed boundary; it is not a certified
global tick or independent proof of every source readiness predicate.

The snapshot is display484, frames2/3, random local cursor95, clock0, intro
inactive and pending actions[0,0]. `touchFloor=null` remains null. No expected
state is substituted. Full actual state is retained at every observed root
snapshot, including after Ready. Snapshot helper fields remain present even
when invisible; visibility is not a license to discard an instance.

## Executed results

Godot 4.7.2.stable.official.ed1daf0bf, same official executable/hash recorded in
replay-runtime-cleanup. Full raw reports/logs are gzip-compressed unchanged;
artifacts.json records uncompressed hashes.

- Strict r13 log: exit0, 1166/1166 body boundaries match.
- Unchanged full validator, horizon600: **exit1**, status unknown, first reason
  `source_build_provenance_not_clean`, intervention flag `body_boundaries`.
- Ready+600: 601/601 frame rows, 1202/1202 actual-state rows and 1202/1202 geometry
  rows match. RNG sequence298/298 and observed Ready cursor95 now satisfy the
  diagnostic RNG scope check. This is not newly proved native RNG completeness.
- Ready checkpoint **still refused**: the runtime contains Gaara and Kon helper
  objects, while r13 has no helper_load records for the validator's source
  identity list. Both helpers remain in the snapshot; neither the validator nor
  provenance is changed. Complete reporting is not complete acceptance.
- Six runtime identity negatives (wrong fighter, slot, AI, helper, fighter source
  hash, helper source hash), plus positive qualification pass the GDScript test.
- Two end-to-end receipt negatives: changed event bytes and changed build bytes
  both exit1, with no M0_BOOT_OK (scene never initialized).
- Three Python regressions pass: new actual/cursor checks versus the old
  differences-only report, mutation refusal, and equality of all prior simulation
  boundaries/geometry/frames/tapes/input transitions. Expected rows and delta
  records alone cannot substitute for actual state.
- Legacy r12 strict log exits0; original ql precision mismatch at boundary722
  remains unchanged. No threshold or number-format change.

The next executable offline step is to inspect the locked helper load/placement
path and retained r13 instrumentation for a justified identity observation plan.
Do not remove the two actual helpers or invent missing source helper_load rows.
Even a later helper match cannot clear the intervention-bearing provenance.
Clean native capture, certified scheduling/input join, noninterference and full
native oracle acceptance remain separate, unproved obligations.

## Commands

From the worktree, set GODOT to the pinned installed executable and ROOT to the
worktree path. Recorded executable: /tmp/bvn-rng-godot/Godot.app/Contents/MacOS/Godot.

```sh
python3.11 tools/run_godot_checked.py --log /tmp/identity.log -- "$GODOT" --headless --quit-after 120 --log-file /tmp/identity-engine.log --path godot -s res://tests/r13_report_identity_test.gd -- "$ROOT/evidence/ai/input-binary-r13/events.jsonl"
python3.11 tools/run_godot_checked.py --log /tmp/r13-ready.log -- "$GODOT" --headless --quit-after 5000 --log-file /tmp/r13-ready-engine.log --path godot -s res://tests/intro_continuous_reference.gd -- "$ROOT/evidence/ai/input-binary-r13/events.jsonl" /tmp/r13-ready.json combat-boundaries r13-report
python3.11 tools/probes/validate_ai_continuous_replay.py evidence/ai/input-binary-r13/events.jsonl /tmp/r13-ready.json --horizon 600 --source-build evidence/ai/input-binary-r13/build.json --output /tmp/r13-ready-acceptance.json
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/replay-ready-report -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_ai_continuous_replay tools.tests.test_godot_result
PYTHONDONTWRITEBYTECODE=1 python3.11 tools/verify.py
PYTHONDONTWRITEBYTECODE=1 python3.11 tools/check_handoff.py
git diff --check
```

For the receipt-negative tests, copy events.jsonl and build.json to a temporary
directory and append a newline to exactly one file. Run the same r13-report
command on that copy; require exit1 and identity_refused, not a replay result.
For legacy r12, use input-alias-r12/events.jsonl with combat-boundaries only.
No headless result here certifies GPU rendering, visual parity or native return.
