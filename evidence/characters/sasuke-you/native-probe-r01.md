# Sasuke fixed-input original probe

This is a retained original-player observation, not a Godot parity result.
The original-player window was acquired after the previous task's
`main.swf` process (PID 59794) was verified and terminated. The capture then
ran under the repository lock and left no Flash process behind.

## Commands

```text
python3 tools/probes/move_cases.py --fighter sasuke --output /tmp/sasuke-cases-r01
python3 tools/probes/build_ai_reference.py \
  --ffdec /private/tmp/bvn-ffdec-26.2.1/ffdec-cli.jar \
  --output /tmp/bvn-sasuke-probe-r01 --run-id sasuke-r01 --frames 360 \
  --p1-character 佐助 --p2-character 一护 \
  --move-case /tmp/sasuke-cases-r01/sasuke-203-nornalhit-neutral.json \
  --dynamic-move-case
python3 tools/probes/capture_native_player.py \
  /tmp/bvn-sasuke-probe-r01 /tmp/bvn-sasuke-probe-r01/original.log \
  --timeout 120 --allow-window-activation
python3 tools/probes/collect_ai_reference.py \
  --build /tmp/bvn-sasuke-probe-r01 \
  --capture /tmp/bvn-sasuke-probe-r01/original.log \
  --output /tmp/bvn-sasuke-probe-r01/collected.json
```

The build and capture completed with `original_capture_completed_not_port_parity`,
14,513 events, one recorded P1 attack-key read, 360 fight frames after Ready,
and zero post-done events. Retained details are in
`/tmp/bvn-sasuke-probe-r01/collected.json/summary.json`; the temporary probe
directory is intentionally outside the source tree.

The probe proves that the automated original capture path accepts Sasuke's
source catalog entry. It does not establish one-to-one behavior until the
corresponding native Godot trace is produced and compared.
