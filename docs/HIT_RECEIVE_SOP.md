# 共用受击链与必杀演出落地 SOP

实施或修改**重击、破防、连击次数、命中火花、防御挡住、必杀黑底与立绘横幅**时必须按本页逐步做。
本页是 [SOURCE_FIRST.md](SOURCE_FIRST.md) 在这些链上的操作规程：源优先闸门约束怎么写代码，
[VALIDATION.md](VALIDATION.md) 约束怎么证明对，本页约束**先编什么、测什么、运行时许不许可什么**。

目标是一比一还原 `game/main.swf` 的 Flash 体验，不是「像格斗游戏该有的样子」。
答不全五问、缺编译字段、或只有截图/schema 绿，不得改 `godot/fighter_runtime.gd`，
也不得把 `M2-04` 或相关任务标完成。

查阅命令：

```bash
python3 tools/read_script.py scripts/fighter/minren.json --search "function beida"
python3 tools/read_script.py scripts/fighter/minren.json --search "function getHitObj"
python3 tools/read_script.py scripts/main.json --search "function bdxg"
python3 tools/read_script.py scripts/main.json --path DefineSprite_1833/frame_11/DoAction.as
python3 tools/read_script.py scripts/fighter/minren.json --search "showFace"
python3 tools/read_script.py scripts/main.json --search "function showFace"
```

## 1. 原版是什么（不得再猜）

35 个可玩角色的 `beida`、`fangyu`、`checkHit`、`onBeHit`、`isPoFangAct`、
带 `bdfyxg` 的 `onDefence(xgtype)` **函数体相同**。差异只在各形态 `gjlN` 表、
哪一帧调用这些函数、以及援助的 `gjl.atm*`。

26 个援助 SWF **没有**这套受击函数。援助只提供攻击参数；计数加在**被打者**
`mc.hits` 上。

| 现象 | 原版做法 | 源路径 |
|---|---|---|
| 命中取值 | `checkHit()` → `getHitObj()`：按 `hitks` 扫对手当前存在的 `{key}atm`，`this.hitTest(clip)` 是两剪辑 AABB | 各角色 `DefineSprite_*/frame_1/DoAction.as`（受击/攻击框元件都是 `DefineSprite_2`） |
| 判定几何 | Flash MATRIX：`x' = scaleX*x + rotateSkew1*y + tx`，`y' = rotateSkew0*x + scaleY*y + ty`。画面斩击和 `*atm` 常是不同剪辑 | JPEXS `Matrix.transform`；时间轴 `PlaceObject` 的 `matrix` |
| 再中条件 | `getHitObj()` **没有**“已命中”标记。同名 `*atm` 被移除后再 `PlaceObject` 是新实例，可再中 | 同上 `getHitObj`；时间轴 `changes[].move` |
| 破防 | `zl > 10`；`fangyu()` 减 10 后 `gotoAndPlay(htype)`，否则 `gotoAndPlay("防住")` | 同上 `fangyu()`；AI 用 `isPoFangAct` = `_curGJL[name+"zl"] > 10` |
| 重击档位 | 减 10 后的 1–10 交给 `_root.bdxg()`：1 `XG_kan`、2 `XG_qdj`、**3 `XG_qdjx`**、4 `XG_mfdj`、**5 `XG_mfdjx`**、**6 `XG_kanx`**、7–10 元素 | `scripts/main.json` → `frame_8/DoAction.as` |
| 重击顿帧/闪/抖 | 在 `XG_*x` 剪辑自己的帧脚本里：第 2 帧 `pauseGame()`+`shine()`，随后抖 `_root._x/_y`，第 15 帧 `resumeGame()` | 如 `DefineSprite_236_XG_qdjx` |
| 防住火花 | `onDefence(xgtype)`：默认 `bdfyxg`，`xgtype==2` 走 `bdfyxg2`；**不加 `hits`** | 角色共用脚本；鸣人三形态有 `onDefence(2)` |
| 防住刀光元件 | `bdfyxg` 的 1→`XG_fykan`、6→`XG_fykanx`、2→`XG_fyq`、3→`XG_fyqx`、4→`XG_mffy`、5/7–10→`XG_mffyx`，各自是独立 `DefineSprite`（216/214/200/196/280/279） | `frame_8/DoAction.as`；`main.swf` ExportAssets |
| 火花音效 | 每个 `XG_*` 剪辑第 1 帧一条 `StartSound`：`XG_fykan`=215、`XG_fykanx`=203、`XG_fyq`/`XG_mffy`=197、`XG_fyqx`/`XG_mffyx`=179 | 各 `DefineSprite` 的 `StartSoundTag` |
| 音量 | `SOUNDINFO` 的 `SOUNDENVELOPE`（0–32768）。197 是 `18008/18893`，比无 envelope 的 215 轻 | 同上 `soundInfo/envelopeRecords` |
| 连击计数 | `onBeHit()` 里 `hits++`；**仅 `hits > 1`** 才 `_root["p"+pn+"hits"].gotoAndPlay("连击")` | 各形态内层时间轴 frame_1 共用脚本 |
| 连击 HUD | `p1hits.pn=2`、`p2hits.pn=1`；`DefineSprite_1833` 第 1 帧 `stop()`，第 11 帧 `sz.changeNum(hits)`，第 50 帧回 1 | `scripts/main.json` → `frame_56/DoAction_2.as`、`DefineSprite_1828`/`1833` |
| 清零 | 各形态内层时间轴上整段等于 `hits = 0;` 的帧（实测都在该 Sprite 的 frame_2，属 `站立` 循环） | 例如鸣人 `DefineSprite_764/frame_2/DoAction.as` |
| 延迟血条 | 受害者 `hits != 0` 时 `bar2` 不追；`hits == 0` 才按 `maxhp/500` 每帧追 | `DefineSprite_1814/frame_1/DoAction.as` |
| 必杀黑底 | `bsd()`/`cbsd()` 内 `blackStg()`：`game.bgmc`/`fgmc` 隐藏，`blackMu.gotoAndStop`（默认帧 2） | `scripts/main.json` → `frame_8/DoAction.as` |
| 必杀立绘横幅 | `_root.showFace(pn, 标签)` 播 `_root.ts_face`：`bg` 走 `"in"`，`face_p1`/`face_p2` 的 `face.gotoAndStop(标签)` 再 `"in"` | 同上 `showFace`；角色时间轴只传标签名 |
| 必杀冻结与火花 | `bsd(pn)`：`zhanting=true`、`shine()`、`blackStg()`、停对手、挂 `XG_bs`；`cbsd` 另切 `_root.焦点` 并用 `XG_cbs` | 同上 `bsd`/`cbsd` |
| 必杀收场 | 对应帧 `_root.bsw(pn)` / `cbsw(pn)`：`hideFace`、`resumeBlackStg`、恢复对手播放、`zhanting=false` | 角色必杀后段 `DoAction`；`bsw` 内调 `hideFace` |

