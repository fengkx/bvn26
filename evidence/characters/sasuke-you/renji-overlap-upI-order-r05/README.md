# upI source callback order probe r05

本次 probe 只在临时 shadow build 中插入事件标记，未修改 `game/` 或
`scripts/`。插桩入口和原始路径保存在 `build_ai_geometry.py`，原始 Flash
日志和事件已压缩归档。

## 可复现输入与完整性

- run id: `sasuke-you-renji-up-special-overlap-start20-original-order-r05`
- 固定输入：佐助 + You 对恋次 + Kon，upI，300 ticks；与
  `renji-overlap-upI-r01` 使用同一 fixture / tape。
- `compare.json` 按 `fight_tick >= 0` 分别比较 canonical 的 602 条
  `state` 和 602 条 `helper_state`：两类均 `602/602` 且逐 tick 相同。
  startup 额外插桩行数为 544（canonical 为 542），这是插桩事件造成的
  观测差异，不纳入战斗状态比较。

## 精确事件链

全局 `sequence` 顺序（见 `sequence-chain.json`）：

1. `seq 3545`, display 516 / fight 62：observer 记录 P2 root frame
   `626`。
2. `seq 3547`：Renji `mc.bdmn` 的 frame 626
   `PlaceObject2_2_28` callback 进入，局部 frame 为 `1`。
3. `seq 3548`：You `p1fz.atm1` frame 48 callback 进入。
4. `seq 3549`：You callback 查询时，P2 `mc._currentframe=969`；
   `_geomTarget` 的 `String` 和 `typeof` 都为 `undefined`，target bounds
   为 undefined，`hitTest` 为 `false`。
5. `seq 3564–3565`：Renji 外层 BODY wrapper 已在 frame `969` 进入/退出。
6. 下一 display 517 / fight 63 的 observer 在 `seq 3570` 记录 root
   frame `969`，You callback 随后看到 root frame `970`，target 仍无有效
   bounds 且 hit 为 false。

frame 626 的 `DoAction` 标记在前一 display tick：`seq 3539–3540`，只
记录该 action 的进入/退出；反编译源内容是 `_root.shine(4218928);`，没有
`goto`。因此本次 sequence 直接证明：frame 626 的 `bdmn` receiver
callback 发生在 You callback 之前，而 You callback 看到的 root 已是
969。`beida()` 后没有出现对应 `renji_receiver_exit` 标记；这只记录为
插桩观测事实，不据此推断 AS2 控制转移细节。

## SOURCE_FIRST 五问记录

1. 每帧脚本：frame 626 的 bdmn clip action 调 `beida()`；frame 626
   DoAction 只调 `shine`；frame 969 DoAction 为 `play()`；frame 970
   DoAction 为 `onBeHit()`；frame 971/972 分别有后续 beidax/beida
   clip action（原始路径见 `build.json`）。
2. PlaceObject/MOVE：源 timeline 在 968 保留 depth 28 的旧对象，969
   移除 depth 28，971 放置新对象，972 放置 `bdmn` depth 26；详见
   `data/slices/Renji-base.timeline.json`。
3. 离开标签：`beida()` 成功后由 `_parent.gotoAndPlay(_loc2_.htype)`
   选择受击标签；本 probe 不把标签或调度顺序改写成猜测。
4. 原版不变量：frame 626 receiver callback 位于 You callback 之前；
   You 查询时 root 已为 969，target 无有效 bounds，hit 为 false。
5. 同输入对照：r05 与 canonical 的 602 条 fighter、602 条 helper
   fight_tick 状态逐项相同；Godot/native 的 63 命中差异仍需由生产
   agent 依据此源证据处理。

