# Yulong projectile and clip-placement runtime validation

Run date: 2026-09-13. The original Flash captures and move fixtures were not
changed. All port replays used Godot 4.7.2 headless with the complete two-fighter
GameWorld.

## Source-grounded fixes

- `scripts/fighter/yulong.json`, `DefineSprite_345/frame_137/PlaceObject2_74_28/CLIPACTIONRECORD onClipEvent(enterFrame).as`: the air projectile advances by local `_X += 20`, `_Y += 10` only in the `else if (played == 0)` branch. On hit, that same `played == 0` block writes `played = 1` before `gotoAndPlay(5)`. The compiler retains literal local deltas, the miss guard, and the hit block identity/order; runtime evaluates that guard once. Losing contact after impact no longer moves the spent projectile.
- `scripts/fighter/yulong.json`, `DefineSprite_345/frame_466/DoAction.as`: `shijie._x` is assigned at source line 3 before `_name = "zh2atm"` at line 9. The compiled clip placement now executes in source order before the root rename; the live projectile alias follows the root rename and then its child-frame rename.
- Projectile hit guards use absolute source block offsets, not equal condition arrays, to associate a one-shot write and child goto. Independent `if (played == 0)` blocks remain separate. Unknown nested guards fail compilation.

## Fixed-capture replays

All ten catalog fixtures were rerun with `tools/test_move_cases.py`, then compared
field by field against their retained original event captures. Result: 10/10
complete cases matched, each with 602 observations and zero differences. The four
targeted regressions also passed individually:

| Case | Original capture | Current GameWorld output | Result |
|---|---|---|---|
| Air jump attack | `catalog-next-flash/captures/air-jump-attack/events.jsonl` | `/private/tmp/yulong-native-batch-20260912/debug/gamework-current-20260913-final/yulong-air_jump_attack.json` | 602/602, exact |
| Ranged down | `catalog-next-flash/captures/ranged-down-r02/events.jsonl` | `/private/tmp/yulong-native-batch-20260912/debug/gamework-current-20260913-final/yulong-ranged_down.json` | 602/602, exact |
| Ranged repeat, neutral side (three casts) | `catalog-next-flash/captures/ranged-repeat-neutral-r02/events.jsonl` | `/private/tmp/yulong-native-batch-20260912/debug/gamework-current-20260913-final/yulong-ranged_repeat_neutral.json` | 602/602, exact |
| Ranged repeat, mirrored side (two casts) | `catalog-next-flash/captures/ranged-repeat-mirrored-r02/events.jsonl` | `/private/tmp/yulong-native-batch-20260912/debug/gamework-current-20260913-final/yulong-ranged_repeat_mirrored.json` | 602/602, exact |

Before these fixes, the retained catalog GameWorld comparisons reported 1,232
different fields for air jump attack and 746 for ranged down:
`catalog-next-flash/gamework/yulong-air_jump_attack.comparison.json` and
`catalog-next-flash/gamework/yulong-ranged_down.comparison.json`. The separate
skill1 root-relative warp correction is covered by its 602-observation exact
replay in `/private/tmp/yulong-native-batch-20260912/debug/skill1-after.json`.

The unchanged shared replays also pass: r13 reports 897 frame comparisons and
1,794 actor snapshots; r14 reports 867 frame comparisons and 1,734 snapshots.
Both consumed their original random and clock tapes. Reports and logs are under
`/private/tmp/uryu-runtime-regressions/current/{r13,r14}/`.

`python3 -m unittest tools.tests.test_uryu_compilers` passes 10 tests, including
independent equal guards and unknown-guard rejection. The projectile instance
variable smoke passes. Godot's editor scan reports no script parse errors; it
does emit host certificate and editor-settings write warnings from this
headless environment.

## Reproduction and hashes

The 10-case replay command was:

```sh
python3 tools/test_move_cases.py \
  --godot /private/tmp/bvn-toolchain-2026-09-12/Godot.app/Contents/MacOS/Godot \
  --cases /Users/fengkx/me/code/bvn2_6/evidence/characters/yulong/catalog-next-flash/cases \
  --output /private/tmp/yulong-native-batch-20260912/debug/gamework-current-20260913-abs
```

Current source hashes:

| File | SHA-256 |
|---|---|
| `tools/importer/build_combat_model.py` | `d88fd3a9bda33355c0ddb6a52c9b8b4828b03b9ad88e661dab25983b75a88ffb` |
| `godot/fighter_runtime.gd` | `1e42dbdda58bfbe5ad88c0d5c5d89a7d6471ea266086b8a228cf2f53737b4f38` |
| `godot/ai_controller_host.gd` | `5123a79d3232ca32a6cb917724a32d8d6bae5bae21bce538c4727ca21d069f17` |
| `tools/tests/test_uryu_compilers.py` | `5e9236bd9050367b43596fcfa9223f1fb0035fe37b564afb35b4f51aaae50d38` |
| `godot/generated/fighters/yulong/combat.json` | `73bce2cfea95698e355a6d914912b3ddc00c0c69919148cf05ef97b5681b8116` |
| `godot/generated/fighters/yulong/ai_controller/controller.json` | `527c7dafa616aaaaf139faf2e68f3ef45448cf19b88a1aad07eb09e0624a9b20` |
| `godot/generated/fighters/yulong/player_controller/controller.json` | `0e0b89813053fc70e40a987a01a9e346cf3be5c31903c86ce13c721d5ba4fe54` |

## Remaining acceptance scope

The ten cases cover standing/air skills, below/exact energy checks, the observed
air projectile hit/miss path, root-relative ranged placement, and repeated casts
from both initial sides. They do not establish full roster parity: there are no
exact input-cancel boundary cases here, no mid-flight target relocation case,
and no visual/audio comparison. These results therefore validate only the
catalogued paths and shared regressions listed above.
