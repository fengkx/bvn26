# 主机权威联机实验

本改动与 G0 插桩放在同一个 Draft PR #285。它增加可玩的实验路径，保留原回滚路径；不代表 G0、弱机验收、真实双机性能或原版一致性通过。

## 使用与边界

2026-11-13 用户批准的新大厅默认使用主机权威；回滚保留在「房间设置」，只允许空房切换。双方分别进入现有角色／援助界面选择后返回大厅；房主确认地图，双方准备后由房主点击开始。固定鸣人／一护／现世的首版限制已移除。实验性质和准入门槛不变，详见[大厅验证记录](../evidence/online/lobby-menu-2026-11-13/README.md)。

实验模式按 30 Hz 采样输入，客端默认零缓冲。房主、玩家槽位、SDP offerer 与本局主机分别处理：房主和 offerer 仍为槽 0，主机可为槽 0 或槽 1。开局选定后不迁移；没有排名、防作弊、重协商恢复、填充包或 60 Hz 输入。主动暂停入口关闭；断流、后台或状态无进展触发安全暂停。

房间兼容指纹仍要求相同协议、构建和内容。`build_online_manifest.py` 将新增根目录 GDScript 和服务端协议加入构建指纹；没有混版本静默回退。

## 启动、输入与结算

1. 建立 reliable、input、state 三通道。后两者 unordered / maxRetransmits=0；原回滚仅使用前两条。
2. 每端在独立临时对战中用固定种子 727、本局所选双方及探测规则预热 120 tick，再测量 120 tick。测量包含 `Battle.advance()` 内同步执行的单次模拟及 materialize（probe 不注册 rollback owner，因此 `_render_frame` 不延迟物化；不含后续引擎 draw/GPU），记录 p95、超过 100 ms 的间隔及可见性。探测场景销毁后重新创建正式场景，不复用 RNG、计时器或输入状态。
3. 双方交换探测结果并独立计算：无有效完整前台样本者不参与；p95 相差严格超过较大值的 15% 时选较低者，否则比较长停顿次数，再平局选 P1。双方可靠确认，再向房间提交一致的 `authority_ack`。
4. 主机创建正式模拟器；客端在任何子节点 `_ready` 前进入纯展示模式，移除模拟子树。客端展示器就绪后可靠通知主机；主机发送初始展示包，最多每秒重试一次，客端校验并实际应用后确认。初态哈希绑定模式、epoch、主机、schema、setup revision、种子、规则、内容/构建和实际展示负载；然后复用 loaded/start_ack 屏障。
5. 客端发送完整 held 输入及序号；主机 FIFO 最多 4 项，每 tick 最多消费一项。缺号短等 34 ms；溢出保留最新完整样本，不 OR 按键；250 ms 没有新序号则中性化。重复旧包不会刷新输入新鲜度，冲突重复会拒绝。状态带已消费输入序号。可靠心跳同时携带单调 ping 序号，回显后按发送方单调时钟记录最近 300 个应用 RTT 样本（含调度和 reliable 阻塞），不参与选主加权。
6. 每轮接收只应用最新状态；主机是唯一推进模拟、源计时器和随机数的端。状态传输用对象禁用的 `var_to_bytes` / `bytes_to_var`，必要时 DEFLATE；单包 16 KiB、解压 256 KiB，类型、深度、数量、资源和层级均受限。超限拒绝，不分块、不发 delta、不传几何。传输队列上限为两份最大包字节数，应用层仅保留最新待发状态。客端每次 drain 应用最新状态后可靠确认，主端常规发送窗口为两份未确认状态；模拟仍为 30 Hz，窗口满时丢弃旧的未发展示状态。若整窗不可靠包丢失，只有客端最近 250 ms 内仍有可靠心跳，才允许每秒一份恢复探测，保留第三份包的接收空间；不加大原有缓冲或 wire 上限。
7. 约 1 秒无输入、心跳或状态进展，或任一端后台时冻结主机。客端确认当前冻结展示状态后，双方前台且输入/心跳恢复才继续；清空旧输入。只恢复同一连接，10 秒无恢复即无胜者终止。
8. 主机声明源 KO/超时终态；客端收到并应用该展示包后可靠回执，双方提交同一结果。服务端记录 `host-declared/guest-received`，不称「双方模拟哈希一致」。继续使用现有结果屏障与返回大厅流程。

