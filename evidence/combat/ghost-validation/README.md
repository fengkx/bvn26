# Direction dash and Naruto Up+I verification

## Result

Six new native Flash fixtures verify the current Vs Com slice. Four player-input fixtures match 324 root snapshots: down+L, up+L, 99 MP rejection, and down+L during authored hurt state. Each uses two separated input windows. Two Up+I fixtures match 482 combat snapshots: short ordinary rush and two CPU direction dashes. No new hit-test mismatch was found in these cases. The prior 723-snapshot dash suite also still matches.

At the chosen late Up+I timing (attacker frame 681), ordinary rush takes 40 HP at tick 100 and another 40 at 104. The direction-dash fixture starts at ticks 85 and 97, spends 100 MP each time, and still receives one 40-HP settlement. These are source-observed outcomes, not a universal statement that this super always hits or always misses.

The existing source-compiled direction-dash BODY was already active in Vs Com. The missing `XG_xdash` linked effect is now imported with the existing asset compiler and spawned by the existing super event path. No invulnerability duration, damage, box size or target tracking was changed. A native screenshot verifies the effect is visible; ghost-reference tests now fail if it is absent.

## Source-first answers

1. `scripts/fighter/minren.json::DefineSprite_764/frame_1/DoAction.as` contains `dash`, `doDashX`, `onDashing`, `on_enterframe`, `hurtSkill` and `doHurtSkill`. `dashQL=100`. The player branch requires L plus up or down, alive/not sw, sufficient MP, action 0/1/2, and opponent not sw. Up chooses Y=-14; grounded down chooses X=10 with updateDirect; airborne down chooses Y=12. Horizontal-direction+L alone is not the source condition. Action -1 (hurt) is rejected. `hurtSkill` uses O and a separate 100-MP rule. Screenshot prose is not the oracle.
2. `onDashing` increments dashF before `<10`, giving nine movement callbacks. During dashing it runs before the root pause gate. The effect is a new attachMovie from `main.json::frame_8/DoAction.as::bsd/addChildXG`, at caster X/Y-25 and facing. ExportAssets maps XG_xdash to Sprite 73. Its child Sprite 71 is newly placed; the parent unloads at 25 and the child stops at 25, so no frame after the child stop can be observed. The compiler retains the nested script and rejects an earlier stop or unsupported nested action.
3. Direction dash repeatedly stops on walk/fall, then calls bsw and resumes stand/fall2 at dashF=10. Ordinary rush instead uses authored frames 20–35 and receiver removal/replacement; see the existing dash-validation evidence. The effect explicitly unloads at frame 25, independent of the earlier movement completion.
4. Tests lock source HP/MP, parent frame, action, position, dashing/dashF, root pause, bs/canhit and receiver frame. Only missing receiver `undefined` maps to native frame 0. No numeric tolerance is introduced.
5. Each directory retains native Flash build hashes, instrumentation diff, source key-read validation and events. Original game/scripts are unchanged. The player fixture enters a source attack/hurt label at tick 10 to isolate the cancel condition; it is not a complete preceding attack/hit input replay. Subsequent direction+L presses are passed through the original kis alias and real Godot input dispatch.

## Reproduce

Build source fixtures with `tools/probes/build_ai_reference.py --ghost-probe down|up|low|hurt --frames 80` plus required ffdec/output/run-id options. `--ffdec` takes the JPEXS jar. Run the isolated build in the native Flash debugger and collect with `tools/probes/collect_ai_reference.py`.

Run `godot --headless --path godot --script res://tests/ghost_reference.gd -- CASE OUTPUT.json` for each player case; it asserts all 81 source observations and effect presence for up/down. An optional third argument is a PNG path for a graphical run. Rebuild the effect using `python3 tools/importer/build_ai_effect_assets.py --workspace /tmp/bvn-main-ko --clip XG_xdash --output godot/generated/effects/XG_xdash`.

For the super cases use `--dash-probe super-rush|super-dashx --dash-trigger-frame 681 --dash-duration 3 --frames 240`; native `dash_reference.gd` uses the same arguments. `compare_dash_reference.py` reports the exact combat-field results and its geometry/child-alias exclusions. Its CPU goran fixture is controlled AI input, not two physical player L presses.

## Remaining scope

This establishes the listed current Vs Com cases, not all combat logic or all modes/characters. The older PvP/training control path was subsequently removed; see [shared-mode validation](../shared-mode-validation/README.md). Full collision geometry, arbitrary timing/airborne interactions, original visual/audio parity and browser gameplay remain pending. The formerly missing afterimage service (`showdow`) is now implemented with separate [snapshot and fade evidence](../../visual-audio/shadow/README.md). Importing XG_xdash alone was not sufficient; full original pixel parity still remains open. Existing headless cleanup warnings remain. Keep M2/M3/M5 pending and add new first-divergence cases instead of inventing unconditional immunity or guaranteed hits.

Final validation: `tools/test_ghost_reference.py` passes all six cases; 68 Python tests, movement/visual and 1800-snapshot super-guard checks pass. r13/r14/r15 observed-field match replays remain matched. Repository integrity/handoff/contracts pass. Web export completed (sandbox prevented saving editor preferences, not export files). See `checks.json`.
