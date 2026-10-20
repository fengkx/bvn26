# 数据契约 v1

本文件定义离线工具、Godot 运行时和对照工具之间的拟定接口。`spec/schemas/` 为可校验 JSON Schema；实际图集、动作时序和 Godot 资源尚未生成。已存在的 `scripts/*.json` 是独立的原脚本索引格式，不可直接当作下列运行时数据。

## 开发输入录制契约

2026-09-22 新增独立的 `match-input.schema.json`，用于已实现的逻辑输入录制与回放。
它不替换下述五类迁移契约中的 `replay.schema.json`，也不代表整局确定性回放。
完整字段、事件顺序、运行时语义校验及使用方式见
[输入解耦实现说明](input-decoupling/IMPLEMENTATION.md)。
`match-input.synthetic.json` 仅为结构示例；其 `complete` 表示存在终止记录，不表示原版验收完成。

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

战斗中间数据 `command_catalog` 用原版时间轴帧标签（`砍1`、`万解`）作为招式 ID，并保留 `doAllAction` 的谓词槽位（`nornalhit`、`bisha`）。尚未接线的标签和取消窗口列入 `gaps`，不得从目录里删掉。新角色只编译自己的 catalog，不另造英文招式名。站立/空中/防御匹配按源函数里 `if(pred) gotoAndPlay` 的先后：`dispatch_orders[context]` 是该函数中的 0-based 下标。`doAllAction` 的 helper（`DefineSprite_16`）放在站立/走；第一个把播放头带离这些帧的 `gotoAndPlay` 会摘掉 caller，因此站立上+招进 `招3`、上+I 进 `上必杀`，后面的 `magichit1`/`bisha` 不得再覆盖。`onDefence` 第一句是 `gotoAndPlay("防御2")` 钉住同一剪辑，后续 if 继续跑，防御中后写获胜。不得把整份 `doAllAction` 都做成后写覆盖，否则站立 `招3`/`上必杀`/`超必杀` 会变成死代码。`cancel_windows` 来自各动作 PlaceObject `enterFrame` 的同类条件 goto；运行时 `match_cancel` 按该 clip 内后写获胜。已由专用路径消费的窗口标 `handled_elsewhere`（防御2 的 skill1/招2/超必杀走 `guard` catalog，防住→防御2，防御2 自钉），不得再走通用取消。`action_exits` 收录全部无条件 `gotoAndStop`/`gotoAndPlay`，目标可以是 `站立`/`落`/`落2`/`击飞` 等，以及带 `land_cancel` 的自跳回环（鸣人 `螺旋手里剑1@902` 钉住直到 `touchFloor` → `超必杀2`）；循环钉住的 `(走,站立)`、`(防御2,站立)`、`(站立,站立)`、`(落,落)`、`(落2,落2)` 不接线。同一帧脚本里写在 goto 前的 `yup`/`htx`/`jhp`/`zl` 一并编进该 exit（鸣人 `超必杀2@942` 自跳 `击飞`）；运行时按 `beidax(true)` 落地进 `击落地`，不得在 GDScript 里按角色猜冲量。`hurt.launch_stop_frame` 是击飞标签上的无条件 `stop()`（鸣人 1035、一护 759），播放头停住后仍由 `beidax` 落地，不能把标签 `end_frame` 当成停帧。相邻标签若中间没有 `stop`/`goto`，编入 `timeline_fallthroughs`：鸣人 `砍技1` 播完必须进入 `砍技12` 炸开，接触 `gotoAndPlay` 只是提前引爆。一护 `砍技1` 没有 fallthrough，第 278 帧无条件回站立。`motion_windows` 除 `speed` 倍数外还编译 `moveLeft`/`moveRight`（`steer_speed_factor`）、`_x += speed * N * scale_X`、以及像素 `_x`/`_y`（`forward_pixels`/`vertical_pixels`）。嵌套剪辑里 `_name="*atm"` 的判定窗口带 `placed_name`（鸣人 `上必杀` 的 `fensheng`/`sbsatm`）。`clip_placements` 收录帧脚本把具名剪辑 `_x`（及同源 `_y`）写成对手容器坐标的赋值：`if(_parent._xscale > 0) clip._x = opponent._x - parent._x`，否则取反；运行时覆盖 PlaceObject 平移，不得按角色猜传送像素。`clip_placements` 的可选布尔字段 `divide_parent_scale_x` / `divide_parent_scale_y` 仅由源 `onLoad` 中 `/ (_parent._xscale / 100)` / `/ (_parent._yscale / 100)` 生成；运行时使用导入的 `mc` 父变换缩放换算局部坐标，缺省不除。`front_only` 保留源背向目标时的提前返回。攻击剪辑 `rename_frames` 同时保留改名进入和退出 `*atm` 的事件，不能把退出名字后的旧攻击框留在受击查询中。`body_warps` 收录玩家容器闪现，不是具名剪辑 `place_at_opponent`，也不是走路。无条件 `_parent._x/_y = _root.game["p"+pn]._x/_y`（可带常量像素和同行 `jump = 1`）编成顶层 `x_pixels`/`y_pixels`/`set_jump`。两分支都写 `_parent._xscale` 再抄对手 X 的，编 `xscale_gt_0`/`xscale_lt_0`（`set_xscale`、`x_pixels` 或 `x_bdmn_width`）；Y 上的 `bdmn._height[*N]` 编 `y_bdmn_height`。不得在 GDScript 里按角色猜闪现距离，也不得把其他形态 Sprite 的脚本编进当前切片。鸣人 `超必杀@832` 只抄 X，所以随后 `cbs1atm` 只在同一水平面能碰到 `bdmn`；跳到另一高度不抄 Y，不得放大框去够。`@884` 才抄 `_y - 40` 并 `jump = 1`。当前一护切片 `DefineSprite_638` 没有这类赋值；`DefineSprite_1672` 的 `招3@442` / `上必杀@555` 是另一形态。

