# 当前状态、风险与待验证项

本文件描述本次交接时的真实状态。

## 已完成

- 用户入口结构检查：普通 V 2.6，600×400，30 FPS。
- 74 个直接外部依赖已补齐，75 个游戏输入文件有校验值。
- 62 个 SWF 已检查，8,853 份反编译脚本按 SWF 合并，原路径与内容保留。
- Brx86 仓库固定提交已检查，确认是“社长改”；25 个资源完全相同，49 个不同，未混用不同版本。
- 资料精简、规格、架构、契约、实施任务、验收计划与工具已编制。
- `M1-01` 已完成：75 个输入、34 类 SWF 标签和 8,853 个脚本已进入可重复生成的来源清单；ClipAction 标签与脚本记录单独计数，未解析语义保持待处理。
- 已建立鸣人/一护基础形态的代码驱动切片：动作标签、AS2 参数、逐帧 display list、
  矩阵、判定实例和可达位图均可重复导出；Chrome 已显示原生 Godot Web 预览。
- 已从 `game/main.swf` 的“现世”标签提取静态背景/前景层；嵌套 Sprite 首帧矩阵和
  JPEG3 alpha 合成 PNG 可重复导出，Chrome 中与两名角色共同显示正常。
- 已生成鸣人/一护全部已标记动作的战斗中间数据：攻击框实例持续窗口、连段输入转移窗口、
  AS2 动作退出帧、受击停帧和 30 Hz 硬直换算均带源路径；开发切片已接入三连、扩展招式
  判定、HP/气量、普通受击、防御受击和必杀条件分支。
- 原版两套默认键位已接入 Godot Web；Chrome 自动输入实际走过行走、三连、跳跃、防御、
  U 和 I。防御长按固定在原版 `防御2` 起始帧，受击硬直结束后恢复，普通受击按源
  `beidax()` 在前 14 tick 连续应用击退。
- 嵌套 Sprite 已按放置时刻推进；位图填充按 Shape 边界裁剪，修复了走路只平移以及 U
  素材整图泄漏造成的重复角色。投射物内部未命名剪辑仍用独立 `clip_age`；根时间轴
  未命名剪辑（鸣人 `走` 的 DefineSprite_31 跑循环）在 `clip_age == 0` 时改回按
  `placed_frame` 推进，左右按源 `doAllAction` 改 `_xscale`。鸣人 `下+J` 按
  `onDefence()/skill1()` 从 `防御`/`防御2` 进入 `砍技1`，不再被防御提前 return
  吃掉。  招式位移已改为由 clip `enterFrame` 编译出的
  `motion_windows` 驱动，不再按角色硬编码。鸣人上+U（`招3`）源第 491 帧
  `gotoAndStop("落")` 已编入 `action_exits`：不再把 485 帧 clip 的 1.7 速
  位移播到标签末帧 503；`zh32atm`（60 伤/`击飞`）仍在 486–487 帧。
  鸣人的 JPEG3 素材已全部改用 JPEXS 合成 alpha 的 PNG，不再把缺失透明通道的
  JPEG 黑底带入 Web。`bdxg()` 的 1–6 级共享命中特效已从 `main.swf` 导入；
  上+U 已以 30 伤 `zh3atm` → 60 伤/击飞 `zh32atm` 的连续实战路径通过无头回归，
  第二段显示 `XG_qdjx` 重击效果。命中候选按原版 `hitks` 顺序编译为
  `hit_priority`，不再依赖节点遍历顺序。  鸣人下+J 的 `kj10atm` 仅作为冲刺接触框；
  接触后按源跳到 291 帧 `砍技12`。`砍技1` 本身没有 `gotoAndStop`，没碰到也会
  播进 `砍技12` 炸开，第 313 帧再回站立。`kj1atm` 在 291–294 帧结算 100 伤害和击飞。
  冲刺的 `speed*2` 位移现对 `kj10atm` 做水平 swept AABB，左右朝向都在第一处交叉
  接触停止并转收尾，避免 30 Hz 离散步进穿过较窄的 `bdmn`。第 292 帧源
  `shine(1403539)` 已编译进通用 `presentation_events`；Web 使用 main.swf 的
  blendMode 13（Overlay）和 DefineSprite 1745 帧 2–9 的 alpha 序列
  `114,100,85,71,57,43,28,14 / 256` 还原深蓝全屏冲击闪光。
  `zl=15` 已按 `fangyu()/beida()` 归一为破防强度 5，防御中仍进入击飞并播放
  `XG_mfdjx` 蓝白收尾爆点，不再被当作未知效果或普通防住。时间轴 atlas 裁切分支
  漏挂 Sprite 的公共渲染错误也已修复，裁切后的命中特效会按原矩阵和透明度显示。
  鸣人 `zh1atm` 等投射物按源 `movspeed`
  累积剪辑本地坐标并参与命中。投射物嵌套剪辑按自身 `DoAction` 推进：鸣人
  `zh1atm`（DefineSprite_260）在第 3 帧 `stop()` 保持三层手里剑列，命中后
  `gotoAndPlay(5)` 才播爆点，不再跟着父时间轴误进命中帧。Python 已断言
  `stop_frames == [3, 11]`；Godot smoke 已写入 `combat_smoke.gd` 的 1→2→3→3→命中5
  路径，并由 Godot 4.7.2 无头运行通过。
  `招换` 在 `doZhaoHuan()` 帧扣气并按 `yfgj` 生成援助放置（鸣人→我爱罗、一护→魂）。
  先前 O 只扣气并播 `招换`：援助节点挂在 `GameWorld` 下，但预览被
  `FileAccess.file_exists` 挡住，frame 1 display list 为空，画面上没有我爱罗。
  `HelperRuntime` 现与角色一样直接作为 `TimelinePreview` 加载
  `woailuo` 时间轴/位图；`yfgj` 后 `activate` 放到 `caster.x - 20*facing`、
  `gotoAndPlay(2)`。`start_action` 不再清掉未消费的 `helper_spawn`。
  推进到 `hide_frames` 后停回 frame 1 的 `(_X,_Y)=(-200,-200)`。
  `fzccXg` 源实现是 `addChildXG(..., "XG_fzcc")` 出场/收场特效，不是隐藏，
  `XG_fzcc` 仍未导入。魂在 72/75/78/81/85/89 帧对对手 `ql -= 20`。
  攻击接触只在存在 `timeline.json` 时采样 display list，不编造判定框。
  已用 JPEXS 26.2.1 导入我爱罗根时间轴（85 帧）与 37 张 JPEG3 PNG：frame 1
  display list 为空，`yfgj` 的 `gotoAndPlay(2)` 后才有画面；`gjl.atm1` 出现在
  44–85 帧，load 时按对手 `_x` 改写剪辑 `_X`。魂 SWF 时间轴/位图仍未导入。
  `combat_smoke.gd` 已断言 956 扣 100、`helper_id=我爱罗`、激活后可见且有
  Sprite 子节点，并由 Godot 4.7.2 无头运行通过。
