# s271 — Full AS coverage: game-menu Button2009 family (unproved)

Base: master `8cf880db` / #148. Branch: `feat/s271-full-as-coverage`.
Exclusive authority: [AFTER-s263 rank 8](../next-fix-priority-after-s263.md).
`production_admitted=false`; `native_parity_proven=false`;
`thin_coverage_cut_proved=false`; zero product obligations closed. M0-02 pending.

This evidence-only slice inventories **one family, two source obligations**:
`game/main.swf` Button2009 `BUTTONCONDACTION on(keyPress Enter)` and `on(release)`.
Both remain `other_action`, `instrumented=false`. No probe or runtime fix is
proved. Existing block-entry instrumentation supports selected fighter DoAction
and load/enterFrame paths, not these button dispatch records; main SWF actions
are deliberately uninstrumented. Changing their classification would not prove
that a native event ran or that a handler returned.

## Source-bound execution prerequisites

[Diagnosis](diagnosis.json) contains both complete handlers, all ten menu frames
(including frames without scripts), button condition bytes, placement attributes,
the load handler and the exact menu-key-listener source suffix. [Input pins](input-sha256.json)
bind original SWF/scripts, the existing s30 XML archive/export provenance, s263
raw capture/metadata/receipt/report, s266 continuation result and unchanged tools.
The analyzer checks XML member and original SWF hashes against s30 provenance,
checks s263 source/raw receipt hashes, rebuilds the full inventory, runs the raw
sequence validator and compares every recomputed coverage field to s263.
This is portable evidence replay, not a new receipt admission or native capture.

| Boundary | Authored fact | Execution prerequisite / limit |
| --- | --- | --- |
| Root frame56 | New Sprite2010 `game_menu`, depth157; load sets `_visible=false` | Placement source does not witness live visibility or event dispatch |
| Menu frame1 | `stop()`; depth5 contains character1998 | Button2009 is not this frame's depth5 occupant |
| Menu frame2 | Removes depths3–7, retains/transforms depth1 | Linear timeline changes do not prove which intermediate frames a goto executes |
| Menu frames3–9 | Only depth1 MOVE changes; no DoAction | Frame1 stop prevents automatic progression without an authored play/goto |
| Menu frame10 | New Button2009 at depth5; `stop()` | Actual menu arrival and button lifetime must be observed |
| Button release | `condOverDownToOverUp=true`; `gotoAndStop(1)` | Requires real mouse button transition on this live button |
| Button Enter | `condKeyPress=13`; `gotoAndStop(1)` | Requires native key dispatch to this button, not a combat key-read alias |

Sprite1991 frame1 installs `onKeyUp` through `Key.addListener(this)`. It first
rejects `_menuEnabled === false`. When the menu is hidden, Enter pauses, sets
selection `_kn=2`, shows the menu and goes to frame1. When visible, selection1
plus Enter invokes `play()`; up/down change the selection. This is a **source
route**, not a captured UI sequence. The same Enter also has a button handler at
frame10; their dispatch order and interaction must be measured, never assumed.

The s263 case injects only P1 attack at ticks10–13 through
`body_kis_alias_with_per_read_trace`. It does not establish real menu Enter or
mouse release dispatch. The family is uninstrumented, so missing entry records
prove neither execution nor nonexecution. No coverage denominator is reduced.

## Continuation boundary and next discriminator

The scoped s266 result is consumed read-only: authored retained control writes
post=1; removed control writes post=0; exact executed PC and exit model remain
unproved. It cannot authorize removal-as-return for Chad or these buttons.
Both button handlers go to menu frame1, whose authored depth5 occupant differs
from frame10. A target-frame observation or disappearance of the button is not
a handler-return observation; no synthetic after-event is added.

The next experiment is bounded to **Button2009 only** in a separate native UI
case, preserving the s76 combat tape and historical outputs:

1. Observe the existing menu-enabled guard, visibility, selection and play branch;
   reach frame10 through the original menu route, without forced frame changes.
2. Correlate actual Enter and, separately, mouse press/release dispatch with the
   live button placement and exact handler entry. Keep frame1/no-button and
   no-dispatch controls. Record Key-listener/button ordering rather than assuming it.
3. Observe owner frame1 and slot replacement independently of handler continuation.
   Establish a source-preserving entry probe before claiming an entry coverage cut.
   Return coverage still requires executed-PC/activation evidence or a separately
   proved equivalent facility; another absent marker cannot resolve it.

Source-first answers: complete selected menu frame scripts and placement/MOVE
inventory are retained; both handlers explicitly goto frame1, never implicitly
return to standing; tests lock source and missing-evidence distinctions. The
same-input original button execution is **missing**. Thus no runtime mechanism
changes and no completed behavior claim are permitted.

## Gates, costs and reproduction

[Gate results](gates.json) retain exact commands, exits and subprocess durations.
Portable diagnosis/raw sequence replay passes. The unchanged full-AS requirement
still rejects **594 unvisited / 415 uninstrumented** obligations (exit1).
The thin-coverage requirement also exits1. **48 focused tests pass**.
[Project checks](project-checks.json) record integrity and handoff results.
No schema or runtime changes require a new Godot run; contracts are checked as
an additional project consistency check, never a substitute for execution.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s271/diagnose.py --output /tmp/s271.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s271/diagnose.py --output /tmp/s271-required.json --require-thin-coverage # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s271/diagnose.py --output /tmp/s271-full-as.json --require-full-as # exit 1
python3 -m unittest tools.tests.test_button_family_inventory tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Zero builds, exports or native player launches; new capture cost is zero.
Locked artifacts suffice to inventory the family and expose the missing native
UI-dispatch prerequisite. A fresh capture is needed to resolve it, but a safe
entry/continuation observation design is not established here. Future capture
cost and person-days remain unknown. [Session timing](session-timing.json)
records actual elapsed work through packaging, without inferred person-days.

Only s271 evidence, its focused test and requested tracking files change.
Other ranks and s254–s270 remain untouched. No broad interpreter, fabricated
returns/after-events, validator whitening, thresholds, gameplay, production
runtime, historical receipts/baselines, merge or deployment changes.
