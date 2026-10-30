# s258 — AFTER-s253 rank 5: recorded countdown callback

Baseline master `230830ed` / #135; branch `feat/s258-countdown-phase`.
Authority: rank 5 in [AFTER-s253 priority](../next-fix-priority-after-s253.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
**Evidence-only diagnosis and isolated callback replay. No common full visual
phase or production clock adapter is proved.** Ranks 1–4 and s254–s257 are untouched.

## Result

One fresh native capture records the registration and **70 actual firings** of
Sprite1813's one `setInterval(time,1000)` callback, including pre-fight firings.
**15 paused firings do not decrement**, but still update digits. The first such
firing changes digit frames 1/1 to 7/1 while `gametime` remains 60.
The remaining 55 firings decrement to 5. No callback count comes from elapsed
milliseconds, a 30 Hz assumption, or an image search.

All **122 actor tick/payload rows** match the locked s220 capture exactly on all
14 fields, including the original tick0 representation. The full 30,052-event
stream and all 61 unmodified bitmap samples pass the unchanged receipt/structure
validation. The read-only audit replay checks countdown continuity at every
firing and snapshot; [replay.gd](replay.gd) independently executes the **existing
source-compiled** `godot/generated/main/timeout/timer.gd` once for each recorded
firing and matches all 70 post-callback `gametime` and digit-frame observations.
This is not a Godot scene/image replay or proof of other HUD state.

| Snapshot tick | Actual prior firings | gametime | Tens/ones source frames |
| --- | --- | --- | --- |
| 0 | 15 | 60 | 7 / 1 |
| 13 | 25 | 50 | 6 / 1 |
| 60 | 70 | 5 | 1 / 6 |

The old s220 image pair remains **47 / 59 at tick13** and the new native tape
observes **50**. The new events cannot retroactively explain the old native
callback count or repair its missing tape. No historical baseline is replaced.
The observed callback `this` string is `undefined`, whereas the saved defining
clip is `_level0.xuetiao.instance76.instance77`. Digit reads use the defining
clip saved at registration; this does not invent a callback receiver or establish
engine allocation identity from a path. The source closure and positive digit
observations are preserved.

## Capture and snapshot boundary

The s220/s253 archive was inspected first: it does not instrument Sprite1813,
so its registration/firings/guards cannot be recovered from its existing bytes.
A new run was necessary. The s220 case bytes (SHA-256
`e2917f172e1515296264e8773dac79c8542b9b39e65f6631bc8cf4a7644c4eea`)
remain unchanged: Sasuke/Ichigo, same setup, helpers, stage, ticks10–12 attack,
and 0–60 snapshots. No new input, timer reset, or image scheduling is introduced.

[build_probe.py](build_probe.py) invokes the ordinary bitmap builder, then patches
only temporary main SWF script copies:

- Sprite1813 frame1 saves its defining clip, observes both sides of the original
  registration, and observes entry/exit of `time()`. A probe-only ordinal counts
  actual entries. Every authored statement, guard, digit goto and interval call
  remains in its original order; the source-preservation test strips only added
  observer lines and recovers the original source exactly.
- Each record includes ordinal, receiver and defining-clip paths, interval ID,
  gametime, pause, both `sw` guards, mode, digit frames and timer clip frame.
  The full AIREF sequence supplies root display, fight tick and measured clock.
- Two observation calls bracket the unchanged synchronous `image.draw(_root)`.
  Each pair is adjacent in the event sequence and immediately precedes the
  original `bitmap_begin`. All 400 rows and `bitmap_end` remain intact, at every
  tick. No additional actor step or draw await is inserted.

A single callback registration is observed (interval ID5); all 70 paired firings
and 61 paired snapshot markers are retained in [diagnosis.json](diagnosis.json).
Raw log, complete instrumented SWFs, generated patches, instrumentation diff,
source/build hashes and receipt are archived. `runtime_fighter=null` remains an
unresolved loader-attestation limit, not a claim that SWF hashes prove live identity.

The fresh build took **8.99 s**, capture **98.82 s**, and median bitmap encoding
was **1,125 ms** (historical s220: 1,980 ms). These are measured costs, not dispatch
counts or a causal benchmark of instrumentation overhead. Actor equality does
not prove zero observer perturbation. The initial sandbox attempt failed at `ps`
before launching; the authorized escalated attempt completed. Both attempts are
retained. The first ad-hoc Godot invocation used a relative evidence path under
`--path godot` and failed loading JSON; it was interrupted, then rerun successfully
with an absolute path and an explicit temporary log path. No source or expected
result was changed to pass that invocation.

## Source-first boundary and next discriminator

1. Full callback source is locked at `scripts/main.json →
   DefineSprite_1813/frame_1/DoAction.as`, also retained in generated `timer.json`.
   It stops the clip, initializes from maxtime, registers the original callback,
   conditionally decrements, and selects digits on every callback, even paused.
2. This capture records the defining clip and its child frames, but does **not**
   prove the complete PlaceObject/MOVE and independent child timeline history of
   the paired display lists. A stable path/frame is not a lifetime proof.
3. The timer clip remains stopped at frame1 in this finite-mode capture; the
   authored unlimited/training branch is a `gotoAndStop("无限时")`. No label-end
   return or timer catch-up semantics are inferred. Timeout side effects are not
   reached and are outside the isolated compiled replay.
4. Tests lock actual observed callbacks, the paused digit update, original source
   preservation and negative rejection. They do not assume one firing per root
   tick or per elapsed second. Replay deliberately uses no clock arithmetic.
5. The unchanged input was run once in the original player, with 122 actor rows
   equal to s220. That is native/native actor control, not full native/Godot parity.

**Next discriminator:** extend this *same callback-bound snapshot contract* with
source-bound full visual state (timer and digit instance placement/lifetime,
independent HUD/child clocks and camera/display state), then run a paired Godot
scene that consumes the recorded callback events in their observed order around
the unchanged snapshot. Assert those states before taking its image. Do not map
pre-fight firings to guessed actor ticks, reset the HUD at tick0, or transfer this
new tape into the old s220 images. Full visual phase remains unproved until those
state joins pass; only then can residual strict bytes isolate renderer behavior.

No production runtime, gameplay, renderer, thresholds, source inputs, existing
validators or baselines changed. No image offset search, admission, merge or
deployment. No product obligations are closed.

## Verification and reproduction

[Gates](gates.json) contain commands, actual exits and measured durations.
The historical strict RGBA recomputation remains **0/61 exact**, 17,732,741
differing channels / 6,864,492 differing pixels / max255, **exit1**. The unchanged
historical full bitmap CLI also remains exit1 at stale receipt provenance; this
is distinct from recomputing its retained raw bytes. No new visual-pair gate pass
is claimed. Receipt, countdown diagnosis and isolated compiled replay exit0.
All **100 focused tests pass**. Integrity/handoff/contracts results are recorded
in [project-checks.json](project-checks.json).

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s258/diagnose.py --output /tmp/s258-diagnosis.json
python3 -m unittest tools.tests.test_countdown_phase_tape tools.tests.test_rgba_clock_diagnosis tools.tests.test_sampling_bitmap tools.tests.test_sampling_native
/path/to/Godot --headless --path godot --log-file /tmp/s258-replay.log --script ../evidence/sampling-upgrade/s258/replay.gd -- /tmp/s258-diagnosis.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s253/diagnose.py --output /tmp/s258-old-strict.json --strict-rgba
python3 tools/verify.py
python3 tools/check_handoff.py
```

Retained evidence diagnosis needs Python/Pillow and no original player. The
isolated compiled replay uses Godot4.7.2 and the existing generated timer source;
no Timer node, clock schedule or renderer is changed. Use the exact commands in
`gates.json` for the full focused suite and product rejection.

For a new capture, supply Java on PATH and JPEXS26.2.1, fresh paths and run ID:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s258/build_probe.py --ffdec /path/to/ffdec.jar --output /tmp/s258-new-build --run-id s258-new
mkdir -p /tmp/s258-new-capture
python3 -m tools.sampling_native --case evidence/sampling-upgrade/s220/sasuke__attack__neutral__ground__near.json --build /tmp/s258-new-build --trace /tmp/s258-new-capture/native.log --receipt /tmp/s258-new-capture/receipt.json --timeout 600 --allow-window-activation
```

Respect the existing native capture lock. The fresh receipt is case/build/trace
bound; historical receipts are never resealed. For retained receipt verification,
restore the archived build and full raw trace at the paths in `native-receipt.json`
and use its pinned sources/player. Input hashes and artifact hashes remain separate
from the repository's reviewed manifest hash updates.
