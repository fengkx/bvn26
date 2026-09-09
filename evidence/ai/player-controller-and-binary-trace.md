# Source player controller and exact trace numbers

Status: native source integration and focused regressions passed; full Vs Com
parity remains unverified. P1 is base Naruto, P2 is base Ichigo, difficulty is 5
(easy). All original inputs and earlier random tapes remain unchanged.

## Source-derived changes

- `scripts/fighter/minren.json`, `DefineSprite_16/frame_1/DoAction.as`: retain
  the `!useAI` branches and the ten `kis` key reads. The compiler emits the
  original 27 predicates, eight dispatch functions, and 39 placed controller
  callbacks. The player now uses these controllers instead of legacy input
  action selection. The existing player BODY compiler supplies 11 functions.
- Controller membership, placement identity and callback lifetime come from
  `godot/generated/fighters/minren/timeline.json` and the exact ClipAction
  paths in generated `player_controller/controller.json`. Both fighters share
  the source callback registry. The production player no longer runs a second
  manual incoming-hit pass or automatic opponent-facing update.
- Naruto `DefineSprite_764/frame_382/PlaceObject2_260_28/CLIPACTIONRECORD
  onClipEvent(load).as` initializes `played=0` and `movspeed=_parent.speed*2`.
  The compiled projectile samples speed once at placement; it must not reread
  changing speed on later enterFrame callbacks. Sprite 260 stops at frames 3
  and 11 and renames itself at frame 5; full renamed-instance behavior remains
  outside this validation.
- Deferred actor frame scripts carry a global enqueue sequence. In r12,
  sequences 7086–7098 demonstrate P2 frame 35 executing before P1 frame 991,
  then P2 frame 1. Initial actor batches precede deferred targets; deferred
  targets drain in enqueue order rather than whole-actor batches. This is a
  fixed-slice integration rule, not proof of a complete world event queue.
- Both compiled BODY objects are now bound to `FighterRuntime.source_body` and
  cleared on driver shutdown. `onBeHit` in both base frame-1 scripts calls
  `updateDirect(true)` after damage, while `onDefence` uses `updateDirect()`.
  The hit adapter now preserves that argument. `true` uses the opponent's
  facing, which differs from facing toward the opponent's position on a cross-up.

Source-frame settlement remains the existing compiled `on_be_hit_frames`
chain. For Ichigo, frame 738 plays, 739 calls `onBeHit`, the new frame-740
controller calls `beidax` from its next callback, and frame 744 stops. This fix
does not add a new reaction or change those placement/lifetime rules.

## Trace precision

FP32's default decimal string drops low binary64 bits: `80/15` prints
`5.33333333333333`, but its stored value is `5.333333333333333`. The analysis
probe now emits `f:sign:exponent:high:low`, with a normalized 53-bit significand
split into 27- and 26-bit integers. Random return values, sampled AI fields,
HP/QL boundaries and state geometry use this encoding; other diagnostic
fields still use the older decimal representation.

The source encoder changes only serialization, not the value returned to the
game. Python and GDScript decode the tokens; comparisons remain exact.
Old r12 logs are retained as captured, without rewriting rounded values.

[Native number evidence](../probes/schedule/number-encoding/comparison.json)
covers seven values. The source fixture's `-0` is emitted as positive zero;
signed-negative-zero decoding is a separate decoder test, not an FP32 result.
Rebuilding the probe produced the same SWF SHA-256 as the captured fixture:

```sh
python3 tools/probes/build_number_encoding_probe.py --ffdec /tmp/bvn-ffdec-26.2.1/ffdec-cli.jar --output /tmp/bvn-number-new
python3 -m unittest tools.tests.test_ai_capture_boundary
```

## Retained comparisons

Reports and native logs are in [player-controller-validation](player-controller-validation/).

| Report | Actual result |
|---|---|
| r12-player-controller | First 634 boundaries match; boundary 635 exposes deferred actor order |
| r12-deferred-fifo | First 721 boundaries match; boundary 722 exposes decimal HP/QL trace precision |
| r13-before-facing | 620 boundaries match; missing XG_qdj random consumer; earlier P2 facing and 54 px displacement mismatch |
| r13-hit-facing | 620 boundaries match; same missing random consumer; P2 facing and displacement differences removed |

These reports are successive diagnostics, not passing golden traces. r13 is
a fresh original run with its own random tape; its boundary count cannot be
compared numerically to r12 as a measure of regression or progress.

[r13 capture](input-binary-r13/summary.json) contains 600 fight frames, 1,486
BODY boundaries, 354 random draws, 69 AI samples, four clock reads, and 3,924
verified key reads. Ready is display 484. Native comparison begins at a
partial post-load checkpoint, not boot. The capture summary's historical
"not compared" note describes collection time; the reports above record the
subsequent failed native comparisons.

After the facing fix, 485 geometry snapshots per actor have no Y or facing
difference. P2 relative displacement matches; P1 still has a maximum
`3.0517578125e-5` relative X difference from native single-precision positions.
Absolute initial position differences remain. No tolerance was added and
geometry parity is not certified.

## Next source-backed failure

`scripts/main.json`, `DefineSprite_256_XG_qdj/frame_1/DoAction.as` contains:

```actionscript
_root._x = 1;
_X = _X + (Math.random() * 10 - Math.random() * 10);
_Y = _Y + (Math.random() * 20 - Math.random() * 30);
```

The current hit-effect compiler drops the two random expressions. The r13
tape expects their four calls (original indices 214–217, sequences 6004–6007)
after P2 frame 739 exits and the root state snapshot. Native replay instead
reaches the next AI refresh at replay draw 158. The next implementation must
compile the expressions and schedule the attached effect's frame script;
inserting four synthetic draws into the AI timer would conceal the defect.
Frame 2 resets root X/Y and frame 19 unloads the clip. Full effect event
ordering and presentation remain pending.

## Validation scope

[checks.json](player-controller-validation/checks.json) records seven native
tests with expected completion markers and no script errors: CPU driver,
player controller, player lifecycle, Vs Com entry, KO flow, binary number
decoding and hit settlement. The collector has seven passing Python tests.
Player controller tests cover held/released keys, simultaneous opposite keys,
source goto priority and projectile load-time speed. Settlement tests cover
both base characters' cross-up facing. Generated player files rebuild exactly;
CPU generated GDScript is unchanged, with only `input_mode` metadata added.

Native logs still include macOS certificate initialization warnings and some
resource-exit warnings. No new Web/browser-matrix acceptance was performed.
Full boot, all source RNG consumers, complete match/round lifecycle, visual
and audio comparison remain open. M5-03 is not complete.
