# 数据契约 v1

本文件定义离线工具、Godot 运行时和对照工具之间的拟定接口。`spec/schemas/` 为可校验 JSON Schema；实际图集、动作时序和 Godot 资源尚未生成。已存在的 `scripts/*.json` 是独立的原脚本索引格式，不可直接当作下列运行时数据。

## 统一约定

- JSON 使用 UTF-8。游戏内部 ID 稳定，文件名保留源大小写；跨文件引用不能依赖显示名称自动拼接。
- 原 SWF 帧号从 1 开始；动作 `tick` 和重放 `tick` 从 0 开始。单位必须体现在字段名中。
- `status` 为 `extracted_partial`、`synthetic_example` 或 `ready`。生产数据只允许 `ready`；schema 合法不等于可发布。
- `source_ref` 指向包内脚本 bundle + 原脚本路径；另存原 SWF SHA-256。原点/形状/矩阵的来源可只定位符号和帧，但不能以编造的脚本路径充当证据。
- 不知道的持续帧、判定区域和偏移填写 `null` 或保留空集合并标 `extracted_partial`。不得用 0、1、默认矩形或估计动画填满以通过发布校验。机制如何从源编进这些字段见 [SOURCE_FIRST.md](SOURCE_FIRST.md)。
- 模拟数值和 JSON 采用有限实数；未定义状态需独立标志。NaN 不得伪装成 0。

## 五类契约

| Schema | 核心字段 | 用途 |
|---|---|---|
| `asset.schema.json` | `id`、`source_swf`、`source_sha256`、`symbol_id`、`atlas_path`、`frames` | 图集和源符号关联，裁切/注册点/时长 |
| `fighter.schema.json` | `id`、`catalog_id`、`source_swf`、`source_sha256`、`forms` | 配置 ID 与原文件/形态/动作集映射 |
| `action.schema.json` | `id`、`fighter_id`、`source_ref`、`damage`、`hurt_time_ms`、`duration_ticks`、`events` | 招式参数及有序行为事件 |
| `replay.schema.json` | `baseline_sha256`、`execution_profile`、`initial_state`、`random`、`inputs` | 完整初始化、逻辑按键输入和随机序列 |
| `trace.schema.json` | `origin`、`replay_id`、`execution_profile`、`frames` | 玩家状态和事件的逐帧记录 |

### Asset 与 Fighter

一张 atlas 可服务多个符号；`frames[].rect_px` 为裁切区，`pivot_px` 为转换后注册点，`duration_ticks` 为显示时长。`source_frame` 始终是原 1-based 帧号。嵌套层级和矩阵在导入中间表示保留，不能通过导出一串平面 PNG 自动获得全部信息。

`forms[].source_root_frame` 映射 `WKframe`，`action_set_id` 引用编译后的动作集。初步示例尚未确认全部形态，故不标 `ready`。当某角色共用同一个 SWF，必须用形态映射，不能复制改版分拆文件。

