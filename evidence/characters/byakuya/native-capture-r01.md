# 白哉基础形态原版固定输入捕获 r01

状态：`original_capture_completed_not_port_parity`。

本次使用原版 Flash Debug Player、JPEXS 26.2.1、独立 `/private/tmp/byakuya-native-move-r01` 构建目录和项目共享锁 `/tmp/bvn-native-flash-capture.lock`。捕获没有清空全局日志，run id 为 `byakuya_move_j_r01`，`done` 唯一且连续事件 11,503 条，`ready` 后保留 360 个 fight tick，`post_done_events=0`。

配置：P1 白哉基础形态，P2 小李基础形态，地图「现世」，P1 援助剑八，P2 援助天天，模式 2，原始输入注入使用源按键读取。该批次观察到白哉的按键读取：右 20 次、J 9 次、下 120 次、空中/招式键 2 次、跳 1 次；这是固定输入送达证据，不能单独证明动作命中或 Godot 对齐。

原始轨迹保留在临时目录：

```text
/private/tmp/byakuya-native-move-r01/original.log
/private/tmp/byakuya-native-move-r01/collected.json/events.jsonl
/private/tmp/byakuya-native-move-r01/collected.json/summary.json
/private/tmp/byakuya-native-move-r01/collected.json/random-tape.json
```

关键哈希：原始日志 `8d3c889ae15201be5af7de92d29351ef4b53ad78a2d2021b963f46b36b6fbe9a`；事件 JSONL `41f59eead183db91d7ff04efae66ae5b9a4272b9e4a7d438cb348a7d22a2cfa2`；随机 tape `94278be1a7b09ca1bbed562a952e8ab3d60c2b7d1cb08c41562924cfa0e85408`。

复现：

```bash
python3 tools/probes/build_ai_reference.py --ffdec /private/tmp/ffdec-26.2.1/ffdec-cli.jar --output /tmp/byakuya-native-move-r01 --run-id byakuya_move_j_r01 --frames 360 --p1-character 白哉 --p2-character 小李 --p1-helper 剑八 --p2-helper 天天 --presentation-probe
python3 tools/probes/capture_native_player.py /tmp/byakuya-native-move-r01 /tmp/byakuya-native-move-r01/original.log --timeout 120 --allow-window-activation
python3 tools/probes/collect_ai_reference.py --build /tmp/byakuya-native-move-r01 --capture /tmp/byakuya-native-move-r01/original.log --output /tmp/byakuya-native-move-r01/collected.json --retain-post-done-frames
```

Godot 同输入回放尚未执行；当前捕获仅作为原版 oracle，不能标记角色一比一通过。
