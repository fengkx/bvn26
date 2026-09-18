# 辅助鼬结印期间瞬身判定诊断 r01

本轮针对“鼬开始结印后移植版仍能瞬身躲开”做了源脚本、时间轴和原版固定输入对照。没有修改 `game/`、`scripts/` 或生产 Godot runtime；当前固定用例没有复现生产差异，因此没有安全依据添加 runtime 补丁。

## 可证的源语义

源输入是 `game/fighter/fz/you.swf` 与 `scripts/fighter/fz/you.json`，对应生成模型 `godot/generated/helpers/you/combat.json`。

1. **逐帧脚本/事件**：鼬根时间轴第 18 帧只写 `动作 = 1`；第 24 帧执行 `_root.bsd(pn,"XG_fzbs",true)`；第 48 帧新放置的 `atm1` 子片段在下一次 `enterFrame` 用 `hitTest` 命中目标后跳到“攻击2”；第 61 帧写 `动作 = 0`；第 65 帧执行 `_root.bsw(pn)`；第 76 帧执行 `fzccXg` 后 `gotoAndStop(1)`；第 92 帧把鼬的 X 对齐目标。位置见 `godot/generated/helpers/you/combat.json:29-68`，攻击字段见 `:70-94`。
2. **PlaceObject/MOVE**：视觉切换从源帧 14、16、18、20、22 开始；第 24 帧只有脚本事件，没有把“动作=1”当作暂停事件。第 22 帧替换显示深度，第 48 帧放置攻击子片段，第 60 帧移除相关深度。对应 `godot/generated/helpers/you/timeline.json:325,378,431,489,542,609,1329,2230`。
3. **标签退出**：第 65 帧通过 `bsw` 解除暂停；未命中分支在第 76 帧显式回到并停在根帧 1，不把标签结束推断为回站立。第 125 帧还有一次 `bsw`，用于后续攻击阶段。
4. **原版不变量**：`scripts/fighter/itachi.json:624` 的 `frame_1/DoAction.as` 中，目标角色 `gameRunning()` 只在 `_root.zhanting == false` 且目标 `mc.sw == false` 时放行输入；`on_enterframe` 先处理已经开始的 dash，再检查 `zhanting`，所以 bsd 前已经启动的瞬身可以继续完成，而 bsd 暂停期间新瞬身不能启动。受击替身 `hurtSkill()` 是同一源条目中的另一条链，只由非飞行 `beidax` 在受击时调用，不能用普通 dash 结果替代。
5. **原版同输入**：固定站位为佐助 p1 x=300、 一护 p2 x=350、双方能量 300、p1 辅助鼬、p2 辅助魂；原版输入 tape 与 Godot port 使用相同 fight tick。严格比较和 fixture 见下文。

## 对照结果

### 已严格逐状态匹配

以下比较均为 fighter 与 helper 状态逐行比较，未放宽阈值：

- 静止基线：鼬的 `atm1` 在 helper local frame 48 / fight tick 62 只是接触分支，目标 HP 首次变化在 atm2 的 local frame 128 / tick 100；随后 tick 116、132、148 命中。原版与 port 均为 `1000 -> 960 -> 920 -> 880 -> 780`。
- 结印前已启动的普通 dash、bsd 暂停窗口、bsw 后继续：`/tmp/you-helper-dash-seal-compare.json`，342/342 matched；helper compare 同样 342/342。
- bsd 窗口内新发起的普通 dash：`/tmp/you-helper-dash-postbsd-compare.json`，362/362 matched；目标停在 x=350，之后仍按同一攻击时序受击。
- 未受击时在暂停窗口按 O：`/tmp/you-helper-summon-paused-compare.json`，302/302 matched；能量、位置、生命和 helper 状态一致。这个用例不是“受击替身已验证”。
- 静止攻击基线：`/tmp/you-helper-static-compare.json`，362/362 matched；helper compare 同样无差异。

### 真实 Timer 的首击后 O 对照

使用 Godot 真实 wall Timer、每个 fight tick 等待约 1/30 秒运行 180 tick：

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot \
  --user-data-dir /tmp/bvn-godot-live-hurt3 \
  -s /private/tmp/you_helper_live_hurt_probe.gd \
  > /tmp/you-helper-hurt-live-port3.log 2>&1
