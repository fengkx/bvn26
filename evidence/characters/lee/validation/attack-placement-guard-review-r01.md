# Lee base attack placement and guard review

Scope: two same-height, same-move guard cases for Lee base form. This review uses the existing source captures and compiled combat data; it does not claim pixel/AABB parity or identify a production defect.

## Input and source chain

| Case | Input and setup | Source path and placement | Source attack data | Observed result |
|---|---|---|---|---|
| Forward guard | P1 Lee: `ranged` (85), ticks 10–13. P2: `down` (40), ticks 1–300. P1/P2 x=300/350; energy=300/300. | Lee `DefineSprite_518/frame_287/DoAction.as` offsets the parent by opponent `bdmn._width * 0.7`, sets facing toward the opponent, and copies opponent y. The `招1` timeline places `zh1atm` at frame 293, active through frame 295. | `zh1`: `zl=5`, `pw=50`, `htype=被打`. `DefineSprite_5/frame_1/DoAction.as` selects an overlapping attack with `getHitObj`; `fangyu` subtracts 10 from `zl` and breaks guard only when `zl > 10`. | P2 down reads true; P2 enters guard. During the hit, HP decreases 1000→995, `hits=0`, and action remains guard. Consistent with a guarded, non-breaking hit. |
| Mirror control currently on file | P1 Lee: `ranged` (85), ticks 10–13. Setup x=350/300. | Same frame-287 width-offset branch and `zh1atm` window. Lee wrapper initialization recalculates facing using relative x; actual facing still must be taken from the captured state. | Same `zh1` values. | This historical mirror build has no P2 `down` input. Its raw reads P2 key 40 as false at ticks 3, 10, and 20; HP decreases 1000→950, `hits=1`, action becomes hitstun. This is an unguarded hit, not evidence about guard direction. |

## Correct mirror capture contract

Create a new case from the forward-guard fixture, changing only the starting x positions to P1=350/P2=300. Preserve P1 `ranged` (85) ticks 10–13, P2 `down` (40) ticks 1–300, energy 300/300, stage, helpers, and all other settings. A candidate input fixture is `/private/tmp/lee-278-magichit1-guard-mirror-probe-r01.json` (SHA-256 `5d70eb496fc867752e365d3c25792d02d4d9d059ed8d99df591e9eace1c8fc59`). Keep the existing baseline immutable. `chushi()` initially assigns P2 xscale=-100, but Lee wrapper initialization calls `updateDirect()` and may overwrite facing from relative positions; therefore verify from the new raw that P2 key 40 is true and record P2's actual facing/action after Ready and wrapper initialization. Then associate the actual `fangyu`/`checkHit` result with the overlapping attack instance and its parent transform.

## Evidence and limits

- Forward source build: `evidence/characters/lee/original/lee-278-magichit1-guard-acceptance-r07/build.json` (SHA-256 `4fd995e45cb43789a4c6ec653c9a82fa0b5dc4c8561659e743e363bee5e23a2e`)
- Forward source events: `evidence/characters/lee/original/lee-278-magichit1-guard-acceptance-r07/events.jsonl/events.jsonl` (SHA-256 `3c773a1181f417d11303373b074931b0eeab6b693c6e8bfca652d92fcaeb3638`)
- Old mirror build: `evidence/characters/lee/original/lee-278-magichit1-mirror-acceptance-r07/build.json`; this is explicitly not a guard fixture.
- Source combat data: `godot/generated/fighters/lee/combat.json` (SHA-256 `b2e39de15cff390747f4a6906897ec3499aaa009f409eed26479974c082c5ef0`)
- Current production hashes: `godot/main.gd` `8ef3f927c78426fbd50b2ed700544aff1b31d2727f59adf018a357a900ca8c7d`; `godot/fighter_runtime.gd` `feb1a03f8a79ef9b9a0e1521d59b4ee57adb7501414c5856cb2c6ded4aefe5ac`.

The existing 14-field state comparison does not expose attack instance generation/removal, complete Flash MATRIX composition, world AABBs, or the exact defense receiver branch. Those require the shared read-only source/native observers; no runtime change is proposed from the current evidence.
