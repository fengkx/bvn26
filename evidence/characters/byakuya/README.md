# 朽木白哉基础形态源分析

状态：`source_inventory_not_behavior_acceptance`。

真实源文件是 `game/fighter/Byakuya.swf`，入口角色目录为 `scripts/fighter/Byakuya.json`。基础形态在根时间轴 `sprite_631` 的 frame 1，frame 2 的 `sprite_1052` 是后续形态替换；`万解` 标签从 frame 1105 开始，当前保持关闭。

五问记录和完整帧脚本索引见 [`source-audit.json`](source-audit.json)。运行：

```bash
python3 evidence/characters/byakuya/build_source_audit.py
```

当前阻塞：共享 `controller_aliases` 将 `DefineSprite_631` 后续帧的多个 controller 也纳入候选，发现不同源 hash 后拒绝提取。基础形态应只从 frame 1 的 placed controller（`character_id=16`）选择；不能按角色手写替代逻辑。原版固定输入捕获尚缺，因此本目录不声明一比一验收通过。
