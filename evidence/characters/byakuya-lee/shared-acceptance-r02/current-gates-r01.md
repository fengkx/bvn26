# SUPERSEDED by `current-gates-r02.md`

# Byakuya / Lee current gates r01

只读审计时间：2026-09-21。当前 runtime 证据绑定 `main=8ef3f927c78426fbd50b2ed700544aff1b31d2727f59adf018a357a900ca8c7d`、`fighter_runtime=feb1a03f8a79ef9b9a0e1521d59b4ee57adb7501414c5856cb2c6ded4aefe5ac`；本表不提升生产 availability。

| 门槛 | 当前证据 | 状态与准确边界 |
|---|---|---|
| Source/native 状态矩阵 | Lee `validation/helper4a0f-current-index-r02.json`：186/186、602 或 802 rows、0 differences、`validated`；Byakuya `validation/source-fixture-map-r01/manifest.json`：81 source-matched、86 Godot-only、11 disabled-negative | Lee 当前矩阵通过其字段门槛；Byakuya 仍有 86 项缺原版 source 对照，不能称两角色完整矩阵 |
| AI | Byakuya `ai-clean-r01/current-runtime-r01/manifest.json`：180 tick bounded；Lee `ai-cpu-r01/current-runtime-r01/manifest.json`：300 tick bounded；两者 random/clock matched | bounded CPU checkpoint 通过；不等于全 CPU 决策、完整 boot/intro 或全部输入分支 |
| KO / timer | Lee `validation/timer-ready-r04/phase-r05-full-summary.json`：153 validated zero-diff；625 clean dead/kill 使用 r05；外部 timer tape 的 register/fire/cancel 链有证据 | 受控 timer tape/状态轨迹通过；不是完整自然 wall-clock KO、next-Ready、回合重开与 UI 生命周期 |
| 音频 619 | `byakuya-619-lifecycle-r03.json`：source frame 963 StartSound 619、无 StopSound，Godot Dummy real-time wait 2s，player natural `finished`，创建后 1415ms | Godot 播放器自然结束已证；不等于 Flash 波形、设备后端或 OutPoint 逐样本一致 |
| 其他音频 | Byak 887/581、934/44、944/52、963/619 source reachability 有记录 | StartSound 触达映射有证；完整 native/source 声音端点、全部 Stop/卸载生命周期仍未闭合 |
| 视觉 819 | `audiovisual-r06/godot-819-gui-r01/metadata.json` paired to old r29 freeze; `visual_child_frames={}` | 旧 freeze phase 不可靠，child lifecycle pending；不能作为当前视觉 parity 通过 |
| 视觉颜色链 | `lee/visual-color-chain-r01.json`：435/434 是 Shape/JPEG tag，无 child playhead；父 CXFORM/alpha/blend 为同 identity/default | bounded read-only 未发现 color-chain defect；不等于像素级视觉一致 |
| Boot / intro / next-Ready | headless intro/ready/round/KO smoke 与 source boot probe 产物 | Godot smoke 通过；fresh Flash boot、Godot/Web 同输入 boot parity、KO 后真实 next-Ready 输入仍缺 |
| Web / production availability | 当前 export/QA overlay 与 candidate flow 有记录；`validate_contracts.py` 仍为 `gameplay_tested=false`、`production_ready_data=false` | 可用性 gate 保持 pending；浏览器完整输入、真实 VsHuman 回合/返回选人、全 production roster 不得由 headless/overlay 提升 |
| 工具完整性 | `tools/verify.py`、`tools/check_handoff.py`、19 harness tests、`git diff --check` 本轮通过 | 仅表示证据/契约/工具完整，不改变上述行为验收边界 |

明确排除：全 35 roster、Bankai/变身形态、完整 HIT_RECEIVE SOP Step E 不属于本轮 Byak/Lee 基础形态 gate；若后续纳入，需另建 source-first 证据，不得从本表推导完成。
