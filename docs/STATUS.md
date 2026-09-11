# 当前状态、风险与待验证项

状态同步日期：2026-09-11。按当前工作树与已有证据核对；本次检查范围见 [同步记录](../evidence/status-sync-2026-09-08.md)。

B-01～B-03、M1-01 已完成，M0-01 进行中；其余任务维持 pending（包含已有局部产物但未验收），对应任务表已补产物与证据。下列开发切片实现不代表里程碑完成。

## 已完成的资料与已实现的开发切片

- 2026-09-10 电脑鸣人浮空受击脱身修复：从原版角色配置编译 `isNaruto`，
  移除 P1/P2 的固定阵营；召唤保留 `hurtSkling` 提前返回，避免误叫援助和重复扣气。
  原版两角色受控序列、连续脱身回归、本地 Web 及既有三份电脑对战轨迹通过当前检查，
  原版替身两个特效已导入；完整视听/真实键盘整局与线上发布仍未验收。
  证据及旧 smoke 基线失败见[受击召唤记录](../evidence/combat/hurt-summon/README.md)。

- 2026-09-09 选人开发切片：Vs Com、Vs Human、Training 已经共用角色/援助选择逻辑，
  名单显示鸣人、一护、日番谷，援助显示我爱罗、魂。背景使用原版四帧素材，头像、
  大立绘与选中后创建战斗角色已接线。`character_selection_smoke.gd`、
  `selected_fighters_smoke.gd` 与原生窗口截图检查通过。日番谷目前仅基础形态可运行；
  卍解切换、完整招式及原版同输入逐帧对照仍未验收，不能视为一比一角色完成。
  日番谷原版对战采集日志存在事件序号缺失，严格收集器拒绝该记录；未修改比较阈值。
  Normal 流程及完整选人画面对照仍待接线/验收。

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
  `XG_fzcc` 已在后续辅助实现中导入。魂在 72/75/78/81/85/89 帧对对手 `ql -= 20`。
  攻击接触只在存在 `timeline.json` 时采样 display list，不编造判定框。
  已用 JPEXS 26.2.1 导入我爱罗根时间轴（85 帧）与 37 张 JPEG3 PNG：frame 1
  display list 为空，`yfgj` 的 `gotoAndPlay(2)` 后才有画面；`gjl.atm1` 出现在
  44–85 帧，load 时按对手 `_x` 改写剪辑 `_X`。魂 SWF 时间轴/位图现已导入，详见下方本次辅助实现记录。
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
- `on_enterframe` 的地面解算在 `被打`/`击飞` 期间同样生效：它是外层 wrapper 放置
  body mc 的 clipAction（`frame_2/PlaceObject2_1180_1` 一类），与当前标签无关。
  `onBeHit0()` 的 `jump = 1` 只覆盖 `_y < floorY` 分支，被负 `yup` 压到地面及
  以下时仍走 `if(_y > floorY - 10) _y = floorY`。防御被 `zl > 10` 破防（鸣人
  `cbs3zl=14`/`cbs3up=-3`）时，对手每帧当帧被拉回地面，`XG_mfdj` 蓝块落在地面；
  修复前受击分支直接 return，会一路下沉到地面以下约 51 像素。`combat_smoke.gd`
  已加这条断言，回退修复即失败。
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
  `blackStg("KO")` / `KOstart` 暂停与 `nextfight` 回合重置已接固定 Vs Com 开发入口，双方两胜结束回归通过；原版调度与画面对照未验收。
