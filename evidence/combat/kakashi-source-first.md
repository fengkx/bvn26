# 卡卡西基础形态源审计

状态：`source_static_ready + geometry_ready + visual_assets_ready`。本记录只覆盖普通 2.6 的可选基础形态「卡卡西」；咒怨/须佐等其他形态和转换入口不在本次范围内。

## 固定身份

- 角色配置：`manifest.json → fighter_catalog.卡卡西`，显示名「旗木·卡卡西」，原版文件 `game/fighter/Kakashi.swf`，援助「我爱罗」，对战候选「宁次」「鼬」。
- SWF SHA-256：`48587becee990fccfd7450a1b605a24b2d654dbd15569857659f67346bddb2fc`。
- 基础形态是根 `frame_1` 放置的 `DefineSprite_710`，30 Hz，共 1385 帧。`data/slices/Kakashi-base.json` 记录了同一角色、时间轴 ID、动作标签和 158 条源脚本。
- `spd=8`、`jumpPower=18` 来自 `frame_1/PlaceObject2_710_1/CLIPACTIONRECORD onClipEvent(load).as`，没有运行时手填角色数值。

## SOURCE_FIRST 五问

1. **每帧脚本**：`evidence/combat/kakashi-source-audit.json` 为 1–1385 每一帧建立索引，逐项保留 `DoAction`、`enterFrame/load` 路径、源码哈希和完整源码。没有脚本的帧也保留为空记录。源包为 `scripts/fighter/Kakashi.json`。
2. **PlaceObject/MOVE**：根角色由 frame 1 的 `PlaceObject2_710_1` 放置；各后续剪辑按源路径和帧/深度保留。使用 `/private/tmp/bvn-ffdec-26.2.1/ffdec-cli.jar` 导出原 SWF XML，再由 `extract_timeline_geometry.py` 生成 1385 帧几何；`materialize_timeline_assets.py` 从同一 XML 生成 `godot/generated/fighters/kakashi` 的 346 个源资产。
3. **离开标签**：审计索引所有 `gotoAndPlay`、`gotoAndStop` 和 `stop()`；无终端脚本的区段仍按时间轴 fallthrough 处理，不能把 `end_frame` 当成回站立。
4. **原版不变量**：根攻击表逐项保留；`hits=0` 在 frame 2；防御 `onDefence(2)` 在 frame 1105；普通受击 `onBeHit()` 在 frame 1117；击飞 `onBeHit(true)` 在 frame 1130；必杀演出为 `bsd/showFace("卡卡西1")`@693、`bsd/showFace("卡卡西2")`@759、`cbsd/showFace("卡卡西3")`@865。
5. **同输入对照**：普通砍1 fixture 已在原播放器完成 360 帧采样，并通过生产 `move_case_reference.gd` 与 `compare_mode_reference.py` 完成 722 对状态字段的完整比较，报告见 `evidence/characters/kakashi/production-comparison-r01.json`。该输入只覆盖 frame 193–218，不能证明超必杀 frame 864/887/900；超必杀 fixture 已构建，原播放器采样仍待下一独占时段。没有把本地静态检查或合成 Godot 输出宣称为一比一轨迹。

## 源攻击表和演出

`frame_1/DoAction.as` 中 `gjl1` 的 23 个攻击记录已解析进审计 JSON；例如 `k1` 为伤害 30、冲击 2、水平 3、硬直 300 ms，`cbs` 为伤害 330、冲击 5、垂直 20、水平 40、反应「击飞」。运行时应由通用编译器读取这些字段，禁止按卡卡西写 GDScript 分支。

可选基础角色的动作标签覆盖待机、移动、空中、三段普攻、砍技、招式、三类必杀、超必杀链、防御、被打、击飞、起身、开场、胜利和失败；完整帧范围在审计 JSON 的 `timeline.action_spans`。

## 验证与边界

已通过：

```text
python3 tools/importer/extract_fighter_slice.py 卡卡西 --output-dir /Users/fengkx/me/code/bvn2_6/data/slices
python3 tools/kakashi_source_audit.py --output evidence/combat/kakashi-source-audit.json
python3 -m unittest tools.tests.test_kakashi_source_audit
/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/kakashi_visual_smoke.gd
```

Godot 视觉 smoke 输出 `KAKASHI_VISUAL_SMOKE_OK`，确认 1385 帧、定义、资产、源动作范围和指定源帧可加载；生产 CPU controller 的 Cbshit/projectile 语义回归输出 `KAKASHI_PROJECTILE_SEMANTICS_OK`。原版普通砍1 采样 marker 为 `original_capture_completed_not_port_parity`；随后生产回放完整比较为 `matched`，722/722 状态行一致，报告见 `evidence/characters/kakashi/production-comparison-r01.json`。源 frame 162 的 projectile load 使用 `speed * 2.5`，frame 900 的 `Cbshit` 条件跳转和 frame 887 命中写入已由通用编译器/运行时回归覆盖；超必杀原版轨迹仍待采样。Web 验证依赖 native；因此卡卡西尚不能标记为“一比一验收完成”。
