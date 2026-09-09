# 源优先实现闸门

实现或修改任何游戏机制之前必须读完本页并完成清单。目标是一比一还原
`game/main.swf` 的 Flash 体验，不是「手感接近」或「像格斗游戏该有的样子」。

查阅路径见 [REVERSE_ENGINEERING.md](REVERSE_ENGINEERING.md)。对照与发布门槛见
[VALIDATION.md](VALIDATION.md)。重击、破防、连击次数、命中火花、防御挡住和必杀黑底/立绘横幅的逐步落地见
[HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md)。本页约束**怎么写代码**；验收页约束**怎么证明对**；
受击链 SOP 约束**先编什么、测什么、运行时许不许可什么**。

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
| 对调 Flash `rotateSkew0`/`rotateSkew1`，或特效盖住就当命中 | 按 JPEXS `Matrix.transform` 建变换；画面斩击和 `*atm` 常是不同剪辑 |
| 按动作名锁死同名 `*atm` | `getHitObj` 无已命中标记；新 `PlaceObject` 可再中，须在显示列表变化时清记录 |
| 把 `_parent._x = opponent._x` 写成前冲，或跳上去也放大框必中 | 编 `body_warps`：832 只闪 X，同一水平面才能让 `*atm` 碰到 `bdmn`。面向/`bdmn._width` 编成 `xscale_*` 分支，不得按角色猜像素，也不得把其他形态 Sprite 编进当前切片 |
| 给「被打」加 `zhongli`，或手写抓取绑死对手 | `beidax` 非击飞不加重力；`cbs2` 的 `yup` 悬停，884 闪到对手身边；最后 `cbsatm` 才击飞对手 |

已发生的反面例子（不得重演）：

- 跳跃：把 `js` 带进下一个跳跃剪辑，一跳升到约 126 像素，能上现世 `ban2`。
  源是 step 1 七次 `14+13+…+8 = 77`，低于墙顶 78.65。
- 鸣人下+J：`砍技1`（260–290）没有终端脚本，空挥也进 `砍技12` 炸开；
  `kj10atm` 命中只是提前 `gotoAndPlay("砍技12")`。把 290 当成回站立，就会「有时不炸」。
- 大招受击：一护 `sbsatm`/`cbsatm`、鸣人 `cbs3atm` 是 `scale=0` 的旋转框。对调旋转分量后刀口收到身后，特效盖住对手也不结算。无旋转的 `k1atm` 测不出这个问题。细则见 [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md) 第 1.2 节。
- 鸣人下+I：`超必杀@832` 是 `_parent._x = opponent._x`，不是前冲。同一水平面才能让 `cbs1atm` 碰到 `bdmn`；跳到上面 Y 仍差一截。不得放大框或按角色补高度。
- 下+I 击中后带着走：源不是抓取。`beidax` 在「被打」里不加 `zhongli`，`cbs2` 把人抬住，884 攻击方闪到 `对手._y-40`。给「被打」加重力会提前落地，最后 `cbsatm@932` 击飞对手对不上。攻击方 942 自跳「击飞」不是对手受击。`cbsd@752`–`cbsw@829` 已按源停对手播放头；`blackMu`/`ts_face` 跟编译字段走。
- 手测「还能漏」不能证明该放大框。MATRIX、实例寿命、只抄 X 的闪现、`cbsd` 停对手，缺哪条补哪条编译/解释；没有步骤 E 轨迹不得称一比一。

## 编译优先于手写

新行为先进入 `tools/importer/build_combat_model.py`（或对应抽取器），再重建
`data/actions/*` 与 `godot/generated/fighters/*/combat.json`。运行时只解释已编译字段。

当前由源编译、禁止改回角色硬编码的字段包括：`motion_windows`、`jump_windows`、
`action_exits`、`timeline_fallthroughs`、`presentation_events`、`clip_placements`、
`body_warps`、
`command_catalog`、
`hit_priority`。受击链落地后还必须由源编译、禁止手写的字段见
[HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md) 步骤 B（`attacks_by_form`、`hits_reset_frames`、
`on_be_hit_frames`、`hit_fx`、`showFace`/`bsd` 等）。缺字段时补编译器，不要在
`FighterRuntime` 里写 `if fighter == "鸣人"`。

