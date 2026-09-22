# Byakuya native capture commands (prepared, not run)

Run only after the desktop token is assigned and while holding `/tmp/bvn-native-flash-capture.lock`. Do not run concurrently with another Flash/browser capture. The builds are `built_not_run` and have `frame_order_probe=false`; the recursive freeze observer must be applied only after the source input naturally reaches the target presentation.

```sh
python3 tools/probes/capture_native_player.py \
  --lock-timeout 600 --timeout 1800 \
  /tmp/byakuya-recovery-p2-base631-special-dash62-66-r01-build \
  /tmp/byakuya-recovery-p2-base631-special-dash62-66-r01-capture \
  --allow-window-activation
```

The capture must use the exact persisted recovery fixture and retain the raw event log. The source targets are base `DefineSprite_631` frame 887/934/944; frame 963 is the normal intro branch and must use the separate intro fixture/build.

```sh
python3 tools/probes/capture_native_player.py \
  --lock-timeout 600 --timeout 1800 \
  /tmp/byakuya-intro-963-r01-build \
  /tmp/byakuya-intro-963-r01-capture \
  --allow-window-activation
```

For visual captures, use the same fixed input configuration and recursive freeze observer from r10/r11 on the prepared builds:

```text
333: /tmp/byakuya-freeze-prep-333-r01-build
576: /tmp/byakuya-freeze-prep-576-r01-build
819: /tmp/byakuya-freeze-prep-819-r01-build
```

At each target, record recursive root/child state before and after stop and keep two screenshots showing child state stability. Preserve the 600x400 customer-area crop and the original retina image separately. Do not direct-jump to a frame or stop the scheduler before the source input reaches the target.
