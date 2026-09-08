# 开发接手约定

适用于本目录的开发工作。先读 README.md、SPEC.md、IMPLEMENTATION_PLAN.md、docs/STATUS.md、docs/SOURCE_FIRST.md、docs/HIT_RECEIVE_SOP.md 和 plan/tasks.json。

- 目标是普通 BVN 2.6 原生 Godot Web 移植。生产运行不得依赖 Flash、AVM、AS2 解释器或 Ruffle。
- game/ 和 scripts/ 是锁定分析输入。保留原文件、大小写和哈希；插桩、转换和试验写入单独工作目录。不要把社长改同名文件覆盖进来。
- 当前已有 Godot Web 开发切片和部分资产转换器；完整转换器、原版固定对战 golden 轨迹和逐项验收通过的角色仍缺。以 docs/STATUS.md 与 plan/tasks.json 的证据为准，工具和文档存在不等于游戏完成。
- 按任务依赖推进。完成一个任务时更新状态、产物路径、验证证据和实际投入；阻塞时说明具体缺口，不凭主观判断将任务置为完成。
- 反编译片段保留原路径。定位规则需同时检查脚本、时间轴和运行观测。未知帧数、判定框和调度顺序不得猜测填充。
- Schema 是接口约束，格式示例是 partial/synthetic。生产内容必须经语义校验和行为验收，不能以 schema 校验代替。
- 文档中的拟定更新顺序尚未确认。以 M0 记录的 ExecutionProfile 为依据，明确暂停、定时器、随机数和枚举顺序。
- 保留既有输入和随机 tape 作为比较依据；不要修改基准输出或放宽阈值掩盖差异。
- 修改工具或资料后运行 tools/verify.py、tools/check_handoff.py；契约变更运行 tools/validate_contracts.py。verify 的哈希覆盖原交付文件，合法变更应经差异核对后更新 manifest.file_sha256，不能跳过输入完整性检查。
- 新增 Godot 实现后按 docs/VALIDATION.md 执行与变更风险相称的检查。没有实际运行证据时保持待验证状态。
- 下载的工具、缓存、临时导出、运行日志和打包副本不加入正式源码目录。部署仅使用后续 dist/web/。
- 目标是一比一还原原版 Flash 体验。实现或修改任何机制前必须按 docs/SOURCE_FIRST.md 答完五问（每帧脚本、PlaceObject/MOVE、离开标签方式、原版不变量、原版同输入对照）。答不全不得改运行时，也不得把任务标完成。
- 标签 end_frame 不是回站立。无 goto/stop 的标签要编 timeline_fallthroughs，播放头继续走。新 PlaceObject 不继承实例变量；enterFrame 从放置的下一根帧开始。
- 新行为优先加编译规则，禁止按角色在 GDScript 里猜补位移、高度或演出。测试只锁源里能指出的不变量，不得把实现假设写进回归再去凑。
- 重击、破防、连击次数、命中火花、防御挡住和必杀黑底/立绘横幅必须按 docs/HIT_RECEIVE_SOP.md 的步骤 A→E 落地：先锁 35 角色共用链和援助无链，再按形态编译 gjlN 与 showFace 标签，运行时只解释编译字段。不得按角色猜重击或手贴大招背景，也不得把第一下显示成连击。大招特效盖住对手却不受击时，先核 Flash MATRIX（`rotateSkew0/1` 不得对调）和 `*atm` 的 PlaceObject 寿命，禁止按角色放大框或写“必中”补丁。下+I 一类 `_parent._x = opponent._x` 是容器闪现（`body_warps`），只闪 X 时不同水平面不中，不得写成走路或按角色补高度。面向/`bdmn._width` 编进同一字段的分支，不得把其他形态 Sprite 混进当前切片。击中后带着走来自 `beidax` 非击飞不加重力，不是抓取，也不得给「被打」加 `zhongli`。最后击飞对手的是 `cbsatm`，不是攻击方 942 自跳。手测大招仍漏时先对 `bsd`/`cbsd` 的 `stopMc(对手)` 和该帧 `*atm` AABB，禁止放大框或写必中；没有步骤 E 轨迹不得称一比一。