招式强度来自该玩家容器当前帧的 `gjlN`（`updateGJL`：`_curGJL = gjl` + `_currentframe`）。
`gjl2`/`gjl3` 与 `gjl1` 不是同一张表。鸣人基础 `kj1zl=15`，二形态破防在 `kj2zl=12`。

角色 `mc.pn` 是**对手**编号（与连击板 `p1hits.pn=2` 同一约定）。`showFace(pn, …)` 里
`pn != 2` 用 `face_p2`，`pn == 2` 用 `face_p1`：P1 放必杀时 `pn==2`，立绘出在左侧 `face_p1`。

### 1.1 必杀背景

截图里那条深蓝速度线横幅 + 高清立绘 + 场地变黑，**不是**招式时间轴自己画的背景，
也不是 `bdxg` 命中火花。根时间轴 `游戏场景` 上 `blackMu`（DefineSprite_1510，默认
`gotoAndStop(2)`）在 `_root.game` 后面，`ts_face`（DefineSprite_1678）也在 game 后面；
`blackStg()` 把 `game.bgmc`/`fgmc` 藏掉后才能透过 game 看到黑底和横幅。HUD 在 game 前面，
必杀时仍显示。

`bsd`/`cbsd`/`showFace`/`bsw`/`cbsw` 已编进 `super_events`。运行时解释根级 `zhanting`、
`stopMc(对手)`、隐藏 `bgmc`/`fgmc`、以及 `showFace` 的槽位/标签/`in` 帧。
`blackMu`（DefineSprite_1510）已导入：帧 1 空、帧 2–4 是 shape 535 的纯黑矢量矩形
（源 `fillStyleType=0` RGB 0,0,0，带 PlaceObject 缩放），不是自制全屏 ColorRect。
`ts_face`（1678）与 `XG_bs`/`XG_cbs` 已按 sprite id 导入；运行时只 `goto` 编译帧。
横幅 `bg` 上的线性渐变 shape 1516（`fillStyleType=16`）尚未画。`blackMu` 帧 5 `KO`
（sprite 1509）未接 `KOplay`。没有步骤 E 轨迹不得称一比一。

鸣人基础形态源调用（`DefineSprite_764`）：

| 帧 | 源调用 | 立绘标签 |
|---|---|---|
| 507 | `bsd` + `showFace` | `鸣人2` |
| 611 | `bsd` + `showFace` | `鸣人1` |
| 752 | `cbsd` + `showFace` | `鸣人2` |
| 1245 | `cbsd` + `showFace` | `鸣人3` |

一护、佐助等 35 个可玩角色都是同一对 `_root.bsd/_root.cbsd` + `_root.showFace(pn,"…")`，
只换标签字符串（`一户1`、`佐助2`、`一户万解` …）。横幅元件和黑幕在 `main.swf`，全角色共用。
场地放射白线、烟尘属于该招时间轴或 `XG_bs`/`XG_cbs`，必须跟对应源帧走，不得当成横幅的一部分手画。

### 1.2 判定几何与命中寿命（已踩过，不得再犯）

本次“大招特效盖住对手却不受击”确认过**公共矩阵和实例寿命**两类错误，但不能据此断定后续漏击也只有这两个原因。35 角色共用 `beida`/`getHitObj`；应沿输入、冻结、坐标、显示列表、碰撞、受击状态逐层取证，在确认的公共层修复。

**画面不等于判定。** `*atm` 多数是同一块 `DefineSprite_2` 矩形（约 1319×810 twips），靠 `PlaceObject` 矩阵拉成刀口。斩击图、全屏闪光、黑底是别的剪辑。特效盖住对手只证明演出在场，不证明 `getHitObj` 的 AABB 相交。

**Flash 旋转分量不能对调。** `scaleX=scaleY=0` 且 `rotateSkew0/1` 非零 = 约 90° 拉伸。Godot `Transform2D` 的两列是 `(scaleX, rotateSkew0)` 与 `(rotateSkew1, scaleY)`，对应 JPEXS：

