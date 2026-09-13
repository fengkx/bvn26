# Kakashi projectile source/runtime checks r01

Status: the two selected projectile cases match the original at all 602 fighter observations and all 602 helper observations. The evidence covers actor state and hit settlement in these inputs; it does not directly expose each child clip's `played`/`movspeed` locals.

Both original Flash builds used explicit P1 helper 鼬 and P2 helper 魂, a 300-tick fixture, and a checked `case.txt` bound by the final SWF's LoadVars URL. Each `build.json` records the source and output hashes, run ID, and helper asset mapping. `source-events.jsonl.gz` contains only that run ID's filtered and collected events.

| Case | Source target reached | Source outcome | Native result |
|---|---|---|---|
| `kakashi-air-ranged-neutral-r01` | `跳招` entered at frame 156 on tick 21; `tzatm` source frame 162 on tick 27 | P2 takes 50 damage at tick 30; 1 hit | fighter 602/602 and helper 602/602 exact |
| `kakashi-ground-ranged-contact-r01` | `招1` entered at frame 419 on tick 11; projectiles appear at frames 425, 431, 437, 443 | P2 takes four 30-point hits at ticks 18, 24, 30, 37; ends at 880 HP with 4 hits | fighter 602/602 and helper 602/602 exact |

The deterministic Kakashi combat build retains source evidence for the changed fields:

- `tzatm` at frame 162: its placed clip's load callback sets `movspeed = _parent.speed * 2.5`; while not paused its enterFrame callback advances both local X and Y by `movspeed`.
- Four `招1` projectile instances at frames 425, 431, 437, and 443: each initializes `played=0` and speed from its parent; the hit callback checks the recorded receiver/target list, writes `played=1` and `movspeed=0`, and goes to child frame 3 once.
- `dogs` placements at frames 816 and 823 are compiled from AS source line 3; `cbs1atm` placement at frame 887 is also source-derived. These placement fields were not separately triggered in the two projectile fixtures; code/source-path review confirms they preserve the line-3 source call order.

The shared exact comparison checks frame, position, facing, action, HP, energy, pause, hit count, and the remaining recorded fighter fields. The local `kakashi_projectile_semantics.gd`, `ai_projectile_instance_variables_smoke.gd`, and `ai_projectile_driver_smoke.gd` tests passed. `ai_projectile_source_smoke.gd` still has its previously recorded failure at line 51 on the Yihu fixture's receiver-name expectation; this Kakashi artifact does not modify Yihu or that test.

The previous Kakashi 20-case original traces were not available at their documented `/private/tmp` paths, and the checked-in regression report contains summaries only. No unrelated cases were recaptured. This evidence does not claim coverage for every Kakashi move.