Facing-warp branches may additionally carry `set_scale_x` when the source explicitly assigns the wrapper `scale_X`. This logical facing is distinct from display `set_xscale`: runtime applies display scale, X, explicit logical facing, then Y in source order. Omitting `set_scale_x` preserves the existing logical facing. Offline controller compilation may resolve stable local wrapper aliases to mapped scalar fields; `opponent_x` / `opponent_y` writes use the same Flash coordinate store as own X/Y and retain the authored callback lifetime and game-running guard.

战斗中间时间轴在抽取内层 `DefineSprite` 时保留根时间轴放置该符号的 `wrapper`
（通常名为 `mc`）矩阵。玩家逻辑坐标是外层容器的 `_x/_y`；渲染和 `bdmn` 必须
再乘这层矩阵，不能把注册点当作脚底。`jump_windows` 来自 `onJumping(step)`
剪辑寿命：step 1/4 递减 `js`，2/5 匀速上升，3/6 只在 `touch` 时落地，不得改写成
连续抛物线。`enterFrame` 从 `PlaceObject` 的下一根帧开始；新放置的剪辑不继承
`js`。

`hit_priority.instances` 必须由原版 `hitks` 与 1–5 后缀展开得到。该表保存源数组的插入顺序；原生 Flash 的 `for…in` 对该稠密数组反向枚举，因此一个 tick 同时存在多个 `*atm` 时运行时反向扫描该表，选中第一个命中，不能依赖 JSON、Godot 子节点或哈希表的遍历顺序。鼬近距离上＋U及最小枚举探针见 `evidence/characters/itachi/README.md`。`impact_strength` 按原版 `bdxg()` 映射共享的 `XG_kan`、`XG_qdj`、`XG_qdjx`、`XG_mfdj`、`XG_mfdjx`、`XG_kanx` 命中特效；`zl > 10` 是破防标记，`beida()`/`fangyu()` 在进入普通受击链前只减一次 10，再用归一后的 1–6 选择效果。该展示属于通用受击链，不属于某一角色招式的硬编码。形态表 `attacks_by_form`、`hits_reset_frames`、`hit_fx`（含 `bdxg`/`bdfyxg`/`bdfyxg2` 与各 `XG_*` 的 `presentation_events`）、`combo_hud`（`p1hits.pn=2` / `p2hits.pn=1`，`连击` 从 DefineSprite_1833 第 10 帧起播，第 11 帧 `changeNum`，第 50 帧回 1）由源编译，运行时只解释这些字段。必杀 `bsd`/`cbsd`/`showFace`/`bsw`/`cbsw` 编入 `super_events` 与 `face_labels`；`ts_face`（sprite 1678）与 `blackMu`（sprite 1510）按 id 导入到 `godot/generated/main/`，运行时只 `goto` 编译帧。`blackMu` 帧 2 的黑底是源 `DefineShape` 535 的 `fillStyleType=0` 纯黑，不得另画全屏矩形冒充。落地顺序见 [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md)。

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