```text
x' = scaleX * x + rotateSkew1 * y + translateX / 20
y' = rotateSkew0 * x + scaleY * y + translateY / 20
```

对调后，一护 `sbsatm@548`/`cbsatm@606`、鸣人 `cbs3atm@904` 会从身前宽刀口收成身后竖条：画面仍能盖人，站在身前的 `bdmn` 打不中。无旋转的三连、`k1atm`、鸣人 `bs1atm` 测不过这个问题。新判定回归必须带至少一个 `hasRotate=true` 的 `*atm`。

**命中记录跟剪辑走，不跟动作名走。** `getHitObj()` 只问“此刻对手身上有没有这个名字的 clip”。同一动作里同名 `*atm` 先移除再 `PlaceObject`（`move=false`），是新实例，可再中。按动作名把 `kj21atm` 锁到标签结束，鸣人 `砍技2@331` 中了之后 `@338` 永远不中。过期必须发生在**显示列表变化的那一帧**（`advance_timeline`），不能等到下一次 `attack_contact`：那时同名已经回来，旧记录会把新实例挡住。

**容器闪现不是走路，也不改判定高度。** 鸣人下+I `超必杀` 第 832 帧是 `_parent._x = _root.game["p"+pn]._x`，只闪 X。双人在同一水平面时，随后 `cbs1atm@837` / `cbs2atm@855` 才能碰到 `bdmn`；对手跳到上面时 Y 仍差一截，AABB 不相交。第 884 帧才抄 `_y - 40` 并 `jump = 1`。这是 `body_warps`，不是 `fensheng` 那种剪辑 `place_at_opponent`，也不得写成前冲或按「跳上去也该中」放大 `*atm`。

### 1.3 手测仍漏时检查完整动作链

编了 MATRIX、实例寿命和 `body_warps` **仍不是**一比一。`M2-04` 的完成条件是步骤 E 的原版同输入轨迹，不是 Web 能放、smoke 绿、或「同平面闪完看起来该中」。

手测「特效盖住 / 闪到身边还是漏」时，先对下面几条，**禁止**放大 `*atm` 或写角色必中：

1. **`cbsd` 冻对手：播放头已接。** `scripts/main.json` → `frame_8/DoAction.as` 的 `bsd(pn)`：`_root.zhanting = true`、`stopMc(对手.mc)`（`hited==0 && bs==0 && sw===false`）、`stopMc` 双方援助；`cbsd` 只是 `bsd(pn,"XG_cbs")` 再切焦点。`pn` 是对手编号，所以 `bsd` 把**放招者** `bs=1`、停的是对手播放头。`cbsw`/`bsw` 才 `playMc` 并 `zhanting=false`。鸣人 `超必杀` 是 752 `cbsd`、829 `cbsw`，之后才 832 闪 X。`on_enterframe` 在 `_root.zhanting` 时直接 return；`doAllAction`/`checkHit` 都在 `gameRunning()` 后面。运行时已解释这些冻结字段。`blackMu`/`ts_face`/`XG_bs`/`XG_cbs` 已按 sprite id 导入并跟 `super_events` 走；不得另贴自制横幅。
2. **同平面是 832 的前置，不是闪完必中。** `getHitObj` 仍要该帧 `{key}atm` 的 Flash AABB 与 `bdmn` 相交。鸣人 837 只有一块旋转 `cbs1atm`（约 157×55 本地像素），不是两个分身身体。画面上左右分身盖住对手，只证明演出在场。
3. **朝向、身体挤压都会拆开框。** `_update_facing` 只在 `站立` 改朝向；闪现当帧的 `_x` 跳变会被身体挤压夹到 ±30。Smoke 若只 `advance_timeline` + `incoming_attack_hits`、不跑 `resolve_body_pair`、不跑 `stopMc`，绿了也不能代替对局。
4. **击中后带着走，不是抓取，也不是给「被打」加重力。** 下+I 源里没有把对手坐标写成攻击方坐标的脚本。`beidax()` 非击飞只在 `time<=13` 用 `yup`/`htx`，**不加 `zhongli`**。`cbs2`（`yup=10`）把人抬在空中停住；攻击方 884 再闪到 `对手._y-40`，看起来像带着走。给「被打」加重力会提前落地，884 闪到空位置，后面对不上。最后一下击飞对手的是 `cbsatm@932`（`gjl.cbs.htype=击飞`），不是攻击方自己 942 的 `gotoAndStop("击飞")`。
5. **整条链才算这招。** 只测 `超必杀2@904` 起手或只测 832 闪 X，测不出悬停和最后 `cbsatm`。902 的 `gotoAndStop("螺旋手里剑1")` 是落地前的回环；没 `touchFloor` 就回站立会跳过 `超必杀2`。
6. **别的角色/别的大招不是同一条赋值。** 当前切片一护是 `DefineSprite_638`：`超必杀` 582–651 没有 `_parent._x = 对手._x`。面向翻转和 `bdmn._width` 在 **另一形态** `DefineSprite_1672` 的 `招3@442` / `上必杀@555`，鸣人另一形态 `DefineSprite_1821@372` 也有。编译器已收这两类分支，运行时只解释编译字段。不得把 1672/1821 脚本编进 638/764，也不得套鸣人 832。
7. **演出链资产已导入，仍缺对照。** `blackMu`/`ts_face`/`XG_bs`/`XG_cbs` 已按 ExportAssets 的 sprite id 导入。横幅渐变 1516 与 `blackMu` 的 KO 帧未接。没有步骤 E 轨迹不得称一比一。
8. **「被打不加 `zhongli`」不等于「被打不解算地面」。** `on_enterframe` 挂在**外层 wrapper 放置 body mc 的 clipAction** 上（`frame_1/PlaceObject2_638_1`、`frame_2/PlaceObject2_1180_1`、`frame_3/PlaceObject2_1672_1`），跟当前标签无关，`被打`/`击飞` 期间照跑。`onBeHit0()` 的 `jump = 1` 只让 `_y < floorY` 那条分支提前 return（因此空中悬停成立），一旦 `yup` 为负把身体压到地面及以下，就会落到 `if(_y > floorY - 10){_y = floorY; touch = touchFloor = true;}` 被拉回地面。防御时被 `zl > 10` 破防（鸣人 `cbs3zl=14`、`cbs3up=-3`）正是这种情况：对手站在地上挨打，每帧 `moveY(3)` 都当帧被拉回，不会陷进地里，`bdxg` 的 `XG_mfdj` 蓝块也就落在地面。运行时若在受击分支直接 return，会连着 `time<=13` 一路下沉几十像素，特效跟着沉下去看不见。`touch` 归 `on_enterframe` 维护，`beidax(true)` 的 `击落地` 判定依赖它，不得在受击分支里另写落地。

