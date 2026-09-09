# 原版电脑 AI 复刻规格

日期：2026-09-08。状态：**静态分析规格；未完成原版固定随机序列的实战对照**。
适用基准：普通 BVN 2.6，`game/main.swf`，SHA-256
`707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`。
对应需求 FR-08、TR-02、TR-03、TR-04、TR-06、TR-07；实施任务 M5-03。

## 1. 范围、证据与结论

原版 AI 是**时间轴动作窗口 + 共享控制函数 + 角色感知区域 + 定期刷新随机值**。
它读取对手当前状态，没有发现搜索未来局面、学习模型、按难度更换策略树的代码。
难度影响随机值分布；招式是否可用、何时允许接招、位移和伤害仍由角色源时间轴决定。
不能用“每隔半秒抽一个动作”或“模拟按下几个键”替代这条控制链。

本次扫描全部 62 个脚本 bundle，其中 35 个主角色、26 个援助、1 个主程序。
发现 69 份控制器脚本，按**完整原文**分为 9 组；49 处 `randAI` 函数定义原文相同，
覆盖全部 35 个主角色 bundle。69 不表示 69 个可选人物或已证明可达的形态。
全形态的 SWF 放置关系与菜单可达性仍须单独核实。

证据分三级：

| 级别 | 本规格使用方式 | 不代表什么 |
|---|---|---|
| S：锁定脚本 | 函数条件、参数、顺序、调用路径 | 不单凭函数存在认定可执行 |
| T：已有时间轴导出 | 鸣人基础 764、一护基础 638 的实例、矩阵、线性显示列表 | 不表示所有跳转路径已运行 |
| P：已有 Adobe FP32 调度探针 | `goto` 调用者继续执行、停止播放仍有回调/定时器等 | 不表示整场游戏或 AI 随机相位已验收 |

可重复生成的 [source-audit.json](../evidence/ai/source-audit.json) 包含：

- 输入文件哈希、全部难度引用、311 个含随机调用的源代码行（不是运行时调用次数）。
- 九组控制器的全部出处、原文 SHA-256、相对鸣人公共控制器的逐行 diff。
- 随机、初始化、受击脱身、援助等核心函数的原文、分组及出处。
- 两个基础切片的 AImain 显示列表和矩阵、全部 Sprite 16 enterFrame 脚本、
  逐源帧脚本索引（空列表明确表示该帧没有导出的脚本）。

重建与检查：

```bash
python3 tools/analyze_ai.py
python3 tools/analyze_ai.py --check
python3 tools/read_script.py scripts/fighter/minren.json --path DefineSprite_16/frame_1/DoAction.as
```

分析器按锁定 JPEXS 导出的列首函数格式提取定义；它是资料索引，不是 AS2 编译器。
时间轴证据来自当前已有切片文件，本次未重新导出全部 SWF。

### 1.1 源路径约定

分析与复刻顺序固定为：**源代码 → 时间轴与实例结构 → 编译结果 → 原生实现 → 对照验证**。
SWF 的时间轴、矩阵、实例放置也是程序输入，应解析其结构；播放画面不能替代这些结构。
逐条条件、比较端点、赋值覆盖、随机调用顺序和显式 return 直接按源保留，
无需先观察电脑“通常怎么打”再设计策略。不得根据录像反推攻击概率、反应延迟或招式优先级。

反编译文本遇到作用域或控制流歧义时，先核对原始 Action 字节码及实例生命周期。
只有剩余的播放器语义问题才使用最小代码探针；完整对战日志用于定位移植与原版的首个差异。
测试不能反过来改写明确的源条件，未验证的调度推论也不能写成确定规则。

文内以下简称均指 bundle 内保留的原始 `path`，不是新建 AS 文件：

| 简称 | bundle 与原始 path |
|---|---|
| MAIN7 | [main.json](../scripts/main.json)，`frame_7/DoAction.as` |
| MAIN8 | 同上，`frame_8/DoAction.as` |
| OPTIONS | 同上，`DefineSprite_836/frame_1/PlaceObject2_691_1/CLIPACTIONRECORD onClipEvent(...).as`，分别为 load、keyDown、enterFrame |
| START | 同上，`DefineSprite_1900/frame_5/DoAction.as` |
| CTRL | [minren.json](../scripts/fighter/minren.json)，`DefineSprite_16/frame_1/DoAction.as`；一护同路径原文一致 |
| BODY | 同上，`DefineSprite_764/frame_1/DoAction.as`；一护基础对应 638 |
| WRAPPER | 主角色 bundle，`frame_1/DoAction.as` |
| N@F | minren bundle，`DefineSprite_764/frame_F/...` |
| I@F | [yihu.json](../scripts/fighter/yihu.json)，`DefineSprite_638/frame_F/...` |

### 1.2 实现前五问的当前答案

1. **每帧脚本**：基础切片全帧索引和控制剪辑原文已入审计；第 8 节列出决策窗口。
   其他形态尚无全帧索引，不得因共用函数相同而直接放行。
2. **PlaceObject / MOVE**：基础两者 AImain 在根帧 1、深度 1 新放置，线性时间轴中
   没有后续深度 1 变更；控制剪辑的放置帧、深度、显示列表成员帧见审计。
   跳转造成的重建、加载首帧回调和定时器相位仍需实例日志。
3. **离开方式**：必须执行实际调用点的有序 `gotoAndPlay`、`gotoAndStop`、`stop/play`
   与自然落帧；不能按标签结束统一回站立。审计保留全帧源路径，第 8 节不是替代动作模型。
4. **原版不变量**：第 12 节的阈值、求值顺序、来源绑定都能指回源；运行时未知项另列。
5. **原版同输入**：已采集原版固定简单对战 600 帧，但移植端尚未通过同输入对照。已有调度探针见
   [ExecutionProfile](../spec/execution-profile.json) 和
   [调度记录](../evidence/probes/schedule/README.md)，不能将其当作 AI 验收。

上述未知项尚未全部解决，M5-03 与 U-05 不得标为完成。
后续编译进度和原版最小探针见 [compiler-progress.md](../evidence/ai/compiler-progress.md)；
27 个判定函数、8 个调度函数和一护 30 个控制回调已生成原生 GDScript 并接入固定 Vs Com 开发入口；KO 换局也已接线，均尚未完成原版对照。
原版固定简单对战已采集开场后 600 帧，见上述进度记录；这不是 Godot 对照验收。

## 2. 对象与控制入口

```text
_root
  AI, p1cpu, p2cpu, zhanting, gamePaused, airanset
  game.p1 / game.p2                 Fighter container
    useAI, scale_X, _curGJL, gjlN
    mc                             Current form timeline
      pn                           Opponent number, not self number
      hp, ql, 动作, sw, canhit, touch, touchFloor, hitBan
      attran, defran, goran, jumpran, bisharan
      AImain                       Per-form sensor clip
      placed controller clips      CTRL functions + per-placement ClipActions
  game.p1fz / game.p2fz             Assistance clips
```

WRAPPER 的 `initCtrl(ai)` 赋值 `useAI=ai`，再调用 `mc.initCtrl()`。
BODY 的 `pn`：容器名为 `p1` 则取 2，否则取 1；CTRL 的 `_parent` 是自身 `mc`，
`_parent._parent` 才是角色容器。移植时必须消除路径歧义，不能将 `pn` 当自身玩家号。

