# s253 — Rank 5: strict RGBA / clock alignment

Base `d7751dbf`, branch `feat/s253-rgba-clock`; exclusive s253 was absent at
start. Evidence-only diagnosis of the **existing s220 native/Godot pair**, using
the unchanged s217 Sasuke attack tape. No new capture, receipt, gameplay,
renderer, timer adapter, validator, threshold or baseline change.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.

## Finding

**The actor sampling boundary agrees at tick 13, but the countdown clock does
not. A common visual phase is not established, so no clock fix is proved.**
The same `root-observer` string in two manifests is not a clock equivalence proof.

Rank-5 context was reviewed in s217/s231/s238 and their linked results. s217's
accepted bitmap pair is s220 (0/61 exact); s231's ordinary receipt failed its
completion boundary, while its independent s234 bitmap pair also has 0/61
exact and a previously observed 47/59 countdown. s238's ordinary receipt passes
but explicitly leaves independent-run clock equivalence open. This slice uses
only s220 for detailed diagnosis; it does not reopen s241–s244 or ranks 1–4.

The unchanged s217 and s220 fixture bytes have SHA-256
`e2917f172e1515296264e8773dac79c8542b9b39e65f6631bc8cf4a7644c4eea`:
P1 Sasuke x=100, P2 Ichigo x=150, attack ticks 10–12, 60 ticks, same helpers and
stage. Native raw bytes are checked against the original receipt's trace hash;
case, build, archives and source/runner inputs are pinned in `input-sha256.json`.
The old receipt is never resealed with today's probe hashes.

## Paired phase, rather than a pixel-selected offset

`diagnose.py` revalidates the complete raw native stream, losslessly decodes all
61 native images, validates all Godot image hashes with the unchanged adapter,
and joins the saved per-image actor states by exact tick and slot. No nearest
image search, crop, registration, resize, gamma change or channel tolerance.

- All 120 actor rows at ticks 1–60 match all 14 recorded fields exactly.
- Tick 0 retains two representation differences: native `touchFloor=undefined`
  versus Godot JSON `null`. They are reported, not silently equated.
- Every restarted Godot run has exactly the same saved actor-state prefix as
  the final run. This checks the recorded actors, not HUD/child-clock identity.
- At tick 13, both sides have P1 source frame **205**, P2 **7**, x=100/150,
  y=-25, action=1/0, HP=1000, energy=300, hits=0 and paused=false.
- Native actor observations are sequence **8892 / 8896**, then bitmap begin
  **8900**, end **9301**, all display **477**, tick **13**. The original image
  is drawn synchronously before bitmap_begin; encoding continues afterward.
- The next native key reads are after bitmap_end. The Godot terminal observer
  returns before deferred frame work and then requests a viewport readback.
  Actor agreement does not establish child display lists or timer callback phase.

The selected full original images are directly reviewable:
[native tick 13](../s220/native-tick013.png) and
[Godot tick 13](../s220/godot-tick013.png). Native countdown reads **47**, Godot
**59**. This is a manual reading of retained images, not an OCR assertion or
acceptance gate. The script retains it explicitly as such.

## Clock diagnosis and source boundary

The exact native timer source is
`scripts/main.json → DefineSprite_1813/frame_1/DoAction.as`. It calls `stop()`,
initializes `gametime=maxtime`, defines `time()` and registers
`setInterval(time,1000)` unless unlimited/training. The callback decrements
only when `zhanting == false`, both fighters' `sw == false`, and `modo != 4`,
then updates the digit clips with `gotoAndStop`. Thus elapsed callbacks are an
independent input, not 30 actor ticks per decrement. The generated source text
is retained in `godot/generated/main/timeout/timer.json`.

The retained native instrumentation diff does not instrument Sprite1813. The
capture scope only names `getTimer` in hurtVoice; it contains no countdown
callback tape. `sampling_bitmap.as` draws `_root` and synchronously encodes
240,000 pixels plus 400 trace rows **on every root observation**. Raw event
clocks show a median begin-to-end encoding interval of **1,980 ms**. Tick 0 to
60 bitmap-begin spans **120,118 ms**; tick 13 spans 50,791–52,742 ms for encoding.
These are measured wall-clock intervals, not a count of dispatched intervals.
They expose why a 60-tick capture cannot stand in for two seconds of wall time.
No claim is made about timer catch-up/coalescing or its exact dispatch PC.