- 战斗中间数据已编译 `command_catalog`：招式 ID 即源帧标签，鸣人/一护时间轴上
  全部标签与 `doAllAction`/`onJumping` 目标均入目录。站立/防御输入已改走目录
  `match_context`（源谓词 `buttons_all`/`buttons_none` + `dispatch_orders`：站立取第一个离站 goto，防御后写获胜），
  不再按角色写 if 链；`万解`（`wankai`：斩+跳 且 `ql >= 300`）已接线。
  `nornalhit` 排除跳/上/下，因此 J+K 气不足时不会误出 `砍1`。
  中段取消已由 clip `enterFrame` 编进 `cancel_windows` 并在 `enter_frame` 里通用分发：
  鸣人 `砍3@217→砍4`、`落地@116→砍1`、`瞬步@21→必杀/上必杀/超必杀`、
  `击落地@1039 standup→起身`，一护 `砍1@173→万解`、`招21` 等。
  同帧取消会先把当前 `*atm` 命中暂存，避免 `start_action` 清掉 display list。
  `action_exits` 已覆盖无条件提前 `gotoAndStop`（含一护 `砍技1@278→站立`、
  鸣人 `超必杀2@942→击飞` 并带源 `yup`/`htx`、`击落地@1069→站立`）；
  自跳 `击飞` 走共用 `beidax` 落地/`launch_stop_frame`，不再卡在 1038。
  走/防御2/站立/落循环钉住仍不接线。`M2-04` 仍 pending。
  `瞬步` 第 21 帧位移改为源 `speed*2.5*scale_X`；`跳砍`/`跳招` 补了 `moveLeft/Right`
  与像素 `_y`。鸣人 `上必杀` 判定来自嵌套 `DefineSprite_489` 的 `sbsatm`/`sbs2atm`
  （根帧 693–705 / 706–718，放置名 `fensheng`）。
  站立上+招是 `招3`，上+I 是 `上必杀`：`doAllAction` 先写更具体的 goto，站立 helper
  被摘掉后后面的 `magichit1`/`bisha` 不再覆盖。防御中仍按 `onDefence` 后写（下+招→`招2`）。
  `空中必杀`：`onJumping`/`onDashing` 会 `gotoAndPlay` 该标签，但鸣人/一护时间轴都没有
  这个标签，catalog 标 `missing_timeline`，不编造帧。一护 `招换` 的魂援助已有
  `godot/generated/helpers/kon/combat.json`，魂 SWF 时间轴/位图现已导入并接线画面。
  旧目录的 `gaps` 仍记录失败/开场等演出及 `空中必杀` 缺标签；其中开场现已通过独立入口接线：
  `BattleIntro` 按源依次播放鸣人/一护登场、切镜头、ROUND/READY/FIGHT，支持 J/Num1 跳过、
  输入锁定和血条入场。46 项 Python 测试及 intro/menu/combat smoke 通过；原版播放器访问超时，
  同输入时序比对仍待完成，详见 [开场证据](../evidence/intro.md)。
  共用受击链已按 [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md) 编进战斗中间数据并接入切片运行时：
  35 角色 `beida`/`fangyu`/`onBeHit` 哈希锁定；`hits` 仅在 `onBeHit` 加一、第一下不播连击板；
  `站立` 源清零帧把 `hits` 置 0 后 `bar2` 才按 `maxhp/500` 追；`zl>10` 破防走 `bdxg`，
  `zl≤10` 防住走 `bdfyxg` 且不加 `hits`；`XG_qdjx` 第 2 帧 `pauseGame`+`shine`、第 15 帧
  `resumeGame`。防住刀光 `XG_fykan`/`XG_fykanx`/`XG_fyq`/`XG_fyqx`/`XG_mffy`/`XG_mffyx`
  已按 ExportAssets 的 sprite id（216/214/200/196/280/279）导入时间轴与位图，不再只记名字：
  挡住普通斩出 `XG_fykan`，第 11 帧 `unloadMovie` 收掉。同时修正了原先把
  `XG_mfdj`(314) 与 `XG_mfdjx`(298) 导反的目录。每个 `XG_*` 第 1 帧的 `StartSound` 与
  `SOUNDINFO` 音量已随时间轴抽出，对应 `DefineSound` 的 mp3 落到剪辑目录，
  运行时按帧事件起 `AudioStreamPlayer`（`XG_fykan`=215 满音量、`XG_fyq`/`XG_mffy`=197
  按 `18008/18893` 衰减），剪辑 `unloadMovie` 时随节点一起停，和 Flash 卸载剪辑一致。
  这是本工程第一处接线的原版声音。角色时间轴 `StartSound`（鸣人 `跳@42` soundId 40 等）
  已按该帧 `soundId` 物化 mp3 并在进入源帧时播放；我爱罗援助两处 `StartSound` 同样接线。
  `bdxg` 的元素档位 `XG_fire`(423)/`XG_ice`(358)/`XG_leidian`(334) 已按 sprite id 导入，
  各带第 1 帧 `StartSound`（396/337/317）；当前切片没有 `zl` 7–10 的招式，档位随附的
  `setColor`/`ColorMatrixFilter` 仍未实现。`zl` 10 的 `XG_stone` 与 `jumpxg`/`luodixg` 的
  `XG_jump`/`XG_luodi` 在 `main.swf` 全无 ExportAssets，原版就挂不上，不得补自制资源。
  `stageSound` BGM 已按 `loadSound()` 编成 `godot/generated/music/music.json`
  （`ichigo.mp3` 随机 <0.8 → `bleach.mp3` <0.5 → 现世 `city.mp3`）并由
  `godot/stage_sound.gd` 解释 `start(0,999)`/`setVolume(80)`，`tests/stage_sound_smoke.gd`
  锁选曲顺序与音量；**尚未接进 `main.gd`**，实际对战里还听不到 BGM。
  `bsd`/`showFace` 已编 `super_events`（鸣人第 507 帧 `鸣人2` 等）。
  `blackMu`（1510）、`ts_face`（1678）与 `XG_bs`/`XG_cbs` 已按 sprite id 导入：
  黑底是源 shape 535，横幅走 `"in"` 与 `face.gotoAndStop(标签)`。横幅线性渐变 1516
  与 `blackMu` KO 帧未接。步骤 E 原版同输入轨迹未捕获，`M2-04` 保持 pending。
  Flash MATRIX / JPEXS `Matrix.transform` 的旋转分量已按
  `x' = scaleX*x + rotateSkew1*y`、`y' = rotateSkew0*x + scaleY*y` 接入共用
  `_matrix_transform`；无旋转的站立/三连不受影响。一护 `上必杀`/`超必杀` 与鸣人
  `超必杀2` 的 `*atm` 是 `scale=0` 的 90° 框，对调分量会把横向刀口收成身后竖条，
  特效盖住对手也不结算。`getHitObj()` 没有“已命中”标记：同名 `*atm` 从显示列表
  消失后再 `PlaceObject`（鸣人 `砍技2` 的 `kj21atm@331` 与 `@338`）可再中。
  运行时只解释该矩阵与实例寿命，不为角色写大招受击补丁。步骤 E 对照仍缺。
  判定几何与命中寿命已写入 [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md) 第 1.2 节。
  鸣人下+I `超必杀` 已按源编 `body_warps`：`@832` 只把容器 `_x` 闪到对手，
  `@884` 再抄 `_y - 40` 并 `jump = 1`。同一水平面时 `cbs1atm@837` 可中；
  对手在跳跃高度则 Y 不相交。这不是前冲，也不按角色放大框。
  `beidax` 非击飞不加 `zhongli`：`cbs2` 的 `yup` 把对手停在空中，884 闪到
  `对手._y-40`，最后 `cbsatm@932` 击飞对手；攻击方 942 自跳「击飞」不是对手受击。
  `bsd`/`cbsd` 已解释为根级 `zhanting` + `stopMc(对手.mc)`：752–829 对手播放头停住，
  `gameRunning()` 为假时不能走/跳，`checkHit` 也不结算。`cbsw` 才 `playMc`。
  面向 / `bdmn._width` 容器闪现已编成通用 `body_warps` 分支；当前切片 638/764
  没有这些脚本，1672/1821 是其他形态，不得混编。
  **仍不是一比一**：横幅线性渐变 1516 与 `blackMu` KO 帧未接；元素档位的 `setColor`
  与 BGM 接线未落到 `main.gd`；`XG_bs`/`XG_cbs` 的 `in_point`/`out_point` 截断未实现；
  步骤 E 轨迹仍缺。`M2-04` 仍 pending。细则见
  [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md) 第 1.3 节。
  Godot 4.7.2 已重新 `export-release Web` 到 `dist/web/`（约 50 MB，无 SWF/Ruffle/AVM）。
- 开发切片首页已按根时间轴 `MENU` 接了三个可达入口，跳过选人、经选图进入战斗：
  `VS MODE`（`modo=3`）和 `TRAINING`（`modo=4`）都经选图进入当前鸣人/一护对战；
  `KEY SETTING` 进入源 `键位设置`。展示用英文（原版轮播按钮字），避免缺 CJK 字库。
  W/S/J 读 `_root.w/s/j`，底栏按 `downtxts` 每 tick 吐一字。键位用源 Flash 键码和
  `showKeyName`，写入 `user://bvn_5d.cfg`（对应 `SharedObject("bvn_5d")`）。
  `checkDead` 已按源在 `modo==4` 时不置 `sw`。`TRAINING` 已接源
  `DefineSprite_1991` `zdbx`：`setInterval(zdbx, 1000)`，`beida==0` 时
  `hp=_root.maxhp`、`ql=300`；`onBeHit0` 置 `beida=1`，回到 `站立`（帧 1）清零。
  未导入原标题轮播/按钮剪辑、HOWTOPLAY、选人；Vs Com 开发入口已接入，尚未完成原版对照；对战暂停菜单已可返回 `MENU`。
  `menu_smoke.gd` 与 `combat_smoke.gd` 已由 Godot 4.7.2 无头通过。
  `M6-02` 仍未完成。
- Adobe Flash Player Debugger 32.0.0.465 已能加载锁定的完整原版并显示主菜单；另以
  可重复构建的最小 AVM1 探针确认了 goto、enterFrame、对象移除、stop/play 和 interval
  的部分调度顺序，结论与哈希已写入 `evidence/probes/` 和 provisional ExecutionProfile。

## 本次辅助显示修正（2026-09-08）

辅助容器深度已按 main.swf 1738 的 p2/p1/p2fz/p1fz（7/9/11/13）接入；
嵌套贴图不再把局部深度加到场景深度上。MP 条已显示实际辅助的原版头像和裁切框
（当前 P1 我爱罗、P2 魂）。来源、重建与验证边界见
[辅助显示修正](../evidence/helper-presentation.md)。原版固定输入逐帧对照仍待完成，相关里程碑状态不变。

## 本次 P2 魂辅助实现（2026-09-08）