BODY `initCtrl()` 按以下顺序执行：

1. `useAI == undefined`：返回，不初始化。
2. 更新自身及对手 `updateGJL()`；`_curGJL` 来自容器当前帧对应的 `gjlN`。
3. 电脑：`AImain.gotoAndStop(2)`，`_root.airanset=setInterval(randAI,500)`。
4. 玩家：`AImain.gotoAndStop(1)`，`AImain.unloadMovie()`。

大部分 CTRL 判断先检查 `!useAI`：玩家走 `kis(键)`，电脑读状态/感知/随机值。
这些判断返回真假，不直接扣气或造成伤害。调用点决定跳到哪个动作标签；标签帧脚本才
改变动作值、气量、攻击实例等。例外是 `rush()` 可当场更新朝向，见第 6 节。

## 3. 模式、难度与生命周期

### 3.1 哪些模式开启电脑

菜单按钮各自第 15 帧的脚本明确写入：

| main Sprite | modo | p1cpu | p2cpu | 下一步 |
|---|---:|---|---|---|
| 594 | 1 | false | true | HOWTOPLAY |
| 597 | 2 | false | true | 选人画面 |
| 600 | 3 | false | false | 选人画面 |
| 603 | 4 | false | false | 选人画面 |

START 先恢复指定形态帧，再依次调用 p1、p2 的 `initCtrl`。原菜单这些入口没有双电脑模式。
训练模式不自动启用电脑。双方电脑只能作为额外诊断配置，不能据此推断原版正式模式行为。

### 3.2 难度映射及设置持久化

OPTIONS 的 enterFrame 先 `gotoAndStop(cl)`，再分别判断 cl 并赋值：

| 设置第几档 cl | `_root.AI` | 随机取值范围 |
|---:|---:|---|
| 1 | 5 | [0,500) |
| 2 | 4 | [0,400) |
| 3 | 3 | [0,300) |
| 4 | 2 | [0,200) |
| 5 | 1 | [0,100) |

MAIN7 默认 `AI=5`。已存在设置时从 `SharedObject.getLocal("bvn_5d")` 的 `.data.AI`
读取，读取整组设置的门槛是 `.data.w != undefined`，并非独立检查 AI 有效性。
设置确认/退出脚本在 `DefineSprite_836/frame_1/PlaceObject2_739_33/...keyDown.as`
写回 `.data.AI`。本规格不为五档菜单图形补猜中文名称。

**边界原样记录**：keyDown 中左键用 `cl >= 1` 才 `cl -= 1`，右键用 `cl <= 5`
才 `cl += 1`，所以源条件允许临时得到 0 或 6。enterFrame 仅处理 1～5，
并没有 clamp 或默认赋值。该越界时实际显示、播放头和后续键行为需原版探针，
不能把更合理的边界逻辑写成“原版”。A/D 同时按下也按两个独立 if 的源顺序执行。

### 3.3 回合、重开、变身与清理

- MAIN8 `clearint()` 调用 `clearInterval(_root.airanset)`；多处返回/胜负路径调用它。
- `DefineSprite_1848/frame_350`、`DefineSprite_1858/frame_394` 的同局 `nextfight`
  重置站立、位置相关状态、`sw` 等，未重新调用 `initCtrl` 或 `randAI`；不能自动每回合重置随机相位。
- BODY `doWanKai()` 调用 `initCtrl()`；新形态进入可能再次注册 interval。
  `initCtrl` 内没有先 clear 老 interval 或“已初始化则返回”的保护。
- interval 句柄是根级单一 `airanset`。多次注册会覆盖存储的句柄，源文本并不能证明旧回调已消失。
  旧形态销毁、回调接收者、重复初始化后的存活定时器必须实测，见 AI-U03。
- CTRL `wankai()` 的电脑分支直接返回 false：标准入口不会让电脑按“斩+跳”主动变身。
  这不排除加载指定形态或时间轴其他路径带来的形态变化。

## 4. 随机与时钟

### 4.1 固定消费顺序

BODY 的 `randAI()` 每次读取当时的根级 AI，令 `R=100*AI`，然后严格按顺序消耗五次随机数：

```text
attran   = Math.random() * R
defran   = Math.random() * R
goran    = Math.random() * R
jumpran  = Math.random() * R
bisharan = Math.random() * R
```

除 `randAI` 外，本次全 bundle 扫描未发现这些五个变量的额外赋值入口。
函数本身没有暂停、死亡或 readying 判断。初始化路径只注册 interval，没有立即调用
`randAI()`。首次回调前不能用全零补齐；需保留尚未赋值与有效随机样本的区别。

同一次刷新后的值会被多个动作窗口重复读取。`attran<50` 与 `attran<100` 等条件高度相关，
不能给每个技能独立抽签，也不能把当前随机值当作逐帧抽取的新样本。
函数只读随机值的调用不消费新的随机数；判断短路会改变状态读取，但不增加抽签。

### 4.2 概率是条件通过率

对于有效五档：`P(r<t)=clamp(t/R,0,1)`；`P(a<r<b)=max(0,min(b,R)-max(a,0))/R`。
表中四舍五入，不用于生产比较。生产保留源比较运算符及浮点值。

| 条件 / 代表路径 | AI=5 | AI=4 | AI=3 | AI=2 | AI=1 |
|---|---:|---:|---:|---:|---:|
| g<120：向对手移动 | 24% | 30% | 40% | 60% | 100% |
| a<100：范围内普通出招 | 20% | 25% | 33.33% | 50% | 100% |
| a<120：对手受击时续普攻 | 24% | 30% | 40% | 60% | 100% |
| d<100：防普通攻击 | 20% | 25% | 33.33% | 50% | 100% |
| d<130：防必杀/援助 | 26% | 32.5% | 43.33% | 65% | 100% |
| g<30：受击脱身 | 6% | 7.5% | 10% | 15% | 30% |
| 100<j<130：非追高的随机跳 | 6% | 7.5% | 10% | 15% | 0% |
| b>95：部分非受击目标的必杀分支 | 81% | 76.25% | 68.33% | 52.5% | 5% |
| 200<a<300：部分对防御目标出招 | 20% | 25% | 33.33% | 0% | 0% |
| a>90 且 b<100：对 D<2 的援助判断 | 16.4% | 19.375% | 23.33% | 27.5% | 10% |

最后一行以两次随机调用均匀、独立的通常模型推导；不代表已统计原版 RNG 的质量。
所有比例都还受空间、动作窗口、气量、前序分支及后续 goto 影响，**不是实战使用率**。
高难度不是所有行为单调增强：一些区间在 R=100/200 时根本不可达。

### 4.3 半秒与 30 Hz 不可合并为一个计数器

`setInterval(...,500)` 是毫秒定时器；动作窗口是主程序 30 Hz 的显示/时间轴回调。
正常速度下半秒约 15 显示帧，但不能未经验证改成“每 15 战斗 tick 刷新”。
MAIN8 的 pauseGame 设置 `zhanting` 并选择性 stop 剪辑，未 clear AI interval。
已有探针确认 stop 不停 interval 和 enterFrame。因此游戏暂停期间随机回调仍可能更新样本，
恢复时不应无依据恢复旧随机值或重新开始完整 500 ms 倒计时。

