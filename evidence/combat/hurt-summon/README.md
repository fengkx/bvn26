# 电脑鸣人浮空受击时错误召唤援助

2026-09-10。修复范围是当前三名基础角色共用的受击脱身分支、召唤抑制及鸣人替身特效。完整角色、整局视听和线上发布验收仍未完成。

## 原版依据与根因

用户确认电脑角色是鸣人。原版不是禁止所有空中动作，而是区分两种受击路径：

- `beidax(flying)` 在根暂停时直接返回；只有非 `flying` 且递增后的 `hstm < 20` 才调用 `doHurtSkill()`。
- `hurtSkill()` 检查 HP、死亡、100 气和对手动作；电脑还要求 `goran < 30`。
- `doHurtSkill()` 扣 100 气并设置 `hurtSkling`。火影角色使用 `XG_tishen`，按面向 `moveX(150)`，创建 `XG_tishen2`，回站立，800 ms 后恢复；死神角色使用 `XG_bsq`，600 ms 后恢复、进入“招换”并创建爆气攻击。
- `doZhaoHuan()` 的第一条分支是 `if(hurtSkling) return undefined`，所以死神脱身经过“招换”时不生成援助、不额外扣气，也不执行 `bs=1`。

源码位置：

- [主脚本](../../../scripts/main.json)：`frame_6/DoAction.as` 中鸣人配置 `isNaruto:true`；`frame_8/DoAction.as` 的 `chushi` 开局初始化把各自所选配置的 `isNaruto` 复制到 P1/P2 容器。
- [鸣人](../../../scripts/fighter/minren.json)：`DefineSprite_764/frame_1/DoAction.as` 的 `beidax`、`hurtSkill`、`doHurtSkill`、`doZhaoHuan`。
- [一护](../../../scripts/fighter/yihu.json)和[日番谷](../../../scripts/fighter/rifagu.json)：基础形态同样位于 `DefineSprite_638/frame_1/DoAction.as`。

移植有两个相连的缺口：P1 的 `is_naruto` 固定为 true，P2/电脑默认 false；召唤转换器只保留生成、扣气与 `bs`，漏掉提前返回。电脑鸣人因此走错死神脱身分支，随后错误生成我爱罗。只加“空中不能召唤”会掩盖根因并改变原版规则。

## 源码五问及生命周期

1. **脚本与调用链**：沿上述 BODY 函数追到定时回调和招换事件。鸣人/一护/日番谷分别在源帧 956/657/818 调用 `doZhaoHuan()`，在 981/682/843 `gotoAndStop("站立"); play();`。其间无脚本帧继续播放，不能按标签边界另造退出。35 个角色 bundle 的全部同名函数均通过严格编译检查。
2. **实例寿命**：`isNaruto` 属于所选角色容器，不能属于玩家槽位；`hurtSkling` 属于当前角色 BODY，脱身到招换间必须保留。原版重新执行站立第 1 帧时恢复该标记；不能由召唤函数或定时器擅自清除。没有改变战斗剪辑的 PlaceObject/MOVE 调度。
3. **退出方式**：火影脱身立即 goto 站立，死神定时回调 goto 招换，再由上述源帧回站立。定时器保持原来的 800/600 ms，未改成猜测的逻辑帧数。
4. **源不变量**：角色阵营不随 P1/P2、玩家/电脑改变；真正击飞不调用普通受击脱身；暂停不调用脱身；一次脱身只扣 100 气；标记为真时召唤三项副作用全部跳过；同一角色恢复后仍能正常召唤。
5. **原播放器对照**：两份独立原版副本执行同一受控序列：首次普通召唤、空中普通受击脱身、再次普通召唤、真正击飞。记录实际原函数调用和援助生成。坐标、气量、随机决策字段和受击入口由夹具设置，因此这是受控原函数/时间轴对照，不是新增的真实键盘整局同输入验收。既有 r13/r14/r15 随机/时钟/输入轨迹另外保持原样回放。

## 修复

- 转换器从已锁定角色配置编译 `is_naruto`；共用 BODY 上下文读取它，移除 P1 的固定值。
- 严格编译 `doZhaoHuan()` 的提前返回、扣气及状态写入。无法识别完整函数时构建失败，不静默丢分支。运行时解释 `skip_if_truthy`；一次被跳过的帧执行也结束本次事件，不在同帧稍后偷偷重试。
- 导入原 `XG_tishen`（Sprite 98）和 `XG_tishen2`（94），接通共用 `addChildXG`。前者第 3 帧闪光、第 35 帧移除，后者第 20 帧移除；位置分别来自移动前与移动后，偏移参数顺序按原版 offsetY/offsetX。

## 验证证据

- [原版观测摘要](original-comparison.json)：电脑鸣人脱身后 X 从 700 到 550，气量 300→200，没有援助调用；一护在 `hurtSkling=true, ql=200, bs=0` 时到达召唤函数，但没有调用 `yfgj`。两次普通召唤均实际生成，真正击飞未扣脱身气量。
- 原始日志、独立副本哈希和插桩差异：[鸣人构建记录](naruto/build.json)、[一护构建记录](ichigo/build.json)。同目录保存 `native.log.gz`、`instrumentation.diff.gz` 和捕获完成记录。构建记录中的 P2 援助字段已纠正为夹具实际使用的我爱罗。
- [角色分支修复前](faction-before.log) → [修复后](faction-after.log)：主场景 CPU 鸣人从错误的 `XG_bsq/600 ms/X=700` 改为 `XG_tishen/800 ms/X=550`；CPU 日番谷保持死神分支，P1 一护不再被当作火影角色。
- [召唤修复前](summon-before.log) → [修复后](summon-after.log)：旧实现在脱身招换第 657 帧多扣 100 气并生成援助；同一角色两轮普通召唤/空中脱身现在通过，含暂停、击飞、回站立重置。
- [源码检查](python.log)：53 项通过，包含 35 个角色的召唤提前返回、未知分支拒绝、替身资源哈希与闪光/移除帧。
- [共用模式](shared-modes.log)：双人和练习各 602 条角色状态匹配。[既有电脑对战回归](ai-regressions.json)：r13/r14/r15 当前比较字段和边界匹配；没有改输入或比较阈值。
- [Web 日志](web-log.json)、[Web 受控适配器](web-test.gd)、[替身画面](web-substitution.png)：浏览器执行主场景角色切换、电脑脱身、定时回调及完整招换抑制窗口，核对移动前后两组特效实际绘制。它没有验证真实键盘/失焦，也不是跨渲染器逐像素比较。

## 未混入本次通过率的检查

[原生检查清单](native-checks.json)保留每项脚本错误及退出资源警告。旧 `ai_combat_services_smoke.gd:58` 的直接扣血断言失败；在隔离的未修改 HEAD 中同样失败，见[基线日志](legacy-service-baseline.log)，没有为本次修复改期望。部分旧 smoke/并行进程退出时有资源警告；不能把退出码 0 当成整组通过。

本地生产 Web 已从源码重建；隔离浏览器夹具另行导出。没有部署到 `bvn26.vercel.app`，不能把本地验证表述成线上已更新。
