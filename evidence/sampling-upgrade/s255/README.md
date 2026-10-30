# s255 — AFTER-s253 rank 2: one AImain unload lifetime

Baseline master `544ec6f5379bef8007acebb0bb390e5a4020af30` / #132; branch
`feat/s255-aimain-unload-identity`. Authority: rank 2 in
[the AFTER-s253 priority](../next-fix-priority-after-s253.md), explicitly selected
for this slice. Exclusive to one **P1 Yijiao initCtrl unload lifetime**.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.
Evidence-only diagnosis: **no safe mapping fix is proved; zero obligations fixed**.

## New observation

Historical s250 captures begin sampling after the relevant unload and cannot
recover it retrospectively. One new native capture reuses the unchanged s231
static attack tape and s249 standalone display builder. An isolated wrapper
inserts observations immediately around the original `AImain.unloadMovie()` in
`fighter/yijiao#DefineSprite_455/frame_1/DoAction.as`; the original preceding
`gotoAndStop(1)` and unload statement remain intact. Only the first P1 lifetime
is armed. P2 and all other sources use the ordinary instrumentation.

The observer stores receiver/parent/depth outside unloaded content. It records
saved receiver, named lookup and `parent.getInstanceAtDepth(savedDepth)` together,
plus native reference equality, parent identity token, path/name/depth,
current/total frames, source stamp, temporary token, display ID and children.
The next-root hook runs just after `aiDisplay++`, before fight/input processing;
the first-sample hook runs immediately after the first ordinary `display_end`.
It does not create or replace the collector's display ID.

| Phase | Identity sequence / root period / fight tick | AImain frame / total | Stamp / receiver token |
| --- | --- | --- | --- |
| Immediately before authored unload | 22 / 7 / -1 | 1 / 2 | Sprite3 frame1 / s255-receiver-1 |
| Immediately after authored unload returns | 27 / 7 / -1 | 1 / 2 | both retained |
| Next root observer | 34 / 8 / -1 | 1 / 2 | both retained |
| First display sample | 2901 / 433 / 0 | 0 / 0 | both undefined |

All three lookups agree at each boundary; `saved == occupant`, `named == occupant`
and `saved._parent == parent` are true. The parent token survives all four
observations; parent frame is 1, parent totalframes 1041. The AImain depth remains
-16383 (authored depth 1), name/path remain AImain, and its child inventory is
empty at all four boundaries. At first sample all lookups have ordinary display
ID 15, matching the collected node. Full records are in `diagnosis.json` and the
complete raw stream is retained in `native-capture.log.gz`.

This establishes **delayed observable content clearing**, not synchronous
frame-zero conversion at the unload instruction or the next root callback.
The authored slot is fighter Yijiao Sprite3, not main; the first sampled content
has zero total frames and has lost its authored source stamp. Authored slot
provenance must not be equated with a currently loaded authored timeline.

AS2 reference equality and stable paths are recorded observations, not an
engine allocation ID. The receiver's own token disappears, and the four requested
boundaries leave the transition somewhere between periods 8 and 433. We do not
claim that these observations rule out same-path replacement or reference
retargeting within that interval. Mapping zero to authored frame1, or treating
unloaded nodes as exempt, remains unjustified. No sampler/collector/validator
or production runtime is changed.

## Source-first boundary and next discriminator

1. Locked Yijiao Sprite3 frame1 contains only `stop()`; frame2 has no DoAction
   and places AI sensors. Complete relevant script text and child depths are in
   the report. `initCtrl` selects frame2 for AI; the observed non-AI branch goes
   to frame1 and calls unload.
2. Sprite455 frame1 places a new named AImain Sprite3 at depth1 with
   `placeFlagMove=false`; the hash-checked XML placement is retained. This is
   authored slot provenance, not proof of loaded content after unload.
3. Authored frame1 stops; the non-AI branch explicitly unloads. There is no
   authored frame-zero destination. We have not audited unrelated move lifetimes
   for a runtime change.
4. Tests lock the retained native boundary facts and exact authored insertion,
   reject missing/duplicate observations, and keep all frame-zero obligations.
   They do not turn a guessed identity model into an expectation.
5. One native run uses the original s231 tape. All **122 actor rows / 14 fields**
   match retained s249 exactly, including tick0. This is an observation-control
   comparison, not native/Godot parity or a guarantee that probe cost is zero.

Next discriminator: observe every root boundary from this same unload to the
first frame/totalframes=0 transition. Pair those observations with an external
engine identity, or a separately validated control that distinguishes retained
AS2 references from same-path/depth replacement. Determine when content clears
and whether the occupant is retained before proposing a bounded lifecycle model.
No such control or mapping is claimed in this PR.

## Gates and cost

- One native launch: 8,238 full events, one done, no suffix trimming; receipt
  validation exit0. No terminal callbacks occurred after done in this capture;
  the existing display completion window is unchanged.
- Display structure: 61 samples; full display/source gate **exit1**, retaining
  **169 obligations**, including 122 AImain frame-zero obligations across P1/P2.
- Portable diagnosis recomputes from repository archives with exact input,
  built-SWF, instrumentation and XML hashes. It does not reseal historical receipts.
- 53 focused tests pass; integrity, handoff and contracts pass. Commands, actual
  exits and subprocess durations are in `gates.json` / `project-checks.json`.
- Native capture cost: **32.902 seconds** including launch/wait/cleanup; successful
  build **13.539 seconds**. These are measured wall costs, not person-days or total
  session time. See `capture-cost.json` and `native-build.json`.

`development-notes.json` retains the pre-launch build/preflight issues, archive
path correction and initial test type mismatch. None changed the validators or
native observations. Ranks 1/3/4/5, geometry, AS continuation, RGBA, masks/camera,
other AImain families, gameplay and baseline tapes remain untouched. No merge or
deployment.

## Reproduce

From the repo root, no player or external XML cache is needed for diagnosis/tests:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s255/diagnose.py --output /tmp/s255-diagnosis.json
python3 -m unittest tools.tests.test_aimain_unload_identity tools.tests.test_display_source_frame_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_display tools.tests.test_display_completion_default tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

To recapture, use a fresh output directory/run ID with `build_probe.py --ffdec
/tmp/bvn-s66-tools/ffdec/ffdec.jar --output /tmp/bvn-s255-new-build --run-id
s255-yijiao-new`. Then use `python3 -m tools.sampling_native --case
evidence/sampling-upgrade/s231/yijiao__attack__neutral__ground__near.json --build
/tmp/bvn-s255-new-build --trace /tmp/bvn-s255-new-capture/native.log --receipt
/tmp/bvn-s255-new-capture/receipt.json --timeout 180 --allow-window-activation`
(create the capture directory first). The existing serialized native capture
lock is `/tmp/bvn-native-flash-capture.lock`; no lock is removed.

For retained receipt/full-display checks, restore `native-build.tar.gz` to
`/tmp/bvn-s255-r02-build`, decompress the full raw stream to
`/tmp/bvn-s255-r02-capture/native.log`, and restore `native-receipt.json` there as
`receipt.json`. Restore XML paths from `source-exports.json` using s30's common
archive and s233's Yijiao archive. Run the exact commands in `gates.json`. Player:
`/Volumes/Flash Player/Flash Player.app`; all receipt-bound probe files must match.
