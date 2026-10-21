# Pain 上 I：通用视觉与摄像机精度修复

基线：`875506cf`；最终实现变基到 `3a3bafd8`（PR #45）后重新验证。
原始 `game/`、`scripts/` 未修改。运行时没有 Pain／Sprite 405 专用分支。

## 结果与前后对照

**原版上 I 没有二段伤害。** 源帧 772–780 只有一个 `sbsatm`；20／50／150 px 案例均在观察 tick 41（源帧 773）命中一次，250 伤害，`sbstm=0`、击飞冲量 X/Y 均 20。300／500 px 空挥，完整恢复后也无第二击。

| 项目 | 修复前 | 修复后与原生 Flash |
|---|---|---|
| 状态／命中 | 12 案例、7,224 状态已匹配 | 重新捕获并回放，仍全部精确匹配；没有改伤害、命中次数或受击参数 |
| 全局攻击矩形 | 214 中 179 个不同，最大 1 twip | 214/214 四边整数 twip 完全一致，无放宽阈值 |
| 上 I 的 Screen | 丢失，黑色区域遮住人物和背景 | 从 PlaceObject3 保留 mode 4；按剪辑层级合成真正 Screen |
| 子特效结束 | 命中后多重播 14 tick；空挥多重播 1 tick | 两案均到空白第 45 帧停止；105 个子帧观察全部匹配 |
| 主体恢复控制 | 空挥 74、命中 87 tick | 保持 74／87 tick，与原版相同 |

截图左侧为 Flash Player Debugger 32 的原生 `BitmapData.draw`，右侧为 Godot 生产绘制节点。统一 600×400、灰底、角色原点 (300,300)，隔离摄像机；不是 JPEXS 代替原生渲染，也不是完整对战窗口截图。

| 源帧 | 修复前 | 修复后 | RGB 平均绝对误差（0–255） |
|---|---|---|---|
| 772 | [before](before-772.png) | [after](after-772.png) | 7.513515 → 0.119981 |
| 780 | [before](before-780.png) | [after](after-780.png) | 3.022464 → 0.125332 |
| 800 | [before](before-800.png) | [after](after-800.png) | 2.375229 → 0.116229 |
| 816 | [before](before-816.png) | [after](after-816.png) | 12.161500 → 0.079844 |

772 的发黑与 816 的错误重播已消失；**图片不是逐像素零差异**。GPU 与 Flash 的 8-bit 舍入仍有 1 级色值差异，人物边缘也保留既有栅格化差异；完整数值见 [pixel-metrics.json](pixel-metrics.json)。Screen 原生小样中 128 灰叠 128 灰为 191，Godot 为 192；50% 父 alpha 原版 159、Godot 160。两个重叠子图仍只在父级合成一次，不能把每个子图分别 Screen／ADD。

视觉大小沿用源矩阵：特效 bitmap 442×268、placement scale=100%，wrapper Y=1.000701904296875。上 I 局部攻击矩形约 `(-220.65,-215.25,456.75,235.35)`；白光轮廓本来就不等于攻击框。没有放大／缩小攻击范围或逐图调 tint。

## 阶段与时长

30 Hz，输入 tick 10，tick 11 首次观察源帧 743。下表原版与修复后相同。

| 主体阶段 | 源帧 | 空挥 ticks | 命中 ticks |
|---|---|---:|---:|
| 起手 | 743–744 | 2 | 2 |
| 必杀冻结／展示 | 745–768 | 24 | 24 |
| 解冻及特效放置 | 769–771 | 3 | 3 |
| 唯一攻击框 | 772–780 | 9 | 22（含 13 tick hit-pause） |
| 后摇 | 781–816 | 36 | 36 |
| 动作开始→恢复控制 | 743→站立 | 74（tick 85） | 87（tick 98） |

从按键算为 75／88 tick。根层冲击图序列 772–791：20／33 tick；人物 Shape 197 在 771–810：40／53 tick。独立特效 Sprite 405 两案均 tick 39 放置，1–44 帧可见，tick 83 到空白 45 并停止；父层分别到 tick 85／98 移除。持有寿命 46／59 tick，可见寿命都是 44 tick。父层命中停顿不冻结这个子播放头。

I 其他有效窗口保持不变：地面 I `bs1atm` 644–681、`bsatm` 685–689；空中 I `kbsatm` 862–866；下 I `cbs1atm` 943–1044（951 MOVE 缩框）、`cbsatm` 1054–1056。四招逐 tick 全局矩形见 [hitbox-rects.json](hitbox-rects.json)。

## 源优先五问与实现原因

