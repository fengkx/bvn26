# s292 — Independent ones entry-clock qualification

Base: origin/master `3c6fc07e70dda6878e594c0f388f6e7066cc1f43` (#169).
Branch: `feat/s292-ones-entry-clock`. Exclusive authority:
[AFTER-s290 rank #2](../next-fix-priority-after-s290.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

**Evidence-only, honest-unproved.** The archived observer cannot qualify an
all-ten-frame entry clock. Both proof gates exit 1 with
`S292_ENTRY_OBSERVER_UNPROVED`. No fresh capture is made before qualification.
Ranks 1 and 3–9 are not executed, and no product obligation is closed.

## New bounded audit

[diagnose.py](diagnose.py) replays the locked [s282 diagnosis](../s282/README.md)
and requires exact equality. Its unchanged historical validator rechecks the
26,828-event s274 stream, receipt and build provenance. The denominator remains
63 selections: four observed frame1 joins, 45 selections of empty frames2–10,
and 14 pre-fight frame1 windows whose independent entry remains **null**.
These are historical observations, not a new clock or new capture.

The new SWF reader enumerates **every tag** in original and archived Sprite1810,
retaining uncompressed offsets, full payload bytes and hashes in
[diagnosis.json](diagnosis.json). It checks ten ShowFrames and terminal End,
compares every non-DoAction tag in order, and decodes frame1 action record
boundaries. All non-action payloads are byte-identical. The original action
payload is `07 00` (Stop, End); the archived frame1 observer retains that terminal
pair. Frames2–10 contain no DoAction in either SWF. File offsets are not live
AVM dispatch addresses. This parser does not interpret AVM instructions or prove
helper side effects, timing, or action-execution equivalence.

The new control audit binds exact archived source ranges to the historical
control boundaries, two retained-entry events and six load/unload events:

| Existing control | What it actually establishes | Missing qualification |
| --- | --- | --- |
| ticks1/5 retained control | `gotoAndStop(2)` then `gotoAndStop(1)` in one callback; later frame1 entry | Isolated repeated target and isolated changed target; frame2 entry |
| ticks2–3/6–7 replacement | Remove/duplicate at depth100001 with encoded generations | All-ten-frame entry across replacement; native allocation identity |
| Historical sampled actor equality | Same retained actor samples as s265 | Independent observer-off/on entry-order and perturbation control |

The s265 comparison is only the retained validator's historical regression;
no tape or entry observation from another run is inserted into s274. Existing
s274 helpers write serial/generation/calibration fields and emit events; retaining
Stop bytes does not erase those effects. No independently qualified all-ten-frame
observer or independent control set is present in this locked evidence.

## Qualification decision and source-first boundary

The thin cut stops at the missing observer facility. Adding DoAction to nine
originally empty frames would itself introduce new action dispatch. A future
candidate must preserve original actions and evaluation order, audit complete
opcode/timeline deltas and helper effects, and independently observe entry for
all ten frames. Separate repeated-target, changed-target and same-depth
replacement controls must distinguish selection, entry and next root/callback
order; observer-off/on controls must use an independent observation channel.
An off trace missing the observer's own events is not a non-perturbation proof.
Keep control gotos on isolated controls, never the natural ones clip. Only after
these prerequisites pass should one fresh, independently identified ones-only
capture be attempted with complete logs, receipts and unchanged input actions.
This is a concrete missing facility, not a claim that observing empty frames is
impossible or that a repeated goto necessarily dispatches a script.

1. `scripts/main.json#DefineSprite_1810/frame_1/DoAction.as` is `stop();`;
   frames2–10 have no script. s282 source inventory and the new byte audit agree.
2. Sprite1813 places outer ones1810 new at depth3, removes it at frame10.
   Inner glyphs1800–1809 at depth1 use a new placement then MOVE/replacement.
   These source facts are locked in s282; encoded generations are not allocation IDs.
3. Timer callback uses gotoAndStop; no synthesized stop/advance/entry is added
   to empty frames and label ends do not imply resets.
4. Mutation tests protect source bytes, placement, action boundaries, control
   provenance and null observations; none asserts a guessed schedule.
5. Only historical original-player evidence is available. There is no new
   original/Godot comparison, all-frame clock proof or runtime authorization.

Scope: only s292 plus docs/STATUS.md, docs/SAMPLING_UPGRADE.md, plan/tasks.json
and reviewed manifest hashes. s254–s291, game/scripts, runtime, contracts,
shared sampler/threshold/validator remain unchanged. No synthetic clock,
scene/intro repair, HUD reset, images, cross-run tape or renderer change.
Zero builds, player launches and captures; no merge or deployment.

## Reproduction

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s292/diagnose.py --output /tmp/s292.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s292/diagnose.py --output /tmp/s292-observer.json --require-observer # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s292/diagnose.py --output /tmp/s292-clock.json --require-child-clock # exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s292 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s282 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) record actual commands, expected/actual exits and measured
costs. [Project checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) retain
validation evidence. Initial reading/design, future qualification/capture costs
and person-days are unmeasured. No runtime or contract checks are applicable.

Validation result: **67 tests pass** (12 new, 9 retained s282, 46 retained
tools). Diagnosis, integrity, handoff and diff checks exit0. Both proof gates
exit1 with `S292_ENTRY_OBSERVER_UNPROVED` as expected.
