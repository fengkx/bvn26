# 状态同步核对 — 2026-09-08

本次只修改文档、任务说明、覆盖口径与对应 manifest 哈希，保留已有未提交实现及产物。未改运行时、锁定输入、验收条件或覆盖布尔值；未新增 completed 任务。

## 核对结论

- B-01～B-03 与 M1-01 completed；M0-01 in_progress；其余 26 项 pending。pending 包含已有局部实现但未通过验收的工作，任务表新增进度说明、实际产物和证据引用。
- Godot 工程、两角色战斗切片、两援助、原素材 HP/连击 HUD、暂停返回、键位设置、十图导入与选图已有产物。SPEC、README、AGENTS 和计划不再写“尚无工程”。
- 原生参照播放器及调度探针可用；兄弟深度顺序与 24 FPS 外载剪辑已有隔离探针。ExecutionProfile 仍 provisional，嵌套创建首回调、焦点时钟域及同时命中待确认。
- AI 仅有静态规格与全库审计；BGM 清单与播放器存在，但 main.gd 尚未接线。KO/回合闭环、完整内容及原版同输入对照仍缺。
- 选图 navigation.log 已存在，但捕获来源、插桩和输入配方不足，不升级为完整原版 golden。覆盖表 false 表示尚未通过逐项验收，不表示没有素材或代码。
- 本轮未重新启动原版、复测浏览器或重新导出 Web；已有启动、截图与战斗测试记录保留其原始范围和日期。实际开发耗时无完整记录，不新增猜测人日。

## 本次实测

- `python3 -m unittest discover -s tools/tests`：41 项通过。
- Godot 4.7.2 `--headless --path godot --script res://tests/map_selection_smoke.gd`：退出 0，输出 `MAP_SELECTION_SMOKE_OK`，覆盖导航、重复输入、计时、取消及十图载入/出生点。启动有 user 日志写入及 macOS CA 证书错误，不能记为干净引擎日志或浏览器验收。
- `python3 tools/analyze_ai.py --check`：通过；62 bundles、69 controllers、9 variants。
- `python3 tools/validate_contracts.py`：5 schemas / 5 examples 通过；不代表游戏行为通过。
- 初始 `verify.py` 发现 README、REVERSE_ENGINEERING、STATUS、tasks 四项资料哈希过期；核对差异后仅刷新发生变化的资料哈希。game/ 与 scripts/ 哈希保持不变。
- 最终 `tools/verify.py` 通过（75 assets、74 dependencies、62 SWFs、8,853 scripts）；`tools/check_handoff.py` 通过（16 documents、90 links、31 tasks、20 requirements）；`git diff --check` 通过。旧 PACKAGE_CHECKS 保留为基线历史记录。