- 气量按源脚本接入：普通对战初值 0，招式帧 `ql +=/-=`、命中/受击/防住公式和低血量回气
  均有断言；左右下角气条按 `qitiao` 的 round/floor 分段显示，尚未导入原 `qt/bss` 元件。
-   现世 `ban2/ban3` 按源 `isHitBan()` 读入：站立平面是剪辑注册点 `ban._x/_y` 与
  `_width`，不是 shape AABB 顶边或带镜头的 global bounds；`floorY = -25` 来自
  `p1` 放置与 `frame_7`。角色 SWF 根时间轴把内层时间轴放在 `mc` 上（鸣人
  `translateY=-478` twips，一护 `-479`）；`_parent._x/_y` 仍是玩家容器，画面和
  `bdmn` 走这层矩阵，不再把脚画进墙顶下面。  跳跃按 `onJumping(step)` 分段：step 1/4 先 `js-=1` 再 `_y-=js`，step 2/5
  保持 `js`，step 3/6 只检测落地，`jump!=1` 时 `on_enterframe` 用 `zhongli=10`。
  `onClipEvent(enterFrame)` 从放置的下一根帧开始（`clip_lifecycle` 探针）；
  第 50 帧是新 `PlaceObject`，`js` 不继承。鸣人一跳上升 77 像素，低于
  `ban2` 的 78.65，单跳落不上去。受击浮空后按 `zhongli = 10` 落地。平台上
  `S+K`（含已进入 `防御2`）按源 `jumpDown/doDropDown`：`_y += zhongli` 后播
  `落2`，离开 `ban._y - 10` 窗口落到下一层。`combat_smoke.gd` 已加地面/ban
  站立 Y、穿层、`onJumping` 顶点 77 与单跳落不回 `ban2` 断言，并由 Godot 4.7.2
  无头运行通过。
- 对战镜头按 `DefineSprite_1991` 的 `onEnterFrame` 实现：焦点 `all` 时
  `scale = 2 * (1000 - max(|dx|,|dy|)) / 1000`（下限 0.8），再以 0.5 缓动
  `_root.game` 的位置/缩放；墙为 `[20, mapSizeX-30]`，间距 ≥ 700 锁定两端。
  现世站位改用地图 `p1/p2`  twip 原点，尚未与原版逐帧截图对照。
- 双方 `bdmn` 身体碰撞已接入每 tick 的双方运动结算：按源脚本把横向增量限制到
  `[-30, 30]`，用朝向、对方 `vecx / 2` 和 `heavy` 差分摊挤压；等重量静止重叠时
  每 tick 注入 10 像素压力（双方各 5）直到身体框分离。无头回归覆盖同点出生、
  首 tick 精确分到 `195/205` 以及最终 `bdmn` 不相交；普通瞬步期间按源跳过挤压。
