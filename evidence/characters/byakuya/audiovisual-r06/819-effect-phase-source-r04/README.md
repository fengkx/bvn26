# Byakuya 819 source effect phase r04

This is a native Flash capture built from the locked Byakuya/YiHu source with dual 魂 helpers and the explicit 814 summon fixture. The optional `--effect-phase-probe` is a read-only observer inserted into the source root callback after the actor/helper state observations; it does not alter input, goto, timing, or effect dispatch.

Command:

```sh
python3 tools/probes/build_ai_reference.py --ffdec /private/tmp/ffdec-26.2.1/ffdec-cli.jar --output /private/tmp/byakuya-effect-phase-r04-build --run-id byakuya-effect-phase-r04 --frames 300 --p1-character 白哉 --p2-character 一护 --p1-helper 魂 --p2-helper 魂 --move-case evidence/characters/byakuya/fixtures-full/byakuya-814-zhaoHuan-neutral.json --dynamic-move-case --effect-phase-probe
python3 tools/probes/capture_native_player.py /private/tmp/byakuya-effect-phase-r04-build /tmp/byakuya-effect-phase-r04-capture --lock-timeout 180 --allow-window-activation
```

At source fight tick 16 / display 472 the root observer sees `p1` frame 819 and helper frame 2, while `effect_state` is `undefined`. The next source callback (fight tick 17 / display 473) observes effect frame 2. This is same callback evidence, not a post-freeze snapshot. It does not by itself prove the production Godot effect implementation; the earlier experimental dispatch fix remains reverted and unaccepted.