战斗中间数据 `command_catalog` 用原版时间轴帧标签（`砍1`、`万解`）作为招式 ID，并保留 `doAllAction` 的谓词槽位（`nornalhit`、`bisha`）。尚未接线的标签和取消窗口列入 `gaps`，不得从目录里删掉。新角色只编译自己的 catalog，不另造英文招式名。站立/空中/防御匹配按源函数里 `if(pred) gotoAndPlay` 的先后：`dispatch_orders[context]` 是该函数中的 0-based 下标。`doAllAction` 的 helper（`DefineSprite_16`）放在站立/走；第一个把播放头带离这些帧的 `gotoAndPlay` 会摘掉 caller，因此站立上+招进 `招3`、上+I 进 `上必杀`，后面的 `magichit1`/`bisha` 不得再覆盖。`onDefence` 第一句是 `gotoAndPlay("防御2")` 钉住同一剪辑，后续 if 继续跑，防御中后写获胜。不得把整份 `doAllAction` 都做成后写覆盖，否则站立 `招3`/`上必杀`/`超必杀` 会变成死代码。`cancel_windows` 来自各动作 PlaceObject `enterFrame` 的同类条件 goto；运行时 `match_cancel` 按该 clip 内后写获胜。已由专用路径消费的窗口标 `handled_elsewhere`（防御2 的 skill1/招2/超必杀走 `guard` catalog，防住→防御2，防御2 自钉），不得再走通用取消。`action_exits` 收录全部无条件 `gotoAndStop`/`gotoAndPlay`，目标可以是 `站立`/`落`/`落2`/`击飞` 等，以及带 `land_cancel` 的自跳回环（鸣人 `螺旋手里剑1@902` 钉住直到 `touchFloor` → `超必杀2`）；循环钉住的 `(走,站立)`、`(防御2,站立)`、`(站立,站立)`、`(落,落)`、`(落2,落2)` 不接线。同一帧脚本里写在 goto 前的 `yup`/`htx`/`jhp`/`zl` 一并编进该 exit（鸣人 `超必杀2@942` 自跳 `击飞`）；运行时按 `beidax(true)` 落地进 `击落地`，不得在 GDScript 里按角色猜冲量。`hurt.launch_stop_frame` 是击飞标签上的无条件 `stop()`（鸣人 1035、一护 759），播放头停住后仍由 `beidax` 落地，不能把标签 `end_frame` 当成停帧。相邻标签若中间没有 `stop`/`goto`，编入 `timeline_fallthroughs`：鸣人 `砍技1` 播完必须进入 `砍技12` 炸开，接触 `gotoAndPlay` 只是提前引爆。一护 `砍技1` 没有 fallthrough，第 278 帧无条件回站立。`motion_windows` 除 `speed` 倍数外还编译 `moveLeft`/`moveRight`（`steer_speed_factor`）、`_x += speed * N * scale_X`、以及像素 `_x`/`_y`（`forward_pixels`/`vertical_pixels`）。嵌套剪辑里 `_name="*atm"` 的判定窗口带 `placed_name`（鸣人 `上必杀` 的 `fensheng`/`sbsatm`）。`clip_placements` 收录帧脚本把具名剪辑 `_x`（及同源 `_y`）写成对手容器坐标的赋值：`if(_parent._xscale > 0) clip._x = opponent._x - parent._x`，否则取反；运行时覆盖 PlaceObject 平移，不得按角色猜传送像素。`body_warps` 收录玩家容器闪现，不是具名剪辑 `place_at_opponent`，也不是走路。无条件 `_parent._x/_y = _root.game["p"+pn]._x/_y`（可带常量像素和同行 `jump = 1`）编成顶层 `x_pixels`/`y_pixels`/`set_jump`。两分支都写 `_parent._xscale` 再抄对手 X 的，编 `xscale_gt_0`/`xscale_lt_0`（`set_facing`、`x_pixels` 或 `x_bdmn_width`）；Y 上的 `bdmn._height[*N]` 编 `y_bdmn_height`。不得在 GDScript 里按角色猜闪现距离，也不得把其他形态 Sprite 的脚本编进当前切片。鸣人 `超必杀@832` 只抄 X，所以随后 `cbs1atm` 只在同一水平面能碰到 `bdmn`；跳到另一高度不抄 Y，不得放大框去够。`@884` 才抄 `_y - 40` 并 `jump = 1`。当前一护切片 `DefineSprite_638` 没有这类赋值；`DefineSprite_1672` 的 `招3@442` / `上必杀@555` 是另一形态。

战斗中间时间轴在抽取内层 `DefineSprite` 时保留根时间轴放置该符号的 `wrapper`
（通常名为 `mc`）矩阵。玩家逻辑坐标是外层容器的 `_x/_y`；渲染和 `bdmn` 必须
再乘这层矩阵，不能把注册点当作脚底。`jump_windows` 来自 `onJumping(step)`
剪辑寿命：step 1/4 递减 `js`，2/5 匀速上升，3/6 只在 `touch` 时落地，不得改写成
连续抛物线。`enterFrame` 从 `PlaceObject` 的下一根帧开始；新放置的剪辑不继承
`js`。

`hit_priority.instances` 必须由原版 `hitks` 与 1–5 后缀展开得到。一个 tick 同时存在多个 `*atm` 时按该表选中第一个命中，不能依赖 JSON、Godot 子节点或哈希表的遍历顺序。`impact_strength` 按原版 `bdxg()` 映射共享的 `XG_kan`、`XG_qdj`、`XG_qdjx`、`XG_mfdj`、`XG_mfdjx`、`XG_kanx` 命中特效；`zl > 10` 是破防标记，`beida()`/`fangyu()` 在进入普通受击链前只减一次 10，再用归一后的 1–6 选择效果。该展示属于通用受击链，不属于某一角色招式的硬编码。形态表 `attacks_by_form`、`hits_reset_frames`、`hit_fx`（含 `bdxg`/`bdfyxg`/`bdfyxg2` 与各 `XG_*` 的 `presentation_events`）、`combo_hud`（`p1hits.pn=2` / `p2hits.pn=1`，`连击` 从 DefineSprite_1833 第 10 帧起播，第 11 帧 `changeNum`，第 50 帧回 1）由源编译，运行时只解释这些字段。必杀 `bsd`/`cbsd`/`showFace`/`bsw`/`cbsw` 编入 `super_events` 与 `face_labels`；`ts_face`（sprite 1678）与 `blackMu`（sprite 1510）按 id 导入到 `godot/generated/main/`，运行时只 `goto` 编译帧。`blackMu` 帧 2 的黑底是源 `DefineShape` 535 的 `fillStyleType=0` 纯黑，不得另画全屏矩形冒充。落地顺序见 [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md)。