已导入魂的 102 帧时间轴、位图和声音；P2 召唤进入真实辅助动画，37–64 帧使用
源 `atm1`，后段六次各减对手 20 MP。`bsd(...,true)` 辅助分支与 XG_fzbs、
出场/收场 XG_fzcc 已接入。`doZhaoHuan` 的 bs=1 编为 `set_bs`，避免辅助演出
把一护停在召唤动作里。辅助在根时间轴回到 1 时回收，fzccXg 本身不隐藏节点。
我爱罗的对准脚本已改编译为 `clip_load_events`，不再错误影响魂的第 44 帧。
完整场景回归覆盖 P2 出场、冻结分支、六次扣 MP、收场、回站立继续攻击及镜像判定。
源证据与限制见 [魂辅助](../evidence/kon-helper.md)。音频 out_point 截断和原版固定
输入对照仍待完成，不代表 M5-02 或一比一验收完成。

## 电脑 AI 复刻规格（2026-09-08）

开场对照新增证据：从原版加载后的单个站立检查点连续推进，267 个显示帧的双方源帧、10 次轮询输入及 Ready 时点全部吻合。见 [连续片段报告](../evidence/ai/intro-continuous-r03.json)。此结果不覆盖完整加载、随机全序、视听或后续战斗，不能作为整场一比一验收。

已完成 [AI 静态分析规格](AI_SPEC.md)：扫描 35 个主角色、26 个援助和主程序，
记录五档难度、500 ms 随机刷新、全部标准决策分支、69 份控制器的 9 组原文变体，
以及鸣人/一护基础形态的感知矩阵和续招窗口。
[源审计](../evidence/ai/source-audit.json) 可由 `tools/analyze_ai.py` 重建；
[验证记录](../evidence/ai/README.md) 区分静态检查与待执行的原版对照。
尚缺完整随机/timer tape、首次回调与重复初始化寿命、缺失引用语义和全形态可达绑定。
现已接入原生 Vs Com 开发入口：P1 鸣人、电脑一护、简单难度。菜单、选图、开场、P1 输入、电脑攻击和退出清理的主场景测试通过；残影/颜色等效果服务、部分帧函数和整场原版对照仍缺。U-05 与 M5-03 保持未完成。详见 [AI 实现进度](../evidence/ai/compiler-progress.md)。

## 尚未完成

Godot 单线程 Web 导出已建立，4.7.2-stable 的无头、应用内浏览器和 Google Chrome
启动通过；Firefox/Safari 尚未完成，因此 `M0-01` 仍为进行中。当前开发切片可操作，但
尚未完成两名角色的全部动作语义：已编译的位移/投射物/援助生成覆盖源时间轴，
  我爱罗援助已有根时间轴与位图，元素档位的 `setColor`、BGM 接线（清单与 `stage_sound.gd` 已就绪，未进 `main.gd`）、`XG_bsq`/`XG_tishen`/`XG_xdash`（35 角色公用 shell 的 `bsd` 调用，尚无编译调用点）、滤镜、HUD 入退场动画、回合标记和计时模式、KO 字幕和若干取消分支仍缺失。角色与我爱罗援助时间轴上的 `StartSound` 已接线。连击次数与延迟血条逻辑已在切片里解释编译字段；`blackMu`/`ts_face`/`XG_bs`/`XG_cbs` 已按 sprite id 导入，横幅渐变与 KO 帧、步骤 E 对照仍缺。击飞/倒地/起身和现世主地面/
平台已有开发切片实现，尚未与原版逐帧对照。Flash 调度已有第一批原生播放器实测，但
兄弟回调深度顺序及 24 FPS 外载剪辑按宿主 30 Hz 推进已有隔离探针；嵌套创建首回调、OS 焦点时钟域和游戏同时命中顺序仍未确认；KO 演出/下一回合、原版
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

实现闸门已写入 [SOURCE_FIRST.md](SOURCE_FIRST.md)，并由 `AGENTS.md` 强制：改运行时前必须能指出每帧脚本、剪辑寿命和离开标签方式。重击、破防、连击次数的落地步骤见 [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md)；SOP 本身不是实现完成。跳跃高度与下+J 空挥不炸属于违反该闸门的已修案例，后续不得用标签结束帧或手感公式补全。

## 下一项工作

优先补固定输入原版捕获与未决调度探针，并完成 Firefox/Safari 启动记录；以下运行时缺口须先通过源优先五问再实施。

把 `stageSound` BGM 接进 `main.gd` 的进场（源 `startGame()` 即 `chushi()` 之后），补 `XG_bs`/`XG_cbs` 的 `in_point`/`out_point` 截断与元素档位的 `setColor`/`ColorMatrixFilter`，补横幅线性渐变 shape 1516 与 `blackMu` KO 帧，并按 HIT_RECEIVE_SOP 步骤 E 做原版同输入轨迹（三连 HUD、破防、`XG_qdjx` 顿帧、必杀横幅收放，以及一护 `上必杀`/`超必杀`、鸣人 `超必杀2` 的旋转框命中）。在对照记入 `evidence/` 前 `M2-04` 不得标完成。
把魂和我爱罗的命中、扣 MP 与 `XG_fzcc` 特效对照原版固定输入轨迹。
把走路循环、墙顶站位、`砍技1`、`万解`、位移、投射物、三连、受击、必杀与原版固定输入逐帧对照。并行完成 `M0-01` 的
Firefox/Safari 实测及 `M0-03` 未解决调度探针；在对照通过前保持 M2/M3 任务未完成。

### 连击板原版素材接入（2026-09-08）

已用 main.swf 的 1833 时间轴与 1816/1829/1831 位图替换纯数字 Label，保留左右根坐标、数字位数和闪白/闪烁。专用 HUD smoke、实机图形截图与 40 项 Python 检查通过；战斗 smoke 输出成功标记，退出仍有资源泄漏提示。原版同输入逐帧对照待补，M2-04 保持 pending。来源与重建命令见 [连击板记录](../evidence/combat/combo-presentation.md)。

## HP HUD (2026-09-08)

已接入源素材 HP HUD：双侧头像与遮罩、即时黄条、连击后延迟红条、低血量外框动画与当前无限时间图标。顶部开发文字默认隐藏。显示层直接读取真实 HP/hits，延迟层按源百分比计算；未更改伤害结算。源路径、重建和截图验证见 [HP HUD evidence](../evidence/health-hud.md)。同输入原播放器轨迹、入退场动画与计时模式仍待验证，不将 M2/M3 标为完成。

## Battle pause menu (2026-09-08)

原版 Enter 松键菜单已接入当前 Godot 切片：默认返回、上下循环、恢复战斗及返回主界面；复用原素材。出招表详情暂缓。菜单测试和图形截图通过，原版同输入轨迹及浏览器验收仍待完成，M6-02 保持未完成。见 [暂停菜单证据](../evidence/pause-menu.md)。

## 地图与 AI 状态同步（2026-09-08）

十张地图已导入，`main.gd` 已接入 `MapSelection`、按目录换图及平台配置；不能再记为“仅素材、未接运行时”。选图导航日志存在，但缺完整捕获来源与固定输入说明，不能替代全地图原版对照。地图动态背景、逐图对战与浏览器验收仍缺，覆盖布尔值保持 false。见 [地图记录](../evidence/content/stages.md)。

