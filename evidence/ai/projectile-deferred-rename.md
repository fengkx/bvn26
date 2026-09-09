# Deferred projectile names and source attack lookup

Status: both retained independent 600-fight-frame segments pass their
discrete-field comparison. Full match and presentation parity remain open.
This resolves the r14 frontier in
[the preceding report](effect-registry-and-root-observer.md).

## Source and lifetime

Naruto base frame 382 places a new Sprite 260 projectile named `zh1atm`.
Its placement load initializes `played=0` and `movspeed=_parent.speed*2`.
The placement callback tests the opponent's body/projectile properties; on
first collision it sets played=1, speed=0 and calls `gotoAndPlay(5)`.

Sprite 260's complete exported DoAction inventory is frame 3 `stop()`, frame
5 `this._name="abcd"`, and frame 11 `stop()`. Other sprite frames have no
DoAction. These paths and authored membership are already present in
`godot/generated/fighters/minren/player_controller/controller.json`.
Ichigo's compiled projectile carries the same named-frame mechanism. There
is no new per-character runtime branch or hand-authored attack exception.

`DefineSprite_2/frame_1/DoAction.as → getHitObj` resolves the opponent's current
named property. A visual instance still displayed under the authored timeline
name is not proof that the source property `zh1atm` still exists.

The [native rename probe](../probes/schedule/projectile-rename/comparison.json)
shows that the old name remains visible after goto returns, and becomes
undefined only when the target frame script runs. The new `abcd` property is
then visible. The [removal extension](../probes/schedule/projectile-rename-removal/comparison.json)
also verifies that removing another clip before its queued frame-5 script
prevents that script from executing.

```sh
python3 tools/probes/build_effect_attach_probe.py --probe effect_rename --ffdec /tmp/bvn-ffdec-26.2.1/ffdec-cli.jar --output /tmp/bvn-projectile-rename-new
```

## Native implementation

Each source projectile instance now owns its current source name separately
from its authored rendering identity. Reached rename scripts enqueue a typed
operation; they do not rename immediately when the playhead changes. These
operations share the actor target-frame FIFO sequence in Main. The original
root observer still runs before deferred target scripts.

Source attack lookup and projectile collision lookup both resolve this live
name. Before frame 5 executes, the first body hit can still find `zh1atm`.
After frame 5 executes, the same query returns no box, while a query for
`abcd` resolves the retained visual instance. This fixes the r14 repeated hit
without restoring a per-attack consumed-hit cache.

Operations for removed instances are canceled. A retained old object also
checks its source placement generation before applying the operation, so it
cannot rename a replacement instance at the same authored path. Driver
shutdown clears name bindings, queue connections and pending operations.
Missing child-frame queue integration fails explicitly when a compiled
rename is reached. Legacy standalone projectile lookup retains its existing
behavior outside the source driver path.

## Results

[Retained reports](projectile-rename-validation/) use the unchanged r13/r14
input, random and clock tapes. Both runs finish without script errors and
consume every expected boundary/random/clock record.

| Capture | Boundaries | Post-checkpoint random draws | Frame-pair snapshots | Frame/state differences |
|---|---:|---:|---:|---:|
| r13 | 1,166 | 298 | 897 | 0 |
| r14 | 1,084 | 287 | 867 | 0 |

Each segment contains 600 fight frames and a partial post-load intro prefix.
The initial checkpoint is still not full boot. r14's prior 3 px extra hit
movement disappears. Remaining maximum relative position differences are
`3.0517578125e-5` for P1 X, `2.4414062522737368e-5` for r14 P2 X, and
`1.5258789076710855e-6` for r14 P2 Y. No comparison tolerance or coordinate
correction was added. Small native single-precision offsets are not certified
as exact source geometry.

[Six native tests](projectile-rename-validation/checks.json) pass: projectile
callback/name lifecycle, player controller, repeated source contact, Vs Com
entry, KO flow and player lifecycle. The projectile regression checks old/new
names on both sides of the deferred script, retained name through later
frames, and isolation after same-tick removal/recreation. Some native tests
still report resource-exit or certificate warnings.

Full-match reference capture through KO and round reset, further action and
random paths, exact coordinate storage/collision arithmetic, visual/audio
comparison, and the Web browser matrix remain required. Two passing short
segments do not complete M5-03 or establish one-to-one gameplay.