与显示 tick 重合时的先后顺序、卡顿补发、失焦、后台节流、首次触发相位待 AI-U02。
复刻的离线 replay 应重放已记录的 timer-fire 事件及其顺序，不依赖测试机墙钟碰巧一致。
这是一项实施方案；尚未成为已确认的生产调度契约。

### 4.4 共享随机消费

同一游戏还在受击语音、天气/效果、菜单选人等处调用 `Math.random()` 或 `random()`。
源索引记录 311 个调用所在行；同一函数可被多处反复执行，不能按 311 次分配固定 tape。
例如 BODY `hurtVoice(p)` 先抽 `Math.random()>p`，之后才检查距离上次语音的 2000 ms：
即便本次语音被频率限制挡住，也可能已消费随机值。

要求记录**全部相关随机消费者**的顺序。`Math.random()` 与 `random(n)` 是否共享同一
底层流、加载/菜单消耗多少值不能只从函数名推断；U-05 仍未解决。
不能为了调试方便给 AI、伤害语音、天气各自固定 seed 后宣称原版等价。

## 5. 标准控制器决策定义

本节针对 CTRL 所代表的 49 份原文完全相同的控制器，以及第 9 节明确不改变这些条件的变体。
旧控制器不能无条件套用。

记号：`D=对手.mc.动作`；`a/d/g/j/b` 分别为五个随机字段；
`Q=自身.mc.ql`；`P(name)=自身容器._curGJL[name+"zl"]>10`；
`H(sensor)=自身.mc.AImain.sensor.hitTest(对手.mc.bdmn)`。
以下都是**电脑分支**，条件按表中顺序求值，先返回的分支结束当前函数。
未命中任何分支通常返回 false；不能将各行合成无序权重。

`动作` 是源字段，不是由动画名推导的新枚举。已见 -1 受击、0 普通/可行动阶段、
1 攻击阶段、2 防御、3 必杀阶段。例 N@171 设 1、N@991 设 2、N@505 设 3，
BODY `onBeHit0` 设 -1；N@299 等招式中途会重新设 0。
`D<2` 包含 -1，必须保留先判断 `D==-1` 的优先级；不能翻译成“对手站立”。

### 5.1 普攻、技能与连击

| 函数 | 非 combo 感知框 | 有序条件 |
|---|---|---|
| `nornalhit()`（原拼写） | kanmian | D=-1 → a<120；否则 D<2 → a<100；否则 D=2 → 200<a<300 |
| `airhit()` | tkanmian | 同上 |
| `airMagichit()` | tkanmian（不是 tzmian） | 先 `P("tz")>10` → a<60；否则 D<2 → a<60；否则 D=2 → 200<a<300 |
| `magichit1()` | zh1mian | P(zh1) → a<60；D=-1 → a<70；D<2 → a<50；D=2 → 200<a<300 |
| `magichit2()` | zh2mian | P(zh2) → a<60；D=-1 → a<80；D<2 → a<55；D=2 → 200<a<300 |
| `magichit3()` | zh3mian | P(zh3) → a<60；D=-1 → a<80；D<2 → a<50；D=2 → 200<a<300 |
| `skill1()` | kj1mian | P(kj1) → a<60；D=-1 → a<80；D<2 → a<50；D=2 → 200<a<300 |
| `skill2()` | kj2mian | P(kj2) → a<60；D=-1 → a<80；D<2 → a<50；D=2 → 200<a<300 |

表中先要求 H 为真，再判断有序条件。破防技分支并未要求对手正在防御。
`P("tz")` 本身返回布尔，再与 10 比较通常永不成立，是保留的疑似源缺陷，见第 10 节。

`combo === true` 使用严格布尔参数，不要把所有 truthy 值都当 true：

- `nornalhit(true)`：直接 `combohitAI()`，不检测 kanmian。
- `magichit1/2/3(true)`、`skill1/2(true)`：分别传 zh1/zh2/zh3/kj1/kj2 给 `combohitAI`，不再检测对应感知框。
- `airhit(true)`、`airMagichit(true)`：仅 D=-1 且 a<120，其他 false，不检测感知框。

`combohitAI(act)`：

1. D=-1 → a<120。
2. 否则 D<2 → 50<a<100。
3. 否则 act 有定义且 P(act) → a<90。
4. 否则 D=2 → 80<a<150。
5. 否则 false。

第 3 步不是只对防御生效；如果 D=3 且传入破防技，也可能通过。
“不测感知框”的续招只放开输入判断，不等于攻击必定命中，实际 `*atm` 仍需命中结算。

`holdJ()` 与 `holdU()` 的电脑分支完全相同：

- D=-1：返回 `(a<120)==false`。
- D=2：a<100。
- 其他：100<a<300。

它们是招式中特定保持/取消条件，不能与 `nornalhit(true)` 合并。
若 a 尚未赋值，也不能未经语义测试将第一条改写为 a>=120。

### 5.2 必杀

先检查 Q。标准 `bisha/bishaUP/bishaAir(combo,qi)` 在 `isNaN(qi)` 时使用 100，
`bishaSuper` 使用 300；Q<qi 返回 false。合法命令能否扣气由目标帧脚本执行，
判断函数不可提前扣气。传参默认值和旧控制器固定值的区别见第 9 节。

| 函数 | 感知框 | P 检查键 | combo=true 且 D=-1 | 非 combo：P 为真 | 否则 D=-1 | 否则 D<2 | 否则 D=2 |
|---|---|---|---|---|---|---|---|
| bisha | bsmian | bs | b<90 | b<60 | b<80 | b>95 | 200<b<250 |
| bishaUP | sbsmian | sbs | b<90 | b<60 | b<100 | b>95 | 200<b<250 |
| bishaAir | absmian | kbs | b<90 | b<60 | b<80 | b>95 | 200<b<250 |
| bishaSuper | cbsmian | cbs | b<80 | b<60 | b<90 | b>95 | 200<b<250 |

combo=true 且 D≠-1 直接 false；combo 分支跳过 H。非 combo 必须先 H 成立，再依列顺序返回。
不是必杀越高级越容易出，也不是难度越高越频繁空放。

### 5.3 防御、起身与变身

| 函数 | 有序规则 |
|---|---|
| `defence()` | 自身 !canhit → false；D=3 或对手援助 `.动作==1` → d<130；D=1 → d<100；否则 false |
| `standup()` | 自身 `sw==false` 才返回 g<40；否则 false |
| `wankai()` | 电脑一律 false；玩家才检查 Q>=300 与斩+跳 |

defence 没有距离/感知框门槛，也没有读取玩家键盘的“输入预判”；它读的是对手已写入的动作值。
死亡、暂停等并非每个判断函数都自行检查，必须保留调用点的守卫，不能只看此表做全局调用。

## 6. 移动、跳跃与资源动作

### 6.1 左右移动

- `moveLeft()`：自身容器 X > 对手 X+20 且 g<120。
- `moveRight()`：自身容器 X < 对手 X-20 且 g<120。
- 在 ±20 区间内两者均 false；判断使用容器 X，不使用身体框中心。

函数本身不移动。调用点可能减/加 speed，设置 `_xscale`/`scale_X`、跳到“走”。
没有寻路或平台拓扑规划；跳跃/下平台另按垂直差判断。不得添加导航网格绕路作为原版规则。

### 6.2 普通瞬步 `rush()` 与闪避 `hide()`

`rush()` 有序规则：

