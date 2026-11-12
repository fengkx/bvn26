# Explicit helper-observation profile isolation

Base: b3859d6e852add4fb761e461c1f571c4a7344d68. Offline only; no Flash,
Godot, capture, debugger connection, or completion observation was executed.
Status: compiled-and-audited-not-live-validated. All five admission/proof flags
and native_initialization_complete remain false; M0-02 is pending.

## Source-bound isolation

`tools/probes/build_ai_reference.py::validate_profile` refuses an unspecified or
unknown profile before creating output. The helper-observation branch returns
through `helper_observation_profile.build` before the legacy diagnostic patch
pipeline. It requires explicit --helper-init-observer, --p1-helper woailuo and
--p2-helper kon (catalog aliases also resolve through the pinned config).
All non-default diagnostic switches are refused, including body_boundaries.
No fixture selection is assigned: helper arguments specify what a future trace
must prove, not what the movie has selected. Physical menu selection is required.
The legacy --frames option does not install a timer/auto-quit in this profile.

The separate diagnostic profile requires ALL of --diagnostic-auto-start,
--diagnostic-key-injection and --diagnostic-trace-hooks. These explicitly authorize
the legacy mandatory gotoAndPlay(6)/fixture launch, Key.isDown replacement,
and RNG/timer/predicate/intro/state logging bundle. Existing optional probes,
including --body-boundaries, still require their own options. Old caller scripts
without a profile now intentionally refuse; historical reproduction commands
must explicitly acknowledge diagnostics. No historical package was edited.

The observation builder checks locked SWF and source-site hashes before compiling
independent copies. Five exact source sites are changed:

- main root frame1: observation-only aiSeq/aiEvent logger, no key/RNG API override,
  scheduling callback, fixture launch, input tape, timeline jump or auto-quit.
- main root frame8: append ready marker at the tail of the existing startFight,
  after unchanged zhanting/readying/menu writes. This is a source-tail observation,
  not native return or a certified Ready clock. Both tick columns are -1 (unknown).
- main DefineSprite_1900 frame1: retained audited helper request before loadClip,
  and entry to the existing onLoadComplete callback for the actual p1fz/p2fz target.
- woailuo/kon root frame1: retained audited marker after original initialization.

The last three sites retain #280's helper schema and fail-closed event analyzer.
Request is not completion; onLoadComplete is not onLoadInit; source frame tail
is not native initialization completion. Missing/duplicate/foreign/reordered
chains remain refused. The new logger uses the same event envelope without
inventing ticks. There is no observed complete chain in this offline slice.

## Compiled audit and preservation limits

Retained build.json pins sources, compiler, outputs, sites and instrumentation.
FFDec SHA256: 090ab695053ad94cba6408574c7d7eea20ec60b6ae789ee6056a23f45106762f.
Original-to-copy audit: main three DoAction tags, each helper one DoAction;
all tag paths/header/other payloads unchanged. All 75 asset paths are retained;
only main.swf and the two helper SWFs differ. Locked game/ and scripts/ stay intact.
No compiled SWFs or tools are committed. Compiler logs and source diff are retained.

helper_init_observer is STILL an intervention. Logger/ready hooks also add work;
no noninterference or clean-source claim is made. Full acceptance now explicitly
rejects the new diagnostic provenance fields too. This tightens accounting,
never erases historical provenance. All successful builds and handled CLI build
refusals emit six explicit false flags. CLI syntax errors still use argparse
usage errors and never produce a successful build.

## Executed verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_builder_profiles tools.tests.test_helper_init_observer tools.tests.test_helper_source_resolution tools.tests.test_ai_continuous_replay tools.tests.test_godot_result
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/replay-ready-report -p 'test_*.py'
python3.11 tools/probes/build_ai_reference.py --profile helper-observation --helper-init-observer --p1-helper woailuo --p2-helper kon --ffdec /private/tmp/bvn-m0-observer-tools/ffdec/ffdec.jar --output /tmp/bvn-helper-profile-isolation --run-id helper-profile-offline-20261112
python3.11 evidence/oracle/helper-profile-isolation/check_historical.py
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_deidara_atm1_load_stamp tools.tests.test_helper_schedule
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
git diff --check
```

Use a fresh output directory. 27 targeted tests, nine legacy probe tests and five Ready-report tests pass.
Legacy diagnostic test callers were updated to supply explicit consent; without
that update their older error-message assertions correctly hit the new earlier
profile refusal instead. No legacy source/config guard was relaxed.
Negatives exercise every Boolean diagnostic switch, non-default fixture options,
missing profile/individual consent/helper configuration, source drift, CLI false
flags, and intervention accounting. Full r12/r13 validation exits1; checks and
provenance match retained acceptance reports exactly, including missing helper
identities, body_boundaries refusal, and strict r12 precision failure. Replay
hashes are retained in historical-checks.json; no new Godot execution was needed.

Next step after independent review: separately authorize a bounded physical-menu
capture with explicit helper selection, freshness and owned-PID cleanup. This
profile has no auto-quit; a reviewed host capture must own the duration/cleanup.
Relative resource resolution and live helper sequence remain untested. Even a
complete observed chain will not repair r13, prove noninterference, establish a
global tick/OS join, or admit native parity. Official weekly remaining UNKNOWN.
