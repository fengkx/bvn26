# Live assist verification

Tested the 17 new assists on the local build of PR 310. Each case runs Ichigo against Naruto on 现世 at x=300 and x=450. All 17 matched the original projector on 14 fighter fields and six helper fields. Both streams contain 6,254 rows. The seven previously archived mirrored casts are outside this new visual run.

Each comparison sheet shows five 600 × 400 frames captured from the original Flash player (top) and a rendered Godot battle (bottom). Every bottom-row image was independently replayed from the start to the exact root observation tick. We also ran the whole match and restored five checkpoints. Per-frame lossless image hashes and the difference between the two capture methods are retained in [checks.json](checks.json). The first-damage tick determined the two contact samples. Other samples cover entry, follow-through and return to idle.

| Name | Flash / Godot frames | Actor rows | Active Web ticks | Final opponent HP | Browser |
| --- | --- | ---: | ---: | ---: | --- |
| 手鞠 | [shouju](shouju.jpg) | 372 | 90 | 825 | [WebGL](web/shouju.jpg) |
| 夜一 | [yeyi](yeyi.jpg) | 372 | 74 | 800 | [WebGL](web/yeyi.jpg) |
| 天天 | [tenten](tenten.jpg) | 372 | 117 | 800 | [WebGL](web/tenten.jpg) |
| 志志雄 | [shishio](shishio.jpg) | 372 | 93 | 680 | [WebGL](web/shishio.jpg) |
| 自来也 | [jiraiya](jiraiya.jpg) | 372 | 85 | 700 | [WebGL](web/jiraiya.jpg) |
| 蒂雅 | [harribel](harribel.jpg) | 372 | 67 | 890 | [WebGL](web/harribel.jpg) |
| 葛力姆乔 | [grimmjow](grimmjow.jpg) | 372 | 114 | 690 | [WebGL](web/grimmjow.jpg) |
| 四代 | [sidai](sidai.jpg) | 372 | 148 | 800 | [WebGL](web/sidai.jpg) |
| 史塔克 | [stake](stake.jpg) | 302 | 79 | 870 | [WebGL](web/stake.jpg) |
| 纲手 | [gangshou](gangshou.jpg) | 372 | 78 | 880 | [WebGL](web/gangshou.jpg) |
| 八千流 | [baqianliu](baqianliu.jpg) | 372 | 81 | 900 | [WebGL](web/baqianliu.jpg) |
| 牛头白一护 | [yihuxuliu](yihuxuliu.jpg) | 372 | 94 | 720 | [WebGL](web/yihuxuliu.jpg) |
| 雏田 | [zhitian](zhitian.jpg) | 372 | 65 | 850 | [WebGL](web/zhitian.jpg) |
| 碎蜂 | [soifong](soifong.jpg) | 372 | 84 | 600 | [WebGL](web/soifong.jpg) |
| 水月 | [shuiyue](shuiyue.jpg) | 372 | 91 | 900 | [WebGL](web/shuiyue.jpg) |
| 涅音梦 | [nemu](nemu.jpg) | 372 | 80 | 860 | [WebGL](web/nemu.jpg) |
| 斑 | [ban](ban.jpg) | 372 | 78 | 700 | [WebGL](web/ban.jpg) |

## Browser run

The local release-format Web export uses the PR's game code and assets, plus a QA startup scene. The harness picks the assist through the selection grid, confirms the fighters and stage, runs the intro, places the fighters and gives P1 300 energy. Chromium sends an actual O keydown/keyup through DevTools. Each browser case recorded visible helper sprites, damage, the active duration and the return to root frame 1. Both final opponent HP and active tick count matched the Flash and native traces for every helper. Keyboard navigation of the complete menu, the public deployment, multiplayer transport and audio listening were outside this run.

## Visual findings

- Yachiru at tick 71 and Tsunade at tick 65 show a screen displacement and a missing top HUD in Godot during impact. Direct terminal replay reproduces the discrepancy. The Yachiru terminal screenshot is pixel-identical to the checkpoint image at that tick.
- Tsunade at tick 96 and Grimmjow at tick 132 show overhead 1P/2P markers in Flash that are absent in the sampled Godot images.
- Shishio's explosion at tick 82 and Suigetsu's red hit splash at tick 63 differ in orientation from Flash. These can be seen independently of the matching damage and receiver state. This audit does not isolate the random sequence or camera cause.
- The timer in the sampled Godot fixture displays 00. The Flash time also advances while the bitmap probe runs. These fixtures supply no matched wall-clock timer tape. The countdown is excluded from the matched field totals.

## Reproduction

Use the sibling summon fixture for each helper and add the five `bitmap_ticks` from [checks.json](checks.json). Build the diagnostic Flash reference with the original helper and `--sampling-bitmap`, capture it with the native projector, and decode its bitmap rows. The Godot checkpoint runner is the [existing roster runner](../../../characters/roster-live-2026-11-18/runners/checkpoint_visual.gd). For terminal images the standard move-case bitmap runner was restricted to those five ticks in both loops. The cross-check uses the existing actor and helper reference comparators without tolerance changes. Browser assets are from the same source revision and the QA package hash is recorded in the results.


The compressed files under `traces/` include the input fixture, original actor and helper events, and native projections for replaying both comparators. Full-size frame pairs for the HUD, player markers and hit effects are under `detail/`. The [QA scene script](runners/browser_case.gd) is attached to an otherwise empty Node scene used as the test export entry point. The [browser driver](runners/browser_keys.mjs) connects to a dedicated Chromium debug endpoint. The ordinary headed browser was throttled during concurrent native window captures. The completed 17-case browser run used an isolated headless Chromium WebGL session.