`XG_*` 剪辑目录（`godot/generated/effects/<元件名>/`）按 `main.swf` ExportAssets 的 sprite id 抽取，目录名即 `bdxg`/`bdfyxg`/`bdfyxg2` 表里的元件名，导入后必须能用 `timeline.json` 的 `sprite_id` 反查同一个元件。必杀火花 `XG_bs`（459）/`XG_cbs`（441）同样落在该目录。`bvn26-timeline-geometry-v1` 的 `frames[].events` 除 `action_bytecode` 外还收录 `start_sound`：`sound_id` 取该帧 `StartSoundTag`，`SOUNDINFO` 的 `envelope`（`left_level`/`right_level`，满值 32768）、`loop_count`、`in_point`、`out_point`、`sync_stop` 原样保留，被 `StartSound` 用到的 `DefineSound` 以 `type: "DefineSoundTag"` 进 `definitions`，`materialize_timeline_assets.py` 再把它的 mp3 落到同一目录并记入 `assets.json`。运行时只解释这些字段：播哪条声音、什么时候播、音量按 envelope 折算；不得按元件名手挑音效、手写时长或手调音量。`in_point`/`out_point` 的单位是 44.1 kHz 采样（与 `SOUNDENVELOPE` 的 `pos44` 同一套），不随 mp3 自身采样率变化：`XG_bs` 的 444.mp3 是 11025 Hz、1.202 s，`5100/51340` 即 0.116–1.164 s；按 mp3 采样率换算会溢出到 4.66 s。角色与援助时间轴上的 `start_sound` 走同一套抽取。`DefineShape` 的 `fillStyleType=0` 纯色填进 `solid_fills`（`blackMu` 帧 2 的 shape 535）；时间轴预览按 `shape_bounds_twips` 画该矩形。线性渐变（`fillStyleType=16`，横幅 shape 1516）尚未抽取。

BGM 不在 SWF 里。`bvn26-stage-music-v1`（`godot/generated/music/music.json`）把 `loadSound()` 的选曲判定编成有序 `selection.steps`：带 `random_below` 的步骤消耗一次 `Math.random()`，命中即停；带 `otherwise` 的末步不抽随机。`p2selt` 的目录项没有 `music` 时第一步整个不存在，因此那种组合只抽一次随机。`getFighterData` 是纯查表，`addFighterClone` 在注册时已把父项键拍平，`manifest.json` 的 `fighter_catalog` 也是拍平结果，不得在运行时按 `clone_of` 回溯继承曲目。`playback` 来自 `startGame()` 的 `start(0,999)` 与 `setVolume(80)`：`volume_percent` 按 Flash 的 0–100 振幅百分比折算成 dB，999 次重复按循环处理（一局打不到第 999 次）。`files[]` 记录源 `game/music/<曲名>` 与 sha256，只复制该 `p2selt`/`curStage` 组合可达的曲目，不整包搬 `game/music/`。

### Action 与事件

`damage`、`hurt_time_ms`、`push_x`、`lift_y`、`impact_level`、`hit_reaction` 是从原攻击参数映射来的数据，仍须和命中选择/受击逻辑一起使用。不能只把伤害表写入 Godot 就视为技能完成。

双方实体碰撞使用当前帧各自可见的 `bdmn`，不能用固定角色宽度替代。原版 `on_enterframe` 将本 tick 横向位移限制在 `[-30, 30]`，乘朝向得到前进压力，再叠加对手 `vecx / 2`；`heavy` 差决定双方分摊，静止重叠时注入 10 像素压力逐 tick 顶开。普通瞬步由 `doDashX` 独占移动期间跳过这套身体挤压。

带 `contact_cancel_to` 的招式位移以其 `contact_instance` 对对手当前 `bdmn` 检查。源脚本仍按“先检测、未命中才移动”的顺序执行；Web 端还对单 tick 位移做 swept AABB，防止 30 Hz 下转换后的矩形从一侧跨到另一侧。命中时停在首次交叉位置并切到源目标标签，启动接触框本身不得结算伤害。