[AI_SPEC.md](AI_SPEC.md)、`tools/analyze_ai.py` 与全库审计已存在；已实现源代码编译的控制器、共享随机输入与 Vs Com 主场景开发入口；固定随机样本的原生 smoke 通过，完整原版同输入对照未通过，M5-03 保持 pending。受击冻结的两项 P1 已有修复及复测记录，见 [受击复核](../evidence/combat/review-2026-09-08.md)，不再列为未修问题。

本次复跑 41 项 Python 测试及十图选图 smoke 通过；Godot 启动日志有环境错误，未重做浏览器或一比一验收，详见同步记录。

## Move List and current fighter SOP audit (2026-09-08)

出招表详情已接入：复用 main.swf 第 2–10 帧的展开动画与共用说明，支持鼠标返回及原脚本的 Enter 路径；图形、菜单回归与 41 项 Python 测试通过，Web 已重建。原版同输入时序及浏览器验收仍待完成。

当前鸣人/一护 SOP 尚不完整：三形态攻击表已抽出，但形态切换、抖屏接线、SOUNDINFO 截断、横幅渐变/完整 KO 与步骤 E 轨迹仍有缺口。`wired` 仅代表输入目录接线，不能当作整招验收。详见 [逐角色审计](../evidence/combat/current-moves-sop.md)；M2-04/M3-01/M6-02 保持未完成。

## 选地图开发切片（2026-09-08）

模式菜单现跳过选人/援助，进入原版两列五行选图；10 张地图均可进入，重建出生点/平台并接入原版音乐选曲。原版探针与 Godot 已对照默认位置、循环导航、5 帧长按重复和 500 毫秒确认（原播放器实测 503 毫秒）。取消/重进与 10 图切换已通过回归。完整地图行为及跨渲染器像素一致性仍待验收，M6 不标完成。详见[选图证据](../evidence/content/map-selection/README.md)。

## 固定 Vs Com 的 KO 换局接线（2026-09-09）

致死请求已驱动源 KO 时间轴及字幕，接入 KO 暂停保护、死者/胜者焦点、
HUD 退场、胜场更新、nextfight 与 Ready 清理间隔。源计数从 1 开始，达到 3
即两次实际获胜。固定角色切片继续跳过选人，结束比赛返回选图。
`VS_COM_KO_SMOKE_OK` 覆盖 P1/P2 各连续获胜两局：真实 receive_attack 致死，
首胜后重置血量、保留胜场、播放 Ready 并清理 nextfight；第二胜清理 CPU/KO。
测试显式触发已注册的 Timer 回调，不证明真实时钟或原版调度。
仍有退出资源残留、未实现的计时器消费者、P1 旧运行路径、像素/完整轨迹对照等缺口；
M5-03 与完整游戏验收保持未完成。以上接线进度更新了本页早期 KO 未导入的记录。

开场连续对照的扩展状态检查发现首个差异：Ready（原版 display tick 453）时，一护 `touchFloor` 原版仍为 undefined，原生已经为 true；前 266 帧双方新增的 10 个状态字段一致。见 [首差报告](../evidence/ai/intro-state-first-difference-r03.json)。源帧对齐不代表回调状态时序已通过。

上述 Ready 首差已通过分离开场时间轴推进与帧脚本执行修复：相同记录下，267 帧的双方源帧与每人 10 个状态字段、10 次轮询和 Ready 边界全部一致。见 [扩展状态对齐报告](../evidence/ai/intro-state-aligned-r03.json)。普通对战与双方获胜的 KO 回归通过；完整目标仍待后续战斗和随机全序验收。

连续重放已延伸到 Ready 后 30 帧：补齐玩家主地面精确相等分支的源状态写入后，297 帧的源帧与每人 10 个状态字段、轮询均匹配，95 次检查点后的随机调用完整消费。见 [首 30 战斗帧字段报告](../evidence/ai/combat-first30-fields-r03.json)。此段没有玩家按键，且尚未比较坐标/几何、完整状态及视听，不能作为完整战斗验收。

600 帧原版记录的重放现停在首次受击结算差异：display 469 两端均进入鸣人源帧 1014，但原生提前扣血；原版在 1015 的 `onBeHit()` 才结算。见 [长记录首差](../evidence/ai/combat-input-first-difference-r04.json)。按键投递单独验证通过，连续重放尚未到玩家首次按键区间。

- 受击结算时机修复：接收攻击与 onBeHit/onDefence 源帧调用已拆开，首次命中数值对照推进至 display 470；display 471 火花暂停和受击位移仍有差异。双角色结算帧测试、双方两轮 KO 测试通过，未完成一比一。见 [源码诊断与实测](../evidence/ai/hit-settlement.md)。

- 命中火花纳入 Main 固定逻辑调度：禁用各实例自主物理步，按 tick 开始时的实例快照推进，保留新实例创建时的第 1 帧。源 XG_qdjx 第 2 帧暂停、第 15 帧恢复的集成测试通过。连续对照见 `evidence/ai/combat-hit-clock-r04.json`：此前 display 471 暂停差异已消失，帧及观察字段匹配至 474；随后随机消费者缺失（预期鸣人 frame_1 的 site 1，实际进入一护 randAI），回放显式停止并保存 random_failure。该次日志包含拒绝随机刷新断言，不是完整通过；受击位移及受击语音随机调用仍待核实。

- 受击语音随机链：从共享 hurtVoice 编译随机调用点、1000/2000 ms 冷却及 onBeHit 的概率，保留先抽签再检查冷却、死亡分支不抽签。扫描所有锁定 game SWF 的 ExportAssets，voice_hurt1/2/voice_die 均不存在；不伪造语音，但保留 Sound 对象选择的随机和计时效果。新增边界测试通过。连续对照 `evidence/ai/combat-hurt-voice-r04.json` 的随机失败为空、无 SCRIPT ERROR，下一状态首差 display 485 为 P1 touch/touchFloor/hstm；受击位移仍不一致。真实 getTimer 起点及语音冷却跨启动/重放校准尚未完成，本次首次抽签 0.6356 > 0.5 不进入冷却或选音，不能据此声称全链原版时序验收。

- 玩家 BODY 编译准备：现有 CPU 编译器在源 useAI 守卫处删除玩家分支，不能直接复用于 P1。新增 `compile_ai_body.py --player`，产物 `godot/generated/fighters/minren/player_body/` 保留 11 个 BODY 函数及两个超时回调中的玩家按键路径，状态仍为 compiled_not_integrated。原生测试验证 hurtSkill 读取换键（不按 goran 判定）、敌方必杀阻止脱身、上+冲得到源 dashY=-14、beidax 按源移动并递增 hstm/time、暂停仍先 applyColors 而不移动。现有一护 CPU body.gd 重建后逐字节一致。此为 P1 受击替换的编译前置，尚未连接源实例生命周期，display 485 首差仍待修复。

