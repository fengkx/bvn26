# s256 — AFTER-s253 rank 3: P1 receiver availability at tick11

Baseline master `e27af582` / #133; branch `feat/s256-geometry-p1-receiver`.
Authority: rank 3 in [AFTER-s253 priority](../next-fix-priority-after-s253.md).
Exclusive to **Deidara P1 bdmn at tick11 of the locked s64/s251 summon tape**.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.
Evidence-only: **no eligibility fix proved, zero product obligations closed**.

## Finding

The missing sampled receiver is **not an empty bdmn slot**. One fresh native
capture observes the named bdmn, the occupant at runtime depth -16355, and a
reference saved at tick10 immediately before the unchanged geometry sampler.

| Tick / parent source frame | Live slot / child frame | Receiver functions / lists | Stamp ID / birth display |
| --- | --- | --- | --- |
| 10 / 1 | MovieClip / 1 of 1 | both functions; all three lists present | 67 / 299 |
| 11 / 840 | MovieClip / 1 of 1 | both functions and all three lists undefined | undefined / undefined |
| 12 / 841 | MovieClip / 1 of 1 | both functions; all three lists present | 75 / 509 |

The three lookups report identical fields and reference equality at all three
boundaries. In particular, the saved tick10 reference reads the unstamped fields
at tick11 and the new stamp at tick12. AS2 reference equality/path/depth therefore
must not be promoted to proof of a continuously retained initialized instance.
The source placement is new; the old stamp is not inherited. Display 509 is the
tick11 observation period; the tick12 stamp reports birth in that period. These
root samples bound initialization but do not observe its exact instruction order.

The sampler requires both `getHitObj` and `getStgHitObj` to be functions before
it considers a receiver. At tick11 this bdmn does not satisfy that predicate;
it also has no stamp or candidate lists. Changing eligibility to accept its path
or symbol would invent readiness and would not establish valid source lists.
The unchanged full geometry gate still exits **1: missing p1 receiver at tick 11**.
No initialized receiver, geometry exemption, copied stamp or ancestor pn is added.
The other P1 slot is not independently diagnosed here.

## Source and observation control

`diagnosis.json` retains the authored depth29 history through frame841, complete
summon-label scripts, receiver initialization script, and all targeted native
observations. XML comes from the hash-checked s30 archive; original SWF and bundle
hashes are verified. Depth29 maps to runtime -16355.

1. `scripts/fighter/didala.json → DefineSprite_542/frame_840/DoAction.as`
   calls two `shine` functions; frame845 calls `doZhaoHuan`; frame870 calls
   `gotoAndStop("站立")` then `play()`. The other frames in label840–878 have no
   DoAction. The frame840 bdmn enterFrame calls `beida()`. Sprite2 frame1 defines
   the receiver functions and initializes `_fsArray`, `_fzfsArray`, and `stgks`.
2. Sprite542 frame840 places Sprite2 named bdmn at depth29 with
   `placeFlagMove=false`. Frame841 has no placement/removal. Linear source
   history contains RemoveObject2 depth29 at826; **the observed jump 1→840 does
   not prove that frame826 executed**. The original frame1 slot and destination
   placement do not justify carrying instance variables across the jump.
3. The summon label explicitly exits at870; its end is not treated as a return
   to standing. Tick11/12 samples cover840/841 only, not the whole summon lifetime.
4. Tests lock authored placement, observed function/list/stamp absence and return,
   retained missing geometry, and missing/duplicate observation rejection. They
   do not assert an inferred runtime allocation identity or eligibility rule.
5. One new native run uses the exact s64 tape and existing s251 load-stamp mode.
   All **122 actor tick/payload rows** exactly match retained s251 (all 14 state
   fields). The existing atm1 fix is reused unchanged, not repeated or extended.
   This control is not Godot parity and does not prove zero instrumentation cost.

Historical s251 proves the gap and surrounding stamp change (64→72), but does
not record named/depth lookups at tick11; it cannot distinguish an empty slot
from an uninitialized slot. That missing fact required one new capture. The
isolated observer only reads P1 bdmn at ticks10–12 and saves one reference on the
root; it never writes receiver fields or invokes receiver functions. Full raw
stream, build/diff/SWF archive and receipt are retained without suffix trimming.

## Next discriminator and limits

Observe this same lifetime immediately before/after the authored jump and at
entry/exit of Sprite2 frame1 initialization, paired with the root geometry sample
and the first authored bdmn enterFrame. Use an independently validated identity
control if claiming allocation continuity: saved AS2 references alone are
insufficient. Establish the order and the first point at which collision methods
and lists are usable before proposing any sampling/eligibility change. Current
evidence does not justify moving sampling, initializing early, or accepting an
unready receiver. Runtime loader attestation remains unproved (`runtime_fighter=null`).

Ranks **1/2/4/5**, s254/s255, tick41 diagnosis, Yulong/nested ownership, BitmapData,
completion boundaries, thresholds, tapes, validators and gameplay are untouched.
The complete original tape is retained; later samples are not new scoped work.
No merge or deployment.

## Gates, cost and reproduction

- Native stream: **5,400 events**, one successful launch; receipt exit0.
- Portable diagnosis/61-sample structural collection exit0; full geometry exit1.
- **61 focused tests pass**; integrity, handoff and contracts pass (see
  `gates.json` and `project-checks.json` for commands, exits and measured times).
- Build: **10.386 seconds**; capture/launch/wait/cleanup: **32.039 seconds**.
  These are measured subprocess costs, not person-days or total session time.
  No capture retries. See `native-build.json` and `capture-environment.json`.

From repository root, portable diagnosis/tests need no external player/XML cache:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s256/diagnose.py --output /tmp/s256-diagnosis.json
python3 -m unittest tools.tests.test_p1_receiver_availability tools.tests.test_deidara_atm1_load_stamp tools.tests.test_deidara_atm1_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

For retained receipt/full geometry checks, restore `native-build.tar.gz` into
`/tmp/bvn-s256-r01-build`, decompress `native-capture.log.gz` into
`/tmp/bvn-s256-r01-capture/native.log`, and copy `native-receipt.json` there as
`receipt.json`. Use the exact commands in `gates.json`, pinned probe sources and
player `/Volumes/Flash Player/Flash Player.app`; do not reseal historical receipts.

To recapture, choose fresh paths/run ID:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s256/build_probe.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar --output /tmp/bvn-s256-new-build --run-id s256-p1-new
mkdir -p /tmp/bvn-s256-new-capture
python3 -m tools.sampling_native --case evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json --build /tmp/bvn-s256-new-build --trace /tmp/bvn-s256-new-capture/native.log --receipt /tmp/bvn-s256-new-capture/receipt.json --timeout 180 --allow-window-activation
```

Use the existing serialized native-capture lock; do not remove locks.
