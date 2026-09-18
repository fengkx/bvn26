# 辅助鼬结印后连续瞬身诊断 r02

本轮按用户给出的近距离场景复现：佐助 p1（x=300）召唤辅助鼬，一护 p2（x=350，面向 p1）从鼬源帧 18、22、24 附近开始反复按普通瞬身；每次按键为 1 tick 按下、1 tick 释放，间隔 2 ticks，持续 180 个 fight tick。没有修改 `game/`、`scripts/` 或生产 Godot runtime。本轮结论是：**指定输入下原版也能躲，移植版与原版严格匹配；用户报告的生产差异仍未复现，因此没有修复补丁。**

## 输入有效性与站位基线

- 角色/辅助：佐助 + 鼬，对一护 + 魂；同一地面、同一朝向。
- x=380 的单次普通瞬身基线已验证：p2 从 x=380 穿过 p1 并到达身后 x=230；原版/移植版 fighter 82/82、helper 82/82 匹配。这个基线证明 x=380 确实满足“单步穿身”，不是坐标假设。
- 连续点按主案使用更近的 x=350（与 p1 相差 50），每次严格一 tick 按下加一 tick 释放，没有把长按误当成多次按下。
- 原版构建使用锁定 BVN 2.6 `game/main.swf`；采集器报告 `source_key_reads_match_recorded_intent`。原版 `input_bindings` 为 p1 summon/O=79、p2 dash/N3=66；frame18/22/24 三个 capture 分别记录 p2 N3 pressed reads 48、59、48 次，非直接写动作状态。

## SOURCE_FIRST 五问定位

1. **每帧脚本/事件**：`scripts/fighter/fz/you.json`：frame18 写 `动作=1`；frame24 调 `_root.bsd(pn,"XG_fzbs",true)`；frame48 的 atm1 子片段在下一次 `enterFrame` 以 `hitTest(opponent.mc.bdmn)` 命中后跳“攻击2”；frame61 写 `动作=0`；frame65 调 `_root.bsw(pn)`；frame76 `fzccXg` 后 `gotoAndStop(1)`；frame92 把 X 对齐目标。生成模型对应 `godot/generated/helpers/you/combat.json:29-68`。
2. **PlaceObject/MOVE**：视觉变化从源帧 14、16、18、20、22 开始；frame24 只有脚本事件。frame48 在 depth 3 放置 `atm1`，frame50 的 MOVE 更新同一实例，frame60 移除它；frame128 才放置 `atm2`。对应 `godot/generated/helpers/you/timeline.json:325,378,431,489,542,609,1329,2230`，frame128 的 `atm2` 见同文件约 2140 行。
3. **标签退出**：`bsw` 在 frame65 解暂停；未命中分支在 frame76 显式根 `gotoAndStop(1)`；标签结束本身不推断为回站立。后续攻击阶段 frame125 还有一次 `bsw`。
4. **原版不变量**：`scripts/fighter/itachi.json:624` 的普通 dash 路径在 `on_enterframe` 先处理已开始的 dash，再检查 `gameRunning/zhanting`；因此 bsd 前启动的 dash 可继续，bsd 窗口中新 dash 不应启动。`hurtSkill` 是受击后的另一条 `beidax` 链，不能用普通 dash 结果替代。
5. **原版同输入**：以下三组连续点按均使用同一 case tape 采集原版与移植版，fighter/helper 比较均为逐字段、逐 tick 严格匹配；原始 build/summary、case、compare JSON 已保存到本目录 `you-helper-dash-gate-r02-*` 文件。

## 端到端结果

| 起点 | 按键窗口 | pause 前是否已有 dash | bsw 后是否 dash | atm1 捕获 / 实际伤害 | 结果 |
|---|---|---|---|---|---|
| helper frame18 | 首按 tick32 | 是；tick35 开始移动，bsd 时到 x290 | 是；随后继续移动 | 静止基线的 atm1 捕获语义保持；本 tape 两边均未产生 HP 变化 | fighter/helper 362/362 matched；原版也躲 |
| helper frame22 | 首按 tick36 | 否；pause 在位移前生效，p2 保持 x350 | 是；恢复后向远离方向移动 | 两边最终 HP=1000、hits=0 | fighter/helper 362/362 matched；原版也躲 |
| helper frame24 (bsd) | 首按 tick38 | 否；pause 窗内 p2 保持 x350、frame21/4 | 是；tick96 解暂停，tick99 才开始位移，最终到 x20 | 两边最终 HP=1000、hits=0 | fighter/helper 362/362 matched；原版也躲 |

