# Do not erase affirmative intervention provenance

Base: 5d397fcac186ab81bbba2070e823582937619461. Offline acceptance-tool fix.
No capture, Flash, Godot execution, FDB connection or new observer facility.
All five admission/proof flags and native_initialization_complete remain false;
M0-02 pending. Observation profiles/helper_init_observer remain interventions.

## Demonstrated path

validate_ai_continuous_replay.validate supports intervention fields both at the
build root and in configuration. Its former build.get(name, configuration.get())
used nested data only when the top-level key was absent. A false/null/zero/empty
root value therefore concealed an affirmative nested intervention. With otherwise
eligible synthetic horizon/CPU metadata, source_build_provenance.clean became
true and the refusal advanced past source_build_provenance_not_clean.

20 negative subcases reproduce that wrong clean assertion: five fields
(body_boundaries, helper_init_observer, auto_start, key_injection,
diagnostic_trace_hooks) times four false-like top-level values. They use an
explicitly synthetic temporary build, while reading unchanged retained r13
source/replay bytes. This is not a new source receipt or a claim that historical
r13 was fully admitted. Other historical Ready/helper obligations still refuse.
regression-before.log retains the failing assertions.

The fix unions affirmative intervention evidence from both supported locations.
A negative assertion in one location cannot erase a positive in the other.
No tape, provenance receipt, threshold, runtime or builder was changed. Existing
root-only intervention tests remain passing; contradictory metadata now refuses
at the original provenance gate. No new cleanliness attestation is introduced.

## Other examined paths and unsuccessful demonstrations

- Continuous frame/state/geometry maps have key-set and row-count guards.
  Duplicating a row at Ready display_tick484 in temporary copies of r13's replay
  returns matched=false in all three checks. An initial duplicate of the first
  frame row remained matched: inspection showed that row was outside the scoped
  Ready window, so it was not evidence of an in-window uniqueness bypass. No
  patch was justified for that attempt.
- Source actor/helper maps explicitly reject duplicate keys. Replay helper_map
  compares both keys and row count. #282 Ready and #283 recipe fixes are unchanged.
- helper_init_observer checks sequence/run identity and duplicate pre-Ready kinds
  before slot assignment. Its existing missing/duplicate/reload negatives pass;
  it keeps native_initialization_complete and all admission flags false.
- Retained r05 actor-clock validation requires paired callback ordinals and
  adjacent complete p1/p2 snapshots; r25 retains that refusal and explicitly sets
  certified_global_tick/os_input_join_proven=false. Static inspection found no
  true-setting path in the searched tools/probes Python files. This is not proof
  that all acceptance paths are defect-free or that local ticks are certified.

## Executed validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_helper_init_observer.HelperInitTests.test_top_level_false_cannot_mask_configured_intervention
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_helper_init_observer tools.tests.test_builder_profiles tools.tests.test_ai_continuous_replay tools.tests.test_replay_recipe_players tools.tests.test_helper_source_resolution tools.tests.test_godot_result
python3.11 evidence/oracle/helper-profile-isolation/check_historical.py
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
git diff --check
```

The first command failed 20 subcases before the fix; after it, all 29 tests in
the suite pass. Historical-checks.json records identical r12/r13 checks and
provenance, unchanged replay hashes, and both full CLI exits1 with
source_build_provenance_not_clean. The helper-identity and r12 decimal refusals
remain. verify/handoff/diff pass. No Godot rerun was required.

Next step is independent review only, not an automatic experiment. Native oracle,
noninterference, certified tick/OS join and native repeat remain unproved.
Official weekly remaining UNKNOWN.
