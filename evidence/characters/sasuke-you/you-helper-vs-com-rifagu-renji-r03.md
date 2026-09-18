# You helper VS COM 日番谷/恋次 diagnostic r03

## 结论

本轮锁定用户描述的方向：human 日番谷召唤鼬，CPU 恋次作为目标。受控 VS COM 链已推进到鼬结束和恋次恢复后的移动。两端都完成两次伤害结算（1000 → 960 → 860），没有证据支持在该链上修改生产运行时，因此本轮没有 runtime patch。

报告中的 source 与 port tick 以各自 fight tick 为准。source 首次受击后的恢复步行从 tick 180 开始，port 从 tick 179 开始，攻击和首次恢复位移约有一个 tick 相位差。source 在 tick 192 回到 frame 1，而 port 在 tick 193 仍为 frame 36；因此不能泛称整个恢复段逐帧匹配。source 在回到 frame 1 后首次记录的 AI moveLeft=true 是 tick 193；这不是恢复步行的起点。需要用户实际 Web URL/构建版本和可复现的一局自然 CPU random seed 才能继续定位该相位边界。

## 固定输入和运行

- VS COM：P1 human 日番谷 + 鼬，P2 CPU 恋次 + 魂，场景 现世。
- 起点 x=300/350，面向互相朝向；P2 energy=300。
- P2 goran 从 400 在 fight tick 79 置为 0，仅用于窄定位；之后不再清理或推进受击状态。
- P1 O 使用一 tick 按下、随后释放的重复 tap（fight tick 10..88）。
- source 原版捕获来自 /private/tmp/bvn-vscom-rifagu-renji-you-close-source-delay0-r01-collected/events.jsonl。
- port 使用 /private/tmp/vs_com_you_renji_live_timer_probe.gd，由 Godot 4.7.2 的 _advance_fight 驱动 240 tick，每 tick 后 await 1/30 秒；输出 /private/tmp/vs-com-you-renji-live-timer.json。

可复用的紧凑输入/结果记录见同目录的 [fixture](you-helper-vs-com-rifagu-renji-r03.fixture.json)。原始 JSON 仍在 /private/tmp，没有复制临时运行日志进源码目录。

## 对齐节点

| 节点 | source | port |
| --- | ---: | ---: |
| You frame 178，atm3 | tick 147–148 | tick 146–147 |
| You 回 frame 1，attacking=false | tick 171 | tick 170 |
| 恋次首击 frame 970，HP 1000→960 | tick 100 | tick 99 |
| 恋次第二击 frame 983，HP 960→860 | tick 148 | tick 147 |
| 恋次回站立 frame 1 | tick 177 | tick 176 |
| 恋次恢复步行首次位移 | tick 180，x 322.65→304.25 | tick 179，x 322.65→304.25 |
| 恋次回 frame1 后首次 AI moveLeft=true | tick 193，x 138.6→130.6 | 当前 port 输出未记录该 predicate；恢复步行已在 tick179 开始 |

### 源语义定位

1. You frame 24 的 DoAction.as 调用 bsd，frame 48 的 enterFrame hitTest 后进入“攻击2”；frame 48 的 atm1 是捕获/停场观察点，首个伤害来自攻击2。
2. You frame 128 的攻击2命中恋次，随后 frame 176 的攻击3/atm3 造成第二次结算。
3. 恋次 frame 971/972 的受击回调进入 doHurtSkill：bsd("XG_bsq")，约 600ms 后 bsw、跳到“招换”、创建 XG_baoqi。这是恋次自己的受击替身链，不能等同于普通瞬身，也不能作为用户问题的根因结论。
4. source 和 port 都在鼬 helper 回 frame 1 前后的恋次受击恢复段执行 frame21 callback 的 authored auto walk（source tick180，port tick179）；source 随后在 frame1 记录 moveLeft=true（tick193）。port probe 没有保存该 predicate 级别日志，且 tick193 仍为 frame36，所以这里只确认伤害与首次恢复位移相符，不宣称整个恢复段逐帧一致。

## probe 局限

CPU Renji 的源 frame 回调仍会调用 kis()，而 AI 分支没有玩家 key_reader。port probe 只注入恒 false 的 source key reader，表示“CPU 没有玩家按键”，防止 Player controller requires source input assertion；它没有写入 AI 状态，也没有替换 CPU random/AI tape。该注入和 goran 置 0 都使本案成为诊断定位，不是完整自然 COM 验收。

## 检查和工作树

本轮没有修改 game/、scripts/ 或生产 Godot runtime。紧凑 fixture 与本报告是新增证据文件；原始 source/port 运行输出保留在 /private/tmp。验证命令和结果由协调端按当前共享工作树记录；仓库既有 verify manifest 的历史 hash 不一致不得通过本轮更新来掩盖。