1. D=1：立即返回 g<40，后面距离和区间分支不再执行。
2. 否则 |对手X-自身X|>80 且 g<80：把 scale_X 设置为朝对手的 ±1，
   `_xscale=scale_X*100`，返回 true。
3. 否则返回 120<g<200。

第 2 步有副作用；不能预先把所有判断作为纯函数并行计算。
第 3 步无朝向更新，也不要求距离>80；不得统一处理成朝向对手的冲刺。

`hide()`：D=1 → g<50；其他 → 100<g<200。
是否存在调用窗口要看该形态 ClipAction，函数存在不等于所有角色都调用。

### 6.3 跳跃与下平台

`jump()`：D<3 时，若对手 Y < 自身 Y-20，返回 j<100；否则 100<j<130。
D>=3 返回 false。Flash Y 向下，Y 更小表示更高。

标准 `jumpDown()`：自身 touchFloor 为真立即 false；然后 D<3 时，
对手 Y > 自身 Y+50 → j<100，否则 100<j<130；其他 false。
`doDropDown()` 通过后：容器 Y += 根 zhongli、jumped=0、fall=true，gotoAndPlay("落2")。
旧版使用脚部 jiao 与 ban1 的 hitTest，并用 20 而不是 50，不能统一，见第 9 节。

`onJumping(step)` 同时承载动作决策和原版跳跃运动：

1. step=1/4 且该控制实例尚未 jumpinggg：记录 js=jumpPower、置 jumpinggg、触发 jumpxg。
   其他 step 清 jumpinggg。该部分在 gameRunning 守卫外。
2. gameRunning 时按先左后右移动；step=1/2 检查 rush；step=2/3 检查 jump 转“跳2”。
3. khit==0 时依次 airhit→“跳砍”、airMagichit→“跳招”、bishaAir→“空中必杀”。
4. 同一 gameRunning 内：step=1/4 执行 js-=1；step=1/2/4/5 执行 Y-=js。
5. zhanting==false 且 step=3/6、touch==true：落地特效并 goto“落地”。

不能只移植第 3 步。js/jumpinggg 属于放置的控制实例，新的 PlaceObject 不继承它们。
旧控制器把部分运动移到了守卫外，必须保留变体差异。

### 6.4 BODY 的耗气突进 `dash()`

它不同于 CTRL `rush()`，共享 goran，但在 BODY `on_enterframe` 的 `doDashX()` 路径执行。
前置检查依次为 hp>0、非 sw、Q>=dashQL、自身动作在 {0,1,2}、对手非 sw；电脑还需 hitBan 或 touch。

电脑条件按源赋值顺序：

1. 自身动作=1 且 D=-1，临时结果=g<40。
2. 自身动作=2 且 D=1，临时结果=g<30。
3. 自身动作=1，临时结果=120<g<140，**覆盖第 1 步**。
4. 临时结果为真时 dashX=10、dashY=0、updateDirect()，返回 true；否则 false。

因此实际自身动作=1 时只用 120<g<140；AI=1 时此分支不可达。
不能把前三个 if 改成 else-if，否则会激活原版被覆盖的 g<40 分支。

`doDashX` 成功后置 dashing、Q-=dashQL（初始化 100）、dashF=0、调用 bsd。
BODY `onDashing()` 每次先 ++dashF，<10 时运动/残影，达到 10 时 bsw、清 dashing 并退出。
这是函数内计数，实际回调是否遇到暂停必须结合 `on_enterframe`：其 dashing 分支位于根
zhanting 返回之前。不能在顶层统一冻结所有回调后假定这些分支自动一致。
CTRL 也有同名 `onDashing(spdPlus)`，是另一个接收者和另一段功能，不可按名字合并。

### 6.5 援助的两个入口

CTRL `zhaoHuan()`：只先检查 Q<100，随后：

- D<2：a>90 且 b<100。
- D=2：200<a<220。
- 其他 false。

BODY `zhaoHuan()` 在相同随机规则前，额外拒绝：hp<=0、Q<100、既非 touchFloor 又非 hitBan、
jump==1、自身动作不为 0/2、对手 sw==true、自身援助 `.attacking===true`。
两个版本不能静默合并为更严格的一份。调用点的 `_parent` 层级决定用哪一个。
BODY `doZhaoHuan()` 若 hurtSkling 则返回；否则 yfgj(自身名)、bs=1、Q-=100。

### 6.6 受击脱身

BODY `hurtSkill()`：依次拒绝 hp<=0、sw、Q<100、D=3；玩家检查换键，电脑返回 g<30。
`beidax(flying)` 在 zhanting 时返回；非 flying 且递增后的 hstm<20 才调用 doHurtSkill。
不能扩大到所有击飞帧都可脱身，也不能把 hstm 当作每次命中自动清零的局部计数。
具体重置来源必须跟随当前形态源脚本。

`doHurtSkill()` 先拒绝 hurtSkling，再检查 hurtSkill，通过才 Q-=100、hurtSkling=true、
wdFrame=0、wdFrameX=10，并按双方深度需要调整层级。

- isNaruto：bsd(...,"XG_tishen",false)、moveX(150)、updateDirect、挂 XG_tishen2、
  gotoAndStop("站立") 后 play；800 ms timeout 调 bsw。
- 其他：bsd(...,"XG_bsq",false)；600 ms timeout 内设置 hurtSkling、bsw、
  gotoAndStop("招换") 后 play，再 addStgHit("XG_baoqi")，参数
  pw=80、zl=5、yup=0、hitx=15、hdtime=0、htype="击飞"。

脱身耗气和特效规则来自公共 BODY，不是难度额外作弊数值；timeout 仍需要进入同一时钟审计。

## 7. 感知区域与空间语义

CTRL 的 H 是 MovieClip 对 MovieClip 的 hitTest。复刻目标是原版变换后的范围判定，
不能替换成贴图透明像素、真实攻击框，或统一“距离小于 N”。

基础两者 AImain 都是 DefineSprite_3，只有两帧：第 1 帧空显示列表并 `stop()`；
第 2 帧含感知区，由电脑初始化 gotoAndStop(2) 激活。
第 2 帧都放置以下 11 个实例：

| 实例 | 标准控制器用途 |
|---|---|
| kanmian | 普攻 |
| tkanmian | 空中普攻、空中招式两者都使用 |
| tzmian | 该标准控制器未引用，不能替代 tkanmian |
| kj1mian / kj2mian | 下J / 上J |
| zh1mian / zh2mian / zh3mian | U / 下U / 上U |
| bsmian / sbsmian / cbsmian | I / 上I / 下I |

CTRL `bishaAir` 引用的 `absmian` **不在这两个基础 AImain 第 2 帧显示列表中**。
这不是给编译器自动补一块空中框的授权；须按 AI-U04 确认运行时引用解析和缺失调用结果。

几何来源：
[鸣人时间轴](../data/slices/minren-base.timeline.json)、
[一护时间轴](../data/slices/yihu-base.timeline.json)，以及审计 `base_slices`。
两者基础框来自 DefineShape_1 的 twip bounds X=[0,1319]、Y=[0,810]，
通过 DefineSprite_2、各个传感器矩阵、AImain、mc wrapper、角色容器及上层变换得到最终区域。
同名传感器的矩阵在不同角色间差别很大，不能共用鸣人的尺寸。

