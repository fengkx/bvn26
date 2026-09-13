# Uryu coverage batch 02 and helper action lifetime

This is a partial source-backed acceptance batch, not a whole-character completion claim. Seven original Flash cases use the locked Uryu/Yihu fighters and explicit 我爱罗/魂 helpers. Each produced 602 fighter/helper observations with the intended source target reached. The exact fixtures, builds, captures, current GameWorld rows, and comparison JSON are retained beside this report.

| Case | Source path / target | Fighter | Helper comparable fields | Root position |
|---|---|---:|---:|---:|
| Air ranged / 跳招 | `scripts/fighter/yulong.json`, `DefineSprite_345/frame_1/DoAction.as`, `onJumping`; 153–163 | 602/602 exact | 602/602 exact | 301/301 exact |
| Guard loop / 防御 | `scripts/fighter/yulong.json`, `DefineSprite_345/frame_1026/PlaceObject2_14_44/...`; 1025–1036 | 602/602 exact | 602/602 exact | 301/301 exact |
| Tapped ground chain / 砍1→砍2 | `DefineSprite_345/frame_1/DoAction.as` → labels 183–246 | 602/602 exact | 602/602 exact | 301/301 exact |
| Incoming hit and recovery | Yihu controlled attack; Uryu frames 1049–1132 | 602/602 exact | 602/602 exact | 301/301 exact |
| Up ranged / 招3 | `DefineSprite_14/frame_1/DoAction.as` `magichit3`; 277–312 | 602/602 exact | 602/602 exact | 301/301 exact |
| Summon / 招换 | `DefineSprite_345/frame_968/DoAction.as` → `doZhaoHuan()`; 963–1024 | 602/602 exact | 602/602 exact | 301/301 exact |
| Same-instance summon repeat / 招换×2 | same source path; helper placed at ticks 15 and 145 | 602/602 exact | 602/602 exact | 301/301 exact |

The first summon case preserved the actual pre-fix red: source and Godot each had 602 helper rows, with 201 differing `action` values. First difference was fight tick 100, P1 helper frame 1 at x=20/y=-200, source `动作=1` and port `0`. The saved red comparison is `gamework/baseline-red/yulong-summon.helpers.comparison.json`.

Source review resolved the lifecycle. `scripts/fighter/fz/woailuo.json` frame 1 initializes the clip hidden and stopped; frame 13 writes `动作=1`; frame 85 only calls `_root.fzccXg(this)`. That call adds an effect; it does not clear the helper action. The clip returns to hidden frame 1 with `动作=1`. `scripts/main.json` defines `removeFZ(mc)` with an explicit `mc.动作=0`, but a search of the locked scripts found no call site. `godot/helper_runtime.gd` now clears this field only for explicit `deactivate()` calls; natural clip completion and source `gotoAndStop(1)` preserve it. The helper's next `activate()` reuses the retained value, matching the same source instance lifecycle.

The repeat trace contains two source `helper_spawn` events at fight ticks 15 and 145. P1 helper action remains 1 at hidden frame 1 on tick 100, remains 1 immediately before the second placement at tick 145, and is still 1 after the second activation at tick 146. The current native GameWorld replay matches all 602 fighter rows, all 602 comparable helper rows, and all 301 root-position rows exactly. Capture run ID: `moves-yulong-summon-repeat-35283c5d28`; source event SHA-256: `ca3938b0638a3b096b82140899e6e066b928667fe6a088debcc90fd2829daf0a`.

The updated `godot/tests/ai_helper_state_smoke.gd` verifies woailuo action 1 survives natural completion and another activation, then verifies explicit deactivation clears it. `ai_helper_state_smoke`, `kon_helper_smoke`, and `you_helper_callback_order` pass. Existing Sakura/Jinye repeat-swap and super-overlap traces also match fighter and helper comparable fields (722/722 each); those source captures contain no `root_position` events, so that field was not compared.

`godot/tests/combat_smoke.gd` still fails at its existing line 177 assertion on the Naruto `zh1atm` local projectile offset. To check whether the helper edit caused it, the test was run in an isolated Godot directory after restoring only `godot/helper_runtime.gd` from `git show HEAD:godot/helper_runtime.gd` and regenerating that copy's Godot class cache with Godot 4.7.2. The same line 177 failure reproduces. This is a helper-file A/B control, not a full clean-HEAD run; the assertion remains unchanged.

Runtime hash: `godot/helper_runtime.gd` SHA-256 `fdc9a9632d33e90c1f9c4f30e0d7c3a7880fcef8ff9601dc02674fad5a5b0559`.
Test hash: `godot/tests/ai_helper_state_smoke.gd` SHA-256 `ab9cc1924247c549d28f33c4e1d81215b05c87124c700f866edab346ec02ae1f`.

No sound-event fields or rendered key-frame images were captured in this batch. The current AI reference probe records no sound-event kind, so audio and visual-timeline parity remain open coverage items.
