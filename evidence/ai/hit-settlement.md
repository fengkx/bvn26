# 首个命中差异的代码定位

状态：已拆分接收与源帧结算；首个命中的数值时机对齐，移动与火花暂停仍有差异。

重建索引：`python3 tools/analyze_hit_settlement.py`；检查：加 `--check`。
[索引](hit-settlement-source.json) 保留两角色基础形态的函数原文、哈希、
源路径及结算调用前一帧脚本。它复用现有受击帧编译器，缺少必需函数即失败。
这里只验证基础形态，不把其他形态同号帧混进当前时间轴。

## 源代码确定的执行边界

| 阶段 | 源行为 |
|---|---|
| Sprite 2 `beida` / `fangyu` | 读取命中对象，写 `jhp/bdzl/yup/htx/tdtime`，规范化破防标记并 goto；不扣血，不增加 hits，不发命中火花 |
| `onBeHit0` | 写动作、beida、jumped、jump、hited、time，再 play；自身没有 goto |
| `onBeHit` | 依序 onBeHit0、bdxg、hits++、条件连击 HUD、hitlosehp、updateDirect、checkDead、hurtVoice、墙边状态和深度调整 |
| `hitlosehp` | 仅 `_root.to == false` 时扣血、受击方回气；攻击方在此时动作不等于 3 才回气 |
| `onDefence` | 火花、转向、条件扣血及双方回气、深度调整、checkDead；不增加 hits |

| 基础形态 | 防住调用帧 | 普通受击调用帧 | 击飞调用帧 |
|---|---:|---:|---:|
| 鸣人 Sprite 764 | 1003 | 1015 | 1028 |
| 一护 Sprite 638 | 727 | 739 | 752 |

防住、普通受击的前一帧都只有 `play()`；击飞前一帧是 `hited = 0; play()`。
因此不能在 goto 接收点立即运行结算，也不能把全部受击处理统一延迟一 tick。
结算属于实际到达的帧脚本，可能受 stop、goto、实例生命周期影响。

## 当前原生实现的差异与修复约束

[连续对照首差](combat-input-first-difference-r04.json) 中，display 469 已一致进入
鸣人 1014、一护 372，但原生已扣掉 80 HP 并写受击状态；原版在下一帧的
`onBeHit` 才结算。此记录用于验证上述代码链，不作为添加一帧计时器的依据。

`FighterRuntime.receive_attack` 当前把转移、结算和 goto 合并；
`apply_attack_contact` 又在碰撞时按缓存的动作分类给攻击方回气。
后者必须改为结算时读取对手当前源动作字段，保留 `_root.to` 守卫。
注释中“onBeHit0 然后 goto”也不符合原文，修复时须一并纠正。

实施应消费已有 `on_be_hit_frames` / `on_defence_frames`，严格筛选当前 Sprite。
伤害来自结算当时的可变接收字段，不能未经证明改成不可变伤害队列。
还需核对受击移动剪辑的放置寿命、目标帧排队执行顺序，以及死亡、火花暂停、
语音和转向的相对时机，再修改运行时。当前测试中立即 receive 后断言 KO 的用例
不能充当正确时机的依据，必须改为实际经过源结算帧。

验收须重跑原版相同输入与随机 tape 的连续对照，越过首个命中及后续玩家输入；
索引可重建或短程 AI 测试通过均不代表完整电脑对战一比一完成。

## 本轮实现与实测

`receive_attack` 现在只转移字段、设置现有移动参数并进入目标标签。
`_apply_ai_source_frame` 消费实际排队的帧，按当前 Sprite 匹配编译的结算调用；
`apply_attack_contact` 不再提前给攻击方回气。结算读取可变 jhp/bdzl 和攻击方当前动作。
新增 root_to 守卫默认 false；完整倒计时到时写入链仍未实现，不能视为已验收。

[连续对照](combat-hit-settlement-r04.json) 越过 display 469、470 的数值差异，
下一个首差在 display 471：原版 paused=true，原生 false，两者源帧仍相同。
位移单独记录显示原生受击移动过早；鸣人源时间轴 1014/1015 没有移动控制实例，
1016 才新放置 depth 30 / Sprite 16，不能在进入被打标签后立即模拟移动。
转向、深度、语音、按源实例寿命移动及全部根级调度仍未完成；当前结算函数不是完整 onBeHit 翻译。

`hit_settlement_frame_smoke.gd` 实测两角色接收帧不结算、下一源帧结算、
攻击方在两阶段之间变为动作 3 时不回气、重复运行同帧不重复扣血。
`vs_com_ko_smoke.gd` 已改为通过真实下一逻辑帧进入结算，双方两轮 KO 流程通过。
日志中的 macOS 证书初始化错误不属于脚本失败；两项均有完成标记且无 SCRIPT ERROR。