必须保留 Flash MATRIX：

```text
x' = scaleX * x + rotateSkew1 * y + translateX
y' = rotateSkew0 * x + scaleY * y + translateY
```

原始 twip 平移与坐标统一换算后再组合；1 pixel=20 twips。
不对调 rotateSkew0/1，不丢 wrapper 位移/缩放，镜像随实际容器矩阵更新。
无旋转案例不足以验证感知框；sbsmian、zh3mian 等含旋转。
相切边界、负 scale、极小旋转分量、缺失实例、嵌套 bounds 必须与原版 hitTest 对照。

感知通过只是发起动作的条件；真正命中仍走攻击 `*atm` 对身体框的源判定、受击链、无敌和冻结规则。
不允许根据“AI 感知成功”直接扣血或锁定目标。

## 8. 时间轴调用顺序与基础切片窗口

标准 CTRL `gameRunning()` 只返回 `根 zhanting==false && 对手.mc.sw==false`，
没有直接检查自身死亡、readying 或 gamePaused。其他入口有的是这个守卫，有的仅检查
zhanting，有的仅检查对手 sw；不能用一个更严格的全局“可行动”条件替代所有调用点。
BODY 的帧回调、CTRL 的帧回调和毫秒定时器也不是同一个入口。

### 8.1 标准 `doAllAction` 的准确顺序

顺序如下，绝大多数为独立 if，而非 else-if：

```text
defence       -> 防御
nornalhit     -> 砍1
wankai        -> 万解
skill2        -> 砍技2
skill1        -> 砍技1
magichit3     -> 招3
magichit2     -> 招2
magichit1     -> 招1
bishaSuper    -> 超必杀
bishaUP       -> 上必杀
bisha         -> 必杀
zhaoHuan      -> 招换
cache moveLeft, moveRight
apply facing from cached left/right
rush          -> 瞬步
jump          -> 跳
cached left   -> X -= speed, 走
cached right  -> X += speed, 走
neither       -> updateDirect()
doDropDown
```

源代码在这些 goto 后没有显式 return，编译结果必须保留后续分支与副作用。
现有普通 goto 探针确认其调用者可继续执行，但尚不能据此证明：父时间轴跳转移除
当前控制剪辑时，该剪辑内的后续语句仍执行。此差异归 AI-U05，需检查字节码、
目标帧显示列表并以最小代码探针确认。现已观察到直接在 enterFrame 中跳父帧移除自身时，
后续语句不执行（见上述编译进度）；函数调用层也已确认同样中断，并保留此前安排的目标帧脚本顺序。不能把所有入口统一改成“首个命中即返回”
或“最后一个跳转必定覆盖”；也不能仅保留最终标签而丢掉已执行的位移等副作用。

`doStand()` 不同：首次调用 resColor/standed 后，defence 成立跳防御并 **return**；
否则依次普攻、skill2、skill1、magichit3、2、1。不能套 doAllAction 的顺序。
`onDefence()` 依次 defence→防御2、skill1、magichit2、bishaSuper、doDropDown。
这些函数是否被实例调用由源路径决定，不能全局每帧全执行。

### 8.2 窗口解释规则

以下是**线性显示列表中实例成员帧范围**，含放置帧；不是运行次数。
源路径格式是 `DefineSprite_ID/frame_START/PlaceObject2_16_DEPTH/...enterFrame.as`。
精确深度和完整脚本在审计 `controller_hooks`；所列调用按源顺序，省略的外层守卫不得丢失。

新放置的 enterFrame 不在放置当帧执行。顺播时通常从 start+1 到移除前一帧；
若 stop 留在窗口中则回调可继续；若 goto 离开则提前终止。不能用窗口长度计数执行次数。
MOVE 沿用实例，重新 PlaceObject 创建新实例。全部源帧脚本索引用于追查没有决策调用的帧及退出路径。

### 8.3 两者共用的基础入口

| 成员帧范围 | 有序调用 |
|---|---|
| 1–12 | gameRunning 时 doAllAction |
| 21–31 | gameRunning 时先 X+=speed*2.5*scale_X，再 bishaUP、bishaSuper、bisha |
| 42–49 / 50–55 / 56–71 | onJumping(1/2/3) |
| 72–82 / 83–88 / 89–114 | onJumping(4/5/6) |
| 116–118 | nornalhit→砍1 |

鸣人控制深度通常为 36，一护通常为 34；帧 1 均为 31，瞬步一护为 28。
同一帧还可有其他深度的 ClipAction，不能按“一个角色一个决策回调”调度。

### 8.4 鸣人基础的主要续招窗口（Sprite 764）

| 成员帧范围 | 有序判断/结果 |
|---|---|
| 127–133 | moveLeft、moveRight |
| 134–137 | **magichit1** → 跳招（不是 airMagichit） |
| 176–181 | nornalhit(true)→砍2，bisha→必杀，magichit1→招1 |
| 194–202 | nornalhit(true)→砍3，bisha→必杀，magichit1→招1 |
| 217–235 | bishaSuper，skill1，skill2，magichit2，nornalhit(true)→砍4 |
| 246–259 | bishaUP，magichit3，rush |
| 349–357 | magichit3，bishaUP |
| 358–364 | magichit3，rush，bishaUP |
| 385–400 | bisha，magichit2 |
| 401–407 | bisha，magichit2，rush |
| 991–997 | defence→防御2，skill1，magichit2，bishaSuper，doDropDown |
| 1007–1013 | 对手 sw==false 时 defence→防御2，外层没有 gameRunning |
| 1039–1042 | gameRunning 时 standup→起身 |

例如 176 和 194 的源码在普攻/必杀判断之后仍写有 magichit1 判断；应保留此顺序。
是否实际执行到后者并覆盖跳转，取决于 AI-U05 的实例移除语义，不能提前断言。
不得改成固定“必杀优先”的全局策略。受击的 1016、击飞的 1029 等 BODY 回调另见审计。

### 8.5 一护基础的主要续招窗口（Sprite 638）

| 成员帧范围 | 有序判断/结果 |
|---|---|
| 127–133 | 非暂停且对手存活时 moveLeft、moveRight；非暂停时另有 Y-=1 |
| 134–137 | moveLeft，moveRight，airMagichit→跳招 |
| 181–184 | nornalhit(true)→砍2，magichit1→招1，bisha→必杀 |
| 198–205 | skill2，nornalhit(true)→砍3，bishaSuper，magichit2 |
| 219–231 | skill1，magichit3，magichit2，rush |
| 305–319 | bishaUP，jump |
| 379–389 | bishaSuper，bisha，magichit3，magichit1 |
| 429–445 | rush，jump |
| 715–721 | defence→防御2，skill1，magichit2，bishaSuper，doDropDown |
| 731–737 | 对手 sw==false 时 defence→防御2，外层没有 gameRunning |
| 763–766 | gameRunning 时 standup→起身 |

一护 181 的顺序与鸣人 176 不同，不能仅按招式名映射共用续招表。
一护 173 还有 wankai 调用，但标准电脑分支返回 false；审计保存该 ClipAction。

## 9. 全角色控制器变体

九组按完整脚本原文区分，包含纯反编译局部变量差异；不是九种难度。
以审计中的 SHA 和成员列表为准确绑定依据，不以本节顺序作为持久 ID。

