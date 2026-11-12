# Replay recipe identity before slot indexing

Base 2bec1106f86c4e9e642c73962635993579bf9088. Offline correctness fix,
not a new observation facility. No player, Godot capture, debugger or live run.
All five admission/proof flags and native_initialization_complete remain false;
M0-02 pending. Observation profiles/helper_init_observer remain interventions.

## Reproduction and fix

`tools/analyze_diagnostics.py::replay_preflight` previously normalized list-form
match.players with a slot-keyed dict comprehension and filtered non-dict rows.
That discarded contradictory/identical duplicates and malformed extra rows.
The synthetic test isolates player recipe validation with mocked coverage/hash
checks and a temporary synthetic catalog, not a native receipt. Correct p1/p2,
reordered p2/p1, and dictionary-form recipes pass. Before the fix, all three
invalid lists also returned no preflight problems:

- extra p1 with resourcePath=res://wrong followed by correct p1/p2;
- identical duplicated p1 followed by p2;
- null followed by correct p1/p2.

The first case hides a resource-path identity failure before catalog checking.
The retained regression-before.log records three failing negative subcases.
`run_replay` uses this preflight before launching its fixed executor; no executor
was launched in this reproduction. No claim that other real-world capture/build
prerequisites were proved by this isolated test.

The fix requires exactly two object rows with explicit unique p1/p2 identities
before conversion. No row is dropped and no positional identity is supplied.
Dictionary-form compatibility and catalog/resource checks are unchanged.
Missing/empty/foreign-slot cases also refuse. The synthetic setup and mocks are
restricted to tests; no capture data or acceptance criteria were changed.

## Audit boundary

- Continuous replay consumer state_map, geometry_map and helper_map already
  require matching key sets AND original row counts; source state/helper maps
  explicitly reject repeated keys. #282 Ready actor uniqueness is unchanged.
- helper_init_observer chains reject a second pre-Ready kind per slot before
  assignment; schema and flags remain unchanged.
- Native r05 actor-clock validation (retained by r25) requires adjacent p1/p2
  numeric snapshots and matched callback ordinals. It returns
  certified_global_tick=false; r25 explicitly keeps OS join false.
- ready_observation.gd binds a synchronous two-row batch by slot, tick, phase and
  Godot instance identity; local identity is not native lifetime/global time.
- analyze_diagnostics keeps exactReplayCandidate=false; executor eligibility
  is diagnostic readiness, not certified global ticks or OS input proof.
- New profiles still require explicit consent and refuse helper_init_observer
  for clean-source admission. No historical metadata is upgraded.

This focused audit found the recipe conversion bug. It is not an exhaustive
proof that every consumer is safe and does not certify a clock or native return.

## Checks

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_replay_recipe_players tools.tests.test_ai_continuous_replay tools.tests.test_builder_profiles tools.tests.test_helper_init_observer tools.tests.test_helper_source_resolution tools.tests.test_godot_result
python3.11 evidence/oracle/helper-profile-isolation/check_historical.py
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
git diff --check
```

28 targeted tests pass; historical r12/r13 full CLIs still exit1 with identical
checks/provenance (source_build_provenance_not_clean). Replay byte hashes are in
historical-checks.json. Missing helper identities and r12 decimal refusal remain.
Eight self-contained AnalyzeDiagnosticsTests also pass using unittest's loader,
excluding the three optional external historical-capture tests (the names are
listed below); mocked executor tests execute no Godot. verify/handoff/diff pass.

```python
import unittest
from tools.tests.test_analyze_diagnostics import AnalyzeDiagnosticsTests
excluded = {'test_cli_analyzes_the_historical_user_log',
            'test_native_main_capture_reports_fresh_start_coverage_and_last_hit',
            'test_replay_preflight_requires_matching_build_and_catalog_resolved_resources'}
names = [n for n in unittest.defaultTestLoader.getTestCaseNames(AnalyzeDiagnosticsTests) if n not in excluded]
result = unittest.TextTestRunner().run(unittest.TestSuite(AnalyzeDiagnosticsTests(n) for n in names))
raise SystemExit(not result.wasSuccessful())
```

Next step: independent review only. Native oracle, initialization completion,
noninterference, certified scheduling/OS join and repeat remain unproved.
Official weekly remaining UNKNOWN. No deployment or unrelated workspace touched.
