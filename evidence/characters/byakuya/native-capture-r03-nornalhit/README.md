# 白哉砍1中立场景原版捕获 r03

这是用于两端同输入比较的有效版本：P1 白哉、P2 一护，双方初始 x=300/350、气=300，P1 fight tick 10–12 按攻击键，P1 援助剑八、P2 援助魂，300 fight ticks。构建 fixture 的 `fighters` 与实际 `p1-character/p2-character` 完全一致。

原版捕获使用共享 `/tmp/bvn-native-flash-capture.lock`，`summary.json` 记录唯一首个 `done`，共 14,500 事件，ready 后 300 tick；Flash 退出尾部有 4 个 post-done 事件，按项目 collector 规则保留并单独记录。Godot 同输入比较仍待 controller 产物完成。

压缩后的完整 `original.log.gz`、`events.jsonl.gz`、`random-tape.json`、`summary.json`、`build.json` 和 `capture-environment.json` 均在本目录。

复现：

```bash
python3 tools/probes/move_cases.py --output /tmp/byakuya-cases --fighter byakuya
python3 tools/probes/build_ai_reference.py --ffdec /private/tmp/ffdec-26.2.1/ffdec-cli.jar --output /tmp/byakuya-case-nornalhit-r02 --run-id byakuya_nornalhit_neutral_r02 --frames 300 --move-case /tmp/byakuya-cases/byakuya-169-nornalhit-neutral.json --p1-character 白哉 --p2-character 一护 --p1-helper 剑八 --p2-helper 魂
python3 tools/probes/capture_native_player.py /tmp/byakuya-case-nornalhit-r02 /tmp/byakuya-case-nornalhit-r02/original.log --timeout 120 --allow-window-activation
python3 tools/probes/collect_ai_reference.py --build /tmp/byakuya-case-nornalhit-r02 --capture /tmp/byakuya-case-nornalhit-r02/original.log --output /tmp/byakuya-case-nornalhit-r02/collected.json --retain-post-done-frames
```