- 死亡/KO 判定已按源 `checkDead(fly)` 接入：`hp <= 0` 且非练习（`modo != 4`）时
  置 `sw`、非击飞则 `gotoAndStop("击飞")`，落地进 `击落地` 后在源
  `if(sw == true) stop()` 帧停住，`standup()` 不再进 `起身`/`站立`。
  `KOplay(pn)` 的焦点切到被 KO 一方已接 `GameWorld.focus`；`_root.KO` /
  `blackStg("KO")` / `KOstart` 暂停与 `nextfight` 回合重置尚未导入，无 KO 字幕元件。
- 战斗中间数据已编译 `command_catalog`：招式 ID 即源帧标签，鸣人/一护时间轴上
  全部标签与 `doAllAction`/`onJumping` 目标均入目录。站立/防御输入已改走目录
  `match_context`（源谓词 `buttons_all`/`buttons_none` + `dispatch_priority`），
  不再按角色写 if 链；`万解`（`wankai`：斩+跳 且 `ql >= 300`）已接线。
  `nornalhit` 排除跳/上/下，因此 J+K 气不足时不会误出 `砍1`。
  未接线项（砍4、空中必杀缺标签、瞬步/落地中段取消等）仍在 `gaps`。
- Adobe Flash Player Debugger 32.0.0.465 已能加载锁定的完整原版并显示主菜单；另以
  可重复构建的最小 AVM1 探针确认了 goto、enterFrame、对象移除、stop/play 和 interval
  的部分调度顺序，结论与哈希已写入 `evidence/probes/` 和 provisional ExecutionProfile。

## 尚未完成

Godot 单线程 Web 导出已建立，4.7.2-stable 的无头、应用内浏览器和 Google Chrome
启动通过；Firefox/Safari 尚未完成，因此 `M0-01` 仍为进行中。当前开发切片可操作，但
尚未完成两名角色的全部动作语义：已编译的位移/投射物/援助生成覆盖源时间轴，
我爱罗援助已有根时间轴与位图，魂援助 SWF 本体、XG_fzcc 特效、声音、滤镜、原版 HUD 元件、KO 字幕/`blackMu` 和若干取消分支仍缺失。击飞/倒地/起身和现世主地面/
平台已有开发切片实现，尚未与原版逐帧对照。Flash 调度已有第一批原生播放器实测，但
兄弟回调顺序、暂停/焦点时钟域、24 FPS 援助推进和同时命中仍未确认；KO 演出/下一回合、原版
golden 轨迹/截图、全角色验证和部署尚未完成。现有 Chrome 截图和状态日志只证明开发路径
可运行，不能替代与原版逐帧对照。

## 风险登记

| 风险 | 影响 | 处理任务 | 解除条件 |
|---|---|---|---|
| R-01 原版固定对战参照尚未捕获 | 无法验证一比一 | M0-02 | 已有可信原生播放器；仍需固定输入的鸣人/一护案例和逐帧捕获 |
| R-02 Flash 调度和暂停映射错误 | 差一帧导致连招改变 | M0-03、M2-01 | U-01/U-02 探针完成，关键案例匹配 |
| R-03 时间轴/判定区漏导 | 有画面但技能不正确 | M1-02、M1-03 | 不支持项有清单，玩法事件零静默遗漏 |
| R-04 数值、枚举、未定义值语义变化 | 碰撞、伤害或 AI 偶发不同 | M2-02、M2-03、M5-03 | 语义用例与首次差异追踪通过 |
| R-05 外部资源缺历史原包校验 | 无法证明历史逐字节一致 | B-01 | 当前仅有匹配主程序与来源哈希；后续发现作者原包时单独核验 |
| R-06 位图/矢量/滤镜渲染差异 | 严格像素还原受阻 | M1-04、M6-03 | 分类对照，所有可见差异解决或明确保留未完成状态 |
| R-07 Web 性能/音频/键盘兼容 | 能在编辑器玩但网页体验失败 | M0-01、M4-01～03 | 三类浏览器实际对战通过 |
| R-08 角色数量被误读或范围漏项 | 两角色原型被当作完整版 | M0-04、M6-01 | 配置与实际可达内容逐条有去向 |

实现闸门已写入 [SOURCE_FIRST.md](SOURCE_FIRST.md)，并由 `AGENTS.md` 强制：改运行时前必须能指出每帧脚本、剪辑寿命和离开标签方式。跳跃高度与下+J 空挥不炸属于违反该闸门的已修案例，后续不得用标签结束帧或手感公式补全。

## 下一项工作

导入魂根时间轴与位图，并把我爱罗 `atm1` 命中与 `XG_fzcc` 特效对照原版。
把走路循环、墙顶站位、`砍技1`、`万解`、位移、投射物、三连、受击、必杀与原版固定输入逐帧对照。并行完成 `M0-01` 的
Firefox/Safari 实测及 `M0-03` 未解决调度探针；在对照通过前保持 M2/M3 任务未完成。
