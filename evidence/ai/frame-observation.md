# 回站立首差：观察阶段校准

状态：已完成原版最小调度探针；连续对照工具的阶段校准尚未完成。

`combat-player-body-r04.json` 的 display 500 比较了原版根 enterFrame 中的状态与
原生整个逻辑步结束的状态。一护都是帧 1，但动作分别为 1 和 0。
不能由此认定原生应该延迟站立帧的赋值。

源代码 `scripts/fighter/yihu.json` 中：

- `DefineSprite_638/frame_390/DoAction.as` 是 `gotoAndStop("站立"); play();`。
- `DefineSprite_638/frame_1/DoAction.as` 包含 `var 动作 = 0;`。

新增 `frame_state_enter/exit` 记录源帧号、当前播放头、动作、ql、sw。
[r05 自然对战](frame-state-r05/summary.json) 完成 600 个对战帧，但未经过帧 390，
因此没有把它当成该顺序的证据。

[r06](frame-order-r06/build.json) 是显式 `--frame-order-probe` 夹具：Ready 后第 1 帧
将一护放到帧 389、动作设为 1、根暂停标志设为 true，随后自然推进到帧 390。
这个受控初态用于隔离调度，不是正常对战 golden，也不能用于 AI 策略验收。

[事件顺序](frame-order-r06/observation-order.json) 是：

| sequence | 事件 | 当前帧 | 动作 |
|---:|---|---:|---:|
| 1633 | 帧 390 调用者退出 | 1 | 1 |
| 1636 | 根观察器记录 P2 | 1 | 1 |
| 1637 | 目标帧 1 脚本进入 | 1 | 1 |
| 1640 | 目标帧 1 脚本退出 | 1 | 0 |

根观察器内部递增 aiDisplay，所以调用者与目标的日志 display_tick 也不相同。
不能把该计数差直接解释为目标 DoAction 延迟了一个完整显示周期；相邻时间戳和
既有同显示周期 goto 探针须一起理解。

复核命令：

```sh
python3 tools/probes/analyze_frame_observation.py \
  --events evidence/ai/frame-order-r06/events.jsonl \
  --output /tmp/frame-observation-check.json
cmp /tmp/frame-observation-check.json evidence/ai/frame-order-r06/observation-order.json
```

下一步是在原生同样的帧脚本边界采样，再建立 root enterFrame 与延迟目标帧之间的
对应观察点。当前 first_difference 报告继续保留，不能通过忽略动作字段、放宽阈值、
按某个具体帧伪造快照或延迟源赋值来把它改成通过。

## 原生同边界验证

`FighterRuntime.source_frame_script_boundary(frame, entering)` 在每条实际排队帧脚本的前后发出观察信号，不调整赋值或排队时机。`frame_observation_reference.gd` 在原生同样建立 r06 初态，并比较调用者退出、目标进入、目标退出三个位置。

[native-boundaries.json](frame-order-r06/native-boundaries.json) 三处五字段均与原版相同（源帧、当前播放头、动作、ql、sw），对应日志有 `FRAME_OBSERVATION_REFERENCE_OK` 且无 SCRIPT ERROR。数值按 AS2 Number 统一比较，源帧标识仍保留整数；不以 Godot Array 的 int/float 容器类型区别制造游戏差异。

该测试没有确定根观察器相对所有其他角色、援助和帧事件的位置；连续对照的 display 500 首差仍保留。下一步需要世界级观察阶段或更完整的源脚本边界事件，不能以这个局部通过替代整场对照。