- 玩家受击实例调度组件：`compile_ai_body.py --player` 从源 ClipAction 和逐帧显示列表编译 hurt_hooks，鸣人普通受击 Sprite 16 / depth 30 的成员帧为 1016–1023，击飞 depth 29 为 1029–1038。`source_body_callbacks.gd` 复用既有实例 generation/placed_tick 调度器调用已编译 beidax，原生测试验证放置当帧不调用、下一 tick 执行、停止播放仍回调、移除重放置重新等待、清理后不回调。尚未接入 Main；下一步须建立玩家 BODY context 和源键映射、避免原有物理/碰撞重复执行后替换旧受击路径。直接用 CPU 全控制器编译鸣人遇到未支持 projectile 初始化（frame 382），没有跳过或伪造该投射物；受击 hooks 独立编译，不声称覆盖投射物。

- 玩家 BODY 已接入固定 VsCom：Main 在推进播放头前设置 driver tick；FighterRuntime 的实际排队帧变化通知实例观察器。受击 enterFrame 使用源 beidax hooks，BODY on_enterframe 负责位置/平台/状态，不再重复执行旧受击移动和旧 body collision。其余玩家动作控制仍保留旧路径，未声明全玩家控制器完成。接收结算中的玩家 updateDirect 已接源函数。玩家键映射使用 session 的 up/down/dash/summon 对应源上/下/冲/换；isNaruto=true 来源 MAIN6 鸣人配置及 MAIN8 loadFighters 的字段复制。
  连续对照 `evidence/ai/combat-player-body-r04.json` 消除 display 485 差异，首差推进到 display 500：P2 源帧一致为 1，但源动作=1、原生=0。314 个几何快照双方最大相对位移差均为 0，原始 X 仍保留浮点表示差。双方两轮 KO 测试通过；三次进入/退出对战的弱引用检查证明 driver/body/context 被释放且信号解除。初次回放和 KO 日志有 ObjectDB 退出告警，随后 verbose 回放与生命周期测试未复现；不宣称全部资源泄漏已排除。完整输入及战斗对照仍待完成。

- display 500 首差重新定位为观察阶段未对齐，不能直接判定 CPU 动作错误。原版最小调度夹具 r06 记录 frame390 退出 → 根状态观察（动作1）→ frame1 进入 → frame1 退出（动作0）；r05 自然600帧未经过390，未当作证据。见 [观察阶段分析](../evidence/ai/frame-observation.md)。未改运行时赋值时机；连续对照仍 first_difference，需先对齐源脚本边界与根观察点。

- 回站立同边界原生对照通过：新增只读 source_frame_script_boundary 信号，r06 原生夹具在调用者退出/目标进入/目标退出三处的五字段与原版一致，报告 `evidence/ai/frame-order-r06/native-boundaries.json`。没有改运行时赋值时机，也没有把根观察器与整步末尾的 first_difference 标为通过；世界级采样阶段仍待校准。

- r07 全帧脚本边界对照：原版独立副本完成600对战帧，记录1372条两个基础形态的 DoAction 进入/退出事件。新增 `combat-boundaries` 诊断模式按原始全局顺序比较 source_frame、当前帧和状态；用完整源 DoAction 清单过滤非脚本帧，不用实际出现过的参考帧掩盖原生额外脚本。根快照仍记录差异，模式不将根/整步观察未对齐视为通过。
  已据首差修复：P1 enterFrame 不再提前执行 action_exit，改由编译的 frame_calls 执行；Main 先运行两角色已排队帧，再分批执行 goto 目标；Ready 帧操作移至角色初始帧脚本之后；顶层 ql +=/-= 常量按原行序编为 energy_delta，在源帧退出前执行而不是事后结算，并防止旧 energy_events 重复执行。源直接加减不预先夹到300。
  证据按阶段保存在 boundary-first/player-goto/cross-actor/ready/energy-r07.json。最终426个帧脚本边界状态匹配后因随机消费者不符停止：原版接着执行 main getRandInArray，原生快速回放时的 getTimer 尚未满足 hurtVoice 冷却。须记录并重放原版逐调用时钟，不能跳过随机 tape。当前日志有预期的拒绝随机刷新断言，不是完整通过。两轮 KO、三次驱动清理、r06 同帧边界对照均重跑通过，无 SCRIPT ERROR；部分运行仍有退出资源告警，完整资源清理未验收。

- hurtVoice 逐调用时钟：原版分析副本现在记录该函数四个 getTimer 调用点的实际返回值。收集器保存 clock-tape.json 并校验索引连续、毫秒值单调非负；SourceClock 独立校验调用点顺序，错误锁存、不跳读，回放不再使用本机时间决定该函数的冷却。冷却检查和时间戳写入分别读时钟，概率拒绝不读时钟，死亡分支不读随机数。编译的 hurt_voice.json 保留四处源路径标识。
  r08 完成原版600对战帧采样；原生消费完两个时钟记录，clock_failure/random_failure 均为空，前460个帧脚本边界匹配，第461个事件出现 P1 frame1069 与预期 P2 frame13 的执行顺序差异（source display559，已注入第一个 right 输入）。见 evidence/ai/boundary-clock-r08.json。这不是完整回放通过；倒地起身/玩家控制及世界级观察阶段仍待继续。语音冷却边界/不同检查写入时间/错误锁存测试、两轮 KO、收集器3项边界测试均通过；原生本轮无 SCRIPT ERROR。

### Recovery callback and ordering evidence

Source frame 1064 recovery movement is compiled with placement lifetime; its native regression passes. The unchanged r08 replay now has zero P1 relative displacement error through 375 snapshots, with a remaining 6-pixel P2 error and boundary difference 461. Controlled r09/r10 probes show that cross-actor callback order changes with goto order at unchanged display depths. The shared callback scheduler still needs correction; M5-03 remains pending. See [recovery-order evidence](../evidence/ai/recovery-order.md).

### Shared callbacks and reference input correction

Shared BODY/controller registration and initial-versus-deferred frame batches are implemented for the fixed slice. Source standing hit-count reset and duplicate legacy hurt-fall handling are corrected. Important: the old global Key.isDown override was ineffective; those captures do not prove delivery of their input intents. New `input-alias-r12` completed 600 source fight frames and verified all 3,132 key reads. Native boundaries 1–498 match; boundary 499 and P1 facing still differ in the legacy player walking path. Full source player controllers, all event phases, match replay and Web acceptance remain pending. See [current evidence](../evidence/ai/callback-registry-and-input.md).

## 固定 Vs Com：玩家源控制器与精确数字对照（2026-09-09）

鸣人玩家现使用原版完整基础控制器分支，双方共享回调注册表与跨角色目标帧队列。已修正受击 `updateDirect(true)` 的参数和电脑 BODY 接线；r13 中一护 54 px 相对位移及朝向差异消除。新增原版 binary64 trace 编码，避免将默认十进制输出损失当成气量计算错误。

七项原生定向测试及七项采集器测试通过，生成产物可重复构建。原版 r13 采集了 600 战斗帧，原生对照仍因 `XG_qdj` 首帧四次随机调用缺失而失败（620 个已匹配源帧边界）。P1 小幅坐标精度差异、完整随机/特效调度和整场验收仍待解决；M5-03 保持 pending，没有新增 Web 矩阵验收。见 [证据与下一处源码缺口](../evidence/ai/player-controller-and-binary-trace.md)。

## 特效随机调用与重复防御判定进度（2026-09-09）