改这些之前先答五问：指出该帧 `*atm` 的 MATRIX、是新放置还是 MOVE、`getHitObj` 有没有已命中标记、容器赋值抄的是 X 还是 Y、`beidax` 在「被打」里有没有重力、`bsd`/`cbsd` 停的是谁的播放头。答不全不得按角色放大框、手写“大招必中”。

### 1.4 审阅后的补充：暂停必须覆盖所有消费入口

2026-09-08 最终工作树审阅中，40 项 Python 测试和现有 combat/menu smoke 均通过，
但两个源不变量仍失败，见 [复现与审阅记录](../evidence/combat/review-2026-09-08.md)。
不得把“站立对手不能走跳”扩大描述为“冻结全部正确”。

- `stopMc` 不停 `hited != 0` 的播放头，但 `beidax()` 自己在根级 `zhanting` 时返回。
  必须分别验证播放头、位移和受击计时，不能把它们合并成一个停播布尔值。
- 角色攻击、援助攻击和场地攻击都来自受害者同一个 `checkHit()`，共用
  `gameRunning()` 门槛。拆成多个 resolver 后，每个入口都要守住它；援助停播时
  旧攻击框仍在显示列表中，不能继续结算。
- 冻结矩阵至少包括站立、空中、被打、击飞、援助有效框和恢复首帧。
  接入主循环后还要验证真实双方推进、身体挤压、援助与演出一起运行的路径。
- 每次接续先对实际工作树、资产引用和测试重新核验，再更新状态；其他任务的
  “已导出”“已接线”是检查线索，不是当前版本的验收证据。
- 诊断探针应有退出码和超时。断言失败后 SceneTree 仍在运行不等于测试成功；
  记录退出码、成功标记和引擎错误。不能仅因前面出现 `COMBAT_SMOKE_OK` 就忽略退出时的资源问题。
- 原版固定输入轨迹缺失时，下一步应明确捕获入口、初态、按键与随机消费来源，
  不应反复用“仍不是一比一”代替完成这项验证工作。

### 1.5 援助时长与连续命中：先读代码，最后用 Flash 验证

2026-09-09 我爱罗 O 援助排查，同时覆盖魂。复现、范围和验证结果见
[援助时序记录](../evidence/combat/helper-timing.md)。

- **分开测四段时间。** 援助根播放头、子动画、有效攻击框、对手受击恢复各有自己的
  生命周期。根都是原帧数，不能证明困住对手的时间正确；禁止直接拉长根时间轴。
- **先读完整调用链。** 从 `yfgj`、援助根 DoAction、嵌套 Sprite、PlaceObject/MOVE，
  追到受害者 `checkHit → getHitObj → beida/fangyu → onBeHit/beidax`。魂的 Sprite 18
  虽定义旧版受击函数，但没有调用或 enterFrame 挂载；不得因为搜到函数就让它执行。
- **不能给援助补“一框一击”。** 原版 `getHitObj` 没有 consumed-hit 标记。我爱罗
  `atm1` 于 44 放置并保留到 85；魂于 37 放置、MOVE 后保留到 64，65 移除。
  同一实例仍可再次命中，频率由受害者的回调、受击框寿命、`canhit` 和暂停决定。
  禁止把旧缓存清理得更勤、按角色定连击间隔或每帧强制扣血当作修复。
- **取消缓存必须同时核接收时机。** 一护基础 738–740 没有 `bdmn`，739 执行
  `onBeHit`，741 新放置 `bdmn` 的 `beida()` 回调，下一根帧才执行。源控制器从回调
  发起检测；旧轮询入口也必须尊重放置当帧不执行，不能在 741 提前再中。
- **硬直计时不等动画 stop。** `beidax()` 在播放中的帧就已经 `time++`；编译其
  放置后的第一根回调帧，让旧轮询也从这里计时。等到 744 停播才倒数，会比一护
  原版恢复晚 4 帧。验证必须延伸至最后一击后恢复行动，不能只核命中次数。
