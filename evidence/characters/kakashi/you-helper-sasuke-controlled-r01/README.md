# Kakashi + You vs Sasuke: controlled helper hit check

This is a bounded reproduction check for the report that Kakashi's You assist animation plays but never hits. It does not claim full Kakashi parity and makes no production runtime changes.

## Controlled setup

Both captures use the existing mode-2 battle path and 现世, with Kakashi/P1 selecting 鼬 (the You helper SWF), Sasuke/P2, floor-level positions P1 x=300 and P2 x=350, and 300 energy for P1. P2 receives no movement, attack, guard, or assist input. In the Flash fixture this is achieved by setting `p2cpu=false` while retaining `modo=2`; the fighter, helper, receiver, damage, and timeline code stay active. In Godot the same player-controlled empty-input path is selected for P2. Neither side is repositioned after setup.

The original fixture injects the existing source key reader with O (key code 79) on fight ticks 10–12. The Godot check sends a real `InputEventKey(KEY_O)` for three ticks after ten neutral ticks. The original records the controlled setup (`x=300`, `x=350`, `ql=300`) and the O key read before the helper spawn.

## Result

The original and Godot both spawn the selected You helper at x=280, y=-25, facing right. Sasuke remains at x=350, y=-25 with no defense or movement input. Both receive four hits and end at 780 HP (1000→960→920→880→780); both enter Sasuke's hit state and the final hit enters knockback. The original hit observations are at fight ticks 101, 116, 132, and 148; Godot records hit settlements at 100, 116, 132, and 148. The first-hit one-tick offset is unresolved; it is not normalized away. The subsequent three hit ticks and total damage match.

This controlled case does not reproduce “zero hits.” It does not determine whether a free-moving Sasuke CPU evades or interrupts the assist in the user's natural VsCom match. An earlier free-AI observation is retained outside this controlled result and is not used as a parity conclusion.

## Source path

- Kakashi's source call is in `scripts/fighter/Kakashi.json`, `DefineSprite_710/frame_1035/DoAction.as`, which invokes `_root.yfgj(_parent._name)`. The preceding summon path controls whether O is read and spends energy; the fixture supplies 300 energy so that the input reaches the source call.
- You's outer helper timeline and attack clips are in `scripts/fighter/fz/you.json`. The nested contact clip `DefineSprite_24` checks `hitTest` against the opponent's `bdmn` at its frame 48; the contact path, not the spawn animation, determines whether it enters the attack sequence.
- `godot/generated/main/character_selection/available.json` maps 鼬 to `you`; `godot/generated/helpers/you/combat.json` identifies helper 鼬 and source `game/fighter/fz/you.swf`. `Main._replace_selected_actors` resolves the selected helper through this mapping, and the runtime's helper-spawn signal activates that selected helper instance. Kakashi's authored `summon_events` retains the default helper label 我爱罗, but runtime activation here uses the selected 鼬/You instance; the capture confirms its helper identity and four damage applications.

## Evidence and limits

- `native-events.jsonl` is the task-scoped original Flash trace (run id `kakashi-you-sasuke-vscom-controlled-r01`, 9,247 events, `done=true`).
- `godot-events.jsonl` is the local mode-2 GameWorld trace; `godot-run.log` contains the headless process output. It has no `SCRIPT ERROR`; the log includes platform CA-certificate and user-log-path messages plus shutdown resource-leak diagnostics.
- `controlled-fixture.diff` shows the isolated source fixture change. `build.json` records the source/output hashes and setup. Locked `game/` and `scripts/` inputs were not changed.
- The test bypasses only the opening presentation in the Godot probe, then runs the production GameWorld combat path. It is a fixed-target hit-control, not a complete end-to-end menu or free-CPU test.