`XG_qdj` 首帧两条随机偏移表达式已编译，四次随机调用接入双方共享的原版随机流。最小 FP32 代码探针确认 attach 调用者先返回、再执行新特效首帧；大写 `_X/_Y` 写入实际父坐标。源受击查询已绕过旧的「攻击实例已命中」缓存，恢复同一攻击在防御接收剪辑重新出现后再次命中的行为。

同一 r13 tape 的 1,166 个预期边界及 298 次检查点后随机调用、时钟读取均已匹配，但对照仍是失败：原生末端多出一个 P1 帧边界，根观察点仍有 35 组帧号和 24 条状态差异，P1 最大相对 X 差异约 4 像素。不得据边界顺序匹配称整场一比一。五项原生定向检查和十四项 Python 检查通过；完整调度、视觉、整场及 Web 验收仍待完成。详见 [源码与证据](../evidence/ai/effect-random-and-repeat-contact.md)。

## 特效注册顺序与根观察点（2026-09-09）

最小 FP32 代码探针证明特效帧脚本会按实例注册顺序与角色回调交错。特效现接入共享注册表，替换临时统一早执行阶段；恢复暂停时多跑一次受击回调的问题消除。对照采样移到原版根观察点，并在原版 `done`/`fscommand(quit)` 所在阶段截止，不删除预期事件。比较器同时收紧为检查全部边界、帧号、状态及随机/时钟 tape 消费完整性。

r13 的 600 战斗帧片段离散字段对齐：1,166 个边界、298 次检查点后随机调用、897 组帧号和 1,794 条角色状态全部一致。坐标仍有单精度低位误差，视觉/声音未验收。新采集的独立 r14 在第 723 个边界失败，当前线索是鸣人弹体首碰后改名 `abcd` 与旧攻击名称查询。r13 通过不能替代 r14 或整场验收；M5-03 继续 pending。见 [源代码、探针和两份对照](../evidence/ai/effect-registry-and-root-observer.md)。

## 弹体延迟改名与两份独立片段（2026-09-09）

弹体现保留独立的源实例名：`gotoAndPlay(5)` 先改变播放头，排队执行第 5 帧后才将 `zh1atm` 改成 `abcd`。最小原版探针验证了这两个阶段及移除前已排队脚本的取消。攻击与弹体碰撞查询都读取当前源名字；同名重建不继承旧实例的改名，子帧操作与角色目标帧共用 FIFO 顺序。

修正后 r13、r14 两份各 600 战斗帧片段的离散字段均对齐：分别 1,166/1,084 个边界、298/287 次检查点后随机调用，帧号、状态和时钟 tape 无差异。六项原生定向检查通过。仍有坐标低位误差，且完整 KO/换局对照、其他动作路径、视觉音效和 Web 矩阵未验收；M5-03 继续 pending。详见 [弹体源语义与验证范围](../evidence/ai/projectile-deferred-rename.md)。

### 2026-09-09：完整比赛超时源审计

新增 [倒计时与超时审计](../evidence/ai/match-timeout.md)：静态保留 5 个剪辑、
18 份脚本和完整逐帧变化。当前原生流程缺 timeset 计时器和 timeover 结算；
根/HUD 实例寿命、回调接收者及完整比赛对照仍待补齐，尚未修改运行时。

### 2026-09-09：长对战采集与下一项首差异

[r15](../evidence/ai/match-flow-r15.md) 保留 6000 帧窗口及异步退出尾部，
覆盖原版两局 KO 和返回选人；123 次倒计时回调、一次 timer_load、一次 nextfight。
原生重放在一护 735/726 脚本排队次序处失败。重放器允许第 8 帧正常前驱后，
r13/r14 均继续通过；收集器 10 项测试通过。生产运行时未改，超时和整场一致性仍待完成。

### 2026-09-09：四项共用行为修复

[源审计与验证](../evidence/ai/receiver-rule-fixes.md)：已修复防御 updateDirect 参数、
错误的零后缀攻击映射、HUD 低血量回气缺失及致死血量截断。均使用共用规则，
未新增角色名分支；35 个主角色的对应函数已完成分组审计。7 项原生测试通过，
r13/r14 保持通过；r15 在 2798 个边界后停于 KO 第 30 帧恢复顺序，整场仍未对齐。


### KO instance scheduling and round continuity

The shared scheduler now interleaves each KO root/child instance with actor BODY and initial frame scripts. Round reset preserves source energy/hits/pause, repeated same-frame goto does not repeat its script, and source hit-energy additions are not prematurely capped. r13/r14/r15 match all currently compared fighter fields; r15 consumes 4158 boundaries, 1202 random calls and 19 clock reads across both rounds and battle teardown. Twelve native checks pass. Countdown/timeover, exact geometry, boot, additional characters and presentation/Web parity remain pending. See [evidence](../evidence/ai/ko-instance-scheduling.md).


### Original Vs Com menu entry

Vs Com is restored as the second source menu entry, with compiled held-key scrolling and frame-15 confirmation, original raster assets/key sounds, and the existing fixed-character map-selection route. Native Flash probe, four native checks and Web export evidence are recorded in [menu entry validation](../evidence/menu/vs-com-entry/README.md). Other character migration is deferred. Other menu destinations and full visual/gameplay parity remain pending.

### 2026-09-09 援助连续命中与时长

我爱罗/魂共用的一次性命中缓存已移除，我爱罗子剪辑终端 stop 已编译；旧双人路径
的受击倒计时改从原 beidax 回调开始。原生 Flash 固定 O 案例分别核对 8 次/5 次
命中和时序，并以高气量案例核对魂六次扣气；详见 [援助证据](../evidence/combat/helper-timing.md)。旧双人路径回站立
清 hits 的根观察阶段仍差一帧，完整视听/Web 验收未完成。相关里程碑保持 pending。

### 2026-09-09 跑步子动画回退

修复源控制器按住方向反复 goto 第 10 帧导致跑步子帧固定在 1 的回退。
源驱动路径按保留放置实例独立计时；旧路径的 placed_frame 算法不再作为两条路径
都已验证的依据。控制器、真实菜单键盘、朝向/子帧、松键/反向、生命周期、暂停、
KO 共七项原生检查通过，Web 包已重建。旧 combat_smoke:177 投射物断言在去掉
本次修改的临时副本中同样失败；不称全套通过。原版逐姿势截图对照仍待验收。
详见 [回退原因与防复发记录](../evidence/combat/run-visual-regression/README.md)。

### Super guard regression fixes (2026-09-09)

The current Vs Com source-controlled path no longer overrides an authored super
branch using the legacy contact cache. Renamed attack-only child timelines now
retain independent playheads, natural rename events, and source stop frames.
Naruto's blocked normal/up supers match the original 1/30 HP chip outcomes;
all six guarded-super fixtures match 1800 retained snapshots. Eight native
checks, 29 Python checks, and the r13/r14/r15 observed-field match replays pass.
See [fix evidence](../evidence/combat/super-guard-fix/README.md). Full match
geometry, visual/audio and Web parity remain pending.

### Dash contact boundaries (2026-09-09)

Native Flash proves edge/corner contact is a MovieClip hit, while a one-twip
gap is not. The shared port operation now uses inclusive bounds across fighters,
helpers, stage hits and AI. A late Naruto Up+I rush case previously missed its
second 40 HP; all 241 observed snapshots now match. Three calibrated scenarios
match 723 snapshots, with the helper activation observer phase reported
separately. Repeated player dash presses and run visuals remain covered. See
[dash evidence](../evidence/combat/dash-validation/README.md). Full geometry,
lifecycle, browser and all-character parity remain pending.


