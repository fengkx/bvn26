# s324 — AFTER-s317 rank #7: Button2009 native UI

Base: current origin/master `32dec0541e1586c5ae9790f06ca5613956dc9ed8`
(post-s323 squash #201). Branch: `feat/s324-button2009-entry`.
Authority: [AFTER-s317 rank 7](../next-fix-priority-after-s317.md);
[s315 README](../s315/README.md) and [diagnosis](../s315/diagnosis.json) are locked prior.
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; `thin_coverage_cut_proved=false`;
zero product obligations closed; M0-02 stays pending.

## Actual result and boundary

The exact installed-path operation
`let app = await cua.getApp("/Users/fengkx/me/code/flash-player/Flash Player.app");`
returned `Computer Use server error -10005: timeoutReached` after **16.9532 seconds**
(tool-reported wall time). It returned API documentation but no native window state.
[ui-control-attempts.json](ui-control-attempts.json) records this fresh attempt,
separately from s315's 22.3855-second historical attempt and s296's 16.1641 seconds.
No keyboard or mouse input was sent. No instrumented movie was launched, no build
was made, and no capture or native receipt was produced. App selection may activate
or launch the installed app; that side effect remains unknown.

Proved: this operation failed to provide window state in this session; the locked
s315 diagnosis reproduces in full, recursively including its prior evidence and
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
fresh facility record, and runs the pinned s315 analyzer against its complete
retained diagnosis. It does not rerun a UI attempt or manufacture a receipt.

| Mode | Exit | Meaning |
| --- | --- | --- |
| Base diagnosis | 0 | Reproducible audit, both admission flags false |
| `--require-native-ui` | 1 | `S324_NATIVE_UI_UNPROVED` |
| `--require-opcode-qualification` | 1 | `S324_OPCODE_QUALIFICATION_UNPROVED` |
| `--require-thin-coverage` | 1 | `S324_BUTTON_ENTRY_UNPROVED` |
| `--require-full-as` | 1 | `S324_FULL_AS_UNPROVED`; historical strict failure retained |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s324/diagnose.py --output /tmp/s324.json
# Add each --require-* flag from the table separately; each must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s324 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) and [project checks](project-checks.json) retain exact commands,
exit codes and subprocess durations. Negative tests reject invented window/input,
receipt or activation claims, wrong app paths and invalid timing. Retained s315, s305,
s296, s286 and existing Button/sampling/import tests are also run.
[Artifact hashes](artifact-sha256.json) cover every s324 top-level file except the
hash index itself. [Scope audit](scope-audit.json) and [manifest audit](manifest-audit.json)
record allowed paths and reviewed tracking hash updates. [Timing](session-timing.json)
separates implementation/check time from UI tool time; initial reading/design and
person-days are unknown. The UI attempt precedes the implementation timer.

## Source-first boundary and next discriminator

1. Locked s276 source preparation, preserved by s315, identifies Sprite2010
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

Only s324 plus proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest changes.
Empty diff on s254–s323 and all other evidence directories. Ranks 1–6 and 8–9
are not executed. No game/, scripts/, runtime, contracts, shared sampler,
threshold or validator changes; no forced frames, AS calls as input, combat tape
changes, assumed listener order, timeout-as-non-dispatch proof or full-AS claim.
No merge, deployment or product admission. Delivery of this blocked evidence
slice does not complete the native UI thin cut.

Validation results are recorded in gates.json and project-checks.json. Retained
source preparation is revalidated, not counted as new progress. Ranks 1–6 remain
delivered by s318–s323; ranks 8+ stay planning. The authority table is unchanged.

Validation: **94 tests pass**; base diagnosis exits 0, all four proof gates
exit 1; verify.py, check_handoff.py and diff whitespace checks pass.