| 数量 | 代表/成员 | 相对标准 CTRL 的区别 |
|---:|---|---|
| 49 | 鸣人16、一护16/651等 | 与 CTRL 完全相同 |
| 9 | Byakuya651、Kenshin1735/1910/2024/2050/2075/2091/2273/2274 | doAllAction 中左右局部变量编号互换，使用对应一致，属于等价重命名 |
| 3 | Byakuya69/691、yihu1469 | 旧控制器，缺 combohitAI/holdJ/holdU/hide/doStand/onDefence/onDashing 等；见下 |
| 1 | Kenshin1568 | onJumping/onDashing 的空中必杀目标字面量为“空中必杀你妹” |
| 1 | daitu535 | 必杀不接收 combo/qi，删去必杀 combo 分支；另有左右局部变量重命名 |
| 3 | daitu937、jianba143、mayuri51 | 必杀保留 combo，但不接收 qi；普通三类固定 Q>=100，超必杀 Q>=300 |
| 1 | daitu96 | 同上一行固定气量接口，另有左右局部变量重命名 |
| 1 | ichigo386 | 旧控制器；与 Byakuya69 组主要差别是 onJumping 运动/落地恢复暂停守卫 |
| 1 | yijiao267 | 旧控制器再增加 magichit4/5 与对应 doAllAction 调用 |

旧控制器的关键行为差异：

- `nornalhit(true)` 仅允许 D=-1 且 a<120，不使用标准 combohitAI 对其他状态的逻辑。
- airhit/airMagichit、magichit1/2/3、skill1/2、必杀函数不提供标准版本的相同 combo 接口。
- magichit1 在 H 后，D<2 统一 a<60，没有标准 zh1 破防分支与受击特判。
- skill1 对 D<2 的一般分支 a<45，skill2 为 a<40（标准均为 50）；先前破防/受击判断仍按原函数。
- jumpDown 用 jiao.hitTest(ban1) 判断底层地面，追下方阈值为 20；标准用 touchFloor 和 50。
- defence 不检查自身 canhit。
- doAllAction 在 rush/jump 之后才逐次查询并执行 moveLeft、moveRight；没有标准左右缓存，
  也没有标准“都不移动则 updateDirect”收尾。后一次查询可能看到前一次位移。
- Byakuya69/691、yihu1469 的旧 onJumping 部分运动和落地在 gameRunning/暂停守卫外；
  ichigo386 将这些部分移回守卫。不可把旧版一律按标准修复。
- yijiao267 的 magichit4/5 使用 zh3mian、P(zh3) 和对应随机分支，玩家组合分别为上+跳、上+换。
  doAllAction 在 skill1 后先检查 magichit4→招4、magichit5→招5，再检查 magichit3/2/1。
  其 combo=true 分支引用 `combohitAI("zh3")`，但该脚本未定义 combohitAI。
  此引用是否通过其他作用域解析及是否可达，需验证，禁止自动补标准函数。

本次发现的旧控制器可能是 SWF 中保留但未由当前形态引用的内容。必须从根帧的 mc 放置
递归绑定到控制 Sprite，并核对 WKframe/选人路径，才能决定生产要包含哪些组。
不能因为发现旧版本就把同一个 bundle 的所有形态切换为旧 AI。

## 10. 必须保留或先验证的源异常

| 项目 | 静态事实 | 复刻约束 |
|---|---|---|
| 空中招式框 | airMagichit 使用 tkanmian；基础还有未被它读取的 tzmian | 不按名称“纠正” |
| 二次破防比较 | isPoFangAct 返回布尔，airMagichit 却再 `>10` | 按源表达式建语义测试，不替换为正常破防特判 |
| 空中必杀框 | 标准引用 absmian，基础两者 AImain 未放置它 | 缺失实例必须记录并探测，禁止 fallback 到 tkanmian/bsmian |
| 冲刺条件覆盖 | BODY dash 对自身动作=1 的后续赋值覆盖前一赋值 | 保留三段独立 if |
| 同名函数 | CTRL/BODY 都有 zhaoHuan 和 onDashing | 以接收者区分，不能单按函数名归一 |
| 作用域引用 | CTRL onDashing 检查未加 `_parent` 的 touchFloor | 不擅自改成 BODY.touchFloor；查实际作用域 |
| 越界菜单档位 | keyDown 可让 cl 进入 0/6，映射只有 1～5 | 原版 UI 行为待探针 |
| interval 单句柄 | 重复 initCtrl 可覆盖根句柄 | 不推断所有旧 timer 已回收 |
| hold 逻辑 | `(a<120)==false` | 未定义值阶段不可直接化简为 a>=120 |
| 字面量/缺失函数 | Kenshin 特殊目标字面量、yijiao 缺 combohitAI | 先证明作用域/标签/调用可达性，不静默修复 |

这些记录不等于承诺在新平台保留资源泄漏或崩溃；若最终确认源缺陷且必须作兼容性修正，
应单独列出差异、复现实验、影响范围和决策，不能混入“一比一”实现而不注明。

## 11. 面向复刻的编译与运行设计

本节是待实施设计，字段名是候选，不是已经发布的数据契约。本次不改 schemas。
生产不得加载 AS2、Flash/AVM 或通用解释器；编译器只处理经审计的游戏专用条件和动作操作。

### 11.1 编译产物建议

| 信息 | 必须保留的内容 | 源依据 |
|---|---|---|
| controller binding | bundle/SWF hash、形态根帧、mc Sprite、控制 Sprite、控制函数变体 hash | 根 PlaceObject、ClipAction、函数定义 |
| sensor definitions | 名称、shape bounds、逐层矩阵、AImain 激活帧、实例寿命 | 完整 SWF 时间轴 |
| decision predicates | 有序分支、严格/宽松比较、随机字段、状态/气量/感知读取、副作用 | CTRL/BODY 函数 |
| decision windows | 放置帧/深度/实例世代、MOVE、移除、源守卫、调用参数及有序 goto/位移 | ClipAction + display list |
| timer policy | 注册/清理调用点、500 ms、五值消费顺序、未知初态 | initCtrl/randAI/clearint |
| action graph | 标签帧、条件跳转、stop/play、自然落帧 | 既有动作编译结果 |
| unresolved items | 缺失 sensor/函数/目标标签及其作用域证据 | 全引用审计 |

编译后每项均有源路径；未知表达式/未解决作用域不能静默默认 true/false。
经原版验证的“缺失调用返回无有效结果”可以成为显式兼容规则，但不能用默认值掩盖遗漏导入。
不要把当前只有两个基础切片的 sensor 表扩展成所有形态的默认表。

### 11.2 运行时分工

1. 调度层决定正在存活的控制实例、enterFrame 回调和 timer 事件顺序；保留实例局部变量。
2. 电脑控制器读取当前随机样本和调用当时状态，依有序条件返回，并执行源中已有副作用。
3. 时间轴执行器接受多个有序 goto 请求与位移；目标帧脚本依 ExecutionProfile 执行。
4. 战斗结算仍由既有攻击框/受击链处理；电脑不绕过伤害、防御、气量限制。
5. 日志层只读记录，不消费 RNG、不触发额外声音/时间轴、不改变求值次序。

判定函数的读取不是全局同一 tick 开始快照：同回调前序语句可能已改变朝向/位置，
后续 sibling 回调也可能看到不同数据。为优化统一缓存所有判断会改变语义。
允许缓存的情况以源为准，例如标准 doAllAction 明确缓存左右判断。

