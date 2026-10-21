# Deidara L movement expression fix

Base: `875506cff435a30e016c316afbd4641fb492dba4`, branch `fix/didala-l-movex`.
The generic frame compiler previously ignored expression arguments to wrapper
`moveX`/`moveY`. Deidara's ordinary L reached source frame 34 but did not move.
The new compiled arithmetic operand reads the current timeline fields when the
frame event executes. X uses the current facing; Y uses the wrapper's positive
Y convention. Literal calls retain their existing representation and behavior.
There is no character-specific runtime branch or ActionScript execution.

## Before / original / after

Fresh Flash Player Debugger 32.0.0.465 captures, Godot 4.7.2, AI off, current
world, P1 Deidara at X=300, P2 Ichigo at X=800, energy=300. Press the listed keys
at tick 10, release at 11; airborne cases jump at tick 2. Each run has 120 ticks
and 242 observed fighter states. Coordinates are pixels; velocity below is the
change per 30 Hz observation, not the source's clamped collision `vecx` value.

| Input | Original final X | Before final X | After final X | Original movement phase |
|---|---:|---:|---:|---|
| Ground L | 480 | 300 | 480 | Source frame 34: +180 |
| Ground D+L | 480 | 300 | 480 | Source frame 34: +180 |
| Ground A+L | 120 | 300 | 120 | Source frame 34: -180 |
| Ground W+L | 300 | 300 | 300 | Y -25 → -151 → -25; nine -14 steps, then fall |
| Ground S+L | 390 | 390 | 390 | Nine +10 X steps |
| Air L | 480 | 300 | 480 | Source frame 34: +180 |
| Air D+L | 490 | 310 | 490 | Initial +10, then frame 34: +180 |
| Air A+L | 470 | 290 | 470 | Initial -10, then frame 34: +180 without reversing facing |
| Air W+L | 300 | 300 | 300 | Y -90 → -100 → -226 → -25 |
| Air S+L | 300 | 300 | 300 | Y -90 → -100 → -25; downward steps +12, clamped at floor |

All ten cases match exactly on all 14 established fields, at all 2,420 fighter
observations; the six ordinary L cases retain their failing before traces.
`comparisons.json` records complete comparisons, paths and decompressed hashes.
Ground ordinary L remains at Y=-25. Air ordinary L holds Y=-90 until recovery,
then falls by +10 per tick with a final +5 floor clamp. Directional W+L/S+L use
`dash`/`onDashing`, not the ordinary L label. Their old generic target-frame
marker (29–44) is therefore false; captured dashF/coordinates establish actual
execution. No comparator thresholds or reference outputs were changed.

The same compiler rule also restores Deidara's recovery frame 970:
`_parent.moveX((- speed) * 6);`. In the additional input-driven fixture, Ichigo's
ranged attack knocks Deidara down; held L selects recovery, and both Flash and
Godot move X=252 → 192 on tick 55 / source frame 970. All 242 states match.
The changed operand is also tested with a different current speed and both
facings, rather than hardcoding the observed 180/60 distances.

## Source-first answers

1. `scripts/fighter/didala.json`, Sprite 542: source frames 29–43 have only the
   frame-34 DoAction `_parent.moveX(speed * 18);` and the frame-39 receiver
   callback `beida()`. Frame 44 returns to standing and plays. Frame 966 resets
   root Y, 970 executes the negative-speed movement, and 978 returns to standing.
   `source-first.json` retains every relevant frame, including empty scripts,
   labels and display-list changes; the character's existing full source-first
   index retains the entry/controller and knockdown chains.
2. The ordinary dash's visible Sprite 14 at depth 27 is newly placed at 29,
   transformed by MOVE at 30–32, removed at 33, newly placed at 36, and transformed
   by MOVE at 37–39. The root movement occurs while it is absent. The receiver is
   newly placed at 39. No traveling clone carries the fighter. Native child
   observations remain in the original events; movement is a container operation,
   so newly visible children inherit the corrected world position.
3. The exit is an explicit goto/play at 44 (ordinary L) or 978 (recovery), not an
   invented label-end transition. Directional dash ends through `onDashing`.
4. The invariants are the authored expressions, current speed=10, source facing,
   one frame-34 move, and one frame-970 move. Dynamic-speed/unit tests check that
   the compiler does not bake initial speed into the output. Unsupported fields,
   calls, arithmetic syntax and controlled movement statements fail compilation.
5. All ten ordinary/directional/air inputs were freshly recaptured with
   `capture_native_player.py --allow-window-activation`; the extra recovery
   fixture also ran in the same original player. The account-wide lock serialized
   capture with other tasks, and only owned Flash instances were terminated.

## Scope, regression and reproduction

`compiler-impact.json` compares old and new compilers on the same inputs for all
26 generated fighters. Only **didala** changes, at frames **34 and 970**. No other
fighter needs a new expression-movement native case. Some retained generated
contexts already differ from a rebuild with the *old* compiler; those baseline
regeneration differences were identified separately and left untouched.

`checks.json` records final execution, source/runtime hashes, elapsed wall time,
Python/contract/handoff/manifest gates and the protected-function result.
`regressions.json.gz` records the complete retained-roster replay, including the
12 existing Deidara parity cases. Their historical baseline evidence is unchanged.
The final replay passes **216/216 cases and 127,672 fighter states**, including
all **12 existing Deidara cases / 5,784 states**. The new L/recovery cases are
additional to that retained-roster count.
The PR #37 protected function and both existing call sites remain unchanged.
Full character, pixel/audio, Web/browser and AI acceptance remain partial; this
work neither merges nor deploys.

From the repository root, rebuild with:

```sh
python3 tools/importer/compile_ai_context.py --fighter didala --output godot/generated/fighters/didala/ai.json
python3 -m unittest tools.tests.test_frame_movement tools.tests.test_ikkaku_import
"$BVN_GODOT" --headless --path godot -s res://tests/frame_movement_smoke.gd
BVN_CHECK_DIR=/tmp/didala-roster-check python3 evidence/characters/didala/l-movement/replay_saved_roster.py
```

Import Godot resources first. `BVN_GODOT_PROJECT` optionally selects an imported
scratch copy; the default is `godot`. The roster script checks retained fixture
and original hashes before replay. For each new fixture, run
`res://tests/move_case_reference.gd -- <fixture> <output>` and compare with
`tools/probes/compare_mode_reference.py`. Original build metadata, instrumentation,
input fixture, random/clock tapes and capture logs are retained under
`source-builds/`; unmodified before traces and context are under `before/`.
