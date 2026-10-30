# s264 — AFTER-s263 rank 1: authored queries at the receiver initialization boundary

Baseline master `9d214870` / #141; branch `feat/s264-post-s263-rerank`.
Authority: **only new rank 1** in [AFTER-s263 priority](../next-fix-priority-after-s263.md).
Ranks **2+ are planning only and have not been started**.
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
**Evidence-only: eligibility_fix_proved=false; pre_init_authored_query_proved=false.**
Zero product obligations closed; no runtime or validator fix is justified.

## Result

One new original-player capture uses the exact locked s64/s260 case and the
unchanged geometry boundary. s260 had frame1 and enterFrame observations but no
query entry/operand/result observations; those cannot be recovered retrospectively.
The isolated extension observes existing calls, never calls a collision method
artificially. It preserves all s260 boundary markers.

| Native sequence | Root tick / parent frame | Observation |
| --- | --- | --- |
| 4055 | 11 / 840 | Original root sample sees methods/lists/stamp undefined |
| 4056–4059 | 11 / 840 | Original geometry begin/end; no P1 receiver collected |
| 4060–4062 | 11 / 840 | Destination entry, Sprite2 frame1 entry, then initialized exit |
| 4063–4070 | 11 / 841 | Authored enterFrame brackets beida → checkHit → two getHitObj calls → getStgHitObj → undefined checkHit result |
| 4105–4112 | 12 / 842 | Same authored chain, again with undefined result |

There are **12 query rows**, all after frame1 initialization. Both natural
same-context controls report receiver lists **96/5/10**, valid methods and stamp74.
The fighter query receives `_level0.game.p2.mc`, suffix `atm`, array length96;
the helper query receives `_level0.game.p2fz`, empty suffix, array length5.
The stage query uses `_level0.game.layer_effect` and list length10. These are
actual arguments read at authored function entry, not inferred from actor state.
Neither scan reaches the inserted `this.hitTest` operand site in this window;
there is **no positive hitTest-operand observation** and no numerical AABB claim.
The source's final stage fallthrough permits the observed undefined result; it
is not normalized to null or synthesized as a hit/miss event.

The unready interval from root sequence4055 to frame1 exit4062 has no recorded
query entry. **This does not establish that no query was attempted.** Functions
are defined by that same frame1; a call to an undefined method cannot enter its
instrumented body. External direct hitTests are also not covered. The positive
controls establish observability after initialization, not universal pre-init
call-site coverage. `all_collision_paths_observed=false` is explicit.
Thus the evidence distinguishes the first observed natural query chain from the
unready root sample, but does not admit an eligibility exception or prove safety
of omitting that receiver.

The full stream has **5,437 events**, 61 geometry samples, one done, and no trimmed
suffix. All **122 actor rows, 61 input rows and 954 key-read rows** match s260 by
tick/payload. Five random rows differ and remain preserved. This is not a locked
random replay, zero observer cost, or native/Godot parity. Pre-fight display
counts and stamp allocation numbers differ and are not normalized.
Loader runtime attestation remains absent (`runtime_fighter=null`).

## Source-first scope and preservation

1. The exact authored receiver source is
   `scripts/fighter/didala.json → DefineSprite_2/frame_1/DoAction.as`:
   beida/fangyu consume checkHit; checkHit checks gameRunning/canhit, then fighter,
   helper and stage in that order. getHitObj/getStgHitObj only perform hitTest
   when their authored candidate exists. The complete source, query reference
   inventory and prior destination-label script inventory are in `diagnosis.json`.
   The authored frame840 enterFrame path remains
   `DefineSprite_542/frame_840/PlaceObject2_2_29/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
2. Hash-checked s260/s256 source evidence still binds frame840's new Sprite2/bdmn
   at depth29, not MOVE. Frame841 has no replacement/removal. No variables are
   inherited, populated early or treated as allocation identity by this probe.
3. Summon840–878 has actions at840,845 and870; frame870 explicitly goes to
   standing. There is no invented label-end return. The controller's authored
   summon goto and all original calls, guards, assignments and returns are intact.
4. Tests assert captured order/arguments/results, source preservation and
   incomplete-evidence rejection. They retain the original geometry failure and
   explicitly reject any claim that post-init controls prove all pre-init paths.
5. One new native run uses the unchanged input fixture. Its measured native/native
   controls are above. No Godot gameplay is modified and no product acceptance
   or full move audit is claimed.

`build_probe.py` first runs the unchanged s260 builder, then extends **only** main
frame1 with the observer and Didala Sprite2 frame1 with read-only observation
calls. Observing an already computed checkHit result does not re-evaluate it.
Every imported script is compared against the s260 archive, allowing only the
new observations and explicit build-directory/run-ID changes. Unrelated compiled
outputs, source hashes, complete SWFs, raw trace, receipt and instrumentation diff
are retained and checked by `diagnose.py` and `artifact-sha256.json`.
No shared builder/sampler/collector, existing validator, contract, gameplay,
threshold, baseline or original `game/` / `scripts/` input is changed.

## Remaining discriminator

Observe **source call sites** that can address the newly placed bdmn before
frame1, with positive same-context dispatch/operand controls independent of the
functions defined by that frame. Distinguish an undefined-method dispatch from
no attempted call, and cover any direct external hitTest relevant to that exact
interval. The retained body-entry probes cannot supply this missing evidence.
Do not artificially invoke those methods, move the sample, initialize early,
substitute ancestor pn or exempt receivers. Tick41, nested Yulong and other
receiver slots remain outside this cut. s241–s244 are not reopened.

## Gates, cost and reproduction

- Receipt, portable diagnosis and **73 focused tests**: exit0.
- Explicit pre-init-query requirement: exit1 (unproved).
- Unchanged full geometry gate: exit1, **missing p1 receiver at tick 11**.
- Integrity, handoff and contracts: exit0; commands and measured durations in
  `project-checks.json`. Full gate commands/exits are in `gates.json`.
- Build: **8.566 seconds** including the s260 base; one successful capture:
  **31.910 seconds** including launch/wait/cleanup. Initial sandbox `ps` preflight
  failed before launching; retained in `capture-sandbox-attempt.*`, followed by
  authorized escalation. No successful capture retry or historical resealing.
  A first portable packaging comparison rejected the differing run ID; the
  comparison now allows that explicit build metadata change alongside paths,
  without modifying any source or trace. No total person-days are inferred.

Portable reproduction requires no player or external XML export cache:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s264/diagnose.py --output /tmp/s264.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s264/diagnose.py --output /tmp/s264-required.json --require-pre-init-query  # expected exit 1
python3 -m unittest tools.tests.test_receiver_authored_query tools.tests.test_receiver_init_order tools.tests.test_p1_receiver_availability tools.tests.test_deidara_atm1_load_stamp tools.tests.test_deidara_atm1_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

For retained receipt/full geometry gates, extract `native-build.tar.gz` into
`/tmp/bvn-s264-r01-build`, decompress `native-capture.log.gz` into
`/tmp/bvn-s264-r01-capture/native.log`, copy `native-receipt.json` there as
`receipt.json`, and run `gates.json` commands with the pinned player/probe sources.
Do not reseal historical receipts. For a fresh capture, run `build_probe.py`
with `--ffdec /path/to/ffdec.jar --output /tmp/fresh-build --run-id fresh-id`,
then the native capture command in `capture-command.json` using fresh paths.
Keep the existing serialized capture lock and explicit window activation option.
No merge or deployment.
