# s315 — AFTER-s308 rank #7: Button2009 native UI

Base: current origin/master `693eb1fb1b6e2059143b87d51cfb69cac8ed0e50`
(post-s314 squash). Branch: `feat/s315-button2009-entry`.
Authority: [AFTER-s308 rank 7](../next-fix-priority-after-s308.md);
[s305 README](../s305/README.md) and [diagnosis](../s305/diagnosis.json) are locked prior.
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; `thin_coverage_cut_proved=false`;
zero product obligations closed; M0-02 stays pending.

## Actual result and boundary

The exact installed-path operation
`let app = await cua.getApp("/Users/fengkx/me/code/flash-player/Flash Player.app");`
returned `Computer Use server error -10005: timeoutReached` after **22.3855 seconds**
(tool-reported wall time). It returned API documentation but no native window state.
[ui-control-attempts.json](ui-control-attempts.json) records this fresh attempt,
separately from s305's 18.3654-second historical attempt and s296's 16.1641 seconds.
No keyboard or mouse input was sent. No instrumented movie was launched, no build
was made, and no capture or native receipt was produced. App selection may activate
or launch the installed app; that side effect remains unknown.

Proved: this operation failed to provide window state in this session; the locked
s305 diagnosis reproduces in full, recursively including its prior evidence and
six regenerated candidate patch hashes. The historical 9,774 events / 61 root
samples, 594 unvisited blocks and 415 uninstrumented scripts are unchanged s263
combat data, not fresh menu evidence.

Unproved: native window/input control, compilation/opcode preservation, observer
perturbation, live placement lifetime, Enter/release dispatch, handler entry/return,
listener order and no-dispatch controls. All behavior observations remain null.
**A UI timeout is not a no-dispatch observation.** It does not prove native control
is impossible, the app did not activate, or the button did not run or returned.

The first prerequisite was attempted and remains unmet. Compilation/opcode
qualification and original-menu Enter/release plus no-dispatch controls were
therefore deferred. No compiler-unavailability claim is made. There is no qualified
control facility in the retained evidence; static compilation would not close that
gap. No alternative control technology or repeated product build is introduced.

## Gates and reproduction

[diagnose.py](diagnose.py) verifies [input hashes](input-sha256.json), validates the
fresh facility record, and runs the pinned s305 analyzer against its complete
retained diagnosis. It does not rerun a UI attempt or manufacture a receipt.

| Mode | Exit | Meaning |
| --- | --- | --- |
| Base diagnosis | 0 | Reproducible audit, both admission flags false |
| `--require-native-ui` | 1 | `S315_NATIVE_UI_UNPROVED` |
| `--require-opcode-qualification` | 1 | `S315_OPCODE_QUALIFICATION_UNPROVED` |
| `--require-thin-coverage` | 1 | `S315_BUTTON_ENTRY_UNPROVED` |
| `--require-full-as` | 1 | `S315_FULL_AS_UNPROVED`; historical strict failure retained |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s315/diagnose.py --output /tmp/s315.json
# Add each --require-* flag from the table separately; each must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s315 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) and [project checks](project-checks.json) retain exact commands,
exit codes and subprocess durations. Negative tests reject invented window/input,
receipt or activation claims, wrong app paths and invalid timing. Retained s305,
s296, s286 and existing Button/sampling/import tests are also run.
[Artifact hashes](artifact-sha256.json) cover every s315 top-level file except the
hash index itself. [Scope audit](scope-audit.json) and [manifest audit](manifest-audit.json)
record allowed paths and reviewed tracking hash updates. [Timing](session-timing.json)
separates implementation/check time from UI tool time; initial reading/design and
person-days are unknown.

## Source-first boundary and next discriminator

1. Locked s276 source preparation, preserved by s305, identifies Sprite2010
   stops at frames 1/10; no new per-frame behavior is inferred.
2. Root56 places the menu at depth157; menu10 newly places Button2009 at depth5.
   Source placement does not prove continuous native slot lifetime.
3. Both original handlers explicitly `gotoAndStop(1)`; no forced frame is used.
4. Assertions protect source patch reproduction and distinguish missing evidence
   from native behavior; they do not assume listener order or observer neutrality.
5. Same-input native menu execution remains absent. No runtime change or mechanism
   completion follows from this slice.

Next establish actual native Flash window state and input control at the installed
path. Then compile isolated candidates outside the source tree, qualify complete
original opcode/control-flow preservation, observer-off/on behavior and live
placement/timeline bracketing, before original-menu Enter/release and observed
no-input/frame1 controls with ordered input, dispatch and entry evidence.

Only s315 plus proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest changes.
Empty diff on s254–s314 and all other evidence directories. Ranks 1–6 and 8–9
are not executed. No game/, scripts/, runtime, contracts, shared sampler,
threshold or validator changes; no forced frames, AS calls as input, combat tape
changes, assumed listener order, timeout-as-non-dispatch proof or full-AS claim.
No merge, deployment or product admission. Delivery of this blocked evidence
slice does not complete the native UI thin cut.

Validation result: **85 tests pass** (9 s315, 9 s305, 8 s296, 5 s286,
54 retained tools). Base diagnosis exits 0; all four proof gates exit 1.
`tools/verify.py`, `tools/check_handoff.py` and diff whitespace checks pass.
