# Sasuke + You helper original-player guard capture r03

本记录对应原版 Flash 的持续防御输入，用于核对辅助鼬的初次可见攻击、破防属性和共享防御链。未修改 runtime、`game/` 或 `scripts/`。

## Fixture and source configuration

- Fixture: `/private/tmp/sasuke-you-kakashi-guard-r01.json`
- Setup: 佐助 p1 x=300、卡卡西 p2 x=350，双方 energy=300；p1 summon ticks 10..13；p2 down ticks 1..240
- Frames after READY: 240
- Fresh build/run: `/private/tmp/bvn-sasuke-you-kakashi-guard-r03`, run ID `sasuke-you-kakashi-guard-r03`
- Explicit helper config: `p1_helper=you` / `p1sf=鼬`; `p2_helper=kon` / `p2sf=魂`
- Source hashes and generated output hashes: `you-helper-guard-native-r03.build.json`
- Raw capture: `you-helper-guard-native-r03.original.log.gz`
- Collected events: `you-helper-guard-native-r03.events.jsonl.gz`
- Collector summary: `you-helper-guard-native-r03.summary.json`

The run has 5,943 events, one `ready`, one `done`, 240 fight ticks, zero post-done events, one helper spawn, and 1,050 fighter plus 1,050 helper state events. The capture tool completed through the first `done` and released the Flash window.

## Source attack and guard result

The source helper script is `scripts/fighter/fz/you.json`, `frame_1/DoAction.as`. Its attack values are:

- `atm1`: `pw=5`, `zl=4`, `up=0`, `x=0`, `tm=1000`, `dz="被打"`
- `atm2`: `pw=40`, `zl=11`, `up=0`, `x=0`, `tm=600`, `dz="被打"`
- `atm3`: `pw=100`, `zl=11`, `up=0`, `x=-3`, `tm=0`, `dz="击飞"`

In this capture the helper spawns at fight tick 15. The first hitbox `atm1` is present at helper source frame 48 on fight tick 62. Its source callback advances the helper to root frame 92 (`攻击2`) on the following tick, while the defending target remains in the defense state through tick 98. The first visible attack2 blade is the `atm2` window: it starts at helper frames 128..129 (fight ticks 99..100). The target enters its hit sequence at tick 99 (`currentframe=1116`) and applies the first damage at tick 100 (`currentframe=1117`, `hits=1`), reducing HP from 1000 to 960. Subsequent `atm2` windows at frames 144..145 and 160..161 apply hits at ticks 116 and 132. The `atm3` window at frames 176..177 applies the fourth hit at tick 148; final HP is 780 and hits=4.

Thus, the first visible blade in the requested scenario is `atm2`, and it is break-capable (`zl=11`). The initial `atm1` contact has `zl=4` and follows the guarded branch. This wording follows the source timeline and the observed target transition rather than treating the helper startup hitbox as the visible blade.

The shared guard implementation is in `scripts/fighter/Kakashi.json`, `DefineSprite_2/frame_1/DoAction.as`: `fangyu()` calls `checkHit()`, stores the selected helper `pw/zl/up/x/tm/dz`, and for `bdzl > 10` subtracts 10 and jumps to the hit type; otherwise it clears `yup` and jumps to `防住`. The observed transition from defense (`currentframe=1093`) to the hit sequence (`1116`/`1117`) at the `atm2` window is the original-player evidence for this chain.

## Evidence boundary

This is source capture evidence for the explicit guard case. The instrumentation logs state/helper_state and input delivery, but does not provide a direct `hitTest` callback event. The contact conclusion is therefore based on source attack windows plus the synchronized target state, hit count, and HP transitions. It is not a broad parity claim.
