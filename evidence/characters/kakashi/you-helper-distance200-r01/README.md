# 鼬辅助中距接触判定

## 结论

卡卡西搭配鼬时，距离约 200 的黑烟在原版能触发攻击并造成伤害。Godot 的嵌套接触回调却一直拿 depth 3 实例在 root frame 48 的出生矩阵做 `hitTest`；同一实例在 frame 50–59 经 MOVE 延伸、平移后，屏幕上的烟已经覆盖目标，回调仍用旧矩形，因此错过接触。修复改为按每次显示调度的当前 parent frame 查同一个放置代次，再用该帧矩阵计算 bounds。

## SOURCE_FIRST 五问

1. **每帧执行什么？** `scripts/fighter/fz/you.json` 的 `frame_48/PlaceObject2_24_3/CLIPACTIONRECORD onClipEvent(enterFrame).as` 执行 `this.hitTest(_root.game["p"+_parent.pn].mc.bdmn)`；命中后对父 helper 执行 `gotoAndPlay("攻击2")`。`this` 是 depth 3 的 Sprite24 `atm1` 实例，不是 helper 根容器。
2. **放置与 MOVE 怎样延续？** frame 48 在 depth 3 放置 Sprite24，`placed_frame=48`。frame 50–59 的 MOVE 修改该实例矩阵，不创建新实例；frame 60 移除 depth 3。Shape23 的局部边界为 1319×810 twips。frame 48 矩阵 scaleX=1.7922058、scaleY=0.5614166、translate=(538,-345) twips；frame 50 的 scaleX=2.8313446、translate=(548,-345) twips；frame 56、58 又改变平移和 Y 缩放。
3. **如何离开标签？** 接触回调 goto 到“攻击2”后，helper 根继续播放攻击动作；miss 路径沿原播放头继续，后续源脚本自然隐藏/结束。depth 3 只在 frame 60 移除。此修复不改 goto、实例寿命或 miss 路径。
4. **原版不变量是什么？** 一个 PlaceObject 实例在后续 MOVE 中保留身份和回调，但其世界 bounds 必须使用当前显示列表中的矩阵。不能用 `placed_frame` 同时代表实例身份和当前几何帧。
5. **原版同输入对照？** mode 2、现世、P1 卡卡西 x=300/MP=300、P2 佐助 x=480 且走位/防御输入关闭，O 在 fight tick 10–12。P1 选鼬。原版在 helper root frame 48@fight62、49@fight63 后，于 root frame 50@fight64 跳到 frame 92，随后佐助四次受击，HP 1000→780。Godot 当前 runtime 同设置也造成四次受击并到 780 HP。

## 红绿证据

修复前的 bounds 探针保存于 `bounds-red-before-fix.log`：root frame 50 的出生框仍是 `[306.9,-42.25,118.2,22.75]`，目标身体在 x=480 时从 x=469.7 开始，二者不相交；当前 MOVE 后 bounds 是 `[307.4,-42.25,186.75,22.75]`，与目标相交。root frame 56 的当前框移动到 x≈436.7，仍能触及距离 200；同一出生框不能触及。`bounds-live-vs-birth.log` 还覆盖 helper 朝右/左及距离 50、150、200、250；frame 50 距离 200 两个朝向都呈现出生框不相交、当前矩阵相交。

`godot/tests/you_helper_dynamic_contact_smoke.gd` 在左右镜像下都断言 helper root frame 50 进入攻击2：右向 helper x=280、目标 x=480；左向 helper x=500、目标 x=300。原版完整轨迹见 `native-events.jsonl`；构建及 setup 补丁见 `build.json` 与 `controlled-fixture.diff`；同输入 Godot GameWorld 轨迹见 `godot-events.jsonl`。

原版 observer 记录了 helper 的 root frame、`atm1` 显示状态、frame 50 后的 goto 和对手 HP/hits；它没有直接读取 Flash 的 `getBounds()` 或 `hitTest()` 返回值。因此成功接触由同一 EnterFrame 源块从 50 跳到 92、再由 HP/hits 变化佐证，未声称观察到原版内部 AABB 数值。矩阵与当前/出生 bounds 的数值对照来自锁定源时间轴和 Godot 原始 source-bounds计算。

原版伤害帧为 102、117、133、149；Godot 为 101、117、133、149。首击仍差 1 tick，未把它归一化为完全逐帧一致；其余三次命中帧及总伤害相同。本案只覆盖平地、静止目标和此距离，不证明所有地图或高度下的命中范围。

## 验证

- `you_helper_dynamic_contact_smoke.gd`：左右镜像 frame 50 接触通过。
- `you_helper_callback_order.gd`：frame 48 放置下一 tick、MOVE 保留回调注册、同 tick FIFO 通过。
- `you_helper_lifecycle.gd`：75 帧生命期、自然结束和再次召唤通过。
- `ai_helper_state_smoke.gd`、`sasuke_you_native.gd`：旧辅助回归通过。
- Kakashi + You 对佐助的中距 GameWorld 重放：4 hit、末 HP 780；原版同输入亦 4 hit、末 HP 780。

Godot headless 在此机器会输出既有 `user://logs` 无法打开和 macOS CA certificate 读取错误；上述测试均有明确 `*_OK` 标记且没有 `SCRIPT ERROR`。原版采样前 `/Users/fengkx/mm.cfg` 不存在；本案临时写入两项 Flash trace 开关，capture `done=true` 后已删除并确认恢复不存在。没有改动锁定的 `game/` 或 `scripts/` 输入。
