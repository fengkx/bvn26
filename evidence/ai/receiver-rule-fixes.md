# 共用受击规则修复与 r15 首局推进

状态：四项共用规则已修复，整场对照仍未通过。没有按鸣人、一护名字分支。

## 跨角色适用范围

[35 个主角色审计](shared-receiver-rules.json) 保留每个 bundle 哈希、函数原文、
原路径及分组。运行 `python3 tools/audit_shared_receiver_rules.py --check` 可复查。

- BODY `onDefence(xgtype)` 共 49 处，完整原文相同，覆盖全部 35 个主角色；
  均调用 `updateDirect(true)`。另有 64 处控制器 `onDefence()`，用途是派发动作，
  不能因为同名而与 BODY 的结算函数混用。
- `updateDirect` 和 `loseHp` 各 49 处，分别只有一个原文组，覆盖全部 35 个角色。
- `getHitObj` 共 64 处、两个原文组；差别是 `_loc14_` 与 `_loc13_` 的反编译局部
  变量编号，两组均按传入数组生成精确实例名。没有“去掉末尾 0”的查询规则。
- 低血量回气来自全局 `main.swf` 的 HUD 剪辑，作用于两个玩家槽位，与人物名无关。

这些是源码共用性证据，不代表所有形态可达，也不代表其他角色已经迁移或验收。
后续角色应绑定自身的源函数版本、时间轴、实例和招式数据；保留变体，不按名字补丁。

## 本轮修复

1. **防御朝向**：`FighterRuntime._settle_source_hit` 的防御路径漏传 `true`。
   修正后与源 `onDefence(xgtype)` 一样按攻击方朝向反向转身，而非按双方位置。
   r15 最早的方向差异在显示帧 595；之后的 22/50 像素偏移及 735/726 边界差异
   是后续结果，不是最初的脚本队列问题。回归覆盖两位样本、两个朝向及不增加 hits。
2. **精确攻击名字**：删除 `_attack_from_instance` 把 `zh20atm` 映射成 `zh2` 的
   推测逻辑。一护源 `DefineSprite_638/frame_359/...enterFrame` 使用 `zh20atm`
   判断是否进入“招21”；Sprite 2 的 `_fsArray` 由 hitks 与后缀 1–5 生成，不含
   `zh20`。传感框可触发动作，却不能成为伤害框。回归实际让身体与该传感框重叠，
   验证不返回攻击，同时确认 `zh2atm` 仍绑定 80 伤害。没有改角色碰撞框大小。
3. **低血量回气**：新增 `build_health_rules.py`，严格匹配原版
   `DefineSprite_1814/frame_1/DoAction.as` 的 gameplay 前缀，生成
   `godot/generated/main/health/rules.json`。`SourceHealthRules` 解释阈值与增量，
   注册至共用回调表，由原先更早创建的 HUD 在角色首批帧脚本结算后执行，位于
   root 观测前。具体证据：r15 序号 48536–48541，HP 首次降到 20% 以下后，同一根
   root 快照已含 0.2 回气。双方先各算百分比，任一 <=0 时整段返回；严格 <20，
   不受 zhanting 限制，不在此处钳制气量上限。显示层 `HealthHud` 不负责改气量。
4. **致死血量**：源 `loseHp` 是 `hp -= v`，死亡检查才判断 `hp <= 0`。
   移除结算时额外的零下限。r15 序号 49090 必须先保留 -130，随后 BODY 自己的
   更新可以再处理它；不能提前改写结算边界。回归覆盖 10 HP 接 80 伤害得到 -70。

受击帧、感知框和 HUD 祖先放置证据仍来自原输入：
[受击结算源索引](hit-settlement-source.json)、[AI 源审计](source-audit.json)、
[HUD 祖先与空帧清单](match-timeout-source.json)。本轮没有更改放置、动作离开方式、
随机 tape 或输入；上面四条不变量均能指回原脚本，并由 r15 同输入记录定位。

## 验证与剩余差异

[验证清单](receiver-rule-validation/checks.json) 中 7 项定向原生测试通过，
检查了成功标记且无 SCRIPT ERROR；三个缺陷另保留修复前失败日志。
新增重放检查将朝向纳入失败条件；坐标仍保留原始差值，不放宽精度阈值。

- [r13](receiver-rule-validation/r13.json)：1166 个边界通过，完整随机/时钟 tape 消费。
- [r14](receiver-rule-validation/r14.json)：1084 个边界通过，完整随机/时钟 tape 消费。
- [r15](receiver-rule-validation/r15.json)：2798 个边界对齐，首差异推进至显示帧 2364，
  即首局 KO 第 30 帧恢复游戏。此时原版 P2 仍在 470，原生已到 471；P1 hstm
  原版为 0、原生为 1。该比较尚未覆盖后续换局。

KO 恢复差异的 [最小原生复现](receiver-rule-validation/ko-resume-probe.gd)
与 [预期失败日志](receiver-rule-validation/ko-resume-probe.log) 作为分析证据保留，
不列入已通过测试。原版序号 49224–49228 说明恢复发生在该帧角色推进之后。

曾试验将整个 KO 脚本批次挪到角色之后，虽解决第 30 帧恢复，但在显示帧 2456
又让新建胜利子剪辑的暂停晚于角色脚本。该试验已撤回；
[诊断进度](receiver-rule-validation/progress.json) 明确标记没有保留该运行时改动。
后续应按实例注册顺序统一 KO 根/子时间轴与角色帧脚本调度，不能按人物或具体帧号
加例外。完整超时链、换局计时器相位、精确坐标与视听/Web 验收仍待完成。
