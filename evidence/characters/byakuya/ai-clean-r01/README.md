# Clean Byakuya AI reference

Configuration: P1 一护 human, P2 白哉 CPU, 魂/魂, mode 2, AI 5, stage 现世.
The build uses no frame-order, presentation, schedule, body-boundary, move,
recovery, or shadow probe. `build.json` records every behavior-changing flag as
false.

Native capture completed with 5,225 events, 210 random records, 40 AI refreshes,
699 predicate observations, and 2 getTimer clock records. The old `ai-r02`
fixture is invalid and must not be used for behavior acceptance.

The first full global replay attempt is retained in `godot-replay-attempt.log`. The replay is diagnostic only and is not an acceptance result. `random-order-audit.json` records the first reproducible divergence: with no manual Ichigo draw injection, the source-timed replay first fails at the scheduled Byakuya refresh for fight tick 36: the clean Flash tape still expects Ichigo's hurt-voice probability consumer (`fighter/yihu#DefineSprite_638/frame_1/DoAction.as:1`) from source index 155, while Godot requests Byakuya's refresh (`fighter/Byakuya#DefineSprite_631/frame_1/DoAction.as:2`). The preceding source event is the Ichigo consumer at fight tick 25, which Godot did not issue. The old diagnostic run that manually consumed Ichigo draws is not used. This is a runner/runtime phase difference, not a tape adjustment.

`state-first-difference.json` records the unshifted comparison boundary: the first P1 observation differs at Ready tick 0 (`frame` 7 vs Godot 5), and the first P2 14-field difference is tick 18 (`ql` 6 vs 0). These rows are retained as diagnostic evidence until the production intro/consumer order is aligned.

`godot-replay-clean-r02.json` is the corrected data-driven runner result. It parses the native input, clock, random, and AI sample events; derives the pre-Ready refresh count from the recorded random stream; and stops at source index 154 / fight tick 36 when the next native Ichigo hurtVoice consumer is absent. The unrelated native main music random at index 1 is explicitly outside this fighter-AI scoped replay and is recorded as such; no replacement draw is synthesized.
