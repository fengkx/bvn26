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

## PR #278 P1 CPU review correction

The reviewed d0b2caf6 module rejected any truthy runtime p1cpu, rather than
comparing it with configuration. This was correct for the pinned human-P1 run,
but failed to enforce an explicit contrary configuration. The pinned build.json
omits p1cpu; immutable input-binary-r13/instrumentation.diff line223 explicitly
assigns `p1cpu = false`. The module now uses that source-bound default only for
this already hash-qualified profile, validates a Boolean configuration value,
and compares runtime P1 CPU with the expected value. It does not edit the build
or broaden receipt qualification.

Coverage adds absent-default mismatch, explicit false match, explicit true
mismatch and match, and non-Boolean rejection. Explicit true cases are synthetic
function-contract tests, not another qualified native profile. The explicit
true-config / false-runtime negative fails on the reviewed module (test line51,
strict exit1), and passes with the fix (strict exit0). Previous positives and six
negatives still pass. identity-test.log.gz is re-recorded; p1-cpu-before.log.gz
retains the failing regression. The pinned Godot SHA is rechecked in artifacts.json.

Full r13 rerun strict exit0; replay JSON equals the retained report in full.
The rerun acceptance remains exit1 / source_build_provenance_not_clean, and Ready
helper identity remains refused. New rerun log and acceptance receipts are
retained as p1-cpu-r13.log.gz and p1-cpu-acceptance.json.gz; the unchanged replay
artifact is not rewritten. Three report regressions, six existing Python tests,
verify.py, check_handoff.py and diff-check pass using the commands above.

Residual review notes deliberately not included: record_ready's last-two-row
indexing and the refusal report's absence of five explicit flag keys are separate
reporting concerns, not prerequisites for the CPU configuration comparison.
No helper research, validator/scheduler change, source mutation, live or admission.

## Ready observation binding correction (base 99f9adc9)

The original record_ready read the last two global state rows and overwrote
slot/frame/geometry with current fighters. It never checked row slot, tick or
phase. In an isolated Godot regression, the verbatim old method receives [p2,p1]
and assigns P2's HP=700 to slot P1 (whose actual HP row is900). This demonstrates
a reporting bug under reordered observations, not a claim that the recorded r13
normal path suffered it. The earlier real report remains unchanged.

compare_frames now returns its own synchronous observation batch. Ready reporting
checks exactly two unique p1/p2 rows, the expected display tick and root phase,
and the Godot instance ID plus source model path for each previously qualified
fighter. It assembles each actor's state, frame, geometry and pending actions
from that same row, not fresh reads mixed with old state. Reordered valid rows
are keyed by slot; missing, duplicate, stale, foreign-instance, wrong-phase or
incomplete rows return a structured refusal without a checkpoint. The runner
marks first_difference, reports the error, cleans up and exits1. Godot IDs are
local run identity only, not proof of Flash identity/lifetime or a global clock.

No expected values are used to fill actual fields. Null touchFloor and both
helpers remain. A shared non-admission schema now supplies all five explicit
false flags (and original_parity_verified=false) for success and identity refusal.
This resolves the two previously deferred reporting concerns without changing
source provenance, gameplay scheduling, validator gates, helper coverage or tapes.

Executed with the same pinned Godot4.7.2 executable:
- ready_observation_test: strict exit0, old misbinding reproduced; valid reorder
  bound correctly; missing/duplicate/extra/stale/wrong-phase/foreign/unknown-slot
  and missing-field cases refused; null retained; refusal flag schema checked.
- r13 identity test and full r13 replay: strict exit0. All previous r13 report
  fields, including checkpoint/state/boundary/RNG values, equal the retained
  report; only report_failure={} is added.
- Full validator: exit1, source_build_provenance_not_clean and helper checkpoint
  refusal unchanged. No acceptance or visual proof.
- End-to-end r12 input passed to r13-report: exit1 before scene initialization;
  the refusal JSON explicitly contains all false flags. The r12 tape is unchanged.
- Five package Python tests, six existing unit tests, verify/handoff/diff checks
  pass. New raw evidence is under binding-fix/; previous execution receipts remain.

Run the new adversarial test:

```sh
python3.11 tools/run_godot_checked.py --log /tmp/ready-binding.log -- "$GODOT" --headless --quit-after 120 --log-file /tmp/ready-binding-engine.log --path godot -s res://tests/ready_observation_test.gd
```

To also reproduce the old method's misbinding, create the temporary adapter below
and append `-- /tmp/bvn-ready-legacy.gd` to that command. This extracts the old
method verbatim; only its host is a RefCounted adapter with the two stored fields.
The test uses real FighterRuntime nodes and frees them, without a game/live run.

```sh
python3.11 - <<'PY'
import subprocess
from pathlib import Path
source = subprocess.check_output(['git', 'show', '99f9adc9:godot/tests/intro_continuous_reference.gd'], text=True)
method = source[source.index('func record_ready('):]
Path('/tmp/bvn-ready-legacy.gd').write_text('extends RefCounted\nvar state_comparisons: Array = []\nvar native_checkpoint: Dictionary = {}\n' + method)
PY
```
