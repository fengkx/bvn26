# s262 — AFTER-s258 rank 4: callback-bound visual state

Baseline master `624ca5e0` / #139; branch `feat/s262-callback-visual-state`.
Authority: **rank 4 only** in [AFTER-s258 priority](../next-fix-priority-after-s258.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
**Evidence-only. Common visual phase, complete lifetime joining and a production
adapter remain unproved. The paired scene rejects before imaging (exit 1).**
Ranks 1/2/3/5 and s254–s261 are untouched.

## What this adds

The locked s258 archive was inspected first. Its 70 firings and 61 snapshot
pairs contain timer paths and frames, but no initialization history, HUD child
frames/transforms, or camera snapshot values. Those observations cannot be
recovered from its pixels. A single bounded new capture was therefore required;
[build_probe.py](build_probe.py) extends the unchanged s258 builder, original
case bytes, authored callback, and `image.draw(_root)` boundary.

The new run retains **32,227 events, 61 complete bitmaps, 2,194 visual-node rows,
9 frame1 initialization observations and 68 actual callback firings**. Fourteen
paused firings update digits without decrement. All **122 fight actor rows**
match s258 exactly. This does not establish identical pre-fight scheduling,
random consumption, wall time, or observer non-perturbation.

| Tick | Native display | Firings before snapshot | gametime | Tens/ones frames |
| --- | --- | --- | --- | --- |
| 0 | 450 | 14 | 60 | 7 / 1 |
| 13 | 463 | 25 | 49 | 5 / 10 |
| 60 | 510 | 68 | 6 | 1 / 7 |

These are **s262's own events and images**. s258 remains 70 firings / tick13=50;
the historical s220 image pair remains 47/59. No tape is transplanted and no
historical image or receipt is replaced.

## Snapshot contract and lifetime limit

[observer.as](observer.as) adds a bounded observation block immediately before
s258's adjacent `snapshot_before` / `snapshot_after` pair. Each block retains
its native sequence, display, fight tick and callback ordinal. It enumerates the
timer/digits, HUD children to depth 5, and independent root/game transforms.
Each node records role, path, runtime depth, current/total frames, initialization
serial/display where present, X/Y, X/Y scale, rotation, alpha and visibility.
These are observations, not a source-complete display list or playback flags.
No additional draw, root step, timer firing, or HUD reset is inserted.

Timer Sprite1813 and digit Sprite1810 frame1 receive a probe-only initialization
observer, preceding the unchanged authored script. The parser joins each timer
and digit to the latest matching initialization path, source symbol, depth,
serial and display. It rejects missing nodes, changed digits, missing init
records, interrupted observation blocks and mismatched callback boundaries.

**Initialization serial is not birth identity.** The two digit instances begin
with serials 2/3. The ones digit runs frame1 again at ticks12/25/36/46/56;
the tens digit does so at tick57. **All six executions are immediately after
`bitmap_end`, outside the callback brackets.** The preceding snapshot already
reports digit frame1, while still carrying the earlier initialization serial.
Thus selecting a digit frame and executing its frame script are distinct observed
boundaries. Source `gotoAndStop` re-entry is consistent with this trace; an exact
native dispatch mechanism or six new allocations is not proved.
A stable path, depth, frame, or saved AS2 reference also cannot close allocation
identity. `lifetime_proved=false` is intentional.

[source-contract.json](source-contract.json) retains every placement/removal and
label for Sprite1810/1813/1814/1815 from a fresh locked-main SWF XML export, plus
all their script paths. Timer frame1 places digit clips at authored depths 1/3;
frame10 removes them for the unlimited branch. Sprite1814 places the timer at
depth31. HUD Sprite1815 creates its children at frame1 and uses MOVE-only tags
at frames2–10, including the depth33 health container. These source facts narrow
the expected retained instance chain; they do not supply the missing continuous
native allocation/child-clock observations. Runtime depths are Flash's signed
values and are preserved, not silently substituted with authored depths.

## Paired Godot scene, before images

[build_scene.py](build_scene.py) creates a temporary analysis runner from the
unchanged `godot/tests/move_case_reference.gd`. It loads the actual `main.tscn`,
the same fighters/helpers/stage/input and normal intro, and compares 61 observer
snapshots. It selects the existing recorded-timer mode so there is no unrelated
wall-clock countdown. It does **not** reset the HUD, assign native HUD/camera
values, or map pre-fight callbacks onto guessed Godot actor ticks.

[scene_checks.gd](scene_checks.gd) also executes the existing compiled timer
callback through an **isolated audit adapter** in recorded order through each
snapshot ordinal. All **68 outputs** and snapshot countdown values match. This
extends s258's bounded callback proof; it does not bind that adapter to the
production countdown/HUD. The production scene's digits consequently remain at
their authored initialization state in this diagnostic. Their mismatches are
an unimplemented join, not evidence of a newly discovered renderer defect.

[paired-scene.json](paired-scene.json) records every compared native/Godot value:

- HUD outer frame, both delayed health bars, both win child frames, root X/Y and
  camera Y agree at all 61 snapshots. Other enumerated HUD children are retained
  for diagnosis; their complete state and lifetime are **not** admitted.
- Camera X differs at 12 snapshots. At tick13 native X is **-0.05**, Godot **0**;
  native scale is **189.994799804687**, Godot **189.99739990234374**.
- Exact serialized camera scale comparisons differ at 61 snapshots. Some are
  only decimal serialization precision (e.g. tick0 `147.4` versus
  `147.40000000000003`); this record does not classify every scale difference as
  an engine defect or round it away. Tick13 also has the independent X mismatch.
- Countdown digit differences and unresolved lifetime/root-order obligations
  prevent admission. **No new Godot image is written** (`images_written=0`).

The analysis pre-image gate returns exit1, with actual comparison failures and
explicit missing contract obligations. It is not a full bitmap product gate,
a production adapter, or an assertion that actor ticks imply common visual phase.

## Source-first boundary and next discriminator

1. Per-frame scripts: Sprite1813 frame1 stops, initializes, registers and defines
   the guarded callback/digit gotos; Sprite1810 has only frame1 `stop()`;
   Sprite1814 frame1 defines the independent health `onEnterFrame`; Sprite1815
   stops at frames1/5. Full paths/text and frames without scripts are recoverable
   from the retained source contract. Camera source remains
   `scripts/main.json → DefineSprite_1991/frame_1/DoAction.as`.
2. Placement/MOVE facts are retained above. Complete runtime allocation identity,
   independent child advances and root-to-Godot registration joins remain missing.
3. Timer stays at frame1 in all captured snapshots; unlimited frame10 is not
   exercised. Digit `gotoAndStop` and HUD stops are not label-end returns.
4. Tests assert actual source MOVE/removal facts, observed initialization/callback
   joins, source preservation and negative rejection. No visual offset, guessed
   child age, or numeric tolerance is introduced.
5. The same case was run in original Flash and in the actual Godot scene; 122
   native/native actor rows match s258. Full native/Godot visual phase fails and
   no production behavior is changed.

**Next discriminator:** observe timer/digit PlaceObject load/remove identity with
a positive retained-instance versus same-depth replacement control, independently
of DoAction frame1 re-entry. In that same registration-to-first-snapshot window,
record digit target-frame script entry relative to the draw, encoding completion
and next root/callback, with a no-encoding control. Record HUD child advances and
camera tween entry/exit (inputs and assignment values), and the corresponding
Godot intro/root boundaries. First determine
whether tick13's camera mismatch is a boundary/order or arithmetic difference;
then attempt the callback-to-scene join without resetting child clocks. Require
all contract states to pass before taking paired images. No renderer, threshold,
offset search or production clock changes follow from the present evidence.

## Verification, costs and reproduction

[Gates](gates.json) record commands, exits and measured subprocess costs;
[project checks](project-checks.json) record integrity/handoff/contracts.
Receipt, diagnosis and all **111 focused tests** pass. Paired pre-image rejection, unchanged
historical strict RGBA and historical bitmap product gate retain **exit1**.
Strict historical RGBA remains **0/61 exact**, 17,732,741 differing channels /
6,864,492 differing pixels / max255. The historical product CLI rejects stale
receipt provenance; it is distinct from raw-byte recomputation and this new
pre-image gate. Existing strict validators are unchanged.

The bounded build took **9.27 seconds**, including rebuilding s258's base probe;
the one native capture took **99.58 seconds**. See [capture-command.json](capture-command.json)
and [native-build.json](native-build.json). Native capture used authorized
window activation. No second capture was needed. Total person-days are unknown;
measured subprocess costs are not presented as total human effort.

The initial Godot scene invocation lacked the project's generated class cache
and returned parse errors despite exit0; [failure log](scene-initial-failure.txt)
is retained and is not counted as success. A normal headless editor import built
the cache (its settings-save sandbox warnings were unrelated to source), after
which the scene ran to the explicit pre-image rejection with no SCRIPT ERROR.
The first focused-test run also retained a failed assumption that digit frame1
executes inside the callback. The trace disproved it: all six entries occur after
bitmap encoding. [The failure](focused-tests-initial-failure.txt) is retained;
the final test locks the observed sequence instead, without changing any native
record or product validator. Temporary exports, runner and import caches are not
committed as source.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s262/diagnose.py --output /tmp/s262.json
python3 evidence/sampling-upgrade/s262/build_scene.py --output /tmp/s262-paired.gd
# Use absolute paths for environment variables and the fixture under --path godot.
S262_CONTRACT=/tmp/s262.json S262_SCENE_OUTPUT=/tmp/s262-scene.json \
  /path/to/Godot --headless --path godot --log-file /tmp/s262-scene.log \
  --script /tmp/s262-paired.gd -- \
  "$PWD/evidence/sampling-upgrade/s220/sasuke__attack__neutral__ground__near.json" \
  /tmp/s262-actors.json  # expected exit 1, S262_PREIMAGE_REJECTED
python3 -m unittest tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape
PYTHONPATH=. python3 evidence/sampling-upgrade/s253/diagnose.py --output /tmp/s262-old-strict.json --strict-rgba
python3 tools/verify.py
python3 tools/check_handoff.py
```

If the project has no import cache, run Godot `--headless --path godot --editor
--import` first. To reproduce the source contract, export locked `game/main.swf`
with JPEXS26.2.1 `-swf2xml` into `/tmp`, then run `source_contract.py --xml ...
--output ...`. For a new capture use Java on PATH, `build_probe.py --ffdec ...
--output /tmp/fresh-build --run-id fresh-id`, followed by the exact native capture
command in `capture-command.json` with fresh paths. Respect the native capture
lock. Archived receipts are never resealed; archived build and raw trace can be
restored to their original receipt paths for receipt validation.

No production runtime, renderer, gameplay, threshold, baseline or existing
validator edits; no merge, deployment or product obligation closed.
