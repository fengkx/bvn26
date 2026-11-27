# 开发者指南

本文收纳《死神 vs 火影 2.6》原生 Godot Web 复刻工程的技术基准、环境要求、本地构建与校验命令、仓库结构以及完整文档索引。面向玩家的简介与上手说明见根 [README.md](../README.md)。

---

## 1. 基准决定与零 Flash 原则

- **锁定基准**：普通《死神 vs 火影 2.6》，入口文件 `game/main.swf` 与原上传 `166.swf` 逐字节一致（600×400，30 FPS）。
  - SHA-256：`707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`
- **不混用改版**：`Brx86/BVN2.6` 仓库为 29 FPS 的“社长改”，不能整套替换普通版。本仓库仅采用其中 25 个与当前普通版依赖逐字节相同的资源，其余 49 个不同文件保留匹配本入口的版本；详见 [基准审计](BASELINE_AUDIT.md)。
- **零 Flash / Ruffle 运行时**：`game/`（75 个锁定输入文件）与 `scripts/`（62 个脚本包，含 8,853 条保留原路径的反编译片段）仅用于开发期分析与编译，**绝不进入 `dist/web/` 发布包**。仓库亦不保留重复压缩包、改版完整副本、旧 Flask/Ruffle 网页外壳、重复导出的散图/声音、缓存和运行日志。
- **固定技术栈**：Godot **4.7.2-stable**、GDScript、`gl_compatibility` 渲染、单线程 Web 导出与 30 Hz 固定逻辑时钟。
- **源优先（Source-First）方法**：实现或修改任何战斗机制前，必须按 [源优先闸门](SOURCE_FIRST.md) 核对每帧脚本、`PlaceObject`/`MOVE` 生命周期、离开标签方式、原版不变量与同输入对照，优先扩充 `tools/importer/` 的通用编译规则，不在运行时按角色猜测参数。受击链、破防、连击与必杀演出遵循 [受击链落地 SOP](HIT_RECEIVE_SOP.md)。

---

## 2. 当前验收边界

- 全部六项原版证明与发布准入标志（`production_admitted`、`native_parity_proven`、`oracle_accepted`、`certified_global_tick`、`os_input_join_proven`、`native_initialization_complete`）目前均保持 **`false`**。
- 40 个可选人物/形态与 26 个辅助已完成多轮原版 Flash 与原生 Godot 同输入状态流对照（见 [全角色首轮实测](../evidence/characters/roster-live-2026-11-18/README.md) 与 [辅助全目录对照](../evidence/helpers/remaining-roster/README.md)），但完整音画等价、Firefox/Safari 跨浏览器实测、全模式闭环、有头退出资源清理与完整公网联机实战门禁仍待完成。
- 最新状态、里程碑进度与覆盖矩阵以 [STATUS.md](STATUS.md)、[plan/tasks.json](../plan/tasks.json) 和 [plan/coverage.json](../plan/coverage.json) 为准。

---

## 3. 开发环境要求

- **Python ≥ 3.10**：资源完整性校验、反编译脚本查阅、导入与测试工具（核心校验仅依赖标准库；契约校验依赖 `requirements-dev.txt` 中的固定版本 `jsonschema`）。
- **Godot 4.7.2-stable** 及同版本单线程 Web 导出模板：本地运行工程与导出 `dist/web/`（未随仓库分发）。
- **Node 24.18.0**（可选）：本地运行与测试联机房间服务 `services/matchmaking/`。
- **Java ≥ 17 + JPEXS 26.2.1**（可选）：仅在需要重新从 `game/*.swf` 提取 XML 与素材时使用；原版参照播放器与工具链均不随仓库分发，配置与导入步骤详见 [操作手册](OPERATIONS.md)。

---

## 4. 常用命令

### 4.1 资料完整性校验与脚本查阅

以下命令仅验证锁定资源、脚本关联与交接文档链接，不会启动游戏（也可通过 `just verify` / `just validate-contracts` 运行）：

```bash
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/read_script.py scripts/fighter/minren.json --path frame_1/DoAction.as
python3 tools/read_script.py scripts/main.json --search loadClip --limit 3
```

校验 JSON Schema 与格式示例（Windows 将 `.venv/bin/python` 替换为 `.venv\Scripts\python.exe`）：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/validate_contracts.py
```

> 修改受 `manifest.json` 覆盖的文档或资料后，请经差异核对更新 `file_sha256`，再运行 `tools/verify.py` 与 `tools/check_handoff.py`。

### 4.2 本地构建与预览 Godot Web 版

安装 Godot `4.7.2-stable` 及同版本单线程 Web 导出模板后（Linux x86_64 / Vercel CI 上脚本会自动临时拉取工具链）：

```bash
./tools/build_web.sh
python3 -m http.server 8000 --directory dist/web
```

随后在桌面浏览器访问 `http://127.0.0.1:8000/`。常用任务快捷入口见 [justfile](../justfile)（如 `just export-web`、`just export-web-clean`、`just list-godot-tests`）。