```

源 capture 为 `/private/tmp/bvn-you-helper-hurt-summon-collected/events.jsonl`，port capture 为 `/private/tmp/you-helper-hurt-summon-live-port.json`。关键结果一致：

| 时点 | 原版/port 关键状态 |
| --- | --- |
| tick 100 | 首次 helper 命中，目标 HP=960、hits=1 |
| tick 102 | O 受击替身消耗能量至 200，`hurtSkling=true`，暂停成立 |
| tick 120 | 首次 Timer 后解除暂停 |
| tick 148 | 后续 helper 命中，目标 HP=860、hits=2 |

但实时 Timer 的后续回调存在 **1 tick 相位差**：port 的 `XG_baoqi` 阶段在 tick 123 改变 p1，而原版在 tick 124；port 在 tick 124 进入暂停，原版在 tick 125。该差异尚未归因，不能宣称真实 Timer 逐 tick 一比一；最终 HP/hits 结果相同。此前同步 `move_case` 中 Timer 不触发导致的长时间暂停已排除为 harness 时钟问题，未改 runtime 迁就它。

## 可复用产物

- Fixture：`evidence/characters/sasuke-you/you-helper-dash-gate-r01.fixture.json`
- 可直接交给既有 `move_case_reference.gd` 的单 case fixture：`evidence/characters/sasuke-you/you-helper-dash-gate-r01.case.json`
- 现有源时间轴回归：`godot/tests/you_helper_lifecycle.gd`（锁定 frame 18/61、frame 48 子片段、frame 76 根停）
- 本轮窗口探针：`godot/tests/you_helper_dash_gate_probe.gd`（按 helper source frame 驱动输入，输出 defender 位移/生命/暂停状态）
- 原始源/port capture 与 compare JSON 保留在 `/private/tmp`、`/tmp`，路径和命令已写入 fixture/report。

单 case fixture 的实际运行命令（fixture 路径需为绝对路径，因为 Godot 项目根是 `godot/`）：

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot \
  --user-data-dir /tmp/bvn-you-gate-case-r01 \
  -s res://tests/move_case_reference.gd -- \
  /Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-dash-gate-r01.case.json \
  /tmp/you-helper-dash-gate-r01-port.json
python3 tools/probes/compare_mode_reference.py \
  /private/tmp/bvn-you-helper-dash-postbsd-collected/events.jsonl \
  /tmp/you-helper-dash-gate-r01-port.json \
  --output /tmp/you-helper-dash-gate-r01-compare.json
python3 tools/probes/compare_helper_reference.py \
  /private/tmp/bvn-you-helper-dash-postbsd-collected/events.jsonl \
  /tmp/you-helper-dash-gate-r01-port.json.helpers.json \
  --output /tmp/you-helper-dash-gate-r01-helper-compare.json
```

实际输出为 fighter `matched 362/362`，helper `matched 362/362, difference_count=0`。matrix fixture 则记录同一 setup 下的静止、结印窗口、未受击 O 和真实 Timer 五个 case；窗口探针命令为：

```text
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot \
  --user-data-dir /tmp/bvn-you-gate-probe \
  -s res://tests/you_helper_dash_gate_probe.gd -- /tmp/you-helper-dash-gate-probe.json
```

该 probe 只覆盖 helper source-frame 驱动的普通 dash 窗口，不包含真实 wall Timer 或 O 受击链；真实 Timer 使用上文 `/private/tmp/you_helper_live_hurt_probe.gd`，结果存在 1 tick 未归因相位差，不能用 probe 输出替代。

## 验证命令

通过：

```text
python3 tools/check_handoff.py
Godot --headless --path godot -s res://tests/you_helper_lifecycle.gd
Godot --headless --path godot -s res://tests/you_helper_callback_order.gd
Godot --headless --path godot -s res://tests/hurt_summon_smoke.gd
Godot --headless --path godot -s res://tests/escape_faction_smoke.gd
```

`python3 tools/verify.py` 按项目规则执行但失败于既有 manifest hash mismatch：`godot/fighter_runtime.gd`、`godot/helper_runtime.gd`、`godot/stage_hit_runtime.gd`、`godot/main.gd`、`godot/source_clock.gd`、`godot/web/shell.html`。本轮没有修改这些文件，也没有更新 manifest。

## 当前结论与复现缺口

本轮没有发现可安全修复的生产差异，也没有修改生产代码。已验证的是普通 dash、bsd 暂停、bsw 恢复、静止攻击和未受击 O 输入；未验证用户所说的具体“瞬身”按键路径是否为普通方向 dash，还是受击替身 O，以及用户实际站位和命中结果。

下一轮最小复现信息需要固定：角色双方、辅助槽位、p1/p2 初始 X、普通 dash 或 O 的确切按键、相对鼬 helper local frame（至少 18、24、65 中哪一帧按下）、以及最终目标 X/HP/hits。没有这些输入，不能把“动作=1”或视觉结印起点扩大成必中/禁位移补丁。
