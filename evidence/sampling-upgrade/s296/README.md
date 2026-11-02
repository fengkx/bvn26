# s296 — AFTER-s290 rank #6: Button2009 entry

Base: origin/master `9e24421a65c8579b91aa5626cf9ecd58f50a5449` (s295 #173).
Branch: `feat/s296-button2009-entry`.
Exclusive authority: [AFTER-s290 rank #6](../next-fix-priority-after-s290.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; `thin_coverage_cut_proved=false`;
zero product obligations closed; M0-02 pending.

## Fresh result

One fresh exact-path native app selection returned
`Computer Use server error -10005: timeoutReached` after **16.1641 seconds**,
without window state. [Operation and tool-reported cost](ui-control-attempts.json)
are retained separately from the historical s286 attempts (17.0744 seconds).
No keyboard/mouse input was sent, no instrumented movie was launched and no new
capture or native receipt exists. App selection can activate/launch the app;
that side effect remains unknown. This failure does not prove that native UI
control is impossible, or that Button2009 did not dispatch or returned.

The first prerequisite remains unproved. Compilation and opcode qualification
were deferred, followed by original-menu Enter/release and no-dispatch controls.
No claim is made that a compiler is unavailable. Static compilation alone would
not establish the missing native window/input facility.

[Diagnosis](diagnosis.json) reproduces the complete locked s286 diagnosis by
executing its pinned analyzer and comparing the full result. Its six candidate
patch hashes are regenerated in memory through the retained s276 analyzer.
The 9,774 historical events / 61 root samples, 594 unvisited blocks and 415
uninstrumented scripts remain historical s263 combat evidence, not new UI data.
All observation fields remain null; absence of observations is not non-dispatch.

## Source-first boundary

1. The locked [s276 case](../s276/ui-case.json) and [source audit](../s276/README.md)
   remain the source authority: Sprite2010 stops at frames1/10.
2. Root56 places the menu at depth157; menu10 newly places Button2009 at depth5.
   Source placement does not prove continuous native slot lifetime.
3. Both original handlers explicitly `gotoAndStop(1)`; no forced frame is used.
4. Tests preserve source patch reproduction and reject promotion of facility
   output to a native receipt, activation proof or execution evidence.
5. Same-input native menu execution is still absent. Listener order, observer
   perturbation, opcode preservation and entry/return behavior remain unproved.
   No runtime implementation or mechanism completion is authorized by this slice.

Next obtain actual native window state and input control through the installed
path. Then compile isolated candidate patches in a temporary directory, qualify
the complete original opcode/control-flow projection, observer perturbation and
live placement/timeline bracketing. Only then execute the original-menu
Enter/release case and observed no-input/frame1 controls with ordered input,
dispatch and entry evidence. No forced frames, AS calls as input, assumed listener
order, combat tape change or return/full-AS claim.

## Gates and verification

Archival diagnosis exits0. Each proof requirement exits1 with a distinct code:

- `--require-native-ui`: `S296_NATIVE_UI_UNPROVED`.
- `--require-opcode-qualification`: `S296_OPCODE_QUALIFICATION_UNPROVED`.
- `--require-thin-coverage`: `S296_BUTTON_ENTRY_UNPROVED`.
- `--require-full-as`: `S296_FULL_AS_UNPROVED`, retaining the historical strict error.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s296/diagnose.py --output /tmp/s296.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s296/diagnose.py --output /tmp/s296-ui.json --require-native-ui # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s296/diagnose.py --output /tmp/s296-opcode.json --require-opcode-qualification # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s296/diagnose.py --output /tmp/s296-entry.json --require-thin-coverage # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s296/diagnose.py --output /tmp/s296-as.json --require-full-as # exit1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s296 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s286 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_button_entry_preparation tools.tests.test_button_family_inventory tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) retain
results and measured costs. Initial reading/design and person-days are unknown.
No runtime or contract changes require Godot or contract tests.

Only s296 and proportionate tracking/manifest updates change. Ranks1–5 and7–9
are not executed. s254–s295, game/scripts, runtime, contracts, shared samplers,
thresholds and validators remain unchanged. No production admission, merge,
deployment or default rollout. The Draft PR delivers a blocked evidence slice,
not completed UI coverage.

Validation: **67 tests pass** (8 new, 5 retained s286, 54 retained tools).
`tools/verify.py` and `tools/check_handoff.py` pass; all four proof gates exit1.
