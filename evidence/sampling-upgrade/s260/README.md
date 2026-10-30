# s260 — AFTER-s258 rank 2: receiver initialization order

Base master `64ec4433` / #137; branch `feat/s260-receiver-init-order`.
Authority: **rank 2 only** in [AFTER-s258 priority](../next-fix-priority-after-s258.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
Evidence-only diagnosis: `eligibility_fix_proved=false`, zero product obligations closed.

## Finding

The unchanged P1 tick11 geometry sample completes **before** the newly placed
bdmn executes Sprite2 frame1 initialization. First authored bdmn enterFrame is
observed after that initialization, at parent frame841. Thus the uninitialized
slot at the sample is real; there is no proved thin eligibility or runtime fix.

Native event order (full stream in `native-capture.log.gz`):

| Sequence | Root tick / display | Boundary | Parent frame | Functions / list lengths / stamp |
| --- | --- | --- | --- | --- |
| 3857 | 10 / 495 | unchanged root sample, before geometry | 1 | functions / 96,5,10 / 64 |
| 3892 | 10 / 495 | authored jump pre-call | 2 | functions / 96,5,10 / 64 |
| 3904 | 11 / 496 | unchanged root sample, before geometry | 840 | all undefined |
| 3905–3908 | 11 / 496 | geometry begin/end | 840 | no P1 receiver collected |
| 3909 | 11 / 496 | parent frame840 entry | 840 | all undefined |
| 3910 | 11 / 496 | Sprite2 frame1 entry | 840 | all undefined |
| 3911 | 11 / 496 | Sprite2 frame1 exit, after existing stamp | 840 | functions / 96,5,10 / 72 |
| 3912–3913 | 11 / 496 | first authored bdmn enterFrame, before/after beida | 841 | functions / 96,5,10 / 72 |
| 3941 | 12 / 497 | unchanged root sample, before geometry | 841 | functions / 96,5,10 / 72 |

`aiFight` and `aiDisplay` advance in the root observer. The callback at parent841
still carries tick11/display496; it is not a same-placement-frame enterFrame.
Use sequence and source frame together, not tick labels alone. Stamp72 birth is
496. No receiver methods are called by the observer; it reads types, lengths and
existing stamps only. First exit establishes these fields, not universal collision
correctness or an allocation-continuity identity proof.

The jump-after marker is absent. The pre-call marker, parent840 root sample and
positive destination/frame1 markers bound the observed transition; absence of the
post-call marker does **not** prove VM return/unwind semantics. Chad continuation
(rank5) is not investigated. The old tick10 saved-reference equality from s256
is not used as an allocation identity discriminator.

## Source-first boundaries and controls

1. Authored jump: `scripts/fighter/didala.json → DefineSprite_16/frame_1/DoAction.as`,
   `zhaoHuan()` branch of `doAllAction(special)`, `_parent.gotoAndPlay("招换")`. The full imported
   script is archived. The separately defined Sprite301 controller is untouched.
   Destination: `DefineSprite_542/frame_840/DoAction.as` calls two shines.
   Receiver: `DefineSprite_2/frame_1/DoAction.as` defines getHitObj/getStgHitObj
   and initializes the three candidate lists. Frame840's
   `PlaceObject2_2_29/CLIPACTIONRECORD onClipEvent(enterFrame).as` calls `beida()`.
2. Hash-checked s30 XML and s256 source report remain authoritative: frame840
   places Sprite2/bdmn at depth29 with `placeFlagMove=false`; frame841 has no
   placement/removal. Linear RemoveObject at826 does not prove execution during
   the jump. No instance variables are inherited or prepopulated by this probe.
3. Summon840–878 has DoAction at840,845 (`doZhaoHuan`) and870 (explicit standing
   goto/play); all other frames have no DoAction. Complete scripts and depth
   history are retained in `diagnosis.json`. Only tick10–12 are diagnosed.
4. Tests assert observed event order and source instructions, complete marker
   coverage, unchanged sample boundary and retained receiver gap. No scheduling
   rule, allocation identity or early eligibility is invented.
5. One successful native capture uses the **exact locked s256/s64 input tape**,
   same static fixture, existing load-stamp mode and full 0–60 collection.
   All **122 actor rows, 61 input rows and 954 key-read rows** exactly match s256
   by tick and payload. Five random records differ and remain intact; there is
   no claim of random-tape replay, zero observer cost or Godot/native parity.
   Existing helper/opponent compiled outputs match s256 hashes. Loader runtime
   attestation remains unproved (`runtime_fighter=null`).

The old s256 tape has root-boundary observations but no frame1 or enterFrame
entry/exit markers; it cannot answer this ordering question. That specific gap
required the new capture. `build_probe.py` is an isolated wrapper: six targeted
script patches, no shared builder/sampler/validator or production changes.
Raw stream, receipt, build metadata, exact imported scripts, instrumentation diff
and SWFs are archived without suffix trimming or historical receipt resealing.

## Next discriminator

At the **unchanged tick11 boundary**, establish whether an authored collision
query actually executes against this uninitialized bdmn before Sprite2 frame1.
Observe the source query and exact operands with positive same-context controls;
separately record function/list availability and native outcome. This can
separate an unready object existing in the scene from a receiver being queried
in that interval. It is a proposed evidence step, not authorization to call
methods artificially, initialize early, move the sample or exempt this receiver.
Current data does not justify any of those changes. Other P1 slots remain
independently unproved; this diagnosis does not close full geometry coverage.

Ranks **1/3/4/5**, s254–s259, tick41, nested Yulong, ancestor-pn behavior,
completion windows, baselines, thresholds, strict validators and gameplay are
untouched. Later samples remain in the complete tape but are not new scoped work.
No merge or deployment.

## Gates, cost and reproduction

- Native capture: **5,274 events**, one successful launch; receipt exit0.
- Portable diagnosis / 61-sample structural collection exit0; unchanged full
  geometry exit1: **missing p1 receiver at tick 11**.
- **68 focused tests** pass; integrity, handoff and contracts pass. Commands,
  measured times and exits: `gates.json`, `project-checks.json`.
- Build **10.376 seconds**, successful capture **32.534 seconds** including
  launch/wait/cleanup. One sandbox attempt failed on `ps` before launch;
  `capture-sandbox-attempt.json` retains its cost. No successful-run retries.
  These are measured subprocess costs, not a person-day or total-session estimate.

Portable reproduction (no player or external XML cache required):

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s260/diagnose.py --output /tmp/s260-diagnosis.json
python3 -m unittest tools.tests.test_receiver_init_order tools.tests.test_p1_receiver_availability tools.tests.test_deidara_atm1_load_stamp tools.tests.test_deidara_atm1_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

For retained receipt/geometry checks, restore `native-build.tar.gz` into
`/tmp/bvn-s260-r01-build`, decompress `native-capture.log.gz` into
`/tmp/bvn-s260-r01-capture/native.log`, and copy `native-receipt.json` there as
`receipt.json`. Run the commands in `gates.json` with the pinned probe sources
and `/Volumes/Flash Player/Flash Player.app`; do not reseal historical receipts.

Optional recapture (fresh paths/run ID; existing serialized capture lock):

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s260/build_probe.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar --output /tmp/bvn-s260-new-build --run-id s260-init-new
mkdir -p /tmp/bvn-s260-new-capture
python3 -m tools.sampling_native --case evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json --build /tmp/bvn-s260-new-build --trace /tmp/bvn-s260-new-capture/native.log --receipt /tmp/bvn-s260-new-capture/receipt.json --timeout 180 --allow-window-activation
```

The portable diagnosis is intentionally pinned to the retained r01 evidence;
a recapture is a new record, never a replacement of that baseline.