重建命令见 [OPERATIONS.md](OPERATIONS.md)。改编译器或契约后跑
`tools/verify.py`、`tools/check_handoff.py`；契约变更加跑 `tools/validate_contracts.py`。

## 回归必须锁原版不变量

Godot `combat_smoke.gd` 与 `tools/tests` 的断言对象是源行为，不是当前实现的形状。

- 通过：一跳顶点 77 且单跳落不回 `ban2`；空挥 `砍技1` 仍进 `砍技12` 并在 292 闪光、313 回站立；旋转 `*atm` 在身前相交并进源 `htype`。
- 不通过：为了让现有错误实现变绿而改期望值、放宽阈值、删除断言。只测轴对齐的 `k1atm`/`bs1atm` 就宣称大招受击完成。

对照顺序（与 [VALIDATION.md](VALIDATION.md) 一致，不可只看最后血量）：

输入锁存 → 动作与源帧 → 创建/移除的区域 → 碰撞候选顺序 → 伤害/状态/`hits`/破防 → 位置 → 视听（火花、顿帧、闪光、连击板、`bar2`、黑底、立绘横幅）。

没有固定输入的原版逐帧轨迹时，相关 M2/M3 任务保持未完成。截图和「能玩」只证明开发路径可运行。

## 跑步显示回退的固定回归

修改控制器、goto 调度或角色渲染时，必须运行
`player_controller_smoke.gd` 与 `player_visual_smoke.gd`，同时检查输入、逻辑朝向、
实际显示变换、父帧和可见子帧。原版按住方向会反复 goto 到「走」第 10 帧，
不能用父帧减 placed_frame 作为保留子实例的时钟。新放置重置，保留实例继续播放；
只测坐标或父帧会再次漏掉「人物平移但不跑」。旧的连续 advance_timeline 测试
不能替代真实菜单与源控制器路径。原因和证据见
[跑步显示回归记录](../evidence/combat/run-visual-regression/README.md)。


方向瞬身修改还需运行 `tools/test_ghost_reference.py --godot /path/to/godot`，覆盖招式中上/下＋L、两次输入、99 气拒绝和受击状态拒绝，并与上＋I 的普通/耗气瞬身案例一起对照。截图或网络技巧名不能替代当前版本的 `dash` / `hurtSkill` 分支；不得把方向瞬身和 O 受击脱离合并。详见 [原版输入证据](../evidence/combat/ghost-validation/README.md)。


生产战斗不得再按 AI/双人/练习选择不同的结算器或调度器。`useAI` 只选择原版输入分支；模式特例必须能指到源 `modo` 条件。共享战斗更改须运行 `tools/test_shared_modes.py`，并保留 Vs Com 原版回放；墙钟 `setInterval` 必须记录回调时序，不能换成固定帧数再宣称等价。

### Full move/boundary regression lessons (2026-09-09)

- A command entry and matching final HP do not prove its continuation. Compile
  complete conditional frame blocks and reject unrecognized conditional gotos;
  Naruto frame 538 previously disappeared from source execution.
- Separate source scalar coordinates from float32 render vectors. Native Flash
  truncates each coordinate assignment to twips; recovering an authored twip from
  its render projection is a different operation. Re-run platform landing and
  long AI tapes after such a shared change, not only the originally failing move.
- An absent source label can be referenced by a common controller. Preserve the
  original no-op, rather than inventing a move or throwing a runtime assertion.
- Record case execution, actual target/trigger coverage, and original parity
  separately. A process exit code or an `_OK` line cannot override SCRIPT ERROR.
  Preserve red traces; never round comparator output to hide a coordinate defect.
- Native Flash repeatedly foregrounded its window despite windowed mode and
  `open -g`. Do not claim that flag guarantees background operation. The user
  initially required probes not to cover their work, then explicitly allowed
  popup windows on 2026-09-09 and requested continued sampling. Keep windowed
  launches and use the explicit activation flag under that authorization; do not
  claim that the player stays behind other windows.

- Frame-function expansion must retain the caller's position in the frame's
  statement order. Keep nested function line numbers inside a call event; do not
  sort them together with caller lines. Do not confuse service operands with
  direct frame-state writes merely because both have a field name.
- Exact numeric comparison requires full-precision trace serialization. Godot's
  default JSON formatting can shorten 303.3333333333333 to 303.333333333333; use
  full precision in move recordings rather than rounding the comparator.
