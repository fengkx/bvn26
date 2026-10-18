# Orochimaru / 大蛇丸 (orochimaru), 2026-10-18

Base: `786c058d`, branch `feat/orochimaru`. Coverage is **partial**.
The single base form is source-compiled and selectable locally and in the online
catalog. Sprite 541 contains 1,364 frames and 141 indexed body scripts. The
locked SWF is 434,653 bytes. Controllers, body callbacks, receiver, timeline,
geometry, sounds, original five-frame portraits/footer and natural opening are
included. Existing four helpers remain unchanged; the default assist is outside
this fighter-port acceptance. No Worker deployment was performed.

The character was selected in advance because its Sprite 16 controller, Sprite 2
receiver and body frame-1 implementation match Renji exactly, as with Gin/Chad.
No character-specific runtime branch or guessed movement/hitbox was added.
The slice extractor now retains intermediate numbered normal labels in source
order within the existing combo slice. This preserves `砍1 -> 砍11 -> 砍2 -> 砍3`;
all 16 earlier fighters retain identical action classifications. Later normals
remain in `extended_actions`, preserving the existing slice contract.

## SOURCE_FIRST five questions

1. `data/slices/orochimaru-base.json` indexes every body script at its original
   `scripts/fighter/orochimaru.json` path. `orochimaru-base.timeline.json` retains
   every frame, including empty frames. Shared controller/receiver/body equality
   is asserted in `tools/tests/test_orochimaru_import.py`. The existing shared
   receiver audit still covers all 35 fighters and the 26 helpers without that
   receiver chain.
2. Timeline new placements, MOVE, depth, matrices and removal remain intact.
   Combo callbacks are placed at 211–215, 231–236 and 259–265, each starting on
   the tick after placement. Other examples are body motion at 306–310 and
   590–608, guard receiver at 1079, and hurt motion at 1104. Child targeting at
   397 (`zh1atm`), 489/493 (`zzz1`/`kj2atm`) and 710/714 (`zzz1`/`sbsatm`) is
   source-derived; visible effects are not substituted for hitboxes.
3. Normals explicitly return at 221/241/273/299. Supers return at 651/758/995;
   their pause/face pairs are 540/588, 671/704 and 779/849. Guard recoil returns
   at 1099; ordinary hurt calls `onBeHit` at 1103, stops at 1108 until `beidax`
   releases it, and returns at 1112. Flying hurt calls `onBeHit(true)` at 1116.
   Jump-ranged labels naturally fall through at 172 and 182; no label boundary
   is treated as an invented standing exit. Opening writes `kcplayed` at
   1187/1189/1275 and returns to standing at 1275.
4. Assertions use the source transitions, placement lifetimes, `gjl1` packets,
   1091 `onDefence(1)`, receiver frames and super events. New import checks cover
   the intermediate normal and exact receiver/super frames. No threshold,
   source input, expected trace or combat constant was changed to obtain parity.
5. Eight native Flash same-input cases match all **3,856 states** (482 each)
   over the existing 14 exact fighter fields. Both sides use AI off, current
   world, Orochimaru versus Ichigo, explicit Gaara/Kon helpers and identical
   setup/input. Original traces and native traces are retained compressed under
   `traces/`; per-run build identity and LoadVars payload are under
   `source-builds/`. Hashes and observations are in `comparisons.json`.

## Focused parity

| Case | Result | Actual source coverage |
| --- | --- | --- |
| combo | 482/482 | Four-hit chain, defender reaches hits=4 and HP=760 |
| cancel-super | 482/482 | Source frame 260 at tick 50 -> super frame 534 at tick 51 |
| interrupt | 482/482 | Orochimaru normal interrupted; HP=960, hits=1 |
| guard | 482/482 | Ichigo guards the normal; HP=998, hits=0 |
| receive-guard | 482/482 | Orochimaru guards then receives guard break; HP=916, hits=1 |
| super-guard | 482/482 | Normal super chip; defender HP=974, hits=0 |
| ultimate-guard | 482/482 | Ultimate against guard; source break/knockback and pause |
| upper-super | 482/482 | Targeted upper-super hitbox positioning and hit |

