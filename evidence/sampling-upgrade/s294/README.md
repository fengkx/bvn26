# s294 — AFTER-s290 rank #4: Yulong nested observer qualification

Base: origin/master `928c8821` (s293 #171). Branch: `feat/s294-yulong-nested`.
Exclusive authority: [AFTER-s290 rank #4](../next-fix-priority-after-s290.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; zero product obligations closed; M0-02 pending.

Only Sprite345 frame188 depth28 k1atm (Sprite104) → depth2 mian (Sprite2),
ticks15–22 of the unchanged s239 tape retained in s275. No new build, player
launch or capture. Ranks 1–3 and 5–9 are not executed.

## New qualification evidence

[diagnose.py](diagnose.py) reproduces the locked [s285 diagnosis](../s285/README.md)
exactly, including all 5,214 retained events, then independently decodes the
original and archived s275 Sprite2/frame1 DoAction bytes. The new inventory
retains every function header, parameter register, preload/suppress flag value,
constant pool, complete body and instruction boundary. Branch targets must land
on instruction boundaries or the body's end. This is a bounded binary audit,
not an AVM interpreter or a native dispatch resolver.

| Function | Original registers / flags | s275 registers / flags | Body bytes original → s275 |
| --- | --- | --- | --- |
| gameRunning | 3 / 234 | 3 / 234 | 61 → 73 |
| beida | 3 / 170 | 3 / 170 | 246 → 319 |
| fangyu | 3 / 170 | 3 / 170 | 267 → 349 |
| checkHit | 4 / 234 | 4 / 234 | 213 → 242 |
| getHitObj | 15 / 41 | 9 / 41 | 229 → 316 |
| getStgHitObj | 6 / 233 | 6 / 233 | 147 → 168 |

For `getHitObj(array, player, afterFix, ppw)`, parameter registers change from
`9,13,12,3` to `2,3,4,5`. All six complete headers and bodies differ, as do their
inherited constant pools. Header byte differences include body lengths; five
activation-header field sets remain equal, but getHitObj's does not. Full bytes,
absolute uncompressed offsets and hashes are in [diagnosis.json](diagnosis.json).
These are **file offsets, not loaded AVM cursors or native PCs**.

This narrows s285's source-text preservation result: unchanged AS bodies do not
establish unchanged compiled activation layout. Different bytes alone also do
not establish semantic inequivalence. No register mapping, observer erasure,
complete operand projection or native activation equivalence is proved here.
The source suffix remains initialization-only, with no direct nested entry hooks.

## Gates and blocker

The available observer fails qualification before paired controls:

- `S294_REMOVAL_DISPATCH_UNPROVED`: source frame194/depth28 removal bytes and
  body193/194 slot brackets do not identify an executed RemoveObject2 dispatch.
- `S294_NESTED_ENTRY_UNPROVED`: no naturally executed nested entry with its actual
  receiver, arguments and defining activation is observed. Missing hooks mean
  unknown execution, never zero invocations or ineligibility.
- `S294_ACTIVATION_OPERAND_PRESERVATION_UNPROVED`: compiled register changes are
  now explicit; the complete activation, scope chain, registers and operand stack
  have no proved preservation mapping.
- `S294_OBSERVER_UNQUALIFIED`: aggregate gate remains exit1. The same-placement
  observer-off/on controls and perturbation bound cannot proceed on this evidence.

Next work remains within rank #4: bind the loaded removal tag and current/next
cursor convention to a direct pre/post dispatch witness; bind natural Sprite2
entry to its defining activation; qualify all compiled header/register/branch and
operand changes before independently retained paired controls. Preserve direct
`_parent.pn`, `_parent.pw`, `_parent.fzpw`, existing hitTest receiver/target order,
returns and invalidated continuation. Direct `_parent` is Sprite104, not Sprite345.
No speculative native address, forced call or new candidate is introduced here.

## Source-first and scope

1. Complete source/timeline remains locked in s270/s285. This audit additionally
   bounds all six compiled Sprite2 functions in original and archived binaries.
2. Frame188 and the nested depth2 placement are new PlaceObject instances, not
   MOVE. Static offsets and historical stamps do not prove allocation identity.
3. Sprite104 stops at1, conditionally goes to5, renames at5 and stops at10;
   Sprite345 removes depth28 at194. No label-end exit is synthesized.
4. Tests protect source-bound byte inventories, parameter/register differences,
   branch boundaries, truncation rejection and unknown observations. No guessed
   gameplay outcome is frozen as an invariant.
5. The retained native s275 tape is revalidated through locked s285; no new native
   or Godot run, exact dispatch, nested invocation or parity is claimed.

No ancestor pn, aliases, artificial hitTest/call, enlarged boxes, other chains or
eligibility rule. Only s294 and proportionate tracking/manifest updates change.
s254–s293, game/scripts, runtime, contracts and shared sampler/threshold/validator
remain unchanged. No production admission, merge, deployment or default rollout.

## Reproduction

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s294/diagnose.py --output /tmp/s294.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s294/diagnose.py --output /tmp/s294-q.json --require-observer-qualification # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s294/diagnose.py --output /tmp/s294-r.json --require-parent-removal # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s294/diagnose.py --output /tmp/s294-e.json --require-nested-entry # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s294/diagnose.py --output /tmp/s294-a.json --require-activation-preservation # exit1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s294 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s285 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_yulong_operand_boundary tools.tests.test_nested_owner_diagnosis tools.tests.test_yulong_k1atm_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) and [project checks](project-checks.json) record exact commands,
exit codes and measured subprocess costs. [Scope](scope-audit.json),
[manifest audit](manifest-audit.json) and [session timing](session-timing.json)
record custody and measured effort. Initial reading/design and person-days are
unmeasured. No runtime or contract change requires Godot or contract validation.

Validation: **79 tests pass** (10 new, 8 retained s285, 61 retained tools).
Diagnosis, integrity and handoff exit0; all four qualification requirements exit1.