1. **每帧脚本**：`scripts/fighter/pain.json` 的 `DefineSprite_405/frame_45/DoAction.as` 为 `stop()`；主体 Sprite 573 在 817 跳回站立。导入器只编译自包含的 stop/play/goto 控制块；表达式、条件分支交给既有行为编译器，不在运行时解释 AS2。
2. **PlaceObject／MOVE**：主体 771、depth 31、Sprite 405 的 PlaceObject3 为 `blendMode=4`，原生读数为 `screen`；无额外 tint/filter/缩放。MOVE 保留状态，移除／替换创建新实例；播放头按父实例路径隔离，不能仅按共享符号定义查找。
3. **离开方式**：子 45 为空白并 stop，不能 modulo 回 1；父 817 回站立时删除子实例。命名和匿名可视子剪辑共用播放头，已由战斗事件驱动的命名播放头仍为权威。
4. **原版不变量**：单次 250 伤害；44 个可见子 tick；摄像机每帧写回 twip 位置，缩放 getter 保留赋入的百分数，渲染／碰撞矩阵截为 16.16。**缩放矩阵的量化不反馈到 `_xscale` 百分数 tween**，这点由新增原生精度采样确认，修正调查阶段的粗略表述。根 SWF 的 game 初始平移为 (-205,318.8)，不能直接 snap 到目标。
5. **同输入对照**：通过 `capture_native_player.py --allow-window-activation`，固定输入、随机／时钟 tape，无手动点击；采样串行使用 `/tmp/bvn-native-flash-capture.lock`。12 个全新 Pain 捕获、命中／空挥像素与子时钟、Screen 小样和 Itachi 回归原始轨迹均保留在本目录。

## 回归证据与范围

变基后的最终保存回放 **216/216（127,672 状态）**，另加主线 PR #45 的 **11/11（2,662 状态）**，合计 **227/227、130,334 状态** 全部匹配。其他角色在既有比较字段上无最终输出差异；额外鼬原生复采亦通过。Python 349 项通过、2 项跳过；`PROTECTED_FUNCTION_OK`（1086 bytes）保持原 SHA-256。详见 [checks.json](checks.json) 与 [完整回放结果](roster-comparisons.json)。测试秒数逐项保留，不推算人天。

- [pain-comparisons.json](pain-comparisons.json)：12 案例、7,224 状态，既有 14 字段逐帧精确匹配。
- [bounds-comparison.json](bounds-comparison.json)：214 个整数 twip 全局矩形精确匹配；Godot 的 float32 JSON 投影只还原回整数 twip，不加容差。
- [camera-trajectory.json](camera-trajectory.json)：31 帧原生摄像机位置、百分数、矩阵缩放；回归还锁定百分数经 checkpoint 读回不被再次浮点舍入。
- [child-timing-comparison.json](child-timing-comparison.json)：命中 59、空挥 46 个子时钟样本，零差异。
- [screen-native-fixture.json](screen-native-fixture.json)：单／双重叠子图、100%／50% 父 alpha 的原生 Screen 样本；真实 GPU 测试核对公式与层级。
- 通用播放头新增同符号多实例测试。开发中发现 Itachi 空中 U 的三个错开放置投射物会因错误共享子时钟而提前命中；已改为父实例路径查找，并重新原生捕获，602 状态精确一致。最终角色回放不允许保留该差异。
- [itachi-native-comparison.json](itachi-native-comparison.json)：额外原生采样与变基后鼬空中 U 回放 602 状态一致。
- [visual-impact.json](visual-impact.json) 列出其他角色的源 Screen／静态控制元数据。它表示共享数据的影响面，不冒称这些角色全部画面已经逐像素验收。

补充：开发中的广泛诊断复现了原有 AI／标题菜单测试断言，见 [既有诊断记录](known-baseline-diagnostics.json)；未把这些项目写成通过。最终重点回归中 `battle_checkpoint_smoke` 和若干声音测试的断言通过，但仍打印退出时一个资源未释放的既有警告。

现有保存角色回放集含 25 个主测角色，目录共 26 个角色；恋次没有独立主测 fixture。这是既有覆盖缺口，不以全通过计数冒充补齐。

本次不提升整角色／整局完整视听、浏览器或极限擦边验收状态。回放的“输出一致”指既有状态字段；摄像机与视觉的修正另列上述证据。

## 复现

仓库根运行，`$GODOT` 指向 4.7.2 可执行文件；所有输出写入独立临时目录。

```sh
python3 tools/importer/rebuild_visual_timeline_data.py --xml-cache /tmp/pain-xml --ffdec /path/to/ffdec-cli.jar
python3 tools/test_move_cases.py --godot "$GODOT" --cases evidence/characters/pain/visual-parity/cases --output /tmp/pain-native --jobs 2
python3 tools/probes/compare_collision_bounds.py evidence/characters/pain/visual-parity/hitbox-rects.json /tmp/pain-native
"$GODOT" --headless --path godot -s res://tests/visual_playhead_smoke.gd
"$GODOT" --headless --path godot -s res://tests/camera_precision_smoke.gd -- "$PWD/evidence/characters/pain/visual-parity/camera-trajectory.json"
"$GODOT" --path godot -s res://tests/screen_blend_render.gd
BVN_CHECK_DIR=/tmp/pain-roster BVN_GODOT="$GODOT" python3 evidence/characters/pain/visual-parity/replay_saved_roster.py
python3 evidence/characters/juggo/check_protected.py
```

重新采集原版需要原生 Flash 32；`source-builds/` 保留仪器差异及源哈希，`traces/` 保留 gzip 压缩原始记录。不要对锁定 SWF 原件直接插桩。
