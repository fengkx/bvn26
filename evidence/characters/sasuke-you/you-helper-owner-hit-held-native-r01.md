# You helper owner-hit held original capture r01

本记录采集佐助召唤鼬后，卡卡西持续攻击至 tick 180 的原版 Flash 轨迹，并与实施代理提供的 native 轨迹对照。未修改 runtime、`game/` 或 `scripts/`。

## Fixture and explicit source configuration

- Fixture: `/private/tmp/sasuke-you-kakashi-owner-hit-held-r01.json`
- Fixture SHA-256: `f352f5e23dac6ee62bfd6ea22c69033108431bfed4a3ace486be4ea854b038a7`
- Setup: 佐助 p1 x=300、卡卡西 p2 x=350，双方 energy=300；frames after READY=360
- Inputs: p1 summon ticks 10..13；p2 attack ticks 20..180
- Fighters: p1 `sasuke`/佐助，p2 `kakashi`/卡卡西
- Explicit helpers: p1 `you`/鼬，p2 `kon`/魂（build CLI 显式传入；无默认 helper 依赖）
- Fresh build/run: `/private/tmp/sasuke-you-kakashi-owner-hit-held-original-r01`，run ID `sasuke-you-kakashi-owner-hit-held-original-r01`
- Build metadata: `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-owner-hit-held-native-r01.build.json`
- Raw capture: `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-owner-hit-held-native-r01.original.log.gz`；raw SHA-256 `39bbc5e4a85f5a9aec40994d040c828ae6ccf7409abce27d53a1f8a20304a3d9`
- Collected events: `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-owner-hit-held-native-r01.events.jsonl.gz`；events SHA-256 `a7f80a4e04e49f5c562dff76a5212830e1cdda4377064e014c346c9be4d9ef23`
- Native input: `/private/tmp/sasuke-you-kakashi-owner-hit-held-native-r01/native.json`；native SHA-256 `2e9e49c58e2c920a6f6c334429406681107dcb6779956d9025b5174c8c7cdbe4`

本次采集 10,675 条 raw AIREF 事件，含唯一 `ready`/`done`、360 fight ticks、0 条 post-done event、1,292 fighter states + 1,292 helper states；collector 以连续 run_id/sequence 校验通过，没有拼接多次运行。

## Original trace

原版在持续攻击下仍让本体受击并继续执行鼬 helper：

- 佐助首次受击在 tick25：root frame 862，HP 1000→970；后续 tick34 HP→950、tick38 HP→930，hits 分别为 1、2、3。第三次受击后 `paused=true`，到 tick79 恢复；随后第四次在 tick94 HP→870、hits=4，并在 tick95..107 再次暂停。受击序列持续到约 tick124..127，之后回到本体 frame 56（tick128）。
- 鼬在 helper state 中 tick15 spawn；local frame 48 at tick62，随后自然前进至 local frame75 at tick89，local frame1 at tick90 并回到隐藏位置 x=20,y=-200 at tick91。raw 中没有 helper 跳入 `攻击2` 或对卡卡西造成伤害；卡卡西 HP 保持 1000，hits=0。
- 对应源脚本路径为 `scripts/fighter/fz/you.json`：`frame_48/PlaceObject2_24_3/CLIPACTIONRECORD onClipEvent(enterFrame).as` 以 `this.hitTest(_root.game["p" + _parent.pn].mc.bdmn)` 命中才 `gotoAndPlay("攻击2")`；`frame_76/DoAction.as` 调用 `_root.fzccXg(this); gotoAndStop(1);`。本 raw helper sequence 经过 frame48→75→1，证明未命中分支自然 fallthrough 至 frame76 后回 1。

## Native comparison

比较命令：

```text
python3 tools/probes/compare_mode_reference.py /private/tmp/sasuke-you-kakashi-owner-hit-held-original-r01/collected.json/events.jsonl /private/tmp/sasuke-you-kakashi-owner-hit-held-native-r01/native.json --output /private/tmp/sasuke-you-kakashi-owner-hit-held-original-r01/compare-native.json
```

结果：`different`，source/native 各 722 rows；首差为 tick93 p1，字段 `frame` original 861/native 869、`x` 209/205、`y` -81/-85、`hstm` 20/21。随后 native 在 tick94 仍 HP930/hits3，而原版已 HP870/hits4；原版 tick95 起 paused=true，native 未暂停。详细首差序列保存在 `/Users/fengkx/me/code/bvn2_6/evidence/characters/sasuke-you/you-helper-owner-hit-held-native-r01.compare.json`。

该 diff 是本次 held 输入下的真实原版/native 证据，未调整阈值，也未把旧 native 结果解释为原版事实。它覆盖“owner 持续受击期间 helper 未命中”的控制条件；不能单独推断 helper 对接触场景的伤害行为。