## Config options and timeout — 2026-09-09

Config now exposes source-derived CPU difficulty, quality state, time, life, key configuration and save/return. Difficulty and life apply at fight entry; the source timer and timeout winner/draw timeline are compiled and connected. Normal is hidden and Vs Com is selected initially. Native Flash comparison passes 161 Config and 451 timeout snapshots; native settings/menu/KO checks and three existing combat replays pass. Quality antialiasing and timeout badge blink remain unimplemented visual differences; full browser and mode parity are pending. M6-02 stays pending. See [Config evidence](../evidence/config/README.md).


### Direction dash and Up+I follow-up (2026-09-09)

Four native Flash player direction-dash fixtures match 324 root snapshots; two additional Up+I/CPU dash fixtures match 482 combat snapshots. Source rejects direction dash during action -1 and with 99 MP; up/down + L in allowed states consumes 100 MP. The source-compiled Vs Com logic was already connected; missing XG_xdash assets are now imported and visible. No hitbox, immunity or tracking rule changed. Blue afterimages, older PvP/training control paths and full combat/browser parity remain pending. See [source and regression evidence](../evidence/combat/ghost-validation/README.md).


### Shared source combat in all local modes (2026-09-09)

The production legacy PvP/training combat branch is removed. All three modes now use the same compiled actor callbacks, receiver chain, collision services and deferred queue; player/AI input is selected within the original predicates. Training recovery now uses the source 1000 ms wall-clock interval instead of 30 simulation ticks. PvP and training each match 602 complete actor observations, including exact coordinates; existing r13/r14/r15 replays still match. Mode lifecycle and PvP KO checks cover input ownership, no training KO, timer disposal and returning to the same mode. These close the documented mode-path gap, not every remaining move/character/browser acceptance item. See [shared-mode evidence](../evidence/combat/shared-mode-validation/README.md).


### Move matrix and non-interfering capture requirement (2026-09-09)

The two-base-form matrix now runs 356 native scenarios without script assertions. Of 43 complete retained original comparisons, 38 match and five still differ at form replacement; one additional capture is invalid. Source coordinate storage, Naruto normal-I conditional continuation, and absent aerial-special labels were repaired from source and recordings. The 280 cancel-window edge obligations and other geometry/lifecycle/browser boundaries remain unaccepted. Flash sampling is stopped because windowed/background launch still raises windows; capture is disabled by default. See [move acceptance evidence](../evidence/combat/move-boundary-validation/README.md).


### Resumed original sampling and transformation start (2026-09-09)

The user subsequently authorized Flash popup windows; the remaining original batch has resumed. Ichigo frame 967's dropped `wankai_start()` call is now compiled in source order, including the second 300 energy deduction and cbsd pause. Its retained original prefix matches 202 actor states; full form replacement remains different starting at observation 101. The earlier transformation-difference summary included this pre-replacement defect and must not be read as proving the entire start sequence was already correct. See [resumed evidence](../evidence/combat/move-boundary-validation/resumed/README.md). Full acceptance remains pending while sampling continues.


### Timer digit presentation (2026-09-09)

The HUD no longer draws the unlimited symbol during finite countdowns. Source digit sprites, their frame selections and nested placements are imported and driven by the compiled timer callback; the extra font Label is removed. Native tests cover paused time, 10→09, 01→00, unlimited and training. Rendered 10/09/infinite screenshots are retained in [timer presentation evidence](../evidence/config/timer-presentation/README.md). This corrects the earlier overlay-only diagnosis.

### Transformation availability (2026-09-09)

Playable matches now disable the `万解` action for both slots, including actors replaced through character selection. Transformation entry exists, but form replacement remains incomplete (see the move-boundary validation above); the user requested disabling it until implemented. This is a development availability restriction, not a change to original transformation semantics. Isolated source probes retain access to the timeline. `transformation_gate_smoke.gd` passes for Naruto, Ichigo and Hitsugaya: command/source goto/direct entry is rejected without consuming energy, while normal attack remains available. Full transformation acceptance stays pending.

### KO background child playback (2026-09-09)

Fixed the persistent red square by scheduling the authored blackMu child independently of its stopped parent, including its compiled frame-30 stop. The isolated original-player probe and Godot match all 36 playhead samples; KO, two-round flow and player visual/controller checks pass. Full-match visual and Web parity remain pending. See [evidence](../evidence/visual-audio/ko-background/README.md).


### Hitsugaya base-form acceptance: not passed (2026-09-09)

Bankai is deferred at the user's request. The 167-case base-form matrix has retained same-input original comparisons. Two summon cases remain different: airborne-target freeze/landing at tick 30 and held-summon frame timing at tick 115. A global helper reorder regressed other cases and was reverted. Source-backed fixes restore root shake assignment semantics, the authored landing effect, grouped ice-guard effects, controller-scope guard calls, scene wall-clamp ordering and wall hitNear settlement, sound sample ranges/channel envelopes and single effect-sound playback. Retained red/green ice-guard evidence matches 602 actor and 301 root-position observations. The live acceptance boundary includes 88 explicit cancel-window edges plus visual/audio/browser checks; these are not implied by ordinary move matches. See [base-form evidence](../evidence/combat/rifagu-base/README.md). Full base-form acceptance remains pending.


### Hitsugaya aerial-U bitmap boundary (2026-09-10)

The recovery-frame rectangular ice fragment was reproduced without a map. Shape 107's curved bitmap fill was incorrectly reduced to its AABB. The extractor and shared renderer now preserve its boundary; the complete frame-154 ice remains intact. Native red/green pixel regression and 91 Python tests pass. This fixes a rendering defect and does not close base-form behavior or original-player pixel parity acceptance. See [evidence](../evidence/visual-audio/bitmap-shape-clip/README.md).


### Hitsugaya helper scheduling alignment (2026-09-10)

Original callback instrumentation locates retained helper root frame settlement between newer action clips and older fighter BODY callbacks. Helpers now participate in the existing global registry, fixing both remaining summon timing differences. The 167-case matrix has 152 exercised matches, 4 energy-negative matches and 11 source-missing-label matches, with no state differences; all 69 calibrated cancel-input cases still match. PvP/training comparisons, teardown/reentry and 93 Python tests pass. Both summon scenarios also produce byte-identical 602-row state outputs in Chromium WebGL and native Godot. The production Web package is rebuilt. Full visual/audio, additional geometry/callback boundaries and browser focus recovery remain unaccepted; Bankai remains deferred. See [evidence](../evidence/combat/rifagu-base/helper-registry/README.md).


### Repeated Hitsugaya down+I placement (2026-09-10)

Reset source placement-event bookkeeping on action entry. Previously the first cast positioned cbs1atm correctly, while the second reused the deduplication key and left the new ice instance at its authored default position. Three casts on retained actors now target fresh opponent coordinates across both facings; retained subsequent frames do not chase the opponent. All 11 existing down+I source comparisons and 93 Python tests pass. These short original fixtures had not covered a second fully funded cast. See [repeated-cast evidence](../evidence/combat/rifagu-base/repeated-ice-placement/README.md). Full base-form acceptance remains pending.