- **内部 stop 必须编译。** 我爱罗 Sprite 48 第 33 帧 `stop()`，此时显示列表已空；
  即使根播放头继续走也不能循环。忽略它会在根 79–85 重新出现沙子和攻击区域。
  字段从源脚本编译，显示与碰撞消费同一个子播放头；禁止只藏画面不清判定。
- **测试不能只测第一击。** 同一攻击实例命中后，推进真实受击链，再检测第二击；
  覆盖左右朝向、MOVE、移除、空帧停播、`canhit=false`、暂停及恢复。至少一例走
  主场景 O 输入，记录每次结算帧/HP/hits、沙子消失、援助回收和恢复行动。
  魂另外核对六次独立扣气，不能把扣气次数当命中次数。
- **原版验证放在代码推导与回归之后。** 用隔离 SWF 副本、固定初态和相同输入，
  最后在原生 Flash 比较表现及轨迹；保存原始记录与首次差异，不调期望来凑绿。
  单测通过、静态推导和 Flash 验证分别记录，未验证部分不得称一比一。

## 2. 禁止事项

| 禁止 | 应做 |
|---|---|
| 在 GDScript 写 `if fighter == "鸣人"` 补重击/破防/连击 | 规则进共用运行时；数值进编译表 |
| 只抽 `gjl1`，变身沿用基础表 | 按形态编 `attacks_by_form[N]`，缺表标 `extracted_partial` |
| 按伤害、手感或「看起来重」选 `XG_*x` | 只用归一后的 `zl` 查 `bdxg` |
| 给援助单独做连击计数 | 援助命中仍走受害者 `onBeHit` |
| 第一下就显示连击板 | 源是 `hits > 1` |
| 防住也加 `hits` | 只有进入 `onBeHit` 才加 |
| 假设「第 2 帧清零」写死 | 编译所有整段为 `hits = 0;` 的帧 |
| 在运行时手写顿帧/闪光时长 | 编入 `XG_*` 剪辑的 `presentation_events` |
| Presentation 写回 `hits`/`hp` | HUD 只读快照 |
| 按角色在 GDScript 里贴一张「大招背景图」 | 编 `showFace` 标签 + 共用 `ts_face`/`blackStg` |
| 必杀全程手写黑屏时长 | 开始帧走 `bsd`/`cbsd`，结束帧走 `bsw`/`cbsw` |
| 把放射线/烟尘画进横幅层 | 跟招式时间轴或 `XG_bs`/`XG_cbs` 走 |
| 用 schema 绿、截图、改阈值代替对照 | 按第 6 节门槛 |
| 特效盖住对手就当命中，或按角色放大 `*atm` | 用 Flash MATRIX 算该帧 AABB，再对 `bdmn` 做 `getHitObj` |
| 对调 `rotateSkew0` / `rotateSkew1` | 按第 1.2 节公式建 `Transform2D`；无旋转用例不能代替旋转用例 |
| 按动作名把 `*atm` 锁到标签结束 | 实例离开显示列表就清；新 `PlaceObject` 可再中 |
| 只在 `attack_contact` 时清已命中表 | 在 `advance_timeline`（显示列表更新后）清已经消失的名字 |
| 把下+I 写成前冲，或跳到另一高度也放大框必中 | 编 `body_warps`：832 只闪 X；同平面才中，不同 Y 不中 |
| 给「被打」加 `zhongli`，或手写抓取把对手绑到攻击方 | `beidax` 非击飞不加重力；攻击方闪到对手坐标；最后 `cbsatm` 才是对手击飞 |
| 只测 `超必杀2` 起手或只测 832 闪 X | 必须走完 832→cbs1/cbs2 悬停→884→落地 `超必杀2`→`cbsatm` 击飞 |
| 手测大招仍漏就放大框 / 写必中 | 先对第 1.3 节：`cbsd` 是否停对手、该帧有没有 `*atm`、是不是另一条未编译赋值 |
| 把放招者身上的 `zhanting` 当成已实现 `bsd` | `_root.zhanting` + `stopMc(对手)`；`super_end` 才 `playMc` |
| 按名字手挑一个音效或自己调音量 | 只播该剪辑第 1 帧 `StartSound` 的 `soundId`，音量按 `SOUNDENVELOPE` |
| 按目录名认剪辑 | 用 ExportAssets 的 sprite id 核对；`XG_mfdj`(314) 与 `XG_mfdjx`(298) 曾被导反 |
| 给源里不存在的剪辑补自制资源 | `XG_stone`（`bdxg` 10）、`XG_jump`、`XG_luodi` 在 `main.swf` 全无 ExportAssets，原版就是空操作 |

已发生、不得重演的同类错误：跳跃把 `js` 带进下一剪辑；把标签 `end_frame` 当回站立。
受击链上对应的反面是：把 `zl>10` 当成独立防值条，或按角色猜「这招是重击」。
必杀演出上对应的反面是：给鸣人单独铺一张立绘，而不是走 `showFace("鸣人2")`。
判定上对应的反面是：大招特效盖住对手却不受击时，给鸣人/一护写受击补丁或放大框，而不是修共用 MATRIX 与 `PlaceObject` 寿命。
闪现后仍漏时对应的反面是：不读 `bsd`/`stopMc`，却把 832 只抄 X 的招改成吸到空中或放大 `cbs1atm`。

## 3. 落地顺序（必须按步，不得跳）

每一步结束要有源路径或测试证据。前一步红，不准开始改运行时。

### 步骤 A — 源清单锁共用链

在 `tools/tests` 对 **35** 个 `scripts/fighter/*.json`（不含 `fz/`）断言：

