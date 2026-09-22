# 李洛克基础形态源审计 r01

状态：`source-derived-artifacts-ready`；尚未接入生产选人、共享运行时或 Web 入口。

## source identity

| 字段 | 值 |
|---|---|
| 角色配置 | `manifest.json → fighter_catalog → 小李` |
| 显示名 | `李·洛克` |
| source id | `sprite_518`（`DefineSprite_518`） |
| 基础形态 | `form_frame=1`；配置没有 `WKframe`，没有证据支持额外形态入口 |
| SWF | `game/fighter/lee.swf` |
| SWF SHA-256 | `2443dc112dbf2be696abb9d924831814ae01990536df8298fa2c1432f35c93d1` |
| 脚本 bundle | `scripts/fighter/lee.json` |
| bundle SHA-256 | `82230e0e97e0b2751ecba3e27b6f82e46c467ae956c51b0a2ba4d9c114c7e967` |
| 时间轴 | 1297 帧，38 个标签 |
| 源脚本数量 | `DefineSprite_518/` 下 167 条（含帧脚本和 clip enterFrame） |

## SOURCE_FIRST 五问

1. **每帧脚本 / enterFrame**：已保留 `DefineSprite_518/` 下全部 167 条源脚本路径与内容；基础动作区间来自 `sprite_518` 标签，不能只用标签端点代替帧脚本。代表性入口为 `frame_1/DoAction.as`、`frame_1/PlaceObject2_518_1/CLIPACTIONRECORD onClipEvent(load).as` 和 `frame_1/PlaceObject2_518_1/CLIPACTIONRECORD onClipEvent(enterFrame).as`。专属回归锁定全量计数，防止后续切片漏掉中间帧。
2. **PlaceObject / MOVE**：根角色在 `frame_1/PlaceObject2_518_1` 创建；`load` 初始化 `spd=10`、`jumpPower=15`。已用 JPEXS 26.2.1 导出 `/tmp/lee-export/lee.xml`，并由 `extract_timeline_geometry.py --sprite-id 518` 生成 `data/slices/lee-base.timeline.json`；生成时间轴保留 1297 帧的 display-list changes、PlaceObject/MOVE 和嵌套定义。实例生命周期仍需运行时/原版轨迹验证，不能由导出成功替代。
3. **离开标签**：源中同时存在无条件 goto（如 `DefineSprite_518/frame_634/DoAction.as` 回 `站立`）、条件 goto（如 `frame_625/DoAction.as` 的 HP 条件回 `必杀1`）、`stop()`，以及无终端脚本的自然 fallthrough。`end_frame` 未被当作自动回站立。
4. **可断言不变量**：基础形态动作标签、源帧区间、气量扣除、必杀/超必杀的入口帧与 `bsd`/`cbsd`/`showFace` 调度可由源直接断言；位移、判定框寿命、矩阵、音画和回调次序仍需时间轴/原版轨迹，不写猜测值。
5. **原版同输入**：本轮尚未完成李洛克原播放器固定输入捕获，因此没有宣称一比一行为通过。原版捕获须与朽木白哉共用 `/tmp/bvn-native-flash-capture.lock`，串行清理日志并校验连续事件。

## 已确认的基础形态源事实

- 标签：`站立 1–9`、`走 10–19`、`瞬步 20–33`、`跳 34–49`、`落 50–65`、`跳2 66–82`、`落2 83–108`、`落地 109–120`、`砍1 157–180`、`砍2 181–208`、`砍3 209–244`、`必杀 574–634`、`超必杀 795–986`、`被打 1073–1085`。
- 普通必杀在 `frame_575` 扣 100 气；超必杀在 `frame_796` 扣 300 气。源分别在 `frame_578`/`frame_798` 调度 `bsd`/`cbsd` 和 `showFace`。
- `frame_634` 明确 `gotoAndStop("站立"); play();`；`frame_625` 仅在对手仍存活且动作为 `-1` 时进入 `必杀1`。
- 标签集合没有 `万解`；`超必杀` 是基础形态必杀演出，不能据此打开变身入口。变身/共享 WKframe 保持关闭，待源菜单映射与原版输入证据。

## 当前边界

已验证：锁定输入哈希、`sprite_518` 身份、标签与帧数、167 条源脚本存在、基础必杀扣气和退出脚本的源锚点。

未验证：每个攻击的判定框窗口与矩阵/注册点行为、AI 固定 tape、援助生命周期、能量不足/取消/防御/命中轨迹、原版同输入、Godot 原生/Web 运行和视听一致性。已生成 178 个源命令 fixture，状态仍为 `generated_not_validated`；已从 43 个源帧抽取声音区间，生成 `godot/generated/fighters/lee/sound_segments.json`，声音触发仍未做原版对照。

变身暂缓：`plan/coverage.json` 中“小李”当前 `WKframe=null` 且状态为 `not_started`；在共享注册表整合和原版可达证据前不开放入口。

## 复现

```bash
python3 tools/importer/extract_fighter_slice.py --output-dir /tmp/lee-slice 小李
python3 tools/importer/export_swf_xml.py --ffdec-jar /tmp/ffdec-26.2.1/ffdec-cli.jar --output-dir /tmp/lee-export game/fighter/lee.swf
python3 tools/importer/extract_timeline_geometry.py /tmp/lee-export/lee.xml --sprite-id 518 --ranges-from data/slices/lee-base.json --source-swf game/fighter/lee.swf --output data/slices/lee-base.timeline.json
python3 tools/importer/build_combat_model.py --fighter data/slices/lee-base.json --timeline data/slices/lee-base.timeline.json --scripts scripts/fighter/lee.json --output data/actions/lee-base.json
python3 tools/importer/materialize_timeline_assets.py --workspace /tmp/lee-export --timeline data/slices/lee-base.timeline.json --fighter-slice data/slices/lee-base.json --combat-model data/actions/lee-base.json --output-dir godot/generated/fighters/lee
python3 -m unittest tools.tests.test_lee_source_audit
```

抽取器输出是中间反向工程资料；`/tmp/lee-slice/lee-base.json` 不进入发布物。
