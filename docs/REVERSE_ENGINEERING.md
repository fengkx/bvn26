# 逆向与素材导入工作手册

## 已有材料和定位方式

- `game/main.swf` 是用户入口；`game/fighter/` 及 `fz/` 是角色与援助；`game/music/` 是外部音乐。
- `scripts/*.json` 中每个 `scripts` 元素含原导出路径 `path` 和完整 `source`。路径中的 Sprite/帧/PlaceObject/ClipAction 是定位线索，不是适合直接写死到业务代码的永久 API。
- 同名局部变量（如 `_loc2_`）是反编译结果，不代表原作者命名。不存在原 `.fla` 工程、注释或完整作者源目录的保证。
- 运行 `python3 tools/read_script.py scripts/fighter/minren.json --path frame_1/DoAction.as` 查看配置；也可使用 `--search` 找源片段。

## 查阅优先级

| 对象 | 定位 |
|---|---|
| 版本 | `scripts/main.json` → `frame_1/DoAction.as` |
| 人物/形态/地图配置 | 同上 → `frame_6/DoAction.as`；结构化副本在 `manifest.json` |
| 键位、默认变量、外部目录 | 同上 → `frame_7/DoAction.as` |
| 公共特效、暂停/恢复等 | 同上 → `frame_8/DoAction.as` |
| 动态加载 | 同上搜索 `loadClip` / `loadSound` |
| 鸣人招式数值 | `scripts/fighter/minren.json` → `frame_1/DoAction.as` |
| 鸣人受击规则 | 同上 → `DefineSprite_2/frame_1/DoAction.as` |
| 鸣人共用控制 | 同上 → `DefineSprite_16/frame_1/DoAction.as` |
| 一护 | `scripts/fighter/yihu.json`，用源方法名查找，不套用鸣人的 Sprite ID |

## 从一个动作向外追踪

1. 找动作帧标签和进入条件，例如普通攻击的 `gotoAndPlay("砍1")`。
2. 找该标签对应的原帧区间、嵌套 MovieClip、放置/移除的攻击对象和可见动画。
3. 找攻击对象名称与 `getHitObj` 对参数的索引规则，关联伤害、击退、硬直、受击状态。
4. 找下一招/防御/跳跃等取消条件、计数重置、气量变化和冻结恢复。
5. 记录每一阶段的来源路径，并在原版上输入固定按键进行对照。没有激活帧/判定区的数据只能标为 `extracted_partial`。
6. 开始写 Godot / 编译器之前，用 [SOURCE_FIRST.md](SOURCE_FIRST.md) 核对：区间内每一帧脚本、剪辑是新放置还是 MOVE、离开标签的四种方式、以及测试锁的是不是原版不变量。标签 `end_frame` 不是回站立；空帧表示播放头继续。

## 导入必须保留的信息

SWF header 与哈希、符号 ID、形状/位图内容、注册点、矩阵、颜色变换、深度、父子实例、实例名称、帧标签、ShowFrame 时长、PlaceObject/RemoveObject、声音事件、遮罩、混合/滤镜以及脚本事件关联。

原 AS2 的 ClipAction 可能附着在放置对象上，而不只在帧上的 DoAction。仅遍历 `frame_N/DoAction.as` 会漏掉输入和碰撞等重要逻辑。

分析阶段可以从 JPEXS 导出位图和音频；精确嵌套时间轴宜用 SWF 标签或结构化 XML 处理。`tools/inspect_swf.py` 只给出基础结构信息，不是已经实现的完整资产转换器。不得把它的 JSON 当作完整动画数据。

## 重点未知项和探针

| ID | 需要解决的问题 | 最小探针 |
|---|---|---|
| U-01 | 帧脚本、enterFrame、对象创建、goto 与删除的顺序 | 单帧内多个记录点，嵌套对象和目标帧各输出事件序号 |
| U-02 | stop/play 与冻结对不同回调/定时器的影响 | 同时运行动画计数、enterFrame、interval，分对象触发暂停 |
| U-03 | hitTest 的边界与坐标变换 | 相切/重叠/透明判定区、镜像、缩放、父级矩阵 |
| U-04 | 未定义/NaN/比较/枚举语义 | 摘取实际分支，对照原代码与 GDScript 的结果 |
| U-05 | AI 和视听随机数的消费顺序 | 记录每次调用位置、结果和触发 tick，关闭/开启声音比较 |
| U-06 | 24 FPS 的四代援助被 30 FPS 宿主加载后如何推进 | 对比宿主 tick 和援助源帧，不凭子文件头推断 |
| U-07 | WKframe 变身共享的状态、计数和资源 | 变身前后同一输入重放，跟踪血量/气量/方向/位置/援助 |
| U-08 | 最终模式名、可达内容及原 UI 行为 | 逐路径遍历菜单并截取配置 ID 与实际选择结果 |

这些问题均尚未完成运行验证，责任任务见 `plan/tasks.json`。取得探针结论后写入项目 `evidence/` 和 ExecutionProfile；不要在本包伪造已完成结果。

## 重新导出

JPEXS 26.2.1 与 Java ≥17 可用后：

```bash
java -Djava.awt.headless=true -jar /absolute/path/ffdec.jar -config parallelSpeedUp=false -export script,image,sound /absolute/path/output game/main.swf
```

输出到工作目录，不覆盖基准。此前批量导出曾出现非空动作被导出为空的情况，重导修正后只保留一个原本仅含 End 指令的空帧。因此必须检查空导出是否与原始动作长度相符，不能仅看工具退出码。