frame24 的关键状态是：tick38..95 两边 `paused=true` 且 p2 x=350 不变；tick96 `bsw` 后解除暂停；tick99 两边同时开始普通 dash。这个结果证明移植版没有在暂停期间接受新的 dash，但也证明本 case 的攻击接触发生前两边都获得了同样的恢复后位移。

## atm1 的真实语义

静止 x=350 基线中，You 在 helper local frame48 / fight tick62 放置 depth-3 `atm1`。frame50 的 MOVE 继续更新该实例；其 `enterFrame` 条件满足后在 tick63 跳到 helper frame92（“攻击2”）。这一步是捕获/转入攻击阶段，不是已经对目标造成 5 点伤害。原版与 port 的首个 HP 变化在 helper local frame128 / tick100，命中的是后续 `atm2`（compiled damage=40、hitstun=600）；静止时后续命中为 tick100/116/132/148，HP `1000 -> 960 -> 920 -> 880 -> 780`。

源与编译字段：`scripts/fighter/fz/you.json` frame48 的 `hitTest` 回调；`godot/generated/helpers/you/combat.json` 的 `contact_gotos`（约 59-68 行）和 `attacks.atm1/atm2`（约 70-85 行）。`atm1.damage=5` 是攻击字段，但在已验证源路径中先执行捕获回调跳“攻击2”，不能据此声称 atm1 自动命中；后续 `atm2` 仍必须在其实际 AABB 与目标接触时才造成伤害。

## 可复用产物

- 总 fixture：`/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-dash-gate-r02.fixture.json`
- 单步穿身：`you-helper-dash-gate-r02-baseline-x380.case.json`及同名 `.compare.json` / `.helper-compare.json`
- 连续点按：`you-helper-dash-gate-r02-frame18-x350.*`、`frame22-x350.*`、`frame24-x350.*`（case、native-build、native-summary、compare、helper-compare）
- 生产源与脚本仍未改动；运行时没有新增代码或回归假设。

以 frame24 case 为例，移植版命令为：

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot \
  --user-data-dir /tmp/bvn-you-near-repeat-tap-frame24-x350-port \
  -s res://tests/move_case_reference.gd -- \
  /Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-dash-gate-r02-frame24-x350.case.json \
  /tmp/you-near-repeat-tap-frame24-x350-port.json
```

原版使用本轮实际命令链：`tools/probes/build_ai_reference.py` → `tools/probes/capture_native_player.py`（项目 Flash capture lock）→ `tools/probes/collect_ai_reference.py`，再以 `compare_mode_reference.py` 和 `compare_helper_reference.py` 生成同名 compare JSON。具体参数模板与三组 run id 保存在总 fixture 的 `commands` 字段；原始 `/private/tmp` 路径也记录在各 case/summary 中。

仓库内 fixture 已实际重放（frame24）：

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot --user-data-dir /tmp/bvn-you-near-repeat-tap-frame24-x350-repo-fixture -s res://tests/move_case_reference.gd -- /Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-dash-gate-r02-frame24-x350.case.json /tmp/you-helper-dash-gate-r02-frame24-x350-repo-port.json
```

输出 `MOVE_CASE_REFERENCE_OK sasuke-you-near-repeat-tap-frame24-x350-r03`；再比较仓库 fixture 生成的 port 输出，fighter `matched 362/362`、helper `matched 362/362, difference_count=0`。

## 验证与边界

- 本轮 4 组原版/移植对照：单步基线 82/82；frame18、22、24 各 fighter/helper 362/362，`difference_count=0`。
- `python3 tools/check_handoff.py` 已通过；既有生命周期、callback order、hurt summon、escape faction smoke 在本轮前已通过。
- `python3 tools/verify.py` 仍受本轮前已存在的 6 个 manifest hash mismatch 阻塞（fighter_runtime、helper_runtime、stage_hit_runtime、main、source_clock、web/shell）；本轮未改这些文件，也未更新 manifest。
- 未覆盖 hold 语义、用户可能使用的受击替身 O 路径、不同角色/站位/输入节奏；因此结论只针对这里明确记录的普通 N3 连续点按。若用户仍能复现，需要最小补充：双方角色/辅助槽位、初始 X、N3 的实际按下/释放节奏、相对 helper local frame、以及攻击结束时目标 X/HP/hits。不能把视觉 frame18 或 `动作=1` 扩大成普遍禁位移补丁。
