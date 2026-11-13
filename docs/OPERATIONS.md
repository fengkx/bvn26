# 使用、验证与未来构建

当前保存的全角色 Flash 回放、Godot/回滚检查、五项历史失败及复现命令见[回归证据索引](REGRESSION_INDEX.md)。该索引不替代逐项验收。

## 现在可执行的命令

解压后进入 `bvn26/`。以下工具已包含：

```bash
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/read_script.py scripts/fighter/minren.json --path frame_1/DoAction.as
python3 tools/read_script.py scripts/main.json --search loadClip
python3 tools/inspect_swf.py game/main.swf
python3 tools/importer/build_source_inventory.py
python3 tools/importer/extract_fighter_slice.py
```

资料校验、脚本读取和源清单生成仅需 Python 标准库。源清单命令会从锁定
`manifest.json`、全部 SWF 和脚本 bundle 重建 `data/source-inventory.json`；
分类是保守的静态提示，`pending`/`unresolved_semantics` 不代表可直接转换。
检查规格示例时安装开发依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/validate_contracts.py
```

Windows 将 `.venv/bin/python` 改为 `.venv\Scripts\python.exe`。Godot、Java、JPEXS、原版参照播放器未捆绑。

JPEXS 工作区必须放在临时或缓存目录，不写入 `game/` 和 `scripts/`：

```bash
python3 tools/importer/export_swf_xml.py \
  --ffdec-jar /absolute/path/ffdec-cli.jar \
  --output-dir /tmp/minren-export game/fighter/minren.swf
python3 tools/importer/extract_timeline_geometry.py \
  /tmp/minren-export/minren.xml --sprite-id 764 \
  --ranges-from data/slices/minren-base.json \
  --source-swf game/fighter/minren.swf \
  --output data/slices/minren-base.timeline.json
python3 tools/importer/build_combat_model.py \
  --fighter data/slices/minren-base.json \
  --timeline data/slices/minren-base.timeline.json \
  --scripts scripts/fighter/minren.json \
  --output data/actions/minren-base.json
python3 tools/importer/compile_hit_receive.py
cp data/actions/minren-base.json godot/generated/fighters/minren/combat.json
python3 tools/importer/materialize_timeline_assets.py \
  --workspace /tmp/minren-export \
  --timeline data/slices/minren-base.timeline.json \
  --fighter-slice data/slices/minren-base.json \
  --combat-model data/actions/minren-base.json \
  --output-dir godot/generated/fighters/minren

python3 tools/importer/extract_timeline_geometry.py \
  /tmp/main-export/main.xml --sprite-id 1738 --frame 2 \
  --source-swf game/main.swf \
  --output data/slices/current-world.timeline.json
python3 tools/importer/materialize_timeline_assets.py \
  --workspace /tmp/main-export \
  --timeline data/slices/current-world.timeline.json \
  --output-dir godot/generated/stages/current_world
```

命中/防住火花按 `main.swf` 的 ExportAssets 名对应的 sprite id 单独导入，目录名必须与
`bdxg`/`bdfyxg` 里的元件名一致（`XG_fykan` 216、`XG_fykanx` 214、`XG_fyq` 200、
`XG_fyqx` 196、`XG_mffy` 280、`XG_mffyx` 279、`XG_kan` 159、`XG_kanx` 125、
`XG_qdj` 256、`XG_qdjx` 236、`XG_mfdj` 314、`XG_mfdjx` 298、`XG_bs` 459、`XG_cbs` 441、
`XG_fire` 423、`XG_ice` 358、`XG_leidian` 334）。`bdxg` 第 10 档的 `XG_stone` 以及
`jumpxg`/`luodixg` 的 `XG_jump`/`XG_luodi` 在 `main.swf` 没有 ExportAssets，导不出也
不得补自制资源。
必杀根剪辑同样按 sprite id 导入：`blackMu` 1510 → `godot/generated/main/blackMu`，
`ts_face` 1678 → `godot/generated/main/ts_face`。

```bash
python3 tools/importer/extract_timeline_geometry.py \
  /tmp/main-export/main.xml --sprite-id 216 \
  --source-swf game/main.swf \
  --output /tmp/bvn-effect-timelines/XG_fykan.timeline.json
