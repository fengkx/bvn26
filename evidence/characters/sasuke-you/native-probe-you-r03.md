# Sasuke + You helper original-player probe r03

This is a source capture record, not a claim that the helper has passed full
presentation/audio parity.

## Build and capture

The build used the source helper selector explicitly:

```text
python3 tools/probes/build_ai_reference.py --ffdec /private/tmp/bvn-ffdec-26.2.1/ffdec-cli.jar --output /tmp/bvn-sasuke-you-probe-r03 --run-id sasuke-you-r03 --frames 240 --p1-character 佐助 --p2-character 一护 --p1-helper you --p2-helper kon --move-case /tmp/sasuke-cases-r01/sasuke-775-zhaoHuan-neutral.json --dynamic-move-case
python3 tools/probes/capture_native_player.py /tmp/bvn-sasuke-you-probe-r03 /tmp/bvn-sasuke-you-probe-r03/original.log --timeout 120 --allow-window-activation
python3 tools/probes/collect_ai_reference.py --build /tmp/bvn-sasuke-you-probe-r03 --capture /tmp/bvn-sasuke-you-probe-r03/original.log --output /tmp/bvn-sasuke-you-probe-r03/collected.json --retain-post-done-frames
```

The build report records `p1sf=鼬`, `p2sf=魂`, and source hashes for
`game/fighter/fz/you.swf` (`a00ed19723373b43b347f802a13c822eae21662d2a85b38336fdba9eb641f604`)
and `scripts/fighter/fz/you.json`
(`6f2b9c27fa900866d91fb1dced55c7d8efb73c7b250e60413032ecf98d92f9ca`).

## Observed source behavior

The collected trace has 240 fight frames, 7,183 retained events, 3,857
`key_read` events, 1,058 fighter states, and 1,058 helper states. The source
instrumentation records:

```text
helper_load: p1,鼬,you.swf
helper_load: p2,魂,kon.swf
helper_spawn: fight_tick=15, p1,鼬,1,false
p1 helper frame: 2 -> 199 -> 1
```

The helper action field is `1` at source frame 18, `0` at frames 61 and 181.
Named attack instances are present at `atm1` frames 48–59, `atm2` frames
128–129, 144–145, 160–161, and `atm3` frames 176–177. Direct Flash audio
events are not part of this instrumentation; the source sound schedule is
covered by `you-helper-lifecycle.md` and its native Godot lifecycle test.

Raw compressed trace, original log, build report, and summary are retained
beside this file.