- `beida` / `fangyu` / `checkHit` / `onBeHit` / `isPoFangAct` / 含 `bdfyxg` 的 `onDefence` 归一化哈希一致
- `onBeHit` 含 `hits++` 且仅 `hits > 1` 触发 `"连击"`
- 每个出现 `gjlN` 的形态 Sprite，都有至少一帧整段为 `hits = 0;`
- 每个可玩角色至少有一处 `_root.showFace(pn,"…")`，且与 `_root.bsd` 或 `_root.cbsd` 成对（万解可只有 `showFace`，如一护 `wankai_start()`）
- `showFace` 的标签字符串必须出现在该角色源里，禁止编译器发明英文 cut-in 名

对 **26** 个 `scripts/fighter/fz/*.json` 断言：没有上述受击函数，没有 `hits++`。
援助可以有 `bsw`（收场），但立绘标签仍只来自主角时间轴的 `showFace`。

任一角色脚本以后分叉，测试必须红。此时停下来读源，禁止在运行时打补丁。

### 步骤 B — 编译器补字段

新字段进 `tools/importer/build_combat_model.py` 与 `build_helper_model.py`，
再重建 `data/actions/*` 与 `godot/generated/fighters/*/combat.json`。
契约变更跑 `tools/validate_contracts.py`。

| 字段 | 来源 | 缺了怎么办 |
|---|---|---|
| `attacks_by_form[N].*.impact_strength` 等 | `gjlN.<name>zl/pw/up/x/tm/dz` | 不得用 `gjl1` 顶；标 `extracted_partial` |
| `hit_priority.instances` | 已有：`hitks` + 1–5 | 已编译则保持 |
| `hits_reset_frames` | 源整段 `hits = 0;` 的帧号与 Sprite | 不写死 frame 2 |
| `on_be_hit_frames` | `onBeHit()` / `onBeHit(true)` | `true` 才是击飞路径的 `flying` |
| `wall_hit_near` | `onBeHit` 的 `_parent.hitWall` 分支、距离 100 与朝向/500 分界；场景 `DefineSprite_1991` 在角色回调后更新墙限与 `hitWall` | 不得把场景墙限放到根观察点之后，也不得在离墙后擅自清空 `hitNear`；见[原版墙边对照](../evidence/combat/rifagu-base/wall-source-first.md) |
| `on_defence_frames` + `xgtype` | `onDefence()` / `onDefence(2)` | `2` → `bdfyxg2` |
| `hit_fx`（`bdxg` / `bdfyxg` / `bdfyxg2` 表） | `scripts/main.json` → `frame_8/DoAction.as` | 表变更则全角色一起变 |
| `hit_fx_clips[].presentation_events` | 各 `XG_*` 的 `pauseGame`/`shine`/`_root._x`/`resumeGame`/`unloadMovie` | 不得按招式臆造时长 |
| `XG_*` 时间轴与位图 | 按 ExportAssets 的 sprite id 跑 `extract_timeline_geometry.py` + `materialize_timeline_assets.py` | 名字对不上就是导错剪辑，不得靠改目录名蒙过去 |
| 帧上的 `start_sound`（含 `envelope`） | 该 `DefineSprite` 的 `StartSoundTag`/`SOUNDINFO`；`DefineSound` 的 mp3 一并落到剪辑目录 | 不得自选音效或按手感调音量 |
| `start_sound` 的 `in_point`/`out_point` | 同一 `SOUNDINFO`；单位是 44.1 kHz 采样，与 mp3 自身采样率无关。`XG_bs`=5100/51340（444.mp3 为 11025 Hz、1.202 s，即 0.116–1.164 s），`XG_cbs`=51892 | 不得整段播完或按 mp3 采样率换算 |
| `combo_hud` | `p1hits.pn`/`p2hits.pn`、`DefineSprite_1833` 第 1/11/50 帧、`changeNum` | HUD 属 Presentation |
| `presentation_events`：`super_start` / `super_end` | 源帧 `_root.bsd`/`cbsd`/`showFace`/`bsw`/`cbsw` | 只编调用，不编自制横幅 |
| `face_label` | `showFace(pn,"鸣人2")` 的字符串 | 必须与 `ts_face` 内 `face` 的帧标签对得上 |
| `ts_face` / `blackMu` 资产 | `game/main.swf` 的 `_root.ts_face`、`_root.blackMu` | 按 sprite id 导入；`blackMu` 帧 2 的黑底是源 shape 535，不得另画全屏矩形 |

当前已知缺口（不得宣称整条链或 `M2-04` 完成）：