### Shared direction-dash snapshots (2026-09-10)

The previously missing showdow service now snapshots the current fighter display
into the source background-effect layer, with original RGB offsets, wrapper-lived
call cadence and quantized alpha decay. Both slots and all three playable base
forms share the adapter. Three original two-dash references match all 297 ordered
spawn/fade events; native and Chromium WebGL texture-freeze checks pass. Existing
dash, shared-mode and r13/r14/r15 observed-field regressions remain matched.
Full original pixel identity, remaining characters and Firefox/Safari are outside
this acceptance; transformations remain deferred and online is unchanged.
See [shadow evidence](../evidence/visual-audio/shadow/README.md).


### Quality rendering and timeout HUD correction (2026-09-10)

The existing native Config page now drives actual HIGH/MEDIUM sample density
through a shared supersampled rendering surface. The original LOW assignment
bug is retained. The surface preserves logical game coordinates and forwards
keyboard/mouse input; physical allocation excludes letterboxing and redundant
Window viewport stretch, with a WebGL hardware-size limit.

The earlier "missing timeout badge blink" diagnosis was wrong. A new native
original run records 231 ticks: the referenced p1win/p2win/bzxg targets are
undefined and the actual xuetiao win clips remain stopped at frame 1 while the
winner counter increases. The port now preserves that no-op; normal KO still
uses updateWins. Source option and timeout traces, targeted native checks and
100 Python tests pass. See [rendering evidence](../evidence/config/rendering/README.md)
for final Web results and limits. Full Flash raster equivalence, high-DPI
performance budgets and cross-browser coverage remain unaccepted; no deployment.

### Renji base-form expansion (2026-09-10)

阿散井·恋次基础形态已按 `game/fighter/Renji.swf` 的 Sprite 717 源时间轴导入，万解/转换入口按用户要求继续禁用。54 个源驱动 360 帧案例均有原版固定输入 capture；最终显式援助配置 native 复跑为 54/54、每案 722/722 状态匹配，且 r05 记录的五项运行时哈希在采样前后一致，逐案记录见 [Renji explicit-helper freeze r05](../evidence/combat/renji-base/native-freeze-explicit-helper-r05.json)。r04 保留为历史记录，不用于冻结结论。另有 124 个 300 帧 native-only 扩展案，仅用于边界执行，不并入原版 parity。音频探针已核对瞬步、砍1、必杀、上必杀及超必杀关键源帧的 StartSound ID、runtime 单次触发、segment sample 范围与包络；临时 Web 探针通过 CUA 观察了六个同源帧的实际画面，但工具没有持久截图路径。原版播放器同阶段截图、逐像素和浏览器音频计数仍待采集，故不关闭全角色或 M6 条目。详见 [Renji parity audit](../evidence/combat/renji-base/original-parity-audit-r03.json)、[Renji explicit-helper freeze r05](../evidence/combat/renji-base/native-freeze-explicit-helper-r05.json)、[Renji audiovisual audit](../evidence/combat/renji-base/audiovisual-audit-r01.json) 与 [Renji Web evidence](../evidence/combat/renji-base/web-audiovisual-r03.md)。


### Expanded base roster integration status (2026-09-10)

The source-driven selection registry now exposes six base-form fighters (`鸣人`, `一护`, `日番谷`, `佐助`, `卡卡西`, `恋次`) and three helpers (`鼬`, `魂`, `我爱罗`); transformation and second-form entries remain unavailable. Sasuke's WKframe=1 base form has 18/18 clean source/native comparisons matched at 602/602; its 66 boundary fixtures have completed native-only target-reach execution and all 66 explicit-helper original/native comparisons matched at 602/602 with zero differences or tool errors (see [Sasuke boundary r02](../evidence/characters/sasuke-you/sasuke-base-boundary-final-r02.json) and [runtime hash audit](../evidence/characters/sasuke-you/sasuke-base-boundary-runtime-hashes-r02.json)). You helper (`you.swf`, display name `鼬`) has 482/482 rows matched on six common fields (`frame`, `x`, `y`, `orientation`, `action`, `attacking`); source-only `hits`/`atm1`/`atm2`/`atm3` remain un-compared. Kakashi's final frozen regression covers 20/20 cases (19 regular plus no-hit), including the revalidated `757` case; see [Kakashi final regression](../evidence/characters/kakashi/final-regression-r01.md). Renji's final frozen 54-case, 360-frame native rerun is complete at 54/54 matched; the separate 124-case native-only expansion used 300-frame fixtures and is excluded from original-player parity. See [Sasuke/You evidence](../evidence/characters/sasuke-you/), [Kakashi evidence](../evidence/characters/kakashi/), and [Renji audit](../evidence/combat/renji-base/original-parity-audit-r03.json).

The Web selector and combat path have been exercised for the newly registered roster, including portrait/name rendering, entry, movement, attack, pause/resume and return/reselect flows. On the current 8062 export, Enter closed the pause overlay and the timer/CPU resumed with HP changing. Original-player screenshots, exact pixel comparison, visual/audio comparison and per-event browser audio counts remain open; remaining character-specific audiovisual captures require clean exclusive Flash windows. M6 remains pending until the remaining per-character acceptance records are complete.

- 2026-09-11：键位面板加入独立方向键 / Enter / Esc 导航，修复 P1 Up/Right 同绑 D 时 P2 不可达；方向键名改用 ASCII，避免缺字方框。`KEY_SETTINGS_SMOKE_OK` 与 `CONFIG_FLOW_SMOKE_OK` 通过；浏览器视觉与原版同输入对照未验证，M6-02 保持未完成。见 [修复记录](../evidence/config/key-settings/README.md)。

- 2026-09-11：按用户要求，主菜单隐藏未接入的 Information、More Games、Exit，连同已有隐藏的 Normal 一起从导航和确认路径排除；保留 Vs Com、Vs Mode、Training、Setting。此为 Web 入口裁剪，不修改原版导入数据。


### 2026-09-11 — helper/super overlap freeze

Helper roots now preserve undefined `sw`, and shared stopMc/playMc require
strict boolean false as in the source. The reported Hitsugaya Up+I / P2 Gaara
overlap reproduces before the repair; afterward all 602 fighter states match
a fresh original-player run. Three continuous controlled Vs Com overlaps,
shared PvP/training replays and r13 pass. Helper post-exit action, the existing
combat_smoke projectile assertion, and Web/deployment verification remain
separate open boundaries. See [source and evidence](../evidence/combat/helper-super-overlap/README.md).

### 2026-09-11 — Sasuke/You and Renji overlap timing

The focused Sasuke + You versus Renji Up+I and Up+U source replays now match
602/602 fighter states and 602/602 helper rows with zero differences. The
public scheduler advances helper roots before fighter timelines so same-tick
registrations retain source callback behavior; no character-specific hitbox,
delay, or registry-sort rule was added. Focused pause and shared overlap checks
also pass. Full character matrix, visual/audio/Web parity, and HIT_RECEIVE_SOP
step E remain pending. See
[evidence/characters/sasuke-you/renji-overlap-upI-upU-fix-r01/README.md](../evidence/characters/sasuke-you/renji-overlap-upI-upU-fix-r01/README.md).
