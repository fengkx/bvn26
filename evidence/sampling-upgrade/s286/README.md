# s286 — Button2009 native UI prerequisite (evidence-only, unproved)

Base: master `baf51547` / #163. Branch: `feat/s286-button2009-entry`.
Exclusive scope: [AFTER-s281 rank 5](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`;
`thin_coverage_cut_proved=false`; zero product obligations closed; M0-02 pending.

## Result and limits

Native application inventory succeeded, but did **not** establish window/input
control. Selecting the inventory's Flash bundle ID failed because the local
installation and mounted volume share that ID. Retrying the exact installed path
`/Users/fengkx/me/code/flash-player/Flash Player.app` returned
`Computer Use server error -10005: timeoutReached` without window state.
[All three operations and tool-reported costs](ui-control-attempts.json) are
retained: 3.8340 + 3.6477 + 9.5927 = 17.0744 seconds. These are current tool
measurements, not the historical s276 1433.1215-second timeout.

No keyboard/mouse input was sent, no instrumented movie was launched and no new
capture or native receipt exists. App selection may activate/launch an app;
that side effect remains unknown. Neither inventory success nor an empty
observation set establishes button dispatch, non-dispatch or handler return.

The first thin-cut prerequisite failed. Compilation, opcode qualification and
original-menu execution were not undertaken after that failure. This is an
honest blocked diagnosis, **not** completed UI coverage. The existing candidate
remains uncompiled; no unavailable-tool claim is made. A compiler could be used
independently, but would not resolve the missing native window/input facility.

[Diagnosis](diagnosis.json) re-executes the pinned s276/s271 analyzer and source
patch generation in memory. All six candidate patch hashes are reproduced;
original handler source inversion remains checked by the retained tests.
Historical s263 replay still has 9,774 events / 61 root samples, 594 unvisited
blocks and 415 uninstrumented scripts. These are historical combat records,
not new UI observations. No tape, receipt or coverage inventory is changed.

## Source-first boundary and next discriminator

The [locked s276 case](../s276/ui-case.json) and its
[source-first audit](../s276/README.md) remain applicable: Sprite2010 has stops
at frames1/10; root56 places the menu at depth157 and menu10 places Button2009
at depth5 as new placements. Both handlers explicitly `gotoAndStop(1)`.
Source retention does not prove compiled opcode equivalence, listener order,
continuous slot lifetime or native behavior preservation. The fifth source-first
question (same-input native execution) remains unanswered; no runtime changes
or mechanism-completion claim are permitted.

Next, obtain actual native window state/input control using the exact installed
path. Then compile the isolated patches into a temporary work directory, verify
the complete original opcode/control-flow projection and qualify observer
perturbation and live slot/timeline bracketing. Execute only the existing
original-menu Enter/release case and observed no-input/frame1 controls, retaining
full input/dispatch/entry order, hashes and costs. No forced frames, AS calls as
native input, assumed listener order, combat tape changes or return/full-AS claim.
Ranks 1–4 and 6–9 are not executed.

## Verification

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s286/diagnose.py --output /tmp/s286.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s286/diagnose.py --output /tmp/s286-ui.json --require-native-ui # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s286/diagnose.py --output /tmp/s286-entry.json --require-thin-coverage # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s286/diagnose.py --output /tmp/s286-as.json --require-full-as # exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s286 -p 'test_*.py'
python3 -m unittest tools.tests.test_button_entry_preparation tools.tests.test_button_family_inventory tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

Five new boundary tests and 54 retained focused tests pass. Diagnosis exits0;
all three proof requirements retain exit1, including the unchanged strict AS
validator invoked through the historical analyzer. [Gates](gates.json) and
[project checks](project-checks.json) retain measured command costs. Tests reject
new execution evidence without independent analysis and prevent facility output
from becoming a native receipt. No schema/runtime/generated content changed;
Godot and contract checks are not applicable. [Scope audit](scope-audit.json)
and [manifest audit](manifest-audit.json) record the bounded diff.

Only s286 and the four requested tracking files change. Original game/scripts,
s254–s285, runtime contracts, samplers, thresholds and validators are untouched.
No merge, deployment or production-ready claim. The Draft PR delivers this
diagnosis, leaving the native UI experiment unproved.