## 展示与声音

`authority_projection.gd` 的 owners 是展示输入白名单：世界/相机祖先变换、时间轴资源索引和播放头、颜色/滤镜状态、局部偏移、显隐、HP/trail/警告/win/countdown、能量/援助 HUD、闪屏、KO/timeout、开场和冻结残影。连击显示按现有在线策略隐藏。

`authority_timeline.gd` 只渲染，不运行源脚本或自主播放。递归 clip 记录用 depth/symbol/placement-frame 重新绑定本地编译 placement 字典；调用现有 `materialize_display()`。没有传顶点、UV、纹理、Rect2、碰撞框或 shadow bitmap 尺寸。残影从冻结时间轴输入在本地调用同一 bounds/viewport 生成函数，淡出只应用主机 alpha。未注册显示资源/几何直接拒绝。

声音在现有 TimelinePreview、HitEffectRuntime、IntroClip、StageSound 接受播放的位置记录。资源使用本地白名单索引；事件 ID 每个 epoch 重新建立，短事件保留 8 tick，事件集最多 64 项，客端去重，跳过过期声音；active 列表同步停止与循环 BGM。客端不重跑帧脚本来猜声音。浏览器原有音量/静音/解锁外壳继续生效。

## 源优先范围说明

这里改变网络和展示所有权，不新增角色行为，不改变命中、招式、PlaceObject 生命周期或标签退出规则。

- 每帧脚本和暂停/计时器：主机仍执行 `Main._advance_fight`、现有 Battle adapter 和 OnlineTimerAuthority；source clock 的在线策略未被称作 Flash 回调相位证明。
- PlaceObject/MOVE：从已编译的 `timeline.json` 和现有 retained clip 状态投影；本地 placement 重新绑定，未造实例变量继承规则。
- 标签退出：客端不判断标签退出；只应用主机播放头，主机继续沿现有 goto/stop/fallthrough 行为。
- 不变量：测试对比现有主机与客端的渲染结构、冻结残影及模拟计数，不把新的网络假设当原版机制。
- 原版同输入对照：本 PR 没有新 live/Flash/FDB/debugger 捕获。已有原版未证明项保留，所有 admission/proof flags 不变。

残影函数的提取保留现有 `getBounds`、twip 取整、BitmapData 大小、透明 viewport 和颜色偏移计算；仅允许纯展示时间轴复用。HUD 新字段只供纯展示节点使用，原模拟路径继续读取 fighter/countdown。

## 验证与交接

G0 固定工作负载、分段、独占计时和离线输入到对应提交基线见 [G0_INSTRUMENTATION.md](G0_INSTRUMENTATION.md)。frame-submit CPU 不是 GPU 完成或 time-to-photons；不可靠 GPU 数据记 UNKNOWN。

本次实际运行记录见 [实验验证记录](../evidence/online/host-authority-experiment/README.md)。弱机与两台真实机器的性能判断留待后续运行，不需要另拆实现 PR。不得据本机/headless 结果改写 G0 或生产准入状态。

自动检查入口：

- `godot/tests/authority_foundations_smoke.gd`：选主机边界、输入重排/重复/过期/溢出和实际二进制编码。
- `godot/tests/authority_probe_smoke.gd`：独立探测、120 个实测样本、正式场景重置。
- `godot/tests/authority_projection_smoke.gd`：330 帧中跳过 220 帧，渲染结构、冻结残影、恶意状态拒绝和 guest tick=0。
- `godot/tests/authority_pair_smoke.gd`：两种主机槽位、输入、同连接安全恢复、源 KO 到结果服务屏障；状态经过真实编码器，网络/房间为夹具。
- `services/matchmaking/test/server.test.mjs`：真实本地 Worker 的模式/内容/选主机/loaded/start/result/回退边界。
- `godot/tests/authority_browser_smoke.gd` + `tools/test_authority_browser.mjs`：仅在独立导出中替换入口，启动本地 Worker（8787）和两个独立 Chromium 调试端点；脚本自动操作同一房间 UI 并报告主机 tick 与客端收到状态数。不是性能门槛。

