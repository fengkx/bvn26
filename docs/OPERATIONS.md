# 使用、验证与未来构建

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

`export_swf_xml.py` 会拒绝非 JPEXS 26.2.1 或非预期 XML 版本。中间数据只保留
可追溯的源帧、原矩阵和事件；JPEG3 使用 JPEXS 的 PNG 导出合并原 alpha，嵌套
Sprite 保留首帧 display list。遇到不支持的时间轴状态会直接失败。

## 文档导航

先读根 [README](../README.md)、[SPEC](../SPEC.md)、[实施计划](../IMPLEMENTATION_PLAN.md) 与 [STATUS](STATUS.md)。接口见 [DATA_CONTRACTS](DATA_CONTRACTS.md)，正确性见 [VALIDATION](VALIDATION.md)，来源见 [SOURCES](SOURCES.md)。

## Godot 工程构建

`godot/` 已固定为 Godot 4.7.2-stable、GDScript、Compatibility 和单线程 Web
导出。当前场景是鸣人/一护源时间轴预览，不是完整战斗。

```bash
godot --headless --path godot --editor --import
godot --headless --path godot --export-release Web ../dist/web/index.html
```

导入器目前覆盖首个角色切片、现世静态视觉首帧和外部位图。嵌套动画、平台碰撞、声音、
滤镜和生产数据编译器仍未完成；不得把当前预览冒充完成的转换器或战斗实现。

## Web 发布要求

最终 `dist/web/` 只包含 Godot 的 HTML/JS/WASM/资源包和转码资源。WebAssembly 本身允许使用；禁止的是执行 Flash/AS2 的运行时。不得混入源 `game/`、`scripts/`、开发追踪、源码映射、旧 Ruffle 文件或游戏平台桥接。

提供正确 MIME、压缩传输、版本化资源和一致的缓存策略。HTML 更新时不能混用旧资源清单。部署使用 HTTPS；本地验证可使用 localhost。单线程是默认方案，如启用线程需重新评估跨源隔离与部署条件，不能悄悄改导出配置。

用户点击开始后解锁声音；请求全屏置于用户输入事件中。加载失败需给出重试入口。浏览器存储不可用时保留内存设置并继续游戏。所有这些都必须实际测试，而不能只靠静态配置判断可用。

首发测试记录 Chromium、Firefox 和 Safari 的完整版本、OS、DPI 与设备。手机触控不属于当前首发范围，不能以桌面通过代替移动端性能承诺。

## 后续资料维护

`game/` 是锁定基准；修改之前先创建新基准版本并重新做来源与行为审计。`scripts/` 是关联这些 SWF 的导出，不能与另一批 SWF 混用。任何文件改变后更新清单并运行校验。清单可防止意外变化，但不是历史原作者签名。

任务实际完成后记录到 `plan/tasks.json`，内容验证记录到 `plan/coverage.json`。真实录屏/轨迹、性能报告等放到未来的 `evidence/`；不要在该目录放合成示例并把它们作为通过证明。