`action_events` 保留援助根 DoAction 中无条件的 `动作` 整数赋值，包含
`frame`、`value`、`source_path`、`source_sha256`。新实例未赋值时保持 undefined；
`removeFZ` 清零，再召唤不重置。CPU 读取对手援助的该字段，不能用
`attacking` 或可见性替代。跨对象帧脚本调度仍待原版对照。

### AI source context (base slice)

`godot/generated/fighters/*/ai.json` 使用 `bvn26-ai-context-v1`，由
`tools/importer/compile_ai_context.py` 编译。`frame_writes` 保留顶层常量赋值的
源帧、字段、值及原路径/行号；`function_writes.onBeHit0` 保留该无条件函数的
写入顺序。`undefined_declarations` 只在新实例创建时初始化缺失值，重新进入
帧 1 不得把已有 `sw` 等字段清空；带初值的声明仍按每次帧脚本执行。

`AiSourceState` 当前接收这些写入及运行时受击入口；它还不是全部 BODY 字段的
完整镜像。条件性写入、定时器和物理回调仍需接入。跳转产生的目标帧写入要按
顺序排队，不能只保留最终动作；帧脚本执行完后还需处理它安排的新目标。

`sensing` 保留 AImain 的放置、固定激活帧 2、子感知框矩阵、所需定义和缺失引用。
`AiSenses` 用同一角色时间轴的矩阵/边界工具计算这些框，目标为当前 `bdmn`。
缺失 `absmian` 返回缺失值，不能创建默认框。原版实际局部框边界与当前浮点计算
有未解决的精度差异，见 `evidence/ai/geometry-comparison.json`；当前模型保持
`source_compiled_partial`，不能据此宣布几何或 AI 一比一验收通过。

`load_writes` 与 `frame_writes` 是不同调度事件。写入项包含字面 `value`，或
`read_field`（当前用于 `speed = spd`），不能提前折叠为常数。
`base_power_fields` 只表示当前基础形态的 `gjl1.*zl`，不能用于其他形态。

生成的 `ai_controller/controller.json` 保留原始 hook 路径、放置帧、深度和
`member_frames`。Godot 读取 JSON 后须把帧号转换为整数；数组的 Variant 类型比较
不能直接用于浮点 JSON 帧号与整数播放头的身份匹配。回调宿主负责提供执行顺序，
每次 goto 后立即同步显示列表身份，目标帧状态写入仍由帧脚本阶段消费。

`ai_controller/body.gd` 是离线编译的原生函数，`body.json` 记录其源哈希、函数和
两个具名 timeout 回调。外部颜色、特效、舞台攻击和定时调度由宿主接入；不能把
这些调用空实现后宣称完整行为一致。当前 BODY 比较使用明确的外部调用替身，
验证返回值、状态写入、调用顺序及 timeout 回调内容，不证明实际到期相位。

`ai_hit_state.gd` 从 Sprite 2 的 `beida/fangyu` 编译，接收已判定命中的原始
`pw/zl/yup/hitx/hdtime/htype` 包，写入 BODY 状态并返回目标标签意图。
它不执行碰撞、伤害、特效或目标帧脚本。`hdtime` 换算后的 `tdtime` 保留小数，
普通防御保留既有 `time`；这些不能用现有运行时的整帧硬直计数反填。

### AI receiver placement metadata

`ai_controller/controller.json.receiver_hooks` records the base body's Sprite 2
`beida` / `fangyu` enterFrame placements, separately from generated Sprite 16
methods. Each entry retains `path`, `receiver`, `depth`, `placement_frame` and
`member_frames`; the host merges both lists before depth ordering and applies
the same placement-tick and removal identity rules. The callback determines
normal versus guard reception. This does not establish whole-battle callback
order or replace the pending target-frame damage timing validation.

### Projectile initial motion

