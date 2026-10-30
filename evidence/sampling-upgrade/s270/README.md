# s270 — Yulong nested geometry owner binding (unproved)

Base: master `53dd5222b41ea69e59a44381e0d0d4f7fbd9e663` / #147.
Branch: `feat/s270-display-source-ownership`.
Exclusive authority: [AFTER-s263 rank 7](../next-fix-priority-after-s263.md).
`production_admitted=false`; `native_parity_proven=false`;
`runtime_binding_proved=false`; zero product obligations closed; M0-02 pending.

**Evidence-only diagnosis of one chain:** Yulong body Sprite345 frame188
→ depth28 `k1atm` Sprite104 → depth2 `mian` Sprite2.
No safe runtime receiver-ownership/eligibility rule is proved or implemented.
The authored placement and sampled stamp relation are narrower facts than an
executed call's receiver/target binding or continuous allocation identity.

## What this slice adds

[diagnose.py](diagnose.py) independently inventories the complete ten-frame
Sprite104 timeline and the body depth28 interval from the locked XML already
used by s247. It joins the full s247 raw stream's outer/inner geometry boxes,
body frames and nine provenance observations, rather than treating the selected
nested path's absence as the end of both instances. It also enumerates all five
ordered hitTest expressions in the exact outer enterFrame source.

[Input hashes](input-sha256.json) pin the original source, archive, raw capture,
metadata, receipt and unchanged validators. The tool verifies archived outputs
against both build and receipt hashes, verifies source hashes and the XML member
hash, and runs the unchanged full raw sequence validator. It does not rewrite
or trim any historical file. [Diagnosis](diagnosis.json) retains all selected
source scripts, frame tags, ordered operands and observed chain boxes.

| Boundary | Authored / observed fact | Limit |
| --- | --- | --- |
| Body frame188 | New Sprite104 at depth28; load sets `played=0`, `movspeed=20` | Load source is not an executed load observation |
| Sprite104 frame1 | `stop()`; new Sprite2 `mian` at depth2 without clip actions | Function definitions do not establish gameplay receiver eligibility |
| Tick15 | Selected child absent at root seq3509, initialized/stamped at seq3534, display448 | Root sampling precedes this initializer; no intra-frame callback trace |
| Ticks16–18 | Outer stamp70 / frame1 and inner stamp71 / frame1; both birth448; direct child parent pn undefined | Stamps are analysis properties, not engine allocation IDs |
| Tick19 | Child absent at seq3607; outer still recorded at seq3612 as `k1atm`, stamp70, **frame5** | Child absence is not parent death, nor proof that the rename statement already ran |
| Sprite104 frame5 | Removes depth2, assigns `this._name="abcd"`, changes depth1 art | Exact runtime removal/rename ordering is unobserved |
| Body frame194 | Removes depth28 | Different source boundary from child frame5 removal |

Sprite104 frames2–4 have no frame actions or display changes. Frames6–8 change
only depth1 art, frame9 removes depth1, frame10 stops. Frames without DoAction
are explicit in the report. The frame1 stop means frame5 cannot be inferred
from elapsed root ticks alone. The outer handler conditionally goes to frame5;
its actual branch and operands were not instrumented in s247.

## Two distinct contexts, and an extra receiver hop