The Godot bitmap runner creates a fresh scene for **each** requested image and
calls `_advance_fight` synchronously through that tick before awaiting a draw.
It sets `recorded_training_timers`, but never sets `ko_recorded_timers`; these
are distinct controls. `main.gd::_start_countdown` passes the latter (default
false) to `MatchCountdown.configure`, which starts a wall-clock `Timer` with
`PROCESS_MODE_ALWAYS` and `ignore_time_scale=true`. Disabling the game parent
for readback is therefore not proof that this Timer cannot fire during the
await. `_drive_source_timers` concerns the KO nextfight timer and is not a
recorded countdown tape; this fixture does not opt into it anyway.

**Isolated:** a concrete non-common HUD clock state despite a matching actor
boundary. This rules out treating this pair's entire discrepancy as a simple
actor tick shift or as exclusively rasterization. **Not isolated:** how many
pixels belong to timer drift, independent child phases, camera/composition or
rasterization. Edge differences are visible, but this PR does not label their
cause. The evidence cannot justify replaying guessed 1000/30 deadlines, resetting
the HUD, disabling native timers, or offsetting all image indices.

This is observer diagnosis, not a game-mechanism implementation. The source
callback, capture order and identical tape are identified; full per-frame
PlaceObject/MOVE/child-clock equivalence is absent. The source-first runtime
implementation gate is therefore not satisfied and no runtime is changed.

## Checks, negative proofs and remaining gates

`diagnosis.json` retains all 61 timing windows and actor differences. The strict
RGBA recomputation uses existing `collect`, `godot_images`, and `difference`
functions, and checks every per-frame result equals the old comparison:
**0/61 exact; 17,732,741 differing channels; 6,864,492 differing pixels; max 255**.
The `--strict-rgba` invocation returns **1**. A diagnosis invocation without that
flag returns **0**, meaning evidence recomputation only.

The full current receipt/bitmap CLI is also attempted, with its actual failure
retained in `gates.json` and the gate logs. Historical receipt validation on a
new worktree/probe revision is distinct from raw-structure and byte recomputation;
no fresh receipt pass is claimed. The original s220 negative proofs remain
unchanged. Focused tests retain all sampling negatives and add broken sequence,
nonmonotonic clock, missing actor, and shifted-tick checks. They never promote
matching actor fields to visual parity.

Before implementing a clock adapter, record this exact countdown callback's
registration, each actual firing, phase relative to the root snapshot, guards,
`gametime` and digit frames, then replay those events with the unchanged actor
inputs and captured random/clock tape. Bind both images to full visual state at
the chosen boundary. Only then test whether remaining bytes isolate rendering.
Capture cost must itself remain measured; do not derive callback counts from
wall duration. Full child/camera/render equivalence and production admission
remain blocked. No source obligations are closed by this diagnosis.

## Reproduction

All inputs already live in the repository. Archives are read without restoring
historical absolute paths or writing into original evidence. Requires Pillow.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s253/diagnose.py --output /tmp/s253-diagnosis.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s253/diagnose.py --output /tmp/s253-strict.json --strict-rgba
python3 -m unittest tools.tests.test_rgba_clock_diagnosis tools.tests.test_sampling_bitmap
python3 tools/verify.py
python3 tools/check_handoff.py
```

Exact subprocess commands, exits and measured durations are in `gates.json` and
`project-checks.json`; elapsed session time is in `session-timing.json`.
No merge, deployment, earlier-slice modification or admission claim.

Final verification: **88 focused tests pass**. Integrity, handoff and contracts
all exit **0**. Raw-capture structure and diagnosis recomputation exit **0**;
strict RGBA, current receipt validation and the full bitmap gate remain **1**.
The initial receipt CLI invocation omitted capture arguments and returned usage
exit 2; it is retained as `initial-receipt-cli-usage.txt`, then corrected to a
read-only `validate()` invocation (exit 1: changed capture/build/engine/probe
artifacts). It did not launch a player or alter the receipt.
