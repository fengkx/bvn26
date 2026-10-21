# PR #46 review follow-up: native blend and child-clock audit

本次只修改通用导入、绘制和视觉时钟；不按角色分支，不改攻击伤害或判定框，不合并、不部署。原始 `game/`、`scripts/` 未修改。

结果：26 个角色的 59,799 个逐实例帧号样本零差异；全部 39 个非普通混合 placement 已作原生画面对照。合计保存 2,120 个同帧对照，按 304 个试验拼成 304 张图片。帧号样本计数包含固定父外壳及各层子实例。额外扫描的 KO 专用宿主例外和既有像素差异在下文单列，不计为独立时钟通过。

## 修改与原生依据

- **完整处理实际出现的混合模式**：Multiply 3、Screen 4、Lighten 5、Darken 6、Add 8、Subtract 9、Hardlight 14；另覆盖 Normal 0/1 和 Layer 2。39 个独立 placement 段逐个保留源矩阵、CXFORM、blendMode 和 MOVE 状态，并用 Flash Player Debugger 32 的 `BitmapData.draw` 对照。未实现模式在导入及 Web 隔离构建的 manifest 阶段抛错；不存在静默 normal 回退。
- **alpha 与隔离**：先合成显示对象的子图，再施加父 alpha 和 blend。透明底图按预乘 alpha 解码；普通混合公式只作用于重叠区域。原生小样确认 Add/Subtract 使用预乘 RGB 加减、alpha 相加并截顶，不能套用 source-over。嵌套 Screen 在独立层里合成后再进入外层 Screen，包含单子图和多子图两种测试。38 个透明底、父 alpha 25/50/75/100% 小样的预乘 RGBA 误差均不超过 2/255；这是同一小样中普通混合的舍入上限，不是放宽角色状态阈值。
- **控制块编译**：`stop(); var speed = …` 中的无条件 stop 原先因后续初始化而被整块丢弃。现在跳过不改变播放头的栈／变量操作和函数声明，但仍拒绝分支和函数调用。11 个定义的控制元数据因此修正，涉及一护、迪达拉、重吾、鼬及共用立绘，详见 [控制块前后差异](control-compilation-changes.json)。不执行 AS2 解释器。
- **统一宿主**：HelperRuntime、StageHitRuntime、HitEffectRuntime 接入同一 retained visual clock。删除援助按父帧推算子 stop 的旧覆盖；父暂停和 goto 不会重置仍存活的子实例。新增宿主测试覆盖我爱罗援助的暂停／goto 与舞台／命中特效终止帧。

## 覆盖与限制

[逐剪辑／逐 placement 清单](INVENTORY.md)列出每个符号、控制帧、父级 placement 的帧／depth，以及每张 Flash／Godot 并排图；[汇总](summary.json)与[逐帧结果](comparisons.json)给出精确数量。范围包括所有带静态控制的定义和所有多帧子定义，而不是只查有 stop 的特效。单帧静态、无控制的剪辑没有相位变化。清单也保留空白逻辑剪辑；“受影响”指暂停／跳转时具有改变输出的可能，不表示每个普通招式都产生肉眼可见变化。

实际混合 placement 涉及：带土、迪达拉、鼬、剑八、自来也、重吾、小南、蓝染、佩恩、一角、银，以及三个共用效果。循环／停止型剪辑审计覆盖当前全部 26 个角色（包括没有独立战斗回放 fixture 的恋次），另含援助、主界面和共用效果。

**比较方法是源组件试验，不冒充整招式完整画面验收**：从源 SWF 原样复制 definition tag；两帧父外壳固定在帧 1，观察 tick 0–100，在 tick 10 跳到 2、tick 20 跳回 1。原版子脚本照常执行，父停住模拟视觉子时钟所见的暂停条件。源 placement 试验还逐条复制对应 PlaceObject/MOVE，不重写 blend/CXFORM。Godot 使用生产 TimelinePreview 和相同矩阵／背景／观察顺序。每个子实例按 depth 路径比较，不按共享 symbol 合并。完整战斗 hit-pause／空挥另由既有 Pain 和视觉播放头回归覆盖。

