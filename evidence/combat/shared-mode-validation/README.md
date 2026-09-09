# Shared combat path across Vs Com, PvP and training

## Cause and change

The prototype selected its **combat implementation** using `session.p2cpu`: Vs Com enabled source BODY/controller/receiver callbacks, whereas PvP and training used legacy `enter_frame`, direct pair collision and separate pause/effect advancement. This was a migration shortcut, not a rule in BVN 2.6. Consequently fixes verified only in Vs Com did not establish parity in the other modes.

All three production fight entries now unconditionally create the same source callback registry, health rules, KO timeline, compiled controllers, combat services and deferred child/frame queue. The old main-loop pair resolver and alternate pause/effect loop are removed. P2's compiled source preserves both player and AI branches; `useAI` and the input reader choose the source predicate branch, and only Vs Com starts its AI random interval. `opponent_driver` replaces the misleading `cpu_driver` field. Both players still use the same underlying AiCpuDriver scheduler, including the P1 adapter.

Training also had a real clock defect: `_tick_zdbx` approximated a 1000 ms source interval with 30 simulation steps. It now uses an independent, always-processing wall-clock Timer with explicit recording/replay support. Its mode, interval and recovery rule are extracted from source; returning to menus or clearing zdbxint stops and disposes it. Pausing does not suppress the source recovery callback, and `beida != 0` prevents recovery. PvP result handling retains the current mode when returning to the fixed-selection map screen.

## Source-first answers

1. Both base fighters call their BODY `on_enterframe`, and their placed controllers select player/AI predicates via `_parent.useAI`. They do not select a different receiver or collision algorithm by mode. Source paths are `scripts/fighter/minren.json::DefineSprite_764/frame_1/DoAction.as`, `scripts/fighter/yihu.json::DefineSprite_638/frame_1/DoAction.as`, and each `DefineSprite_16/frame_1/DoAction.as`. Newly generated yihu/player_controller metadata retains every controller, receiver, projectile and hurt placement path, frame membership and hash.
2. No gameplay placement is moved by this consolidation. Each source placement continues to use one common registry and resets only on new placement; moves retain instance state. Source `DefineSprite_1991/frame_1/DoAction.as` registers zdbx at 1000 ms when modo is 4; it is independent of character animation frames and the root pause flag.
3. Existing compiled goto/stop/fallthrough and bsd/bsw rules determine action exits in every mode. Recovery only writes HP/MP when loaded and beida==0; it does not change a timeline. Source checkDead rejects KO in mode 4. Menu teardown clears callbacks/timers; ordinary match completion preserves its selected local mode.
4. The state comparator requires the complete source window and exact slot/tick/frame, X/Y/scale, action, HP/MP, sw, touch/touchFloor, hits, pause, hstm and hurtSkling. It does not exclude geometry or add tolerances. Source observations occur after initial scripts and before deferred target scripts. The native harness samples fight tick 0 in the same opening-completion tick, avoiding an extra warm-up step that previously changed touchFloor.
5. The retained `pvp` and `training-timer` captures are native Flash executions with source key-read validation. They exercise both keyboard players, simultaneous approach/attacks, two direction-dash input windows, Up+I against ordinary rush, and summon input. Recovery callback occurrences in `training-timer` are replayed at their recorded display boundary. No expected state is overwritten after initialization.

## Results and retained regressions

| Evidence | Result |
| --- | --- |
| pvp/comparison-before.json | Legacy mode path diverges, including run parent frames; only 576 of 602 source actor states reached. The earlier harness also has a documented tick-0 touchFloor phase difference. |
| pvp/comparison.json | All 602 actor states match, including exact coordinates. |
| training/comparison-before.json | After path consolidation, 71 states still differ because the old frame-count recovery fires at different times. |
| training-timer/comparison.json | All 602 actor states match with recorded wall-clock recovery callbacks. |
| shared_mode_lifecycle_smoke.gd | Repeated 2→3→4→3→2→4 transitions, P2 keyboard input, AI absence in local modes, training no-KO, recovery gates/pause, actual 1.1-second timer delivery, teardown and timer disposal. |
| vs_com_ko_smoke.gd with mode 3 | Both players can win two-round local matches; next round resets and the final route retains mode 3. |

Existing r13/r14/r15 complete observed-field, frame-boundary, random and clock replays still match. The six super-guard fixtures, direction-dash/Up+I references, prior dash references, movement visuals, pause, intro, Config and lifecycle checks are retained as regressions rather than replaced by the new two-mode trace. See checks.json for executed results.

## Reproduction

- Rebuild P2 source code: `python3 tools/importer/compile_ai_controller.py --fighter yihu --player --output godot/generated/fighters/yihu/player_controller`, then the same arguments to `compile_ai_body.py`.
- Rebuild training rule: `python3 tools/importer/build_training_model.py`.
- Original probe: `tools/probes/build_ai_reference.py --mode-probe 3|4 --frames 300`, with required ffdec jar/output/run-id. The collector now correctly permits no AI random samples in local modes. `training` is the initial capture without recovery callback observations; `training-timer` is the separately captured instrumented oracle.
- Native source comparison: `python3 tools/test_shared_modes.py --godot /path/to/godot`.
- Lifecycle and KO: run `res://tests/shared_mode_lifecycle_smoke.gd`; run `res://tests/vs_com_ko_smoke.gd -- 3`.

## Acceptance scope

The production **mode-dependent combat fork is removed**, and the listed original state windows are fully compared. This is not acceptance of all unported characters/forms, every move/geometry boundary, full audiovisual parity or every browser. Existing milestones remain pending until their full acceptance matrices are satisfied. Shared code ensures a future combat fix reaches all three modes; it does not make untested behavior automatically correct. Headless ObjectDB/resource cleanup warnings remain separately visible.
