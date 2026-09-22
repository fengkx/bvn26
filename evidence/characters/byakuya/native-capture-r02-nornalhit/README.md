# 白哉砍1中立场景原版捕获 r02

状态：`original_capture_completed_not_port_parity`。

固定 fixture：`byakuya-169-nornalhit-neutral`，P1 白哉、P2 小李，双方初始 x=300/350、气=300，P1 在 fight tick 10–12 按住攻击键，P1 援助剑八、P2 援助天天，300 fight ticks。原版捕获使用共享 `/tmp/bvn-native-flash-capture.lock`，唯一 `done`，共 13,920 事件，`post_done_events=0`。

持久化文件保留压缩后的完整原始事件、collector 事件流、随机 tape、summary、build 和播放器环境。原始源哈希与复现命令见 `build.json`；Godot 同输入比较尚未执行。

复现：

```bash
python3 tools/probes/move_cases.py --output /tmp/byakuya-cases --fighter byakuya
python3 tools/probes/build_ai_reference.py --ffdec /private/tmp/ffdec-26.2.1/ffdec-cli.jar --output /tmp/byakuya-case-nornalhit-r01 --run-id byakuya_nornalhit_neutral_r01 --frames 300 --move-case /tmp/byakuya-cases/byakuya-169-nornalhit-neutral.json --p1-character 白哉 --p2-character 小李 --p1-helper 剑八 --p2-helper 天天
python3 tools/probes/capture_native_player.py /tmp/byakuya-case-nornalhit-r01 /tmp/byakuya-case-nornalhit-r01/original.log --timeout 120 --allow-window-activation
python3 tools/probes/collect_ai_reference.py --build /tmp/byakuya-case-nornalhit-r01 --capture /tmp/byakuya-case-nornalhit-r01/original.log --output /tmp/byakuya-case-nornalhit-r01/collected.json --retain-post-done-frames
```