The comparator checks frame, x, y, xscale, action, hp, ql, sw, touch,
touchFloor, hits, paused, hstm and hurtSkling, plus alignment/completeness.
It does not establish pixel, audio, full AI, every move or exhaustive cancel
boundary parity. The final check record is `checks.json`. All 103 saved cases across the 16
existing fighters also match 65,726/65,726 states; see `regressions.json`.
Python: 307 passed, 2 skipped. Nine existing Godot checks plus the dedicated
rollback check pass (the documented headless audio shutdown warning remains).
Local matchmaking: typecheck and 31/31 tests pass. Handoff, locked-input hashes,
online manifest and six contract schemas/examples pass.

**Retained Flash deviation:** the existing shared
`FighterRuntime._clear_interrupted_super_preparation` clears the orphaned `bs`
lock when a real hit interrupts preparation before super pause. The user
explicitly requires retaining this anti-deadlock fix. This PR neither introduces
nor changes it. Its protected 544-byte SHA-256 remains
`d39b2b50d96d37ac717e1d1e8e9ccd711a67f6bbadcee6afc30593d6e0caa91e`.

The matchmaking Worker must be redeployed separately to accept the new catalog.
This PR updates its catalog and client fingerprints only. Full visual/audio,
browser, AI, remaining move/cancel boundaries and the default assist remain
outside this partial acceptance; milestones remain pending.

## Reproduce

Use the unchanged locked inputs, Python 3.10+, JPEXS 26.2.1 and official Godot
4.7.2. See `docs/OPERATIONS.md`: extract 大蛇丸, export `orochimaru.swf`, extract
Sprite 541, build `orochimaru-base` combat and materialize to
`godot/generated/fighters/orochimaru`. Compile player controller and body with
`--player` into `player_controller`, the player body convention into
`player_body`, and AI controller/body into `ai_controller`. Compile context
`ai.json`, hit state, hurt voice and sound segments. Generate portraits/footer
to a temporary directory and merge only 大蛇丸 into the production indexes.
Run `tools/build_online_manifest.py` after both catalog updates.

The current full `build_intro.py` hits a pre-existing main HUD mask-1751
extraction limitation. This port used its unchanged per-fighter compilation
block only, preserving all existing main opening assets. Reproduce that bounded
compilation after materializing the fighter:

```python
import json, sys, textwrap
from pathlib import Path
sys.path.insert(0, 'tools/importer')
import build_intro
spec = json.loads(Path('evidence/intro-source.json').read_text())
source = Path('tools/importer/build_intro.py').read_text()
block = source[source.index('        for name in candidates:'):
               source.index('        # Keep decompiled evidence')]
exec(textwrap.dedent(block), dict(vars(build_intro), candidates=['orochimaru'], spec=spec))
Path('evidence/intro-source.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
path = Path('godot/generated/main/intro/intro.json')
runtime = json.loads(path.read_text())
runtime['fighters']['orochimaru'] = {
    k: v for k, v in spec['fighters']['orochimaru'].items()
    if k not in ('scripts', 'frames')}
path.write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + '\n')
```

Build the dynamic original probe with `tools/probes/build_ai_reference.py`
using `--p1-character 大蛇丸 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂
--frames 240 --dynamic-move-case --move-case
 evidence/characters/orochimaru/cases/combo.json`. Run `test_move_cases.py` and
`test_move_references.py` with that same case directory. Pass
`--player-app '/Users/fengkx/me/code/flash-player/Flash Player.app'
--allow-window-activation` to the capture runner. It uses `open -g`, temporary
instrumented copies, and the account-wide lock; Flash can still raise windows.
The player is Adobe 32.0.0.465; executable SHA-256 is
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
Raw workspaces/captures and downloaded toolchain remain under `/tmp/orochimaru-*`.

Replay the saved 103-case roster corpus with `docs/REGRESSION_INDEX.md`.
Run `res://tests/orochimaru_rollback_smoke.gd` for natural production opening,
checkpoint/replay through ultimate pause/guard break, delayed guard-input
correction and source next-round reset. The test budget allows the longer
source opening; it does not shorten source frames. Run the existing Python,
selected Godot, online manifest, local matchmaking and handoff checks recorded
in `checks.json`.
