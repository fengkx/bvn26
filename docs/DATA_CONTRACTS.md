# 数据契约 v1

本文件定义离线工具、Godot 运行时和对照工具之间的拟定接口。`spec/schemas/` 为可校验 JSON Schema；实际图集、动作时序和 Godot 资源尚未生成。已存在的 `scripts/*.json` 是独立的原脚本索引格式，不可直接当作下列运行时数据。

## 统一约定

- JSON 使用 UTF-8。游戏内部 ID 稳定，文件名保留源大小写；跨文件引用不能依赖显示名称自动拼接。
- 原 SWF 帧号从 1 开始；动作 `tick` 和重放 `tick` 从 0 开始。单位必须体现在字段名中。
- `status` 为 `extracted_partial`、`synthetic_example` 或 `ready`。生产数据只允许 `ready`；schema 合法不等于可发布。
- `source_ref` 指向包内脚本 bundle + 原脚本路径；另存原 SWF SHA-256。原点/形状/矩阵的来源可只定位符号和帧，但不能以编造的脚本路径充当证据。
- 不知道的持续帧、判定区域和偏移填写 `null` 或保留空集合并标 `extracted_partial`。不得用 0、1、默认矩形或估计动画填满以通过发布校验。
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

战斗中间数据 `command_catalog` 用原版时间轴帧标签（`砍1`、`万解`）作为招式 ID，并保留 `doAllAction` 的谓词槽位（`nornalhit`、`bisha`）。尚未接线的标签和取消窗口列入 `gaps`，不得从目录里删掉。新角色只编译自己的 catalog，不另造英文招式名。`action_exits` 收录无条件 `gotoAndStop`：连段/受击/必杀回 `站立`，以及离地招式切到 `落`/`落2`（鸣人 `招3` 第 491 帧）。走路等循环标签上的回站立不自动接线，以免打断当前切片手感。

`hit_priority.instances` 必须由原版 `hitks` 与 1–5 后缀展开得到。一个 tick 同时存在多个 `*atm` 时按该表选中第一个命中，不能依赖 JSON、Godot 子节点或哈希表的遍历顺序。`impact_strength` 按原版 `bdxg()` 映射共享的 `XG_kan`、`XG_qdj`、`XG_qdjx`、`XG_mfdj`、`XG_mfdjx`、`XG_kanx` 命中特效；`zl > 10` 是破防标记，`beida()`/`fangyu()` 在进入普通受击链前只减一次 10，再用归一后的 1–6 选择效果。该展示属于通用受击链，不属于某一角色招式的硬编码。

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
