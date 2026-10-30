# s251 — Rank 3: source-bound helper load stamp

Baseline master `95ea9b7f`, branch `feat/s251-geometry-stamp`. Exclusive s251
was absent from STATUS/tasks and disk at start. Only the unchanged s64
`didala__summon__neutral__ground__near` tape with Woailuo as P1 helper.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.

## Thin fix and observed result

The opt-in `--deidara-atm1-load-stamp` adds one call to the existing
`aiGeoStamp(this, source)` at the end of the hash-checked Woailuo frame-44
atm1 load handler, before the existing `load_after` observation. Its source is
the exact authored placement/load path, not a fabricated frame-1 DoAction or
an inherited parent source. Original handler statements and all authored
DoActions remain unchanged. The prior `--deidara-atm1` diagnosis remains
read-only. Ordinary geometry sampling and other helpers are unchanged.

One fresh native capture retains **5,343 events**. The source-bound child
starts without any stamp at load entry; the injected call assigns ID **76**,
source `game/fighter/fz/woailuo.swf#frame_44/PlaceObject2_48_2/CLIPACTIONRECORD onClipEvent(load).as`,
and birth display **550**. All three fields persist at ticks **58/59/60**, child
frames **1/2/3**, helper frames **44/45/46**, runtime depth **-16382**. Parent
ID 58 is distinct and unchanged. The new path binds all three helper geometry
records; the old three `unbound` errors disappear. No synthetic child action,
manual ID assignment, new stamp policy or geometry gate exception is added.

The receipt and bounded lifetime proof exit **0**. The unchanged geometry
collector structurally reads **61 samples / 241 boxes**, but the **full geometry
gate still exits 1**: P1 hurt receiver is absent at ticks **11 and 41**. Both
absences also exist in the raw s64 and s246 evidence; their earlier unbound
error prevented the full gate from reaching its receiver check. These are
retained obligations, not a reason to alter receiver ownership or eligibility.
No full geometry report is admitted. `lifetime-proof.json` explicitly separates
structural collection from full-gate success.

All **122** fight actor-state tick/payload pairs exactly match both retained
s64 and s246 captures. This bounded native/native check does not prove Godot
parity or eliminate instrumentation timing effects. Pre-fight event counts and
display offsets differ and remain untrimmed. The static loader still reports
`runtime_fighter=null`; independent runtime-loader attestation is unproven.

## Source-first proof

The source binding is [s246/source-binding.json](../s246/source-binding.json).
The focused test independently checks its locked SWF/bundle hashes and the XML
member hash in the retained s30 source archive, then reads the actual tags.

1. Sprite 48 has no DoAction at frames 1–32 and only `stop()` at frame 33
   (`DefineSprite_48/frame_33/DoAction.as`). The parent frame-44 DoAction is
   `_root.shine(9461816)` and its stamp targets the parent. The exact selected
   `frame_44/PlaceObject2_48_2/CLIPACTIONRECORD onClipEvent(load).as` body only
   sets X using facing/opponent position; those statements are preserved.
2. Parent frame 44 is a new PlaceObject2, characterId 48, depth 2, name atm1,
   `placeFlagMove=false`, with that load handler. The fresh native boundary
   confirms an initially unstamped child, followed by a distinct stamp; the
   parent stamp is never copied. This is source-bound, not a name-only match.
3. The child naturally advances through the sampled frames; its authored end
   action is `stop()` at 33. No goto, stop or playback scheduling is injected.
   The capture ends at child frame 3; removal, later frame 33 and recasts are
   outside this proved lifetime window.
4. Source tests lock the new placement and absence of early authored actions;
   generated-text tests preserve the original handler and reject changed
   source, tape/configuration and unrelated source instrumentation. Native
   proof requires both load/stamp boundaries, stable ID/source/birth, and all
   three corresponding geometry records. Missing/duplicate observations,
   changed source/ID/birth and removed boxes reject. Old s64/s246 unbound
   traces and their negative tests remain rejecting.
5. Fresh native Flash used exactly the original s64 case, no tape edits. Raw
   trace, receipt, build/diff/SWF archive and capture environment are retained.
   There are no gameplay, Godot, bitmap, other-rank or validator changes.

## Reproduction

Use fresh output paths/run IDs for new captures:

```sh
python3 tools/probes/build_ai_reference.py \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s251-build-r01 --run-id s251-atm1-load-r01 \
  --frames 60 \
  --move-case evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 \
  --deidara-atm1-load-stamp
```

Capture used `capture_native_player.capture(build, trace, 180, lock_timeout=45)`
with authorized window activation and the shared native-capture lock, then
`sampling_native.seal`. The initial sandbox attempt failed at `ps` before
launch; the authorized escalated attempt completed once, without rejected
traces or retries. Timing is in `capture-environment.json`. The complete suffix
after `done` is retained. Restore the build archive at `/tmp/bvn-s251-build-r01`,
the decompressed trace at `/tmp/bvn-s251-capture-r01/native.log`, and the receipt
at `/tmp/bvn-s251-capture-r01/receipt.json`. Keep this commit's probe paths and
the pinned engine; do not rewrite historical receipt hashes.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s251/verify_lifetime.py
python3 -m unittest tools.tests.test_deidara_atm1_load_stamp tools.tests.test_deidara_atm1_observer
python3 -m tools.sampling_geometry \
  --case evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json \
  --receipt /tmp/bvn-s251-capture-r01/receipt.json --output /tmp/s251-geometry.json
# Exit 1: missing p1 receiver at tick 11; no admitted full report.
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

`gates.json` records actual gate commands/exits; **159 focused tests pass**, including the old
negative proofs. `project-checks.json` records integrity/handoff/contracts.
`manifest-audit.json` records reviewed tracked-file hashes only;
`session-timing.json` records elapsed wall time, not inferred person-days.
General placement stamping, exact intra-frame/removal lifetime, receiver
ownership, other sampling dimensions and native/Godot parity remain open.
s249/s250 and s241–s244 are not reopened. No merge or deployment.
