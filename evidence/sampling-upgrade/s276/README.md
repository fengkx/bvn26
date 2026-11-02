# s276 — Native Button2009 entry experiment (blocked, unproved)

Base: master `6179ca1e` / #153. Branch: `feat/s276-button2009-entry`.
Exclusive authority: [AFTER-s272 rank 4](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`;
`thin_coverage_cut_proved=false`; zero product obligations closed; M0-02 pending.

**The requested native UI execution is not completed.** One separate
[UI case](ui-case.json) and an isolated candidate observation patch are prepared,
but frame10 arrival, Enter/release dispatch, handler entry and no-dispatch
controls are all **unobserved**, not negative observations. This is an
evidence-only blocked diagnosis, not an implemented or proved coverage cut.

## Experiment and blocker

The sole native UI-control attempt, selecting the installed Flash Player through
`cua.getApp`, failed with `Computer Use server error -10005: timeoutReached`.
The tool reported **1433.1215 seconds**. No window state was returned, no key or
mouse action was sent, and no movie launch or capture was confirmed.
[Attempt record](capture-attempt.json) preserves the exact operation and result.
App selection can itself activate/launch an app; that side effect is unknown.
There were zero instrumented movie launches, SWF builds or captured UI traces.
There is no new native receipt. No failure stream is trimmed or resealed.

The existing s271 artifacts cannot answer this question: their s263 combat case
uses key-read injection, and the two Button2009 source actions are uninstrumented.
[Diagnosis](diagnosis.json) reruns s271's pinned XML/source/full-stream checks:
9,774 events, 61 root samples, 594 unvisited and 415 uninstrumented obligations.
Those are **historical s263 counts**, not s276 UI samples. The strict full-AS gate
still rejects. Missing markers do not prove that the buttons never executed.

A fresh capture is therefore required. Replacing unavailable native input with
an AS call, forced frame or synthetic return would not resolve this blocker.
FFDec was not found at the prior documented temporary location; no build or
opcode-preservation claim is made. Download/build work was not undertaken after
the independent native UI-control prerequisite failed.

## Bounded preparation, not admission

[prepare_probe.py](prepare_probe.py) verifies locked input hashes and generates
six source patches into a separate directory. It retains both original handlers
byte-for-byte after removing only their entry marker, and retains the existing
menu listener, play branch and frame1/frame10 stops. [observer.as](observer.as)
adds separate Key/Mouse callbacks and sequence-numbered observations. It does
not call either button handler, change a source goto, write the menu selection,
inject combat inputs or synthesize a return/after-event.

These are **uncompiled candidate instrumentation**, never production code.
Source inversion is not opcode equivalence or native timing preservation.
Adding a listener can affect ordering/timing; the experiment must record actual
ordering and qualify that perturbation. Independent native input callbacks
prove only callback delivery, not Button2009 dispatch: the exact entry marker
and live placement must also be correlated. Slot strings are not allocation
identity. The candidate alone does not provide continuous slot/lifetime evidence;
that must be added/qualified before admitting a future run. No coverage inventory
is reclassified and no strict validator is modified.

The case separates frame1/no-button, frame10/no-input, Enter, a second natural
menu route, mouse no-input, release and target-frame observation. It requires
fresh UI screenshots for click placement rather than guessed coordinates. The
setup uses the original title/mode/character/stage flow. Its configuration and
actual input timings remain uncaptured, explicitly pending.

## Source-first boundary and next discriminator

1. s271 retains all ten Sprite2010 frames; only frames1/10 have `stop()` actions.
   The complete handlers and Sprite1991 listener remain pinned by source hashes.
2. Root56 places Sprite2010 at depth157; menu10 places Button2009 at depth5,
   both new placements, not MOVE. Menu1 has a different depth5 occupant.
3. Both button actions explicitly `gotoAndStop(1)`. A changed owner frame does
   not establish handler return or a native continuation/exit model.
4. Tests enforce exact original handler retention, changed-source rejection and
   the unknown-versus-false boundary; they do not assert an invented listener order.
5. Same-input native execution is missing. No runtime mechanism is changed.

**Next discriminator:** restore native UI control; compile the isolated patches
against locked original main and verify the complete original opcode/control-flow
projection. Execute this one UI case through original menus. Independently
record native Enter and mouse down/up callbacks, exact source handler entries,
actual menu listener order, and live frame10/depth5 placement before dispatch.
Include observed no-input intervals and frame1/no-button controls; preserve full
ordered logs, inputs, source/build/player hashes and capture costs. Establish
independent slot/timeline bracketing before any entry-coverage admission. Return
coverage remains a separate unresolved obligation. Do not change combat tapes,
force frames, assume listener order or claim full AS coverage.

## Reproduce and gates

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s276/prepare_probe.py --output /tmp/s276-new-patches
PYTHONPATH=. python3 evidence/sampling-upgrade/s276/diagnose.py --output /tmp/s276.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s276/diagnose.py --output /tmp/s276-required.json --require-thin-coverage # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s276/diagnose.py --output /tmp/s276-full-as.json --require-full-as # exit 1
python3 -m unittest tools.tests.test_button_entry_preparation tools.tests.test_button_family_inventory tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s276-venv/bin/python tools/validate_contracts.py
```

Use a new output directory for preparation. It writes AS files only; it cannot
produce an executable SWF or native evidence. [Gates](gates.json) and
[project checks](project-checks.json) record commands, actual exits and measured
subprocess costs. [Session timing](session-timing.json) includes the failed UI
facility wait; future capture cost and person-days remain unknown. No Godot run
is applicable because no runtime/generated data/schema changes are made.

Only s276 evidence, its focused test and the requested tracking files change.
Other ranks, s254–s275, locked game/scripts, all combat tapes, historical
receipts, validators, thresholds and gameplay remain untouched. No merge or
deployment. The Draft PR delivers the diagnosis; it does not claim the requested
native UI coverage has been obtained.

54 focused tests pass; integrity and handoff pass. The first contract check
failed because the historical venv lacked jsonschema. A new temporary venv
installed requirements-dev.txt and the repeated contract check passes. The
default uv cache was sandbox-inaccessible; using an isolated /tmp cache resolved
it without changing permissions. Both attempts are retained in project checks.
