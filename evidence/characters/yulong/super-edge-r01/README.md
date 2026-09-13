# Yulong down+I super at stage boundaries

## Result

In this controlled `现世` flat-stage test, the original Flash player misses the same two intermediate hits at either wall that the Godot build misses. The move still lands the opening three hits, the six-hit `cbs3` sequence, and the final hit. The evidence does not show a migration-only edge regression for these inputs.

The source command is `bishaSuper` (down + special/I), with 300 energy. Source Yulong places its root at the opponent on frame 734. Main-stage source clamps fighter X to `[20, 970]` (`scripts/main.json`, `DefineSprite_1991/frame_1/DoAction.as`). The exact positions below are recorded at the two missing intermediate attacks. Root X/Y values are from the matched per-tick state comparison; the native hit probe separately records successful source hit packets.

| Fixture | P1 / P2 at the missed attacks | Original selected packets | P2 final HP | Godot states |
|---|---|---:|---:|---|
| Center, initial x450 / x500 | at root frame 793: x500 / x654; at 807: x500 / x676 | 12 total; includes `cbs2atm@793` and `cbs1atm@807` | 360 | 1202/1202 rows, 0 field differences |
| Left wall, initial x70 / x20, outward | at 793: x128 / x20; at 807: x128 / x20 | 10 total; no selected packet at 793 or 807 | 480 | 1202/1202 rows, 0 field differences |
| Right wall, initial x920 / x970, outward | at 793: x862 / x970; at 807: x862 / x970 | 10 total; no selected packet at 793 or 807 | 480 | 1202/1202 rows, 0 field differences |

The later sequence still hits on both walls: source packets at root frames 889, 893, 897, 901, 905, 909 (`cbs3atm`) and 913 (`cbsatm`). Thus this result is limited to the two intermediate attacks, not a claim that the super's later portion misses wholesale.

## Cases and evidence

Fixtures are in `cases/`. Original raw `AIREF|...` traces are `mid50-r02.events.jsonl`, `left-original.events.jsonl`, and `right-original.events.jsonl`; despite the suffix, these are raw pipe-delimited Flash trace lines. Corresponding `.normalized.events.jsonl` files are the JSONL normalization consumed by `tools/probes/compare_mode_reference.py`. `*.godot.json` are native replays; `*.comparison.json` preserve exact field comparisons. Build inputs and instrumentation diffs are retained in `builds/`; per-run right capture environment is `right.capture-environment.json`.

The first center attempt (`mid50-original.events.jsonl`, `mid50-r01-attempt.json`) is invalid: the Flash trace configuration was absent and it captured no run events. It is retained as a failed attempt and excluded from the comparison. The successful center run uses fresh run id `yulong-super-mid50-r02`.

All three successful originals completed 600 fight ticks (`done=true`): center 16,968 events, left 17,955, right 18,143. The Yihu receiver probe emits only successful selected packets and reuses the original hit-test result. It does not log live Flash `getBounds()` rectangles; no exact attack/receiver AABB measurement is claimed here.

## Scope and environment

- P1: 石田; P2: 一护; P2 CPU disabled; helpers explicitly set to 我爱罗 / 魂; stage 现世; mode 3; 300 initial energy.
- Input: down + special at fight ticks 10–13; 600 ticks captured through move recovery.
- Source files under `game/` and `scripts/` and baseline thresholds were not modified. No runtime or collision code was changed for this investigation.
- Flash Player capture ended with `done=true`; the temporary `~/mm.cfg` was removed afterward, restoring its initial absent state.
- Godot 4.7.2 headless replay emitted an environment CA-certificate warning, but each replay completed with `MOVE_CASE_REFERENCE_OK`; the source-state comparison is exact for 14 recorded fields.