### 11.3 日志最小字段

每条事件建议记录：run_id、全局 event_sequence、display_tick、timer 时间/到期序号、
玩家/形态/实例 generation、源 Sprite/frame/depth/path、事件类别、暂停标记。

- RNG：消费者路径、Math.random 或 random 参数、原始值、tape_index；AI 刷新还记 AI、R 和五字段。
- predicate：函数/参数、实际读取状态、命中分支 ID、返回值；缺失字段应记 undefined 而非 0。
- sensor：两端实例 generation、最终矩阵/bounds、hitTest 结果。
- action：每个 goto/stop/play/位移/面向赋值的原始顺序、执行前后源帧。
- lifecycle：注册/取消/触发 timer，控制实例的创建/MOVE/移除。
- outcome：动作值、位置、气量、hp、命中、受击/防御状态及当前源帧。

固定 seed 只在 RNG 算法与全部消费顺序已匹配时足够；此前使用记录的原始结果 tape。
timer 事件 tape 与随机结果 tape 都需保留，防止“数值相同但触发相位不同”。

## 12. 验证计划与验收条件

### 12.1 静态验证（本次执行）

- `tools/analyze_ai.py --check`：报告与当前锁定源/切片一致，相关源 SWF 哈希匹配。
- 35 个主角色均可找到 randAI；49 份 randAI 原文完全一致；控制器分组与来源可重建。
- 两个基础形态的全部源帧与 Sprite 16 ClipAction 可追溯，感知名称差异显式可见。
- `tools/verify.py`、`tools/check_handoff.py`：输入完整性、文档链接和任务依赖。

这些检查不执行电脑对战，不是运行时 AI 测试通过的替代证据。

### 12.2 待实现的源语义回归

| 编号 | 输入/场景 | 原版可指出的断言 |
|---|---|---|
| AI-T01 | 五档、注入已知五次随机返回值 | 乘数为 500/400/300/200/100，消费顺序固定，无额外抽签 |
| AI-T02 | 0、30、40、50、60、70、80、90、95、100、120、130、140、150、200、220、250、300 及邻近值 | 严格 <、> 与分支优先级不变；端点不放宽 |
| AI-T03 | 首次 timer 前，含 holdJ/holdU | undefined 不伪造成随机 0；记录原版真实返回值 |
| AI-T04 | D=-1/0/1/2/3，P 为真/假，H 为真/假，combo=false/true/未传 | 对照第 5 节有序决策；combo 跳过 H 的条件准确 |
| AI-T05 | Q=99/100/299/300，qi 未传/有效/NaN，旧接口变体 | 气量检查正确；predicate 不提前扣气 |
| AI-T06 | 距离 ±20、80，高差 -20/+50，左右镜像、平台/地面 | 严格边界、rush 面向副作用、jumpDown 分支不变 |
| AI-T07 | 同时满足攻击/技能/必杀/移动 | 比较所有顺序副作用及 goto，而非只比较最终动作 |
| AI-T08 | N@176 vs I@181，同状态和样本 | 函数调用顺序不同得到相应轨迹；禁止统一续招优先级 |
| AI-T09 | 新放置、MOVE、移除、stop 在窗口、goto 提前离开 | 实例生命周期与回调次数一致；js/standed 等不跨新实例继承 |
| AI-T10 | 感知旋转/镜像/相切、目标身体变形、缺 absmian | 比较原版 bounds/hitTest；不使用攻击框替代 |
| AI-T11 | 自身动作=1、D=-1，g=20 与 130 | BODY dash 前者失败、后者通过；覆盖赋值保留 |
| AI-T12 | 受击/击飞、Q=100、D=3、hurtSkling、hstm 边界 | 脱身守卫、气量、timeout、位移/爆气链逐项一致 |
| AI-T13 | 援助已攻击、空中、自身动作不允许 | CTRL/BODY 两个入口分别测，禁止假定守卫相同 |
| AI-T14 | 九组控制器各一例，绑定根帧和控制 Sprite | 变体保持；未可达组标静态存在，不伪造可选形态 |

阈值表只约束条件，空间/动作状态测试要走真实调用链，不用“最后 HP 一样”掩盖时序差异。

### 12.3 原版同输入/tape 场景

在副本插桩，不修改锁定 game/scripts；保留副本 hash、插桩 diff、运行器版本。
使用原版 game/main.swf 加载外部人物的路径，不以孤立角色 SWF 代替正式调用链。
先鸣人基础对一护基础、现世、P1 固定输入、P2 电脑，对每档执行：

1. 启动到首次两次 randAI，确定开场前后的注册/触发相位。
2. 相距较远接近、近距离静止、普通攻击、防御、跳跃、下平台。
3. 普攻命中续招、空挥续招、对手防御与破防技、Q=100/300 必杀、援助。
4. 被打脱身/被击飞/起身；同一波多次命中，保留 hstm/气量轨迹。
5. 在随机刷新前后暂停、必杀冻结、KO、下一小回合、返回菜单再入场。
6. 关闭/开启语音或效果配置时比较随机消费路径，定位共享 RNG 差异。

同局至少比较：timer 顺序 → RNG 消费 → 谓词分支 → 感知 → goto 序列 →
实例/源帧 → 位置/气量 → 命中与伤害。首差异必须分类，不能改 tape/阈值补偿。
随后扩大到可达旧控制器、特殊字面量/缺失框案例；双方电脑仅用于句柄/调度诊断。

### 12.4 未解决项与关闭证据

| ID | 具体未知 | 所需证据 |
|---|---|---|
| AI-U01 | 首个 randAI 前五字段、sw 等未赋值比较及作用域 | 原版启动逐事件日志、最小数值/undefined 探针 |
| AI-U02 | 500 ms 首次相位、与 display tick 同时到期顺序、卡顿/暂停/失焦 | 注册时间、timer-fire、显示帧、恢复事件 tape |
| AI-U03 | 重复 initCtrl、形态更换、单句柄覆盖后的旧回调寿命 | 实例 generation、timer id、receiver、clearint 前后日志 |
| AI-U04 | 缺 absmian/缺函数/裸 touchFloor 引用的实际解析 | 原版 receiver/path/返回值与显示列表；不能靠猜 false |
| AI-U05 | 同回调多个 goto、兄弟控制剪辑的游戏实际顺序 | 目标帧 DoAction 和调用者语句级日志，复用调度探针但补游戏案例 |
| AI-U06 | 69 份控制器的全部形态可达绑定 | 根帧/WKframe/加载选择与递归 PlaceObject 图 |
| AI-U07 | 全部相关随机消费，Math.random 与 random 的关系 | 原始调用点/结果/tape_index 的完整原版轨迹，关联 U-05 |
| AI-U08 | 菜单 cl=0/6 的显示和返回有效档位行为 | 五档边缘同键/连按录像与变量日志 |
| AI-U09 | 感知框相切、缺失/卸载、嵌套与旋转 bounds | 原版 hitTest 对照表，包含两个基础旋转框 |

实现完成门槛：可达控制器与几何均编译且无静默缺省；源语义测试通过；上述影响首批切片的
未知项有实测结论；五档固定输入/tape 对照无未解释首差异；暂停/回合/退出无未解释 timer 行为。
全角色验收必须另完成 AI-U06 对应覆盖。文档完成、静态扫描通过、可运行电脑和一比一验收
应分别记录，不能互相替代。