python3 tools/importer/materialize_timeline_assets.py \
  --workspace /tmp/main-export \
  --timeline /tmp/bvn-effect-timelines/XG_fykan.timeline.json \
  --output-dir godot/generated/effects/XG_fykan
```

抽取会把帧上的 `StartSound`（含 `SOUNDINFO` 的 envelope 音量）与对应 `DefineSound`
记进时间轴，materialize 再把 `main_assets/sounds/<id>.mp3` 落到该剪辑目录。
sprite id 弄错会导入另一个元件，画面能出但和源不是同一条链。

BGM 不在 SWF 里，是 `game/music/*.mp3` 外部文件。按 `loadSound()` 的选曲顺序编清单
并只复制该组合可达的曲目（`--p2selt` 是源 `_root.p2selt`，`--cur-stage` 是 `_root.curStage`）：

```bash
python3 tools/importer/materialize_stage_music.py \
  --manifest manifest.json --music-dir game/music \
  --p2selt 一护 --cur-stage 现世 \
  --output-dir godot/generated/music
```

`export_swf_xml.py` 会拒绝非 JPEXS 26.2.1 或非预期 XML 版本。中间数据只保留
可追溯的源帧、原矩阵和事件；JPEG3 使用 JPEXS 的 PNG 导出合并原 alpha，嵌套
Sprite 保留首帧 display list。遇到不支持的时间轴状态会直接失败。

## 文档导航

先读根 [README](../README.md)、[SPEC](../SPEC.md)、[实施计划](../IMPLEMENTATION_PLAN.md) 与 [STATUS](STATUS.md)。实现机制前读 [SOURCE_FIRST](SOURCE_FIRST.md)。接口见 [DATA_CONTRACTS](DATA_CONTRACTS.md)，正确性见 [VALIDATION](VALIDATION.md)，来源见 [SOURCES](SOURCES.md)。

## Godot 工程构建

`godot/` 已固定为 Godot 4.7.2-stable、GDScript、Compatibility 和单线程 Web
导出。当前主场景先停在 `MENU` 三入口，再进入鸣人/一护现世切片；不是完整菜单或战斗。

```bash
godot --headless --path godot --editor --import
godot --headless --path godot --export-release Web ../dist/web/index.html
```

导入器目前覆盖首个角色切片、现世静态视觉首帧、外部位图，命中/防住/元素/必杀 `XG_*`
火花剪辑和它们第 1 帧的 `StartSound`，角色与我爱罗援助时间轴上的 `StartSound`，以及
`stageSound` 的选曲清单与曲目。嵌套动画、平台碰撞、滤镜和生产数据编译器仍未完成；
BGM 清单尚未接进 `main.gd`。不得把当前预览冒充完成的转换器或战斗实现。

### UI 静态非 ASCII 文案与字体覆盖（必做）

修改 `tools/test_online_manifest.py` 中
`test_online_ui_font_metadata_covers_static_non_ascii_strings` 扫描的任一源文件内的
静态非 ASCII UI 文案（中文、全角标点等）后，**必须在新建或更新 PR 前**用现有
字体流水线重建菜单字体和元数据。目前测试扫描 `godot/online_lobby.gd` 与
`godot/title_menu.gd`；以后新增扫描源也适用，以测试中的实际列表为准。
生成器还读取 `godot/generated/main/title_menu/controller.gd`，其文案变化也须重建。

在已安装 `fontTools` 的 Python 环境中执行（路径和字体集合索引按实际来源替换，
索引必须对应 `Sarasa UI SC`，可核对现有 `font.json` 的来源记录）：

```bash
python3 tools/importer/build_menu_font.py \
  --font /absolute/path/to/sarasa.ttc \
  --font-number <Sarasa-UI-SC-index> \
  --license /absolute/path/to/OFL.txt
python3 tools/test_online_manifest.py OnlineManifestTests.test_online_ui_font_metadata_covers_static_non_ascii_strings -v
```

核对并随文案提交 `godot/generated/main/title_menu/menu-font.ttf`、`font.json` 及
流水线所需的许可证产物；按差异更新 `manifest.json` 中受影响的 `file_sha256`，
用 `python3 tools/build_online_manifest.py` 重建在线清单及输入记录，再运行
`python3 tools/verify.py`、`python3 tools/check_handoff.py` 和
`python3 tools/build_online_manifest.py --check`。

`test_online_ui_font_metadata_covers_static_non_ascii_strings` **实际执行并通过**是
本地和 Web 构建通过的必要条件；缺元数据导致的 skip 不算通过。缺字应重建字体，
不得删除、跳过、放宽该测试或增加一次性绕过，也不得只手改元数据字符表伪造覆盖。

## Web 发布要求

最终 `dist/web/` 只包含 Godot 的 HTML/JS/WASM/资源包和转码资源。WebAssembly 本身允许使用；禁止的是执行 Flash/AS2 的运行时。不得混入源 `game/`、`scripts/`、开发追踪、源码映射、旧 Ruffle 文件或游戏平台桥接。

提供正确 MIME、压缩传输、版本化资源和一致的缓存策略。HTML 更新时不能混用旧资源清单。部署使用 HTTPS；本地验证可使用 localhost。单线程是默认方案，如启用线程需重新评估跨源隔离与部署条件，不能悄悄改导出配置。

用户点击开始后解锁声音；请求全屏置于用户输入事件中。加载失败需给出重试入口。浏览器存储不可用时保留内存设置并继续游戏。所有这些都必须实际测试，而不能只靠静态配置判断可用。

首发测试记录 Chromium、Firefox 和 Safari 的完整版本、OS、DPI 与设备。手机触控不属于当前首发范围，不能以桌面通过代替移动端性能承诺。

## 后续资料维护

`game/` 是锁定基准；修改之前先创建新基准版本并重新做来源与行为审计。`scripts/` 是关联这些 SWF 的导出，不能与另一批 SWF 混用。任何文件改变后更新清单并运行校验。清单可防止意外变化，但不是历史原作者签名。

任务实际完成后记录到 `plan/tasks.json`，内容验证记录到 `plan/coverage.json`。真实录屏/轨迹、性能报告等放到未来的 `evidence/`；不要在该目录放合成示例并把它们作为通过证明。

## 重建魂辅助

```bash
python3 tools/importer/export_swf_xml.py --ffdec-jar /absolute/path/ffdec-cli.jar --output-dir /tmp/kon-export game/fighter/fz/kon.swf
python3 tools/importer/extract_timeline_geometry.py /tmp/kon-export/kon.xml --root --source-swf game/fighter/fz/kon.swf --output data/slices/kon-helper.timeline.json
python3 tools/importer/build_helper_model.py --scripts scripts/fighter/fz/kon.json --swf game/fighter/fz/kon.swf --helper-id 魂 --output data/actions/kon-helper.json
python3 tools/importer/materialize_timeline_assets.py --workspace /tmp/kon-export --timeline data/slices/kon-helper.timeline.json --combat-model data/actions/kon-helper.json --output-dir godot/generated/helpers/kon
godot --headless --path godot -s res://tests/kon_helper_smoke.gd
```

共用 XG_fzcc/XG_fzbs 按前述 main.swf 元件流程导入 sprite 379/393，执行
`compile_hit_receive.py` 编译其末帧 unloadMovie；不在运行时猜回收时间。

## 重建选地图与全部地图

`tools/importer/build_stage_catalog.py --workspace /tmp/main-pinned` 导入 10 张地图及其音乐清单。
`uv run tools/importer/build_map_selection.py --workspace /tmp/main-pinned --temporary /tmp/map-selection-build --ffdec-jar /tmp/ffdec-26.2.1/ffdec-cli.jar` 重建原版选图素材（脚本内固定 Pillow 依赖）。
临时 SWF/XML 不进入发布物。原版探针与验证命令见[选图记录](../evidence/content/map-selection/README.md)。