图像不是逐像素零差异：Flash 与 GPU 的采样、8-bit 舍入及已存在的位图轮廓栅格化不同。蓝染 Sprite 394 的旋转位图边缘在 Godot 更亮，原生也有较淡边线；这项既有采样差异保留在图片和 MAE/max-error 中，未用 tint、放大判定或修改参考图遮盖。此次混合公式、alpha 隔离与时钟结果由独立原生小样和逐实例帧号验证；不将全图 MAE 作为容许错误相位的门槛。

同一剪辑的采样图按 tick 纵向拼接，保留每帧 1200×430 的原始对照尺寸，不缩放。[旧绘制器复核](checks/baseline-edge-comparison.json)确认蓝染上述边线所在帧与 `50c0609b` 的 Godot 输出逐像素相同。

**额外扫描的宿主边界**：`main/ko` 和 `main/timeout` 的 Sprite 1844 不属于独立视觉时钟宿主。子 Sprite 1843 有依赖 HP 的 enterFrame `play()`，1844 的终帧 stop 位于包含胜者调用的控制块；生产中由已有 `KoTimeline`／`KoClip` 编译控制器处理，`KoClip._nested_frame` 直接读取该控制器，未启用 independent_visual_clock。裸组件外壳缺少 HP 状态，产生的 260 个差异原样保留在 comparisons.json，未计入角色时钟通过数。真实 KoClip 回归覆盖 perfect 到 15 停止、winner 到 50 停止及实例调度顺序；这些控制器没有修改。不能为了让不适用的外壳通过，把条件 gameplay 逻辑提升为无条件视觉指令。KO 背景回归的断言通过，但保留退出时 6 个资源未释放的既有警告。

## 源优先五问

1. 脚本：每个控制块的源 symbol／帧及编译操作见 inventory；对应原文件在 `scripts/fighter/<name>.json` 的 `DefineSprite_<id>/frame_<n>/DoAction.as`。原版定义字节与源 SHA-256 记录在各 capture 的 build.json。
2. PlaceObject/MOVE：39 个段按 owner、depth、placed_frame、blend_mode 区分；COPY 的源 placement 状态与 normalization 存在 cases.json。替换创建新实例，MOVE 保留实例。
3. 退出：stop 保持当前帧；play/goto 使用子播放头。持续存在的实例跨父 goto 保留相位；移除／替换由既有通用回归验证。
4. 不变量：每个采样 tick 的 child frame、每个 blend 的预乘 RGBA、原来的角色状态和全局整数 twip 判定框分别核对，不互相代替。
5. 同输入原生对照：`capture_native_player.py --allow-window-activation` 自动采样，共享 `/tmp/bvn-native-flash-capture.lock` 串行执行，无手动点击。采样外壳可提高观察脚本时限以容纳批量 BitmapData 输出，不修改角色定义。退出后偶尔多发的 tick 101 不在预先定义的 0–100 对照区间内；原始日志完整保留。

## 回归与复现

结果保存在 `checks/`：保存全角色回放、Pain 12 案例、214 矩形、保护函数、Python、Godot 宿主／回滚／视觉／摄像机检查。状态比较不增容差，不改原始 golden。

`captures/` 保留压缩原生像素 RLE／时钟日志、Godot 时钟、源 SHA、采样脚本和启动元数据；没有提交 Flash、FFDec、临时 SWF 或工具缓存。`probes/` 可从仓库根重新生成全量组件试验：

```sh
export BVN_REVIEW_DIR=/tmp/pain-review-repro
export BVN_FFDEC=/path/to/ffdec-cli.jar
export BVN_GODOT=/path/to/Godot
export BVN_FLASH_APP='/path/to/Flash Player.app'
mkdir -p "$BVN_REVIEW_DIR"
python3 evidence/characters/pain/visual-parity/review/probes/inventory.py
python3 evidence/characters/pain/visual-parity/review/probes/build_components.py
python3 evidence/characters/pain/visual-parity/review/probes/capture_components.py
python3 evidence/characters/pain/visual-parity/review/probes/render_components.py
# Requires Pillow; native/Godot images are decoded and compared without rescaling.
python3 evidence/characters/pain/visual-parity/review/probes/compare_components.py
"$BVN_GODOT" --path godot -s res://tests/flash_blend_modes_render.gd
"$BVN_GODOT" --headless --path godot -s res://tests/retained_effect_clocks_smoke.gd
```

Python 使用 3.10+（本次完整测试为 3.14）；Mac 系统自带 3.9 不支持仓库现有的 `Path | None` 注解。完整角色／整局视听、浏览器和全部边界验收状态仍 pending。
