# Byakuya / Lee base-form current gates r03

只读审计，更新至当前 helper4a0f/runtime evidence。范围仅白哉与小李基础形态；全 35 roster、Bankai/万解形态及整项目 production availability 不列为本轮必要门槛。

当前共同 runtime/compiler 证据：

- `main.gd` `8ef3f927c78426fbd50b2ed700544aff1b31d2727f59adf018a357a900ca8c7d`
- `fighter_runtime.gd` `feb1a03f8a79ef9b9a0e1521d59b4ee57adb7501414c5856cb2c6ded4aefe5ac`
- `helper_runtime.gd` `4a0f08ff087a498e9b15ed37bc166e2af9580ed4aa6b8e7853eaf742ce4f94f7`
- `move_case_reference.gd` `b7f70f8c58b6f2035255afbb904be31998d8701a27d4927467647d8d81e65b0d`

| 门槛 | 当前证据 | 当前结论 |
|---|---|---|
| Byakuya 状态矩阵 | `validation/helper4a0f-current-index-r01.json`：178 rows，167 matched、11 disabled-negative；runtime hashes 为上列当前值 | 基础矩阵当前 source/native 门槛已通过；11 disabled 是源不可用负例，不是 runtime failure |
| Lee 状态矩阵 | `validation/helper4a0f-current-index-r02.json`：186 rows，186 matched、0 differences、`validated`；602/802 states，source/native/hash/provenance 均逐行记录 | 当前 Lee 矩阵已通过；r01 的 6 pending 已被 r02 正确替代，不再采用旧 pending 统计 |
| AI | `byakuya/ai-clean-r01/current-runtime-r01/manifest.json`：Ready checkpoint 180 tick；`lee/ai-cpu-r01/current-runtime-r01/manifest.json`：Ready checkpoint 300 tick；两者 random/clock matched | 两个 bounded CPU checkpoint 已通过；仍不等于全 CPU 决策空间、完整 AI 开场或所有输入分支 |
| Source boot / intro / Ready | `evidence/boot-ready/r15/manifest.json`、`flow-summary-r01.json`：fresh native source trace 684 events，`done=true`，覆盖 boot→selection→battle_entry→intro→ready_begin→game_running→ready_horizon | 原版 source boot/Ready 证据已通过；这是 source 侧流程证据，不是 Godot/Web 同输入逐事件 parity |
| Web Vs Human / reselect | `evidence/web/qa-hud-current-r03/chromium-smoke/r07-vs-human/summary.json`，PCK `d921f9a062bebc3bc05a9237b8c959801f5e18b44d594de44d8e20801c6bf23c`：真实选人/援助/地图/战斗、输入动作、返回标题、再次选人并重进战斗 | 当前 bounded Web flow 与 reselect 已通过；完整 178/186 Web 矩阵、timeout/next-round parity、Flash 同输入 parity 仍未声称 |
| 819 source/Godot phase | `audiovisual-r06/819-effect-phase-source-r04/paired-phase-table.md` 与 `819-effect-phase-runtime-r01/README.md`：source 819→820 helper/effect 子时钟，Godot production FIFO 对齐；`helper-fifo-review-r01.md` 确认 generation guard、source-frame FIFO、nested goto 排序 | 819 的实时 phase/FIFO focused gate 已通过；同一项不代表像素级视觉一致；当前 paired evidence 未覆盖 A→B→A 同 activation 重入，该项列为范围外验证限制，不作为已发现缺陷 |
| 819 视觉像素 | `freeze-r18/819/driver-validation.json`：child state set equal，但 `stable_500ms=false`、acceptance rejected；旧 freeze-r29 不作当前依据 | 当前 phase 通过，稳定像素/原版视觉 parity 仍 pending；不能把旧 freeze 截图当通过 |
| Lee callback inventory | `source-callback-inventory-r01.json`：167 source entries，49 `source_observation_pending`；聚合器试运行 249 captures、parse_errors=0，但当前结果不可验收：native_matched 是硬编码 10 帧，body_boundary 未按 payload slot 过滤，且 frame-only 合并了同帧不同 callback | 49 项 callback provenance/native matched 仍 pending；320、29、1017 等只能在真实 compare artifact 证明后计 matched，1088/1098 clip 与 frame_action 必须按 entry identity 分开 |
| 音频 619 | `audiovisual-r05/audio-gap-r01/byakuya-619-lifecycle-r03.json`：frame963 StartSound 619、无 StopSound，Godot Dummy real-time wait 2s，natural `finished`，创建后 1415ms | Godot 自然结束与源无显式 Stop 已有 bounded 证据；不宣称 Flash 波形、设备后端或 OutPoint 逐样本一致 |
| KO / timer | `lee/validation/timer-ready-r04/625-natural-r05/report.json` 与 `source-next-ready-r02/lifecycle-report.json`：自然 Godot Timer register/timeout→Ready→输入恢复；原版 fresh 900-tick capture 记录 nextfight_enter、round2 frame1 reset 与后续 state-derived unpaused resume | source 与 Godot 各自自然 route 已有 bounded 证据；不宣称 OS 毫秒逐帧 parity，也不扩大为完整 Flash/Godot 回合事件 parity |
| 工具与 provenance | `tools/verify.py`、`tools/check_handoff.py`、19 harness tests、`git diff --check` 当前通过 | 证据契约通过，不提升未覆盖的全 AI、像素、波形或全 Web 门槛 |

明确剩余缺口仅限本轮范围内的实证边界：全 CPU AI 行为、819 稳定像素/逐像素视觉、Flash 波形/OutPoint 精确一致、完整 Flash/Godot 逐事件回合 parity，以及完整 Web 输入矩阵。旧 `current-gates-r01.md` 已标记 superseded。
