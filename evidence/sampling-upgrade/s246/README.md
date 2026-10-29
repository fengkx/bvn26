# s246 — Deidara summon helper atm1 geometry provenance

User-selected [s64 follow-up](../s64/README.md#exact-blocker-and-next-discriminator).
Base master `65b7008643514c5f0f313f855b2ec69cf5a7bf5c` (merged s245 / PR #123),
branch `feat/s246-deidara-atm1-provenance`. Only the unchanged s64
`didala__summon__neutral__ground__near` tape, with Woailuo as P1 helper.
This is not a rerun of s66 BitmapData. No Chad/Yulong or other residual work.
`production_admitted=false`; `native_parity_proven=false`.

## Result and exact missing fields

One native capture: **5,498 events**, 61 geometry begin/end pairs, 238 bound box
records, and the same three explicit `unbound:_level0.game.p1fz.atm1` errors at
ticks 58–60. The receipt revalidates with **exit 0**. Both the stamp-binding
report gate and the unchanged full geometry gate exit **1**. No complete
geometry report is admitted and no failing tick is omitted.

Nine additional read-only observations establish the following sequence:

| Site | Sequence / tick | Actual observation |
| --- | --- | --- |
| Root before geometry | 5299 / 56, 5349 / 57 | Helper frames 42/43; `atm1` absent |
| Helper frame-44 stamp before/after | 5390–5391 / 57 | Target is `p1fz`, not `atm1`; parent retains ID 58, source `frame_1/DoAction.as`, birth display 2 |
| Source-bound `atm1` load before/after | 5392–5393 / 57 | Child frame 1, helper frame 44, runtime depth -16382; all three stamp fields undefined |
| Root before geometry | 5405 / 58, 5454 / 59, 5487 / 60 | Child frames 1/2/3, helper frames 44/45/46; all three stamp fields still undefined |

The missing fields are **both `__aiGeoId` and `__aiGeoSource`**, plus
`__aiGeoBirth`. This is not an ID with only its source string omitted. The
parent's successful stamp does not bind its newly placed child. The source-bound
load event identifies the authored placement independently of the runtime name;
no symbol is inferred merely from the text `atm1`.

## Source placement and stamp-site join

`source-binding.json` records the locked helper SWF/bundle hashes and the verified
XML hash from the retained s30 source archive:

- Root frame 44 has a new `PlaceObject2` of **Sprite 48**, authored depth **2**,
  name **atm1**, `placeFlagMove=false`, with a load handler. The runtime depth
  observed in this capture is -16382.
- The exact handler is
  `frame_44/PlaceObject2_48_2/CLIPACTIONRECORD onClipEvent(load).as` in
  `scripts/fighter/fz/woailuo.json`. Its original body only adjusts X from facing
  and opponent position. The probe hash-checks that source and surrounds it
  with observations, retaining its statements unchanged.
- Sprite 48's sole authored DoAction is `DefineSprite_48/frame_33/DoAction.as`
  (`stop()`). There is no frame-1 DoAction in either the bundle or source XML.
- The existing geometry builder appends `aiGeoStamp(this, source)` only to
  authored DoAction blocks. Its frame-44 helper call stamps the helper root;
  its child frame-33 call cannot have run while the observed child is at frames
  1–3. The existing load handler is not a stamp site.

Together the source and native observations locate the gap: DoAction-only
stamping has no child stamp site before this candidate's first geometry query.
A future binding change needs authored placement/load-time provenance for such
instances rather than copying parent stamps, inventing a source, or exempting
helper boxes. This slice diagnoses that requirement; it does not implement a
new binding policy or claim general placement/lifetime ownership.

## Scope and gates

`--deidara-atm1` accepts only the exact s64 case and enables existing geometry
sampling. In generated analysis copies only, it adds load front/back observations,
wraps the existing stamp function with read-only before/after observations, and
samples the selected helper candidate immediately before geometry at ticks 56–60.
It assigns no geometry ID/source/birth, changes no original helper movement,
and leaves `sampling_geometry.as` and the full geometry collector unchanged.
The new source-bound module and AS observer are included in receipt probe hashes.

`provenance.json` retains every field, marks `observation_complete=true` and
`stamp_binding_complete=false`, and lists all three missing fields for each live
sample. The collector checks paired source/receiver identities without imposing
a cross-site scheduling order. `gates.json` records actual commands and exits.
`negative-proof.json` removes each marker kind: native sequence validation and
provenance validation both reject; restoring the original stream restores a
valid receipt, never a complete stamp binding.

**141 focused sampling/probe/import tests pass**, including unchanged source/stamp
assignment checks, changed-source/tape rejection, and missing/duplicate/wrong-source
actual-observation negatives. Integrity, handoff and contracts checks are retained.
All 122 fight actor-state payloads match retained s64 native evidence exactly;
this limited native/native check proves neither Godot parity nor absence of
instrumentation timing effects. Pre-fight event counts/display offsets differ
and remain untrimmed. M0-02 remains pending.

## Reproduction and restoration

Use fresh paths/run IDs for a new capture. The actual one used:

```sh
python3 tools/probes/build_ai_reference.py \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s246-build-r01 --run-id s246-didala-atm1-r01-20261029 \
  --frames 60 \
  --move-case evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 \
  --deidara-atm1
```

Native capture used `capture_native_player.capture(build, trace, 180,
lock_timeout=45)` with authorized window activation, followed by
`sampling_native.seal`. The shared `/tmp/bvn-native-flash-capture.lock` was
acquired and released by that context. Capture took 35.701 seconds; there were
no capture retries or rejected traces. No suffix is trimmed. Launch is the
existing windowed `open -g -n -W -a` player path in `capture-environment.json`.
The trusted static fixture still reports `runtime_fighter=null`; independent
runtime-loader identity and external clock equivalence remain unproven.

Restore `native-build.tar.gz` into `/tmp/bvn-s246-build-r01`, decompress the raw
trace to `/tmp/bvn-s246-capture-r01/native.log`, and restore the receipt to
`/tmp/bvn-s246-capture-r01/receipt.json`. Keep the original s64 case and this
commit's probes at receipt-recorded paths. Do not rewrite receipt hashes.

```sh
python3 -m tools.sampling_atm1_provenance \
  --case evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json \
  --receipt /tmp/bvn-s246-capture-r01/receipt.json --output /tmp/s246-provenance.json
# Exit 1: explicit missing stamp fields, with complete discriminator observations.
python3 -m tools.sampling_geometry \
  --case evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json \
  --receipt /tmp/bvn-s246-capture-r01/receipt.json --output /tmp/s246-geometry.json
# Exit 1: unbound helper candidate; no complete geometry report.
python3 -m unittest tools.tests.test_deidara_atm1_observer
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Residuals: placement-aware stamp compilation, exact intra-frame lifetime, full
native/Godot geometry parity and general AS ownership remain open. No late
frame-33 capture is inferred from the static source. Existing s64/s66 evidence,
tapes, failed gates and all other residuals are unchanged. No gameplay/Godot
changes, merge, deployment or Worker work.
