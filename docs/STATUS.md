# 当前状态、风险与待验证项

状态同步日期：2026-09-08。按当前工作树与已有证据核对；本次检查范围见 [同步记录](../evidence/status-sync-2026-09-08.md)。

B-01～B-03、M1-01 已完成，M0-01 进行中；其余任务维持 pending（包含已有局部产物但未验收），对应任务表已补产物与证据。下列开发切片实现不代表里程碑完成。

## 已完成的资料与已实现的开发切片

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
  `blackStg("KO")` / `KOstart` 暂停与 `nextfight` 回合重置尚未导入，无 KO 字幕元件。
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
  未接线项仍在 `gaps`（失败/开场等演出、`空中必杀` 缺标签）。
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
  未导入原标题轮播/按钮剪辑、HOWTOPLAY、选人、AI 模式；对战暂停菜单已可返回 `MENU`。
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

已完成 [AI 静态分析规格](AI_SPEC.md)：扫描 35 个主角色、26 个援助和主程序，
记录五档难度、500 ms 随机刷新、全部标准决策分支、69 份控制器的 9 组原文变体，
以及鸣人/一护基础形态的感知矩阵和续招窗口。
[源审计](../evidence/ai/source-audit.json) 可由 `tools/analyze_ai.py` 重建；
[验证记录](../evidence/ai/README.md) 区分静态检查与待执行的原版对照。
尚缺完整随机/timer tape、首次回调与重复初始化寿命、缺失引用语义和全形态可达绑定。
本次未改 Godot 运行时；U-05 与 M5-03 保持未完成。

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

[AI_SPEC.md](AI_SPEC.md)、`tools/analyze_ai.py` 与全库审计已存在；没有原 AI 运行时、共享随机 tape 与同输入对照，M5-03 保持 pending。受击冻结的两项 P1 已有修复及复测记录，见 [受击复核](../evidence/combat/review-2026-09-08.md)，不再列为未修问题。

本次复跑 41 项 Python 测试及十图选图 smoke 通过；Godot 启动日志有环境错误，未重做浏览器或一比一验收，详见同步记录。

## Move List and current fighter SOP audit (2026-09-08)

出招表详情已接入：复用 main.swf 第 2–10 帧的展开动画与共用说明，支持鼠标返回及原脚本的 Enter 路径；图形、菜单回归与 41 项 Python 测试通过，Web 已重建。原版同输入时序及浏览器验收仍待完成。

当前鸣人/一护 SOP 尚不完整：三形态攻击表已抽出，但形态切换、抖屏接线、SOUNDINFO 截断、横幅渐变/完整 KO 与步骤 E 轨迹仍有缺口。`wired` 仅代表输入目录接线，不能当作整招验收。详见 [逐角色审计](../evidence/combat/current-moves-sop.md)；M2-04/M3-01/M6-02 保持未完成。

## 选地图开发切片（2026-09-08）

模式菜单现跳过选人/援助，进入原版两列五行选图；10 张地图均可进入，重建出生点/平台并接入原版音乐选曲。原版探针与 Godot 已对照默认位置、循环导航、5 帧长按重复和 500 毫秒确认（原播放器实测 503 毫秒）。取消/重进与 10 图切换已通过回归。完整地图行为及跨渲染器像素一致性仍待验收，M6 不标完成。详见[选图证据](../evidence/content/map-selection/README.md)。