浏览器 smoke 必须使用独立测试配置，不能连接个人浏览器。网络环境若要求回环测试，Chromium 的 [`allow-loopback-in-peer-connection`](https://chromium.googlesource.com/chromium/src/+/lkgr/content/public/common/content_switches.cc) 仅用于本地测试进程；记录所用选项，不把它当真实局域网/互联网验收。

### 复现命令

在独立暂存项目（例如 `$TMPDIR/bvn-authority-check`，复制 `godot/`，不复制 `.godot`）导入资源后执行：

```sh
python3 tools/run_godot_checked.py --log "$TMPDIR/authority-pair.log" -- \
  "$GODOT" --headless --path "$AUTHORITY_STAGE" \
  --log-file "$TMPDIR/authority-engine.log" --script res://tests/authority_pair_smoke.gd
```

其他原生 smoke 用同样命令替换 script。导出浏览器 smoke 时，仅将暂存项目的 `run/main_scene` 改成 `res://tests/authority_browser_smoke.tscn`，使用匹配的 Godot 4.7.2 Web release 模板和原有 Web shell。不要改正式入口或部署此测试包。HTTP 服务必须支持正常 Web 导出的响应头；例如本地 `python3 -m http.server 8078 --directory "$AUTHORITY_WEB"`。

```sh
# 两个独立测试浏览器已分别监听 9334/9335；真实 Worker 本地监听 8787。
node tools/test_authority_browser.mjs http://127.0.0.1:9334 http://127.0.0.1:9335 \
  http://127.0.0.1:8078/index.html "$TMPDIR/authority-pair-browser.json"
# 同机单页面展示验证，不建立 WebRTC，不替代上一项。
node tools/test_authority_browser.mjs http://127.0.0.1:9334 http://127.0.0.1:9335 \
  'http://127.0.0.1:8078/index.html?offline=1' "$TMPDIR/authority-display-browser.json"
cd services/matchmaking
XDG_CONFIG_HOME="$TMPDIR/bvn-authority-wrangler" npm test
npm run format:check
```

纯展示 smoke 固定种子 727、双方初始气量 300、900 tick；输入在 fixture 中固定，包含普通攻击、援助与必杀。每三份状态仅应用一份，验证跳帧后的绝对展示输入；这不是在线延迟或吞吐测试。当前客端每次状态重建展示节点（资源模板缓存复用），尚无弱机成本结论。

兼容清单须按 `tools/build_web.sh` 的导入后步骤生成，包含 Godot 生成的 `.import` 设置。本次角色/地图内容源文件未改动，菜单字体用已有生成器补齐新文案；独立导入会生成新的 UID，因此整个发布包必须共用同一份导入后的清单。仓库历史生成清单不代表本次发布清单，不提交本机缓存 UID 造成的无关清单重写。

### 2026-11-13 本机候选枚举对照

后续诊断与修复见 [本机连通验证](../evidence/online/host-authority-connectivity/README.md)。原 2026-11-12 失败记录保持原义。仅当默认本地 ICE 测试因候选枚举/虚拟接口环境失败时，可在**独立临时测试浏览器**使用：

```sh
BVN_LOCAL_ICE_PERMISSION=1 node tools/test_authority_browser.mjs \
  http://127.0.0.1:9345 http://127.0.0.1:9348 \
  http://127.0.0.1:8078/index.html "$TMPDIR/authority-local-ice.json"
```

测试浏览器使用 `--headless=new --disable-features=WebRtcHideLocalIpsWithMdns --allow-loopback-in-peer-connection`，独立 `--user-data-dir` 和调试端口，并关闭后台计时器节流。此次一个浏览器另带 `--force-webrtc-ip-handling-policy=default`；该选项单独测试没有解决问题。runner 在 CDP 会话内为此 loopback HTTP origin 授予 `audioCapture`，让 Chromium 枚举更多候选；不调用媒体采集。它拒绝对非回环地址使用该覆盖，关闭会话撤销。不要连接个人浏览器或把该做法加入生产页面。

不使用覆盖时照常运行原命令；报告中的 `localIcePermissionOverride` 明确区分两种条件。通过需要双方真实 selected ICE pair、三通道 open、主端帧推进、客端 state 接收且模拟为零，以及客端默认 D 键输入经主机返回为位置变化。均不替代真实 LAN/Internet、TURN、两台机器或弱机验收。
