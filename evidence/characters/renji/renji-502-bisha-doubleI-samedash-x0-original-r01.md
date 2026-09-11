# Renji continuous double I same direction dash x0 original capture r01

本记录将 Renji 两次 `必杀` 与一护两次同世界方向右冲刺的原版 Flash 轨迹，与既有同输入 native 结果对照。未修改 runtime、`game/` 或 `scripts/`。

## Fixture and source configuration

- Fixture: `/private/tmp/renji-i-magnet-r02/native/scan-x/x0.json`
- Fixture SHA-256: `98a56018240b0856194dd2ec6a2f421d4fda7a1c2d319afa6afe012c7a5b811d`
- Setup: 恋次 p1 x=300、一护 p2 x=0（原版首 tick 将 p2 clamp 至 x=20），双方 energy=300
- Inputs: p1 special ticks 10..13 and 74..77; p2 dash ticks 10..13 and 74..77
- Target frames: 502, 585, 502, 585
- Frames after READY: 240
- Explicit helper config: p1 `woailuo/我爱罗`、p2 `kon/魂`（build 参数显式传入；fixture 本身未声明 helpers）
- Fresh build/run: `/private/tmp/renji-502-bisha-original-x0-r01`, run ID `renji-502-bisha-original-x0-r01`
- Source/output/instrumentation hashes: `/Users/fengkx/me/code/bvn2_6/evidence/characters/renji/renji-502-bisha-doubleI-samedash-x0-original-r01.build.json`
- Raw capture: `/Users/fengkx/me/code/bvn2_6/evidence/characters/renji/renji-502-bisha-doubleI-samedash-x0-original-r01.original.log.gz`; raw SHA-256 `21c175fe65d6f236cb58f7ab3b9a9a211a3178faa243d6139d7661c836dd326f`
- Collected events: `/Users/fengkx/me/code/bvn2_6/evidence/characters/renji/renji-502-bisha-doubleI-samedash-x0-original-r01.events.jsonl.gz`; events SHA-256 `483812f19966c96fe299dccc4c463d8e7103821641bc976c9850793f3ff5542a`
- Existing native: `/private/tmp/renji-i-magnet-r02/native/scan-x/x0.native.json`; native SHA-256 `2117c79a4583c2fa5d520b93962c0e6efa9cf9a00847a4411b0c1354fd3f4e5d`

## Source placement and native timing

- `scripts/fighter/Renji.json` (`swf_sha256` `7505e9591f46ba1d05bb03fff9450d52583804022a08ba3bb7a0ecfb21cb116a`) maps the physical `I` read to `special` / source label `必杀`. `DefineSprite_717/frame_503/DoAction.as` sets `动作=3`, `bs=1`, and spends 100 energy; `DefineSprite_717/frame_522/DoAction.as` assigns `bs1._x/_y` from the opponent position.
- The source timeline has no depth-26 instance at frame 521. Frame 522 places character 367 as a new depth-26 `bs1` (`move=false`, MATRIX `2699,-416` twips); the child `DefineSprite_367/frame_23/DoAction.as` renames itself to `bsatm`, and frame 550 removes depth 26. The second cast therefore creates a fresh instance after the first instance has been removed; it does not reuse the old instance variables.
- Native observed the first placement at fight tick 31 (P2 x=65) and the second at tick 95 (P2 x=215), with P1 x=300 and xscale=-100 in both casts. The corresponding source local X values are 235 and 85 pixels, with local Y 0; both P2 dash windows move right by the same 75 pixels before the active window.
- The native output contains 482 states and the original comparison contains 482/482 matched states with no differences. The original capture independently reports the same first-miss/second-hit result, including the second hit settling at tick 123.

Collector summary records 6,607 events, one `ready`, one `done`, 240 fight ticks, zero post-done events, 1,054 fighter states and 1,054 helper states. The Flash window exited after `done`; no second run was concatenated.

## Original result

原版第一刀未命中、第二刀命中：

- 第一轮进入 root frame 502 at fight tick 11 and frame 503 at tick 12；攻击放置 frame 522 at tick 31；active frames 544..549 at ticks 53..58。p2 从 clamp 后 x=20 右冲至 x=170，HP 保持 1000，未产生命中。
- 第二轮进入 root frame 502 at tick 75 and frame 503 at tick 76；攻击放置 frame 522 at tick 95；active frames 544..549 at ticks 117..122。p2 从 x=170 右冲至约 x=320；tick 123 进入受击 frame 752，HP 从 1000 降至 700，hits=1。随后受击序列至 tick 183，tick 184 恢复；最终 p2 x=150、HP=700。

HP 使用项目 decoder `tools/probes/collect_ai_reference.py` 的 `decode_number`（line 16）解释，不手解编码。该轨迹完整保留了同一 run 的 first miss → second hit 边界。

## Native comparison

使用命令：

```text
python3 tools/probes/compare_mode_reference.py /private/tmp/renji-502-bisha-original-x0-r01/collected.json/events.jsonl /private/tmp/renji-i-magnet-r02/native/scan-x/x0.native.json --output /private/tmp/renji-502-bisha-original-x0-r01/compare-existing.json
```

结果：`matched`，source states 482，native states 482，`differences=[]`，完整比较字段由比较器记录于 `/Users/fengkx/me/code/bvn2_6/evidence/characters/renji/renji-502-bisha-doubleI-samedash-x0-original-r01.compare.json`。

连续后两次的相对站位不同：第一次 active 阶段 P2 仍在恋次左侧，第二次已推进至恋次附近并发生近身位置碰撞，因此第二次进入攻击框。两次屏幕 AABB 的尺寸变化还受到共同的 camera/global transform 缩放影响；这只解释屏幕坐标大小，不单独造成碰撞差异。原版和 native 同输入结果一致，无需为该现象修改 runtime。

这是 x0 固定输入的原版/native 对照证据，不代表更广泛 Renji parity。