- `attacks_by_form` / `hits_reset_frames` / `hit_fx` / `combo_hud` / `super_events` 已编译；运行时已解释 `hits`、连击板、`bar2` 追血、`XG_*x` 的 pause/shine
- `bdxg` 的 6 个剪辑与 `bdfyxg`/`bdfyxg2` 的 `XG_fykan`/`XG_fykanx`/`XG_fyq`/`XG_fyqx`/`XG_mffy`/`XG_mffyx` 已按 ExportAssets 的 sprite id 导入，并带各自第 1 帧 `StartSound` 的 mp3；运行时只解释时间轴上的 `start_sound` 与 `envelope`
- `bdxg` 的元素档位 `XG_fire`(423)/`XG_ice`(358)/`XG_leidian`(334) 已按 sprite id 导入并带第 1 帧 `StartSound`（396/337/317）；`zl` 10 的 `XG_stone` 在 `main.swf` **没有 ExportAssets**，原版 `attachMovie` 也挂不上，不得补自制资源。档位随附的 `setColor`/`ColorMatrixFilter` 仍未实现，当前切片也没有 `zl` 7–10 的招式
- 角色时间轴上的 `StartSound` 已按该帧 `soundId` 物化 mp3，运行时进入该源帧时播放；`SOUNDINFO` 音量与火花同一套 envelope。`stageSound` BGM 已编成 `godot/generated/music/music.json` 并有 `godot/stage_sound.gd` + `tests/stage_sound_smoke.gd`，**尚未接进 `main.gd`**
- **`ts_face` / `blackMu` / `XG_bs` / `XG_cbs` 已按 sprite id 导入**并跟 `bsd`/`showFace` 走。尚未画横幅线性渐变 shape 1516；`blackMu` 帧 5 `KO` 未接 `KOplay`。步骤 E 仍缺，不得宣称横幅一比一完成
- 面向 / `bdmn._width` 容器闪现已编成 `body_warps` 的 `xscale_gt_0`/`xscale_lt_0` 与 `x_bdmn_width`/`y_bdmn_height`。当前切片 638/764 **没有**这些脚本；1672/1821 是其他形态
- 步骤 E 原版同输入轨迹仍缺，`M2-04` 保持 pending。当前切片**不得**称一比一还原

### 步骤 C — 运行时只解释编译字段

`FighterRuntime` / 战斗结算只允许：

1. 命中后取当前形态表的攻击记录（含 `impact_strength`）。
2. 防御中且 `zl ≤ 10`：伤/10、气按 `onDefence` 公式、进「防住」、播 `bdfyxg(xgtype)`、**不加 `hits`**。
3. 否则：`zl > 10` 则减 10；`goto` 源 `htype`；在 `on_be_hit` 帧执行 `bdxg`、`hits++`、`hits > 1` 发 HUD 事件、`hitlosehp`。
4. 当前源帧 ∈ `hits_reset_frames`：`hits = 0`。
5. 援助命中复用 2–4，不另写援助连击。
6. 源帧出现 `super_start`：根级 `_root.zhanting`、闪光、**`stopMc` 对手 `mc` 与双方援助**、`blackStg`、按 `face_label` 播 `ts_face`、挂 `XG_bs`/`XG_cbs`；`cbsd` 才改焦点。源帧出现 `super_end`：`playMc`、`hideFace`、`resumeBlackStg`、`zhanting=false`。运行时只解释编译字段和已导入时间轴，不得另贴自制横幅或用放大框弥补未冻结的对手。

Presentation 读 `hits`、火花 id、顿帧/闪光/抖屏、`ts_face` 标签、`blackMu` 帧。禁止 HUD 或特效节点改血量、气量、`hits`。

### 步骤 D — 回归锁源不变量

`tools/tests` 与 `godot/tests/combat_smoke.gd` 只断言源能指到的现象：

| 案例 | 通过条件 | 不通过（禁止拿来凑绿） |
|---|---|---|
| 单下命中 | 受害者 `hits==1`，不播「连击」 | 第一下就显示数字 |
| 未回站立再中一下 | `hits==2`，攻击方一侧 HUD 进「连击」，第 11 帧数字为 2 | 左右板读错 `pn` |
| 回站立经过清零帧 | `hits==0`，`bar2` 才开始追 | 站着走两步才清、或走路也清（除非源有） |
| `zl=15` 打在防御上 | 进源 `htype`（鸣人下+J 为击飞）、火花 `XG_mfdjx`、`hits` 加一 | 当普通防住或未知效果 |
| `zl=2` 打在防御上 | 「防住」、`bdfyxg`、`hits` 不变 | 破防或加连击 |
| `zl=1` 打在防御上 | 「防住」、`XG_fykan` 刀光在受击者身上播出并起 `StartSound` 215，第 11 帧 `unloadMovie` | 用 `XG_fyq` 顶、只记名字不出画面、或静音 |
| `XG_fyq` 的音量 | 按 `SOUNDENVELOPE` `18008/18893` 衰减（约 −5 dB） | 全部按满音量播 |
| `XG_qdjx` 播出 | 源第 2 帧停游戏并 `shine`，第 15 帧恢复 | 只贴火花、不停顿 |
| 旋转 `*atm`（一护 `sbsatm@548`/`cbsatm@606`、鸣人 `cbs3atm@904`） | Flash `x' = scaleX*x + rotateSkew1*y`，刀口在身前且能结算 `getHitObj` | 对调 `rotateSkew0/1` 收成身后竖条，特效盖住也不受击 |
| 同名 `*atm` 再次 `PlaceObject`（鸣人 `kj21atm@331` 与 `@338`） | 第一段离开显示列表后第二段可再中 | 按动作名锁死整段，后窗永远不中 |
| 鸣人 `超必杀@832` 只抄 X | 同地面则 X 对齐后 `cbs1atm@837` 可中；对手 Y=-80 则不相交 | 写成前冲、吸到空中、或放大框 |
| 下+I 击中后带着走 | `cbs2` 后对手停在空中；884 攻击方在 `对手.y-40`；`cbsatm@932` 进击飞 | 给「被打」加重力提前落地，或把 942 自跳当成对手击飞 |
| `cbsd@752`–`cbsw@829` | 对手播放头停住，不能跳离平面 | 只给放招者一个 `zhanting` 布尔，对手仍能走/跳。冻结已接线后，缺的是黑底立绘而不是再放大框 |
| 鸣人基础第 507 帧 | 有 `bsd` + `showFace("鸣人2")`：场景隐藏、`blackMu` 非第 1 帧、`ts_face` 左侧立绘为该标签 | 只黑屏没有横幅，或用错「鸣人1」 |
| 对应 `bsw` 帧 | `hideFace`、`bgmc`/`fgmc` 恢复、`zhanting==false` | 必杀结束后背景一直黑 |
| 换一护/佐助同一套输入 | 结果只允许因该形态 `gjlN` 与 `face_label` 不同而不同 | 为某角色改 GDScript 分支或手贴立绘 |