A projectile record may carry `initial_speed`, `initial_played` and
`initial_motion_source` when its nested frame-1 script explicitly initializes
movspeed/played and stops the clip. `initial_speed` is local pixels per callback,
independent of fighter movement speed. `stop_frames` includes that frame even
when initialization shares the same script. These fields do not establish the
first callback phase or complete projectile collision query semantics.

`projectiles[].collision_queries` is an ordered list of `{receiver, target}`
extracted from source hitTest calls. `self` means the projectile clip; an explicit
receiver such as `hitmc` must not be replaced by the whole projectile. Target
lookup observes compiled rename_frames. Missing child bounds remain empty;
unqualified Flash scope resolution is a separate outstanding validation.

`ai_controller/controller.json.projectile_hooks` includes source path, depth,
placement frame, member frames and the compiled projectile record. These hooks
share lifetime tracking with controller/receiver hooks. Their playheads advance
in a separate pre-callback phase; repeated synchronization is not another
playhead advance. A new placement resets offset and frame-1 initialization.

`projectiles[].child_stop_frames` optionally maps immediate child sprite IDs
to source stop frames, compiled only when those child frame scripts consist
solely of `stop()`. Only child IDs explicitly listed in this table opt into
placement clocks; legacy compiled assets retain their existing playback.
Instance records retain `child_clocks`, keyed by depth with
character/placement-frame identity and elapsed age. A new placement resets that
age even after a delayed parent goto; MOVE retains it. These records and the
compiled stop table share the existing checkpointed local-playhead state.
See [Deidara's repeated projectile evidence](../evidence/characters/didala/README.md).

`ai.json.frame_calls` retains top-level super/presentation calls with source
`path`, `line` and `frame`. The AI host merges calls and `frame_writes` by line
number, preserving assignment/call interleaving. Separate bsd and showFace
records must remain separate; the existing combined player super_event is not
used to reconstruct this order. Other source statements remain uncompiled.

`frame_calls` also admits `timeline_goto` (literal label and play flag),
`timeline_play` and `timeline_stop`. Goto applies display-list lifetime changes
immediately and appends its target to the current frame-action queue. Draining
the queue must preserve source writes and commands appended during execution.
Conditional commands and uncompiled BODY calls remain outside this extraction.

`frame_calls` additionally admits `frame_hit_test` (`field_name`, `instance`),
which saves the named body hit-test result when that source DoAction executes,
and `opponent_visibility` (`value`), which writes the opponent wrapper's visible
property. A later `conditional_frame` can read the saved boolean alongside
opponent HP/action; it must not recompute the collision at branch time.
Controller scalar writes expose `opponent_visible` through the same adapter as
opponent X/Y. Visibility is included in native checkpoint state.

### AI effect wrapper linkage

`generated/main/ai_visual_services.json` retains source wrapper names, clip
linkage names, X/Y offsets, wrapper hashes and inspected SWF hashes. An empty
`exported_by` means no retained SWF exports the requested clip. The adapter
creates no replacement for that missing linkage. Nonempty linkage entries
require an implemented native effect adapter; they must not silently vanish.

`effects/<clip>/effect.json` may supply `bvn26-simple-effect-v1` root
`presentation_events`, with source path/hash and exact frame. The bounded
importer currently accepts only one explicit unloadMovie event and no nested
sprite timeline. The runtime uses that event on its source frame; a clip name
mismatch is invalid. This does not certify global effect scheduling.

`hit_fx.color_effects` 按 bdxg 的强度 case 编译：`set_colors` 保存有序
Color.setTransform 对象数组；`set_color_matrix` 保存 20 个 ColorMatrixFilter
系数。未提供的通道仍是未提供，不能在数据层补猜测默认值。源路径随操作
保留。CPU 已接入交替与复位；滤镜按子绘制对象应用，整容器合成及像素一致性尚未验收。

### KO native controller ABI

`main/ko/controller.gd` contains source-compiled frame methods and nextfight.
`controller.json.events` maps original script path/hash to method. Its adapter
must resolve read/write targets against the currently executing clip and root
state, apply goto/play/stop with original instance lifetime, dispatch root
services in order, and return interval IDs. `compiled_not_connected` explicitly
excludes runtime/round-completion acceptance. Unknown compiler syntax fails.

KO event records additionally carry `sprite_id`, `frame`, `kind`; enterFrame
records carry `child_id` and `depth` and belong to the indicated parent
placement. The scheduler retains stopped children and distinguishes fresh
placement from retained membership. Its root service boundary is still
separate from the production match adapter.

KO `root_initializers` are match-entry values compiled from Sprite 1991
frame 1: win counters and rounds start at 1. A counter of 3 means two actual
wins. Do not reset these counters at nextfight. Intro HUD data now contains
all ten `hud_frames`, `hud_labels`, `hud_stop_frames`, and `hud_frame_count`;
frame 10 naturally wraps to frame 1, which executes stop.

Health HUD `win_frames` preserves Sprite 1785 frame display lists, and
`win_source_sprite` identifies that source timeline. Marker shape bounds are
in `layers`; their matrices compose beneath each bar's win placement. The
selected frame equals the one-based source win counter, not actual wins.
Health-only reset must preserve it across rounds.

Combat `death.ko_writes` stores ordered state assignments before KOplay.
`ko_number_binding` stores the source player-name comparison and both numeric
results; pn identifies the opponent. Publish these writes before ko_requested
and before the optional death goto, so AI reads and KO services see the source
state. This event alone does not implement the KO round lifecycle.

The fixed Vs Com main adapter now binds KO controller services. `time_defaults`
and `clear_intervals` are extracted from main scripts; defaults do not imply
a complete countdown implementation. Intro event `clear_intervals` emits
named clearing requests, including nextfight on Ready frame 2. KO remains
`source_compiled_partial`, with full timing/scene parity unverified.

### AI frame color operations

`ai.json.frame_calls` also includes `color_reset` for a top-level `resColor()`
and `color_write` with `field_name` (`_cgap` or `_csn`) and integer `value`.
Both carry frame/path/line and share the ordered frame-event stream. The CPU
host applies reset through the existing source color adapter, then maps the
explicit writes to its gap/index. In BODY frame 1 this leaves both at zero;
resColor alone still preserves index and sets gap to one. These operations
are not limited to a new actor and must execute on repeated frame-1 gotos.

### AI first-load scalar state

`ai.json.initialization_state` projects the scalar prefix of BODY's
`if(!inited)` block: guard name, source frame/path/line and ordered writes
`inited=true`, `_lastX=0`. AiSourceState applies it on first frame-state
initialization, preserves it across frame-1 revisits, and clears it only on
configure for a new instance. The compiler rejects unconditional writes to
these same fields in frame 1, so projecting this prefix after independent
frame writes cannot overwrite a conflicting source assignment. This is a
state projection, not an execution trace of the entire initialization block;
pn binding, doWanKai, updateDirect, timer creation and their scheduling are
still separate host responsibilities and are not validated by this field.

### Recorded intro interval delivery

`BattleIntro.begin(players, true)` enables explicit recorded polling. Its
visual tick still advances clips but does not accumulate elapsed polling
time. `deliver_recorded_poll(sequence, time_ms)` invokes the existing source
kaichang branch once; sequence must increase and timestamps must not decrease.
Malformed order latches `poll_replay_error` until a new begin. Inactive or
cleared polling rejects delivery without changing state. The caller owns
placement of these events relative to frame advance and DoAction dispatch;
this API does not infer that phase or inject expected fighter state. Default
begin remains the provisional delta-driven polling mode.

Main `_advance_fight(recorded_intro_polls=[])` accepts explicitly phased
intro callbacks. Each record carries `phase="after_actor_advance"`, sequence
and time_ms. Delivery occurs after fighter/stage timeline advancement, before
intro state observation and actor callbacks/target frame scripts. No event
is fabricated from timestamps. BattleIntro must already be in recorded mode.
This is one supported replay phase, not a claim that every original interval
callback uses it. Default calls with no records retain existing behavior.

BattleIntro.begin accepts a third `loaded` boolean (default true for the
materialized native scene). While fighters_loaded is false, kaichang returns
before reading kcplayed/frame conditions, matching the original load gate.
Recorded delivery still consumes the callback's sequence/time when gated.

### Intro frame action phase

BattleIntro.tick's optional third argument defers clip frame scripts. Gotos
still change the display frame, but their frame events are retained in an
ordered queue until run_frame_actions. Main uses this mode and drains the
queue after actor callbacks/collision processing, before fighter target frame
scripts; HUD placement is refreshed after draining. Thus Ready frame 127
does not clear root pause before BODY callbacks on that same tick. Standalone
intro clients retain immediate mode by default. Whole-root scheduling outside
this validated intro segment remains provisional.

Main's optional recorded event array also accepts kind=ai_random at the
after_actor_advance phase. It invokes the configured recorded AiRandomClock;
SourceRandom verifies the next site/value sequence. Intro polls and random
events share the caller's ordered array and are not separately reordered by
the runtime. Recorded random registration is required. The continuous probe's
optional combat mode builds this order from event sequence numbers, preserves
global draw indices in its report, seeds the last pre-checkpoint sample once,
and refuses reference segments with held input it does not yet replay.

`ai.json.main_floor_contact` compiles BODY's exact `_y == floorY` branch: two
ordered field writes and source function hash/path. The player body-pressure
adapter applies these writes at its end only at exact main-floor Y, after
the existing dash return and subject to root pause. This is not a replacement
for the full player BODY: platform, jump and near-floor branches still need
source-state integration and must not be inferred from this field.

### Hurt voice source metadata

`godot/generated/fighters/*/hurt_voice.json` is produced by `tools/importer/compile_hurt_voice.py`. It retains the accepted shared function hash, random consumer sites, cooldowns, damage probability thresholds, sound linkage names, and the hashes of all scanned SWFs proving those linkages absent. A newly present linkage fails compilation until its sound is materialized. `AiSourceState` now compiles `_lastvoice` and `_dievoicen` from literal frame writes, including frame-1 revisits. The native adapter checks probability before cooldown and never consumes randomness in the death branch. `FighterRuntime.source_clock` supplies each explicit source clock read; live reads use Godot monotonic uptime. Recorded hurtVoice reads now use their captured sites and millisecond values. Other timer APIs and complete world replay remain unverified.

### Player BODY compilation

`compile_ai_body.py --player` preserves `if(!_parent.useAI)` and compiles `kis(换/冲/上/下)` to the adapter's `source_key(key)` call. Keys retain source action names; the host must resolve them through the configured original key binding. The emitted metadata adds `input_mode: source_player_branches_preserved`. The default CPU specialization and generated code remain unchanged. Player output is not runtime-integrated until its adapter, callbacks, and placement lifetimes are connected.

Player BODY metadata additionally carries `hurt_hooks`: source ClipAction path/hash, depth, placement frame, exact display-list member frames, and the source flying argument. These hooks only accept a single `_parent.beidax()` or `_parent.beidax(true)` statement. `source_body_callbacks.gd` requires the host to observe each display-list change (including goto), then dispatch once in the clip enterFrame phase. Source frames alone cannot identify a same-tick remove/re-place; the host must deliver both observations. Main integration remains pending.

Player integration uses `FighterRuntime.source_frame_changed(frame)` from source frame queue operations. `PlayerBodyDriver.begin_tick` runs before actor timeline advancement. The shared source controller host dispatches the player predicates, action controllers, receiver hooks and BODY callbacks, with `useAI=false` and exact source key names mapped to configured session input fields. The production player uses generated `minren/player_controller`; `minren/player_body` remains an earlier standalone compilation artifact. Driver shutdown disconnects signals, clears callbacks/timeouts and removes the actor BODY binding. The CPU uses the same BODY binding so source-frame hit settlement can call `updateDirect(true)`; guard settlement retains its argumentless call.

`source_frame_script_boundary(frame, entering)` reports the source script identity separately from the current playhead: a goto may already have changed the latter when the caller's exit event is emitted. Listeners used for diagnostics must not mutate simulation state. The signal encloses compiled scalar/call events and hit settlement, before the next queued target executes; it is not a whole-world end-of-tick event.

### Ordered frame batches and boundary diagnostics

`run_frame_actions(false)` executes the actor's already queued frame scripts without draining newly queued goto targets. Main processes every actor's initial batch, then Ready frame actions, then target batches until empty. Standalone callers retain immediate draining by default. Player source BODY mode now consumes the same ordered scalar/frame-call stream as CPU mode, including timeline and color operations. Top-level constant `ql +=/-= value` becomes an `energy_delta` frame call with source line/path; its direct scalar update happens within the observed source frame boundary and suppresses the old post-frame energy event.

The analysis-only builder's `--body-boundaries` records all retained base DoAction boundaries for both fighters. Replay mode `combat-boundaries` checks global boundary order and values, retaining root snapshot differences as diagnostics. It does not certify whole-world sampling phases, timer alignment, geometry, or complete battle parity. Missing/extra boundary events fail; native frame filtering uses the full retained DoAction inventory, not only reference-observed frames.

### Explicit getTimer reads

The probe wraps only `hurtVoice` getTimer calls and preserves the original return value in `clock` events. Each event carries a monotonically increasing capture index, a `bundle#path#hurtVoice:getTimer:N` consumer site, and integer milliseconds. `clock-tape.json` retains original event sequence/time as provenance. A replay checkpoint may omit an earlier prefix but retains original indices in consumed records. SourceClock rejects malformed, fractional, negative, backwards, missing and out-of-order reads; failures latch rather than advancing past mismatches. The supported captured interval excludes getTimer wraparound.

HurtVoice's four lexical sites map to death_check, death_write, hurt_check and hurt_write. The adapter reads only the sites reached by the original branch and reads again when writing a timestamp; it does not reuse a frame timestamp. The shared main clock supplies both actors. Fast deterministic replay uses only recorded values; live mode uses one monotonic host-clock read per source call. Existing captures without clock records cannot validate a reached clock branch and now fail explicitly instead of falling back to wall time.

### Shared source callback scheduling

`SourceCallbackRegistry` supplies monotonic registration identities across the fixed slice. Controller membership retention preserves registration; removal invalidates it; recreation registers a new instance for a later display dispatch. `AiCpuDriver.prepare_display_tick` must precede source timeline advancement so creation receives the correct tick. The source initial frame batch is captured before enterFrame callbacks; callback-generated targets drain afterward. The execution profile now records the nested registration probe, with dynamic helper/player coverage still pending. Source literal `hits` writes reset the native hit counter during source-frame execution. Reference captures now identify `body_kis_alias_with_per_read_trace`; collectors validate each read against event-ordered input state. See [evidence](../evidence/ai/callback-registry-and-input.md).

### Player controller and binary source trace extensions

Controller metadata identifies `input_mode` as `player` or `cpu`. Player generation retains the original `!useAI` input branch rather than stripping it. Projectile `initial_speed_field` and `initial_speed_factor` describe an exact source placement-load assignment; the host evaluates it once per new instance and stores `initial_speed` in that instance's copied model. `initial_motion_source` retains the load script path/hash.

Actor pending-frame entries carry `{frame, order}`. Main supplies a shared monotonic order counter for the fixed Vs Com actors. Existing initial batches retain their phase; newly queued targets drain one at a time by the smallest head order. Standalone actors and the legacy non-CPU path retain their prior draining behavior.

Analysis trace numbers may use `f:sign:exponent:high:low`: value = sign × (high × 2^26 + low) × 2^(exponent−52). Finite nonzero values have 2^26 ≤ high < 2^27 and 0 ≤ low < 2^26; zero has exponent/high/low all zero. Exponent is in [−1074,1023]. Legacy decimals remain accepted as captured, without inferred missing bits. The encoder covers random values, AI samples, HP/QL boundaries and state geometry, not every diagnostic field. See [source and validation evidence](../evidence/ai/player-controller-and-binary-trace.md).

### Source hit-effect random offsets

`presentation_events` may contain `random_offset` with `axis`, `positive_factor`, `negative_factor`, two ordered `random_sites`, and `source_path`. The runtime subtracts the two separately sampled terms and updates parent coordinates; it must not merge, reorder, or synthesize draws. Event identity is the compiled list index, not `(frame, op)`, because a source frame may contain multiple operations of the same kind.

Main defers attached effects' initial frame work until after the caller. Existing effect timelines join SourceCallbackRegistry at attachment and interleave with fighter callbacks by registration order; the former universal early-effect phase is superseded. Full world ordering remains under validation. Source receiver calls use `attack_contact(defender, true)` to bypass legacy consumed-hit and stashed-contact caches while retaining current source hit gates and lookup order. Other resolver paths keep their existing behavior. See [validation limits](../evidence/ai/effect-random-and-repeat-contact.md).

### Root-observer comparison phase

The optional `_advance_fight(recorded_events, root_observer)` callback runs after initial frame batches but before deferred target scripts. Production callers omit it. The replay observer reads frame/state/geometry and returns true only at its selected capture cutoff. Combat mode verifies that this cutoff equals the unique original `done` root event, which immediately calls `fscommand(quit)` in the analysis source. The comparator retains all expected events and additionally fails unconsumed boundary/random/clock tapes and mismatched root frame/state fields. See [interleaving and observer evidence](../evidence/ai/effect-registry-and-root-observer.md).

### Deferred projectile names

Source projectile instances retain a live name separately from the authored rendering identity. Compiled `rename_frames` enqueue `source_child_frame_requested(operation)` when reached; Main assigns the same global sequence as actor target frames and drains both queues in order. Names change when the queued script executes, not on goto. Current source-name lookup is shared by attack-contact and projectile-collision queries. Removed/generation-mismatched operations cannot mutate replacements; driver teardown disconnects and clears the queue/name bindings. A missing queue connection fails explicitly on a reached rename. See [source and validation](../evidence/ai/projectile-deferred-rename.md).

### 分析采集的异步退出尾部

`collect_ai_reference.py` 默认仍要求唯一 done 及同帧尾部。显式
`--retain-post-done-frames` 允许在首个 done 后保留异步退出事件，输出至
`post-done-events.jsonl`，不纳入 `events.jsonl` 的比较窗口。摘要记录
`termination_policy`；序号和时间连续性、Ready 唯一性、首个 done 请求帧、
尾部显示/战斗帧一致性及同帧重复 done 仍受检查。此为分析产物约定，
不改变生产 Trace Schema；案例见 [r15](../evidence/ai/match-flow-r15.md)。

### 全局 HUD gameplay 规则

`godot/generated/main/health/rules.json` 由 `tools/importer/build_health_rules.py`
严格匹配 main 的 Sprite 1814 帧 1 gameplay 前缀生成，保留源路径、哈希、原文、
百分比比例、任一死亡时返回条件，以及按玩家槽位排序的阈值/气量增量。
`SourceHealthRules` 解释这些字段；`HealthHud` 继续只处理显示。此模型仅覆盖
该前缀，不能据此声称整个 HUD 控制器或视觉已经编译完成。


### KO instance scheduling and round continuity

The shared scheduler now interleaves each KO root/child instance with actor BODY and initial frame scripts. Round reset preserves source energy/hits/pause, repeated same-frame goto does not repeat its script, and source hit-energy additions are not prematurely capped. r13/r14/r15 match all currently compared fighter fields; r15 consumes 4158 boundaries, 1202 random calls and 19 clock reads across both rounds and battle teardown. Twelve native checks pass. Countdown/timeover, exact geometry, boot, additional characters and presentation/Web parity remain pending. See [evidence](../evidence/ai/ko-instance-scheduling.md).

### 援助与受击回调时序补充（2026-09-09）

`bvn26-helper-model-v1.nested_stops` 保存 `sprite_id`、终端 `frame` 与源路径/哈希；
当前消费范围是从第 1 帧顺序播放至单个无条件 `stop()` 的援助子剪辑，不代表通用
AS2 执行器。没有 stop 的剪辑保留原循环行为。

战斗模型 `hurt.callback_start_frame` 是非击飞 `beidax()` 放置后的第一根回调帧，
同时保存 `callback_source_path` / `callback_source_sha256`。旧轮询受击计时从此帧
开始，不从 `stop_frame` 开始；源控制器仍按原回调注册表运行。

### Independently advancing renamed attack clips

Controller `projectile_hooks` may also describe an attack clip with no movement
callback. These use `frame_only: true`, the source `frame_count`, `rename_frames`,
`stop_frames` and optional compiled `frame_events` (currently `screen_flash`).
They share the existing placement-generation lifetime and child playback registry.
Natural frame events run at the child's registration; callback-generated goto
scripts remain deferred. Receiver queries use the current source instance name
and current child frame bounds, including an empty terminal frame. Unknown frame
scripts fail compilation instead of being silently treated as a linear clip.