The outer source is
`scripts/fighter/yulong.json#DefineSprite_345/frame_188/PlaceObject2_104_28/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
Here `_parent` is the body Sprite345. It tests, in authored order:

1. `mian` against `_root.game["p" + _parent.pn].mc.bdmn`.
2. `mian` against the same expression ending in `zh1atm`.
3. `mian` against the same expression ending in `zh2atm`.
4. **`hitmc.mian`** against the same expression ending in `zh3atm`.
5. `mian` against the same expression ending in `abcd`.

The fourth receiver is retained literally; neither its live existence nor its
execution is proved here. No spelling correction or receiver alias is justified.
The authored boolean expression and evaluation order must survive future probes.

The structural walker instead visits Sprite2 because it defines `getHitObj`
and `getStgHitObj`, classifies its name `mian` as hurt, then uses
`mc._parent.pn`. In that context the parent is Sprite104, whose sampled pn is
undefined. All three lists exist; the target alone is undefined at ticks16–18.
The body pn=2 is a separate observation, **not permission to substitute an
ancestor**. The outer `mian.hitTest(...)` source use does not by itself prove
that no other path invokes the nested functions. No receiver exemption follows.

## Source-first answers and next discriminator

1. The complete Sprite104 frame inventory, Sprite2 initializer and both exact
   outer clip actions are source-bound (the initializer remains in the pinned
   [s247 binding](../s247/source-binding.json)). No exhaustive dynamic call graph
   or executed operand coverage is claimed.
2. Both chain placements are new, not MOVE. Child depth2 has no clip actions.
   Child removal at frame5 and body removal at frame194 are distinct. Stamps
   and root snapshots do not prove continuous engine identity between callbacks.
3. Child owner stops at frame1; outer handler conditionally goes to5; frame5
   renames; frame10 stops. No implicit return-to-standing is introduced.
4. Tests lock source facts and retained observations, and reject an erased
   `hitmc` hop, ancestor substitution, wrong source, or missing parent boundary.
   They do not turn an implementation assumption into expected gameplay.
5. Existing s247 uses the unchanged s239 tape and contains 5,079 complete events.
   No fresh native capture or Godot comparison is claimed. The actual executed
   receiver/target join and exact removal/rename boundary remain missing.

The next experiment is now bounded to **this frame188 placement only**, ticks
15–22 on the unchanged s239 tape. Observe the original outer callback's branch
and actual receiver/target operands in source order, without introducing extra
hitTest evaluations or altering short-circuit behavior. Observe child placement,
frame5 depth2 removal and before/after rename separately from body frame194
depth28 removal. Correlate direct parents, depths, frames, source stamps and slot
observations; retain undefined targets, skipped sites and all terminal events.
Do not equate a path, stamp or reference equality with allocation identity.
Missing executed sites or lifecycle joins must keep the proposed rule unproved.
A source/operand mutation must reject rather than silently remap to a nearby owner.

Zero builds/player launches in this slice. A new instrumented capture is required
to resolve these missing observations; repeating the old observer cannot recover
them. This evidence-only delivery stops before designing or asserting a safe
operand-preserving probe. Measured analysis/check time is retained in
[gates](gates.json) and [session timing](session-timing.json); capture cost is zero,
future capture cost and person-days are unknown.

## Gates and reproduction

- Portable diagnosis and complete raw sequence validation: exit0.
- Runtime-binding requirement: honest exit1 (missing executed operands/lifecycle).
- Unchanged geometry collector on the entire hash-verified raw stream: exit1,
  `missing-source-list:_level0.game.p1.mc.k1atm.mian`.
- Historical receipt and full geometry CLI: exit1 **before geometry admission**,
  because master changed `build_ai_reference.py`, `deidara_atm1_observer.py` and
  `sampling_native.py` since that receipt. [Exact drift](receipt-environment-drift.json)
  records expected/current hashes. This is not a newly valid receipt. The raw
  trace and archived outputs still match their receipt entries; no resealing,
  rollback of tools or hash repair is performed.
- 54 focused tests pass; project integrity, handoff and contracts checks are
  recorded in [project-checks.json](project-checks.json).

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s270/diagnose.py --output /tmp/s270.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s270/diagnose.py --output /tmp/s270-required.json --require-runtime-binding # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s270/diagnose.py --output /tmp/s270-geometry.json --require-geometry # exit 1
python3 -m unittest tools.tests.test_nested_owner_diagnosis tools.tests.test_yulong_k1atm_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Portable commands require no player, external exports or historical temp paths.
The original-path receipt/CLI attempts are retained separately in `gates.json`.
A successful diagnosis is not geometry, display, mask, camera or parity admission.

Only s270 evidence, its focused test and requested tracking files change.
Ranks1–6/8–9 and s254–s269 are untouched. s248's 166 source obligations and s250's
AImain gap are not closed by this nested chain; s241–s244 remain closed as prior
evidence work. No runtime, shared sampler, strict validator, schema, tape,
threshold, baseline, gameplay, renderer, merge or deployment change.