`presentation_events` 保存源帧上的全局展示调用。目前 `screen_flash` 包含 `action`、`frame`、`color_rgb24` 和源路径/哈希；透明度、混合模式等全局播放器常量必须来自 `main.swf`，不能按招式臆造。鸣人 `砍技12` 第 292 帧的 `shine(1403539)` 使用主程序 `shinemc` 的 Overlay 混合和帧 2–9 alpha 序列。

`events` 中每项包含 `tick`、`order`、`op`、`args`。同 tick 按 `order` 排序；重名序号非法。事件操作采用白名单：

| op | args 约定 |
|---|---|
| `set_velocity` / `add_velocity` | `x`、`y`；使用模型坐标单位，禁止乘渲染 delta |
| `open_hitbox` / `close_hitbox` | `hitbox_id`；该 ID 必须在该动作/角色的判定定义中存在 |
| `play_sound` | `sound_id`；可选 `loop` |
| `spawn_effect` | `effect_id`、可选 `anchor`/`offset_x`/`offset_y` |
| `set_invulnerable` | `enabled` |
| `cancel_window` | `enabled`、`target_actions` |
| `change_action` | `action_id` |
| `set_pause` | `domain`、`enabled`；不同实体/时钟域独立 |
| `native_hook` | `handler_id`、`params`；只允许事先注册的 GDScript handler |

Schema 校验结构与操作名；数据编译器还必须校验操作参数、引用存在、事件范围、重复 order、hook 注册及所有玩法事件已迁移。`native_hook` 是游戏专用逻辑扩展点，不能是 AS2 字符串、任意文件执行或通用 Flash 解释器。

本包的鸣人 `k1` 示例只确认了数值，`duration_ticks` 和 hitbox 时序未知，因此是 `extracted_partial`。示例不会猜前摇/有效帧/后摇。

### Replay

输入是按 tick 记录的 `held`、`pressed`、`released` 三组逻辑按键，玩家固定 1/2，顺序值 `order` 用来保留同帧事件顺序。同 tick 的 order 在两位玩家之间共用且不重复；开始记录时两位玩家的逻辑按键均为释放状态。按键变化后写入一条事件，未变化的 held 状态延续至后续 tick。若原版只采样每 tick 的最终按键状态，则由 ExecutionProfile 说明这一点，不能借格式中的 order 改变原输入规则。暂停/聚焦等生命周期事件不应悄悄折叠为玩家输入；实现时在 initial/profile 与扩展事件轨迹中记录。

随机数据使用 `recorded_tape` 或 `seeded`。原版对照优先使用真实捕获的 tape，只有 engine 内重放可先用种子。使用种子不能自动复制原版随机算法。初始状态至少包含模式、地图、双方配置/形态、位置、朝向、血量/气量和 AI 开关；不能用环境默认值补全。

`purpose = synthetic_format_example` 的示例仅验证格式，无 golden 结果。真实 oracle 必须存放于后续 `evidence/`，注明来源环境与捕获过程。

### Trace

`origin` 为 `original_player`、`reference_emulator`、`godot` 或 `synthetic`。每帧包含 tick、阶段、双方位置/状态/资源值和有序事件。原版日志字段不可用时标注缺项，不假装已观测内部状态。差异比较器输出首次不同 tick/实体/字段与两侧值；不要只给全局相似度。

## 版本和接口迁移

每份文件携带 `schema_version=1`。新增字段必须更新 schema、格式示例与实现消费者；改变单位、tick 起点、命中优先级或暂停语义需要升级 ExecutionProfile。原始输入文件不因接口升级被覆盖。

Schema 只是接口起点。M1/M2 若发现原版需要额外事件或状态，可扩展契约并补例；不得为了维持现有示例格式而丢掉真实行为。测试格式使用 `python3 tools/validate_contracts.py`，需要 `requirements-dev.txt` 中的开发依赖。

## 援助开发切片字段

`helper-model` 的 `presentation_events` 编译根帧 effect/shine/bsd/bsw 调用，
`helper` 保留 bsd/bsw 的 fz 实参，省略值不得改为 true。`clip_load_events` 记录
load 帧、原 character_id/depth 与 aim_opponent_x；魂无该事件。`hide_frames`
不再从 fzccXg 推断，根末帧后按源回到帧 1。角色 `summon_events.set_bs` 来自
doZhaoHuan 的 bs 赋值；不是运行时按角色补的默认值。以上仍为带源路径的中间数据。
