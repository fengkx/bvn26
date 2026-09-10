# Kakashi original capture r01

状态：`original_capture_completed_not_port_parity`。

普通砍1 的固定输入已由原版 Flash 播放器采集 360 帧：

```text
build: /tmp/bvn-kakashi-probe-r01
capture: /tmp/bvn-kakashi-probe-r01/original.log
collected: /tmp/bvn-kakashi-probe-r01/collected.json
fixture: /tmp/kakashi-cases-r01/kakashi-193-normalhit-neutral.json
pressed key: J (key code 74)
frames_after_ready: 360
events: 14577
```

该批次确认原版输入投递和日志收集完成，但没有 Godot 同输入回放，因此不存在可报告的 `first_difference`。普通砍1 只覆盖 frame 193–218，不能验收 frame 864/887/900 的超必杀状态链。

超必杀覆盖 fixture 已构建但尚未占用原播放器窗口：

```text
fixture: /tmp/kakashi-cases-r01/kakashi-863-super-neutral.json
build: /tmp/bvn-kakashi-super-probe-r01
frames_after_ready: 1100
target_frames: 863–920
```

下一批必须采集该 fixture，并确认 frame 864 的 `Cbshit=false`、frame 887 命中写入、frame 900 条件分支；在此之前保留未验收状态。

普通砍1 生产入口回放已用同一固定输入完成比较：

```text
Godot: res://tests/move_case_reference.gd
Native comparator: tools/probes/compare_mode_reference.py
Godot rows: 722
Original rows: 722
status: matched
first_difference: none (complete exact field comparison)
report: evidence/characters/kakashi/production-comparison-r01.json
```

该结果覆盖原版采样的 360 个 fight ticks，比较字段为 frame、位置、朝向、动作、HP、能量、状态、受击与暂停字段；超必杀 Cbshit 目标仍由 `super-targets.json` 单独约束，不能由普通砍1 结果代替。
