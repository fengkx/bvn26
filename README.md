# 死神 VS 火影 2.6 · Godot Web 移植交接包

版本 1.0 · 2026-09-03

目标是把普通 2.6 移植为在桌面浏览器运行的原生 Godot 游戏。包内已有锁定资源、反编译脚本、技术规格、实施计划、数据接口和验收办法，并已开始实现可运行的鸣人/一护/现世开发切片；它仍不是完整或逐帧验收通过的网页成品。

## 建议阅读顺序

1. [SPEC.md](SPEC.md)：范围、12 项功能要求、8 项技术要求和一比一验收边界。
2. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)：M0–M7 实施顺序、阶段门槛与估算方法。
3. [当前状态](docs/STATUS.md)：已完成事项、风险和下一步。
4. [架构](docs/ARCHITECTURE.md) → [逆向手册](docs/REVERSE_ENGINEERING.md) → [源优先闸门](docs/SOURCE_FIRST.md) → [数据契约](docs/DATA_CONTRACTS.md)。
5. [验收计划](docs/VALIDATION.md)与[操作手册](docs/OPERATIONS.md)：如何取得对照证据、使用工具和准备后续 Web 导出。

## 包内内容

| 路径 | 内容与状态 |
|---|---|
| `game/` | 主 SWF、35 个角色 SWF、26 个援助 SWF、13 个外部 MP3，共 75 个锁定输入文件 |
| `scripts/` | 62 个 JSON bundle，包含 8,853 个原路径与脚本片段，用于分析和重写 |
| [manifest.json](manifest.json) | 版本、来源、哈希、74 个外部依赖、64 条人物配置、10 条地图配置及仓库对照 |
| [基准审计](docs/BASELINE_AUDIT.md) | 上传入口完整性、补齐过程、GitHub 改版差异与精简依据 |
| `spec/schemas/` | Asset、Fighter、Action、Replay、Trace 五类 JSON Schema |
| `spec/examples/` | 五份可校验格式示例；部分来自静态提取，部分为合成格式，均非完整运行数据 |
| [任务表](plan/tasks.json) | 含依赖、产物、验收条件和状态的实施任务；未来产物路径不代表文件已存在 |
| [内容覆盖表](plan/coverage.json) | 64 条人物配置与 10 条地图的逐项检查起点；运行验证全部未开始 |
| `tools/` | 资源校验、SWF 结构检查、脚本查阅、契约与交接包检查工具 |
| [来源说明](docs/SOURCES.md) | 来源链接、版本依据和证据限制 |
| [本次校验记录](docs/PACKAGE_CHECKS.md) | 已执行的资料验证与明确未验证的运行内容 |
| [AGENTS.md](AGENTS.md) | 后续开发者或编码助手的接手约束；实现机制前必读 [源优先闸门](docs/SOURCE_FIRST.md) |

人物配置数包含形态和援助，不等于可选角色数。原始 SWF 和脚本仅用于开发分析，未来发布物必须不包含 Flash/AS2/AVM/Ruffle 运行依赖。

## 基准决定

`game/main.swf` 与上传的 `166.swf` 字节相同：普通 V 2.6，600×400，30 FPS。

SHA-256：`707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`

Brx86/BVN2.6 仓库为 29 FPS 的“社长改”，不能整套替换普通版。本包只采用其中 25 个与当前普通版依赖完全相同的资源，49 个不同文件保留匹配本入口的版本。结构和依赖已核对；完整原版运行、历史作者原包身份和 Godot 行为一致性仍需分别验证。详情见基准审计。

未保留重复压缩包、改版完整副本、Flask/Ruffle 网页外壳、重复导出的散图/声音、缓存和运行日志。可重建的导出物后续由工具产生。

## 开始使用

在解压后的 `bvn26/` 中运行，Python ≥3.10：

```bash
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/read_script.py scripts/fighter/minren.json --path frame_1/DoAction.as
python3 tools/read_script.py scripts/main.json --search loadClip --limit 3
```

前两项仅验证资料和交接关系，不会启动游戏。检查 JSON Schema 与格式示例：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/validate_contracts.py
```

Windows 对应使用 `.venv\Scripts\python.exe`。资源校验与脚本查阅只依赖 Python 标准库；契约校验依赖固定版本的 `jsonschema`。Godot、导出模板、Java、JPEXS 和原版参照播放器不随包分发，见操作手册。

## 接下来做什么

从 `M0-01` 建立 Godot 最小 Web 工程、`M0-02` 建立原版参照环境开始。先校准调度和导入，再完成鸣人/一护基础形态的一场完整对战，随后扩展机制和全内容。保持未验证项可见，不把资料完整、可启动、可战斗和一比一完成混为同一状态。