Vercel 会缓存已导入的素材和按需下载的角色包。本地可用 `BVN_WEB_CACHE_DIR=/tmp/bvn-web-cache ./tools/build_web.sh` 连续构建。日志中的 `Godot fighter pack cache` 显示复用和重新导出的角色包数量，`WEB_BUILD_TIME` 显示各阶段耗时。角色及其形态、导入结果、引擎或导出配置变化时，相应角色包会重新生成。

### 4.3 本地运行联机房间服务（可选）

房间服务为独立的 TypeScript Cloudflare Worker + SQLite Durable Objects，仅处理房间租约、建房/入房、阵容与地图协调及 WebRTC 信令，不模拟战斗或转发操作帧：

```bash
cd services/matchmaking
npm ci
npm run dev          # 默认监听 http://127.0.0.1:8787
npm test             # TypeScript 类型检查、workerd 契约与本地 Wrangler 冒烟测试
npm run test:restart # 重启 workerd 进程验证 SQLite 持久化
```

本地联调与客户端配置详见 [services/matchmaking/README.md](../services/matchmaking/README.md) 与 [联机客户端说明](online-multiplayer/CLIENT_IMPLEMENTATION.md)。

---

## 5. 仓库结构

| 路径 | 内容与说明 |
| --- | --- |
| `godot/` | Godot 4.7.2 原生工程、战斗/AI/联机运行时代码、Web 外壳与已编译资源（`godot/generated/`） |
| `services/matchmaking/` | 独立的 Cloudflare Worker + Durable Objects 房间协调与 WebRTC 信令服务 |
| `tools/` | 资源完整性与交接校验、SWF 结构检查、脚本查阅、时间轴与动作编译器、Web 构建脚本（`build_web.sh`）及测试套件 |
| `game/` | **锁定分析输入**：主 SWF、35 个角色 SWF、26 个援助 SWF 与 13 个外部 MP3（共 75 个文件，不进入发布包） |
| `scripts/` | **锁定分析输入**：62 个 JSON bundle，保留 8,853 条原路径与反编译脚本片段 |
| `data/` | 由导入与编译工具生成的中间切片、时间轴几何与动作模型数据 |
| `plan/` | [任务表](../plan/tasks.json)（M0–M7 依赖、产物与验收门槛）与 [内容覆盖表](../plan/coverage.json)（64 条人物配置、10 张地图） |
| `spec/` | `spec/schemas/`（Asset/Fighter/Action/Replay/Trace 等 JSON Schema）与 `spec/examples/`（静态/合成格式示例，非完整运行数据） |
| `evidence/` | 原版 Flash 与原生 Godot / 浏览器对照轨迹、截图与专项检查证据 |
| `docs/` | 技术架构、逆向手册、源优先与受击 SOP、AI 规格、联机设计与状态台账 |
| [manifest.json](../manifest.json) | 版本、来源、SHA-256 清单、74 个外部依赖、64 条人物配置、10 条地图配置与仓库对照 |
| [vercel.json](../vercel.json) / [justfile](../justfile) | Web 构建部署配置与常用本地命令 |

> 注：人物配置数（64）包含基础角色、变身形态与援助，不等于可选角色卡片数（40）。

---

## 6. 建议阅读顺序与文档索引

1. [AGENTS.md](../AGENTS.md) — 接手与贡献约束（输入锁定、源优先、受击 SOP、字体覆盖与哈希校验要求）
2. [SPEC.md](../SPEC.md) — 范围、12 项功能要求、8 项技术要求与 1:1 验收边界
3. [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — M0–M7 实施顺序、阶段门槛与估算方法
4. [STATUS.md](STATUS.md) — 当前已完成项、风险、缺陷与下一步
5. 核心机制与数据：
   - [架构设计（ARCHITECTURE.md）](ARCHITECTURE.md)
   - [逆向手册（REVERSE_ENGINEERING.md）](REVERSE_ENGINEERING.md)
   - [源优先闸门（SOURCE_FIRST.md）](SOURCE_FIRST.md)
   - [受击链落地 SOP（HIT_RECEIVE_SOP.md）](HIT_RECEIVE_SOP.md)
   - [数据契约（DATA_CONTRACTS.md）](DATA_CONTRACTS.md)
   - [电脑 AI 复刻规格（AI_SPEC.md）](AI_SPEC.md)
6. 验收、运行与溯源：
   - [角色还原与缺陷验收 SOP（CHARACTER_PARITY_SOP.md）](CHARACTER_PARITY_SOP.md)
   - [验收计划（VALIDATION.md）](VALIDATION.md)
   - [回归证据索引（REGRESSION_INDEX.md）](REGRESSION_INDEX.md)
   - [操作与导入手册（OPERATIONS.md）](OPERATIONS.md)
   - [基准审计（BASELINE_AUDIT.md）](BASELINE_AUDIT.md)
   - [来源说明（SOURCES.md）](SOURCES.md)
   - [资料校验记录（PACKAGE_CHECKS.md）](PACKAGE_CHECKS.md)
7. 实验性联机：
   - [联机设计总览（online-multiplayer/README.md）](online-multiplayer/README.md)
   - [联机客户端说明（online-multiplayer/CLIENT_IMPLEMENTATION.md）](online-multiplayer/CLIENT_IMPLEMENTATION.md)
   - [联机房间服务说明（services/matchmaking/README.md）](../services/matchmaking/README.md)
