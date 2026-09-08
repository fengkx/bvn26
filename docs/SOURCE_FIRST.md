# 源优先实现闸门

实现或修改任何游戏机制之前必须读完本页并完成清单。目标是一比一还原
`game/main.swf` 的 Flash 体验，不是「手感接近」或「像格斗游戏该有的样子」。

查阅路径见 [REVERSE_ENGINEERING.md](REVERSE_ENGINEERING.md)。对照与发布门槛见
[VALIDATION.md](VALIDATION.md)。本页约束**怎么写代码**；验收页约束**怎么证明对**。

## 原版是什么

BVN 2.6 的招式不是「招式名 + 物理公式」。运行语义来自：

- 根时间轴播放头和帧标签
- 该帧上的 `DoAction`
- `PlaceObject` 上的 `onClipEvent(enterFrame)`（常在 helper clip，不只在帧脚本）
- 剪辑是新放置还是 `MOVE`（实例变量是否继承）
- 离开当前标签的方式（见下）

标签的 `end_frame` 只表示「下一个标签从哪一帧开始」，**不表示**「这里回站立」。
没有脚本的帧 = 播放头继续走。

## 实现前五问

五问都要有**源路径**（`scripts/*.json` 的 `path`、时间轴帧、或
`evidence/probes/` 记录）。答不全不得改 `godot/fighter_runtime.gd` 等运行时，
也不得把任务标为完成。

1. **这一段每一帧的 `DoAction` / `enterFrame` 是什么？**
   必须列出标签区间内的全部帧脚本，包括「什么都没有」。只读了进入条件和
   中间某一段 `hitTest` 不算读完。
2. **剪辑是新 `PlaceObject` 还是 `MOVE`？**
   新实例不继承 `js`、`jumpinggg` 等实例变量。`onClipEvent(enterFrame)` 从
   放置的**下一根**根时间轴帧开始，不是放置当帧。见
   `evidence/probes/schedule/clip_lifecycle.log`。
3. **离开当前标签的方式是哪一种？** 只能是下列之一，且必须来自源，不得混用：
   - 无条件 `gotoAndStop` / `gotoAndPlay`
   - 条件 `goto`（如 `hitTest` 后 `gotoAndPlay`）
   - `stop()`
   - 无终端脚本，播放头落到下一标签（`timeline_fallthroughs`）
4. **测试断言的是原版不变量，还是实现假设？**
   只允许断言源里能指出来的现象。禁止把「顶点高度猜的数字」「只有命中才结算演出」
   写进回归后再用实现去凑。
5. **同一套输入在原版 `game/main.swf` 里走过一遍吗？**
   先看原版的动作标签、源帧、是否落地/炸开/位移，再改移植。没有原版参照时，
   状态保持待验证，不能称一比一完成。

## 禁止的补全

不得用格斗游戏常识、手感或「标签看起来结束了」填原版没写的部分：

| 禁止 | 应做 |
|---|---|
| 把跳跃写成连续抛物线或统一初速度 | 按 `onJumping(step)` 剪辑寿命编译 `jump_windows` |
| 窗口内每一帧都当 `enterFrame` | 放置当帧不跑 clip `enterFrame`；新 `PlaceObject` 重置实例变量 |
| 标签 `end_frame` 一律 `_finish_action` → 站立 | 无 `goto`/`stop` 则编入 `timeline_fallthroughs` |
| 把条件 `hitTest` 当成「不命中就不播后续」 | 条件 goto 只是提前切换；后续标签仍可能被播放头自然到达 |
| 按角色在 GDScript 里写特殊位移/高度/伤害 | 先加编译规则，再让运行时消费通用字段 |
| 用 schema / 中间 JSON 合法代替行为验收 | schema 只证明字段形状 |
| 改阈值、改基准输出来消差异 | 保留 tape 与阈值；差异要回到源 |

已发生的反面例子（不得重演）：

- 跳跃：把 `js` 带进下一个跳跃剪辑，一跳升到约 126 像素，能上现世 `ban2`。
  源是 step 1 七次 `14+13+…+8 = 77`，低于墙顶 78.65。
- 鸣人下+J：`砍技1`（260–290）没有终端脚本，空挥也进 `砍技12` 炸开；
  `kj10atm` 命中只是提前 `gotoAndPlay("砍技12")`。把 290 当成回站立，就会「有时不炸」。

## 编译优先于手写

新行为先进入 `tools/importer/build_combat_model.py`（或对应抽取器），再重建
`data/actions/*` 与 `godot/generated/fighters/*/combat.json`。运行时只解释已编译字段。

当前由源编译、禁止改回角色硬编码的字段包括：`motion_windows`、`jump_windows`、
`action_exits`、`timeline_fallthroughs`、`presentation_events`、`command_catalog`、
`hit_priority`。缺字段时补编译器，不要在 `FighterRuntime` 里写 `if fighter == "鸣人"`。

重建命令见 [OPERATIONS.md](OPERATIONS.md)。改编译器或契约后跑
`tools/verify.py`、`tools/check_handoff.py`；契约变更加跑 `tools/validate_contracts.py`。

## 回归必须锁原版不变量

Godot `combat_smoke.gd` 与 `tools/tests` 的断言对象是源行为，不是当前实现的形状。

- 通过：一跳顶点 77 且单跳落不回 `ban2`；空挥 `砍技1` 仍进 `砍技12` 并在 292 闪光、313 回站立。
- 不通过：为了让现有错误实现变绿而改期望值、放宽阈值、删除断言。

对照顺序（与 [VALIDATION.md](VALIDATION.md) 一致，不可只看最后血量）：

输入锁存 → 动作与源帧 → 创建/移除的区域 → 碰撞候选顺序 → 伤害/状态/计时 → 位置 → 视听事件。

没有固定输入的原版逐帧轨迹时，相关 M2/M3 任务保持未完成。截图和「能玩」只证明开发路径可运行。
