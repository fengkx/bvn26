# 完整比赛缺口：倒计时与超时结算

状态：静态源审计完成，原生实现与完整比赛对照未完成。2026-09-09。

当前 `godot/main.gd` 的 KO 适配器只在换局末帧重置 `_root.gametime`，
`_ko_clear_interval` 将 `timeset` 列为尚未注册的计时器。当前源控制器没有
倒计时 `time` 回调及 `timeover` 时间轴。此前两个 600 战斗帧片段通过，
不能证明默认 60 秒的原版采集配置能走完超时、换局及整场结束。

## 可重复证据

[match-timeout-source.json](match-timeout-source.json) 由锁定普通版的脚本与 XML
静态生成，包含输入哈希、5 个剪辑的逐帧标签、放置/MOVE/移除变化与事件，以及
18 份原路径脚本。帧列表不省略空帧；不使用录像推导帧数。

```bash
python3 tools/importer/audit_match_timeout.py --workspace /tmp/bvn-main-ko
python3 tools/importer/audit_match_timeout.py --workspace /tmp/bvn-main-ko --check
```

工作目录须包含与 `export-report.json` 哈希一致的 `main.xml`，且报告源 SWF
哈希须匹配锁定输入。临时目录路径只是本次已有导出的位置。

## 源规则

以下路径均属于 `scripts/main.json`。

- `DefineSprite_1813/frame_1/DoAction.as`：停止计时显示播放头，复制 `maxtime`
  至 `gametime`；`maxtime == 100` 或 `modo == 4` 时跳到第 10 帧“无限时”，
  否则注册 `setInterval(time,1000)`。不是每 30 个战斗 tick 扣一秒。
- `time` 只有在 `zhanting == false`、双方 `sw == false` 且 `modo != 4` 时扣一。
  其后的超时判断和数字更新不在这些条件内。`gametime` 没有下限截断，
  只有显示用的局部 `tm` 被截到零；复刻不可把两者合并。
- `tm <= 0` 时检查 `_root.timeover.played == 0`，设置 `_root.to = true`、
  调用 `_root.timeover.play()`，却写入不带对象前缀的 `played = 1`。
  不得擅自改为写 `_root.timeover.played`；下述最小探针已确认裸赋值落在定义函数的剪辑。
  `tm > 0` 才明确写 `_root.to = false`。

| timeover 源帧 | 原版行为 |
|---|---|
| 1 | `stop()`，自身 `played = 0` |
| 2 | 双方 `sw = true` |
| 40 | P1 血量严格大于 P2 时令 P2 进入“失败”，否则令 P1 进入“失败” |
| 54 | 同血量跳到 `drawgame`（212），否则 `winner`（62）；先 `gotoAndStop` 再 `play` |
| 62 | 新放置胜方子剪辑 1844；load 根据严格大于关系选 X 为 −0.3 或 203.8 |
| 67 | 胜方计数加一、更新胜场剪辑、播放其 `bzxg` 并切焦点；平局分支跳过此帧 |
| 199 | 跳到 `next`（340），先停后播 |
| 240 | 平局路径写 `zhanting = true` |
| 344 | `qjxg` 进入“关” |
| 350 | 重置比赛时间，按胜场计数决定退出或注册 1000 ms 的 `nextfight` |

同血量时第 40 帧仍会让 P1 进入“失败”；不能因为随后判平局而提前跳过。
胜方不是第 54 帧缓存的对象：第 67 帧及子剪辑回调仍重新读取双方血量。

子剪辑 1844 第 40 帧写暂停，第 49 和 50 帧各自令胜方进入“胜利”，
第 50 帧停止。它在第 20 帧放置的 1843 子剪辑，每次 enterFrame 检查自身
是否为第 1 帧以及胜方是否满血，符合才 `play()`；1843 的第 1、15 帧停止。
这部分回调必须保留实例生命周期，不能替换成超时瞬间的一次性动画选择。

第 350 帧的 `nextfight` 顺序与 KO 第 394 帧一致：增加 rounds、恢复全局焦点、
双方进站立、调用 chushi、重置 fall/touch/sw、再次进站立、开 qjxg、播放 ready。
胜场计数从 1 开始，达到 3 即结束；平局不增加胜场。

## 实现前五问与下一步

1. 每帧脚本：本审计覆盖计时器、超时及全部所依赖子剪辑，含空帧。
2. 放置与 MOVE：剪辑内部及祖先相关深度变化已保留，见下文。
   换局后的实际复用/重建仍需同输入记录确认，不能仅根据线性帧表认定跳转语义。
3. 离开方式：显式 stop/goto/play 如上，其余空帧自然前进，不按标签尾回站立。
4. 可测试不变量：严格比较、平局不加胜场、两次胜利 goto、显示零与真实计数分离、
   nextfight 顺序。不能用“通常的格斗规则”替代这些源行为。
5. 原版同输入：尚无覆盖超时的完整比赛输入/随机/计时器调用轨迹。

先补根/HUD 放置寿命与定时器接收者证据，再扩展编译器、注册原生计时器和超时
时间轴。随后记录 timer/nextfight 的实际回调相位并进行完整比赛对照。
本次不修改游戏运行时，不把 M5-03 或整场一比一置为完成。

## 计时器作用域与祖先实例补充

原版 FP32 最小探针：
[输入哈希](../probes/schedule/timer-scope/build.json)、
[原始日志](../probes/schedule/timer-scope/native.log)、
[逐项比较](../probes/schedule/timer-scope/comparison.json)。重建：

```bash
python3 tools/probes/build_effect_attach_probe.py --probe timer_scope \
  --ffdec /tmp/bvn-ffdec-26.2.1/ffdec-cli.jar --output /tmp/bvn-timer-scope-new
```

探针在子剪辑定义 `time = function()` 并用函数形式 `setInterval(time,1000)` 注册。
原版实际输出 `this == undefined`；回调读到该子剪辑的 `played = 7`，
写 `played = 1`、`tm = 0` 后，子剪辑对应字段变为 1、0，而根 `played = 100`
及根下 `timeover.played = 0` 均不变。此证据限定于函数形式回调，不推广到
`setInterval(object, method, delay)`，也不证明完整游戏的 timer 相位。

XML 祖先深度链现在由同一审计器自动保留：

- 根第 56 帧：新建深度 71 的 `xuetiao`（1815）和深度 113 的 `timeover`（1848）；
  两个深度在根第 86 帧移除，在此线性区间内没有其他变更。
- 1815 第 1 帧、深度 33：新建 1814；第 2–10 帧只有 MOVE/矩阵修改，没有替换角色 ID。
- 1814 第 1 帧、深度 31：新建无显式名称的计时剪辑 1813；没有其他深度变更。
- 1815 第 1、5 帧显式停止；其余祖先脚本原文另存 `ancestor_scripts`。

因此 HUD 动画不能直接被实现成“每换局销毁重建计时器”。自然循环、向后跳转
是否保留已有子实例，仍需在原版换局轨迹中核对 timer_load 次数和计时器回调间隔。

长对战分析副本可用 `build_ai_reference.py --match-flow --frames 6000 --body-boundaries`
记录 root、timer_load、timer_enter/exit、KO/timeover 源帧及 nextfight 入口。
此选项默认关闭，不改历史 tape。新增事件由 `analyze_match_flow.py` 汇总，
必须先通过 collect_ai_reference 的完整性检查；帧数够长不自动代表覆盖超时。
