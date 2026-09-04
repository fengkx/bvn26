# 鸣人、一护基础切片静态证据

状态：转换器前置工作，`M1-02` 仍受 `M0-03` 调度结论约束  
记录日期：2026-09-04（Asia/Shanghai）

本切片以锁定 SWF、AS2 反编译路径和 SWF display list 为依据。Ruffle
不作为动作时序或战斗行为基准；生产预览不包含 SWF、AS2、AVM 或 Ruffle。

## 已确认来源

- 鸣人基础形态是 `game/fighter/minren.swf` 根时间轴第 1 帧放置的
  `DefineSprite 764`；一护对应 `DefineSprite 638`。
- 基础移动速度来自各自 load ClipAction：鸣人每逻辑步 8，一护每逻辑步 6；
  跳跃初值均为 15。
- 普攻三段、受击和必杀范围来自上述角色时间轴的 FrameLabel。
  鸣人同一必杀跨越 `必杀`、`必杀1`、`必杀0` 三段，提取时保留完整链路。
- 攻击数值来自根 `frame_1/DoAction.as` 的 `gjl1` 赋值。首个普攻伤害分别为
  鸣人 15、一护 40；其余数值见 `data/slices/*-base.json`。
- display list 快照保留每帧 Place/Modify/Remove 顺序、深度、实例名、矩阵、
  颜色变换、ClipAction 摘要及声音事件。鸣人 `砍1` 的 `k1atm` 在源第 174
  帧出现，一护在第 177 帧出现。

## 可重复产物

- `tools/importer/extract_fighter_slice.py`：从锁定 SWF 与脚本生成动作与参数切片。
- `tools/importer/export_swf_xml.py`：严格要求 JPEXS 26.2.1 和 XML 3.2，生成临时
  XML/位图/声音工作区及哈希报告；JPEG3 的颜色和 alpha 额外合成为 PNG。
- `tools/importer/extract_timeline_geometry.py`：重建 display list 状态并保留目标帧，
  同时保存嵌套 Sprite 的首帧放置矩阵。
- `tools/importer/materialize_timeline_assets.py`：只复制目标切片可达的外部素材。
- `tools/importer/build_combat_model.py`：把攻击框持续窗口、连段转移窗口、动作退出帧
  和受击停帧从 display list 与目标 Sprite 的 AS2 路径合成为可追溯战斗数据。
- `data/slices/`、`data/actions/`：可追溯的中间数据；`godot/generated/fighters/`：
  Godot 预览输入。

Python 单元测试覆盖基础符号选择、动作边界、移动/伤害值以及 Place/Modify/Remove
状态继承。Godot 4.7.2-stable 已完成资源导入、无头启动和 Web 导出；Google Chrome
152 的独立无头会话显示了两名角色的原素材、源帧动画、身体判定框以及从
`game/main.swf` 第 2 帧“现世”标签导出的背景/前景层；JPEG3 透明边缘显示正常。
同一鸣人临时工作区连续两次完整导出的报告 SHA-256 均为
`67f62b6a7e493fe7cd77305bdcdb32008b304eecb42402a22b078f8606c55dba`。
回归测试固定了两个容易被人工推断改错的事实：鸣人第二段实际仍放置 `k1atm`，
第三段放置 `k2atm`；运行时必须按实例名索引伤害，不能按“第几段”顺移参数。

## 尚未确认

当前预览按 30 Hz 顺序展示源帧，但尚未把 `gotoAndPlay`、`stop/play`、enterFrame、
对象生命周期和命中枚举顺序写死为战斗规则。现世地图目前仅完成静态视觉首帧，
嵌套动画、平台碰撞、声音播放、攻击结算和原版 golden 轨迹仍未完成。因此这些产物
不能视为逐帧对齐验收通过。