### 12.5 跨角色回调次序的新证据

[恢复位移探针对照](../evidence/ai/recovery-order.md)显示：保持双方显示深度不变，仅交换两次 goto 的顺序，鸣人的恢复回调与一护 moveLeft 的执行顺序就会反转，从而决定一护是否多走 6 像素。不能将两个同级剪辑的深度探针推广成固定的整角色执行顺序。实例注册、goto 重建或保留时的排序仍需区分，AI-U05 保持未解决。

### 12.6 实例调度与输入对照更正

[嵌套实例探针与输入更正](../evidence/ai/callback-registry-and-input.md)确认：新实例回调排到旧实例之前，保留实例的跳帧和交换显示深度不改变顺序。固定对战已接双方共享回调队列，但玩家非受击控制器、援助及完整加载仍未全部迁移。

FP32 不接受对 `Key.isDown` 的原有覆写方式，旧捕获不能证明记录的输入意图实际送达。分析副本现改为绑定原 BODY 的 `kis` 别名并逐次记录读取。`input-alias-r12` 的 600 帧、3,132 次读取已验证与输入意图一致；原生仍有首差异，M5-03 保持 pending。历史日志与随机 tape 均保留，不作修订来掩盖差异。

### 12.7 玩家源控制器与数字精度修正

固定鸣人玩家已接入原版 Sprite 16 的完整基础控制器编译产物（27 个条件、8 个调度函数、39 个放置回调），保留 `!useAI` 和 `kis` 分支，替换旧的玩家动作选择。双方 BODY 绑定到同一源帧结算入口；受击保留 `updateDirect(true)`，防御保留无参数调用。回调产生的目标帧按跨角色入队顺序执行。上述接线仍不代表所有动作已经逐项验收。

原版默认十进制 trace 会损失低位：`80/15` 的日志不能直接当成原始 binary64 值。新增 `f:` 编码只改变诊断序列化，保留原游戏计算和旧 tape；r13 已取得 600 帧及 3,924 次实际键读取。原生同 tape 对照在 620 个匹配边界后仍失败：缺少 `XG_qdj` 首帧的四次随机调用。更早的一护受击朝向和相对击退差异已修正，坐标精度差异仍保留。完整对战、特效脚本排队和所有随机调用的对齐未完成。

详细源码路径、可重建命令、失败报告和测试范围见 [玩家控制器与精确数字记录](../evidence/ai/player-controller-and-binary-trace.md)。

## 特效随机调用与重复防御判定进度（2026-09-09）

`XG_qdj` 首帧两条随机偏移表达式已编译，四次随机调用接入双方共享的原版随机流。最小 FP32 代码探针确认 attach 调用者先返回、再执行新特效首帧；大写 `_X/_Y` 写入实际父坐标。源受击查询已绕过旧的「攻击实例已命中」缓存，恢复同一攻击在防御接收剪辑重新出现后再次命中的行为。

同一 r13 tape 的 1,166 个预期边界及 298 次检查点后随机调用、时钟读取均已匹配，但对照仍是失败：原生末端多出一个 P1 帧边界，根观察点仍有 35 组帧号和 24 条状态差异，P1 最大相对 X 差异约 4 像素。不得据边界顺序匹配称整场一比一。五项原生定向检查和十四项 Python 检查通过；完整调度、视觉、整场及 Web 验收仍待完成。详见 [源码与证据](../evidence/ai/effect-random-and-repeat-contact.md)。

## 特效注册顺序与根观察点（2026-09-09）

最小 FP32 代码探针证明特效帧脚本会按实例注册顺序与角色回调交错。特效现接入共享注册表，替换临时统一早执行阶段；恢复暂停时多跑一次受击回调的问题消除。对照采样移到原版根观察点，并在原版 `done`/`fscommand(quit)` 所在阶段截止，不删除预期事件。比较器同时收紧为检查全部边界、帧号、状态及随机/时钟 tape 消费完整性。

r13 的 600 战斗帧片段离散字段对齐：1,166 个边界、298 次检查点后随机调用、897 组帧号和 1,794 条角色状态全部一致。坐标仍有单精度低位误差，视觉/声音未验收。新采集的独立 r14 在第 723 个边界失败，当前线索是鸣人弹体首碰后改名 `abcd` 与旧攻击名称查询。r13 通过不能替代 r14 或整场验收；M5-03 继续 pending。见 [源代码、探针和两份对照](../evidence/ai/effect-registry-and-root-observer.md)。

## 弹体延迟改名与两份独立片段（2026-09-09）

弹体现保留独立的源实例名：`gotoAndPlay(5)` 先改变播放头，排队执行第 5 帧后才将 `zh1atm` 改成 `abcd`。最小原版探针验证了这两个阶段及移除前已排队脚本的取消。攻击与弹体碰撞查询都读取当前源名字；同名重建不继承旧实例的改名，子帧操作与角色目标帧共用 FIFO 顺序。

修正后 r13、r14 两份各 600 战斗帧片段的离散字段均对齐：分别 1,166/1,084 个边界、298/287 次检查点后随机调用，帧号、状态和时钟 tape 无差异。六项原生定向检查通过。仍有坐标低位误差，且完整 KO/换局对照、其他动作路径、视觉音效和 Web 矩阵未验收；M5-03 继续 pending。详见 [弹体源语义与验证范围](../evidence/ai/projectile-deferred-rename.md)。

### 完整比赛补充：倒计时与超时

源码审计确认当前原生切片尚缺倒计时及超时结算链；600 帧片段不能覆盖此门槛。
详见 [完整比赛超时审计](../evidence/ai/match-timeout.md)，包含源帧、平局分支、
子剪辑与计时器作用域的待验证项。M5-03 保持 pending。

### r15 整场原版 KO 记录

[长记录与首差异](../evidence/ai/match-flow-r15.md) 已覆盖两局 KO、换局和选人返回，
但未进入超时分支。原生重放在一护防御脚本 735/726 的执行顺序处失败；
整场对照仍未通过。计时器作用域已由 FP32 最小探针确认，见超时审计补充。

### 共用规则与后续角色迁移

[本轮共用规则修复](../evidence/ai/receiver-rule-fixes.md) 覆盖防御朝向、精确伤害框名字、
低血量回气和致死血量。35 个主角色的函数原文分组已保留；同名 BODY 与控制器函数
不得混用。鸣人/一护是当前验收样本，后续角色应复用源码编译规则与通用运行时，
通过其自身时间轴和实例数据绑定变体，不增加按角色名或手测帧号判断的补丁。
r15 已推进到首局 KO 恢复的调度差异，尚未通过整场验收。


### KO instance scheduling and round continuity

The shared scheduler now interleaves each KO root/child instance with actor BODY and initial frame scripts. Round reset preserves source energy/hits/pause, repeated same-frame goto does not repeat its script, and source hit-energy additions are not prematurely capped. r13/r14/r15 match all currently compared fighter fields; r15 consumes 4158 boundaries, 1202 random calls and 19 clock reads across both rounds and battle teardown. Twelve native checks pass. Countdown/timeover, exact geometry, boot, additional characters and presentation/Web parity remain pending. See [evidence](../evidence/ai/ko-instance-scheduling.md).
