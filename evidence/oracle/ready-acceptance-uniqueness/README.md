# Ready acceptance: preserve actor multiplicity

Base: 5b01734dc1fc960922be600fdf963090c850132d. Offline acceptance-tool fix;
no Flash/Godot capture, compilation, debugger connection or historical rewrite.
All five admission/proof flags and native_initialization_complete remain false.
M0-02 pending. No certified clock, OS input join or native parity claim.

## Demonstrated bug

validate_ai_continuous_replay.validate constructed checkpoint_actors with a dict
comprehension before checking its slots. The original list's multiplicity was
lost. The synthetic regression supplies a correct p1/p2 checkpoint, then prepends
an extra p1 with hp=-123 (or an identical p1). Both incorrectly returned
checks.ready_checkpoint=true. regression-before.log retains both failed negative
assertions on the unmodified validator. This demonstrates silent success of the
Ready subgate, not a claim that historical r13 was fully admitted: other checks
in this synthetic fixture and historical provenance still refuse.

The fix requires exactly two original actor rows AND the exact p1/p2 slot set
before checking their actual fields. It never filters rows, overwrites expected
state, or fills missing values. Unique reordered p2/p1 rows remain valid;
contradictory/identical duplicates, missing actors, empty lists and foreign slots
refuse. Existing frame/state/geometry comparison logic and tolerance are unchanged.

## Bounded audit

- Native actor-clock path: native-fight-r25/analyze.py invokes r05.validate_rows;
  r05 requires adjacent p1/p2 actor pairs, all numeric actor fields and paired
  timer boundaries. r25 keeps oracle flags false and explicitly sets global tick
  and OS join false. No changed historical analyzer or new native execution.
- Godot Ready producer: ready_observation.gd::bind_actors already requires exactly
  two synchronous rows, unique slots, matching tick/phase and actor identity.
  intro_continuous_reference.gd::record_ready uses that batch. The bug is at the
  Python report-consumer boundary, which must independently reject duplicates.
- Tick/OS claim boundaries: Godot non_admission and helper_init_observer.analyze
  retain false proof flags. Helper source completion is not native completion.
  Continuous replay's validated status is a selected diagnostic comparison, not
  global tick certification or production admission. No such flag was promoted.
- New profiles: build_ai_reference.validate_profile requires explicit consent;
  helper-observation bypasses the diagnostic pipeline. helper_init_observer and
  the diagnostic flags are still interventions refused by full acceptance.
  Historical build metadata was not upgraded or altered; current checks compare
  identically to retained r12/r13 reports. Unknown ticks (-1) are not certified.

This is a focused audit, not a proof that all acceptance tools are defect-free.
No additional observation facility or follow-up experiment was introduced.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_ai_continuous_replay tools.tests.test_builder_profiles tools.tests.test_helper_init_observer tools.tests.test_helper_source_resolution tools.tests.test_godot_result
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/replay-ready-report -p 'test_*.py'
python3.11 evidence/oracle/helper-profile-isolation/check_historical.py
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
git diff --check
```

27 targeted tests and five Ready-report tests pass after the fix. The regression
had two failing negative subcases before it. Historical checker invokes both full
acceptance CLIs: each exits1, source_build_provenance_not_clean, with all checks
and provenance identical to retained reports. Historical helper refusal, replay
bytes, body_boundaries and r12 tight decimal comparison remain unchanged.
verify/handoff/diff checks pass. No Godot rerun is required for this Python-only
consumer check; no runtime or reporter fields changed.

Next step: independent review of this fix. Observation profiles remain
interventions, not clean source. Actual native oracle, helper observations,
noninterference, certified scheduling/OS join and deterministic native repeat
remain unproved. Official weekly remaining UNKNOWN.
