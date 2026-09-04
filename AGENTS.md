# 开发接手约定

适用于本目录的开发工作。先读 README.md、SPEC.md、IMPLEMENTATION_PLAN.md、docs/STATUS.md 和 plan/tasks.json。

- 目标是普通 BVN 2.6 原生 Godot Web 移植。生产运行不得依赖 Flash、AVM、AS2 解释器或 Ruffle。
- game/ 和 scripts/ 是锁定分析输入。保留原文件、大小写和哈希；插桩、转换和试验写入单独工作目录。不要把社长改同名文件覆盖进来。
- 当前没有 Godot 工程、完整资产转换器、原版 golden 轨迹或已通过验证的角色。工具和文档存在不等于游戏完成。
- 按任务依赖推进。完成一个任务时更新状态、产物路径、验证证据和实际投入；阻塞时说明具体缺口，不凭主观判断将任务置为完成。
- 反编译片段保留原路径。定位规则需同时检查脚本、时间轴和运行观测。未知帧数、判定框和调度顺序不得猜测填充。
- Schema 是接口约束，格式示例是 partial/synthetic。生产内容必须经语义校验和行为验收，不能以 schema 校验代替。
- 文档中的拟定更新顺序尚未确认。以 M0 记录的 ExecutionProfile 为依据，明确暂停、定时器、随机数和枚举顺序。
- 保留既有输入和随机 tape 作为比较依据；不要修改基准输出或放宽阈值掩盖差异。
- 修改工具或资料后运行 tools/verify.py、tools/check_handoff.py；契约变更运行 tools/validate_contracts.py。verify 的哈希覆盖原交付文件，合法变更应经差异核对后更新 manifest.file_sha256，不能跳过输入完整性检查。
- 新增 Godot 实现后按 docs/VALIDATION.md 执行与变更风险相称的检查。没有实际运行证据时保持待验证状态。
- 下载的工具、缓存、临时导出、运行日志和打包副本不加入正式源码目录。部署仅使用后续 dist/web/。