已有应继续保持：`zl=15` → `XG_mfdjx` 破防；上+U 第二段 `zh32` → `XG_qdjx`。
不得为让新断言变绿而改旧期望、放宽阈值、删测试。

### 步骤 E — 原版同输入对照

固定：AI 关、现世、鸣人基础 vs 一护基础、默认键位。至少走：

1. 三连（轻击 `zl=2`，单下无 HUD，第二下起连击板）
2. 防住普通斩
3. 下+J 破防（`zl=15`）
4. 上+U 第二段重击火花
5. 受击后回到 `站立` 清 `hits`，`bar2` 开始追
6. 鸣人 `必杀`/`上必杀`/`超必杀`：源 `bsd`/`cbsd` 帧出黑底+`ts_face` 横幅，`bsw`/`cbsw` 帧收回
7. 一护 `上必杀`/`超必杀`、鸣人 `超必杀2`：旋转 `*atm` 在身前相交，对手进源 `htype`（击飞/被打），不是只播特效

比较顺序与 [VALIDATION.md](VALIDATION.md) 相同，不可只看最后血量：

输入锁存 → 动作与源帧 → 创建/移除的区域 → 碰撞候选顺序 → 伤害/状态/`hits`/破防 → 位置 → 视听（火花、顿帧、闪光、连击板、`bar2`、黑底、立绘横幅）。

没有固定输入的原版轨迹时，`M2-04` 及相关项保持 pending。截图和「能玩」只证明开发路径可运行。

## 4. 新角色 / 新形态 / 援助

1. 跑步骤 A。可玩角色哈希仍一致则**不要**为他写受击 GDScript。
2. 编译他的全部 `gjlN`、`hits_reset_frames` 与全部 `showFace` 标签。缺形态表或缺 `ts_face` 对应帧不得标该形态必杀完成。
3. 援助只编 `gjl.atm*`，命中走对手已有受击链；援助收场的 `bsw` 不得冒充主角立绘。
4. 哈希不一致：先对照 `scripts/fighter/<id>.json` 的源函数，更新共用规则与步骤 A 的期望哈希；禁止 `if fighter == ...`。

全内容阶段（M6）仍按覆盖表逐条验证，不得因「规则共用」把未编译、未对照的角色标完成。

## 5. 五问（本链专用）

改运行时或把任务标完成前，每条都要有源路径（`scripts/*.json` 的 `path`、时间轴帧、或 `evidence/probes/`）：

1. **这一段每一帧的 `DoAction` / `enterFrame` 是什么？**  
   受击标签从进入到离开：`onBeHit` 当帧、`beidax` 的 clip `enterFrame`、`beida` 的判定框、`stop`/`goto`。空帧也要列出。
2. **剪辑是新 `PlaceObject` 还是 `MOVE`？**  
   `XG_*`、连击板、`bdmn`、`*atm`、`ts_face`、`blackMu`、`XG_bs` 各自何时放置。新实例不继承 `hits`；`hits` 在角色 `mc` 上。`ts_face` 是根上已有实例，用 `gotoAndPlay("in")`，不是每记必杀新建。同名 `*atm` 先移除再放置，是新判定实例，不得沿用上一段的“已命中”。
3. **离开当前标签的方式是哪一种？**  
   `fangyu` 的条件 `goto`（破防/`防住`）、`beidax` 到 `tdtime` 后 `play()`、击飞落地 `gotoAndStop("击落地")`、站立循环里的 `hits = 0`、必杀后段的 `bsw`/`cbsw`。不要把标签 `end_frame` 当回站立或自动收横幅。
4. **测试断言的是原版不变量，还是实现假设？**  
   只允许第 3 节表格和第 1 节源路径里的现象。
5. **同一套输入在原版 `game/main.swf` 里走过一遍吗？**  
   步骤 E。没有则状态保持待验证。

## 6. 完成门槛

同时满足才允许称这条链在**当前切片角色/形态**上落地：

- 步骤 A 测试绿，且覆盖 35+26 个 bundle
- `gjl1` 以外的形态表已抽出，或该形态明确标 `extracted_partial` 且未宣称完成
- 运行时无角色名分支；战斗字段均来自编译结果
- 步骤 D 的 smoke/源测试绿，期望值未为凑绿而改
- 步骤 E 有原版同输入记录（动作/源帧/`hits`/火花/HUD/黑底/立绘标签），差异已分类而不是抹掉
- 必杀演出：`ts_face` 与 `blackMu` 已按 sprite id 从 `main.swf` 导入；横幅渐变 1516 与 KO 帧仍缺时不得宣称必杀一比一完成
- `tools/verify.py`、`tools/check_handoff.py` 通过；契约变更加跑 `tools/validate_contracts.py`

未满足时：文档与 `docs/STATUS.md` 写清缺口，任务保持 pending。
