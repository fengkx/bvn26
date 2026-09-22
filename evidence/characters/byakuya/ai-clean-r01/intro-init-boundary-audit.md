# Byakuya clean AI init boundary audit

This is a read-only audit. Native source is `/private/tmp/byakuya-ai-clean-r01/collected/events.jsonl`; Godot diagnostic output is `/private/tmp/ai-clean-polls4.json`. The machine-readable record is [intro-init-boundary-audit.json](intro-init-boundary-audit.json).

| Boundary | Original Flash | Current Godot runner |
|---|---|---|
| Load/first actor callback | P1 `frame_state_enter` seq 3, display 0, time 12029; P1 `initCtrl` seq 5, display 0. P2 `initCtrl` seq 10, display 1. Helpers load at P1 seq 9/display 1 and P2 seq 12/display 2. | `_enter_current_fight` calls `_initialize_fight`, which calls `start_action("站立")` for both actors immediately; no recorded load/enterFrame event is emitted in the probe. |
| Initial standing range | Both source timelines label `站立` at frame 1; next label `走` is frame 10, so standing range is 1–9. Paths: `game/fighter/yihu.swf`, `game/fighter/Byakuya.swf`; generated source entry is `DefineSprite_631/frame_1/DoAction.as#initCtrl` for Byakuya. | Both `start_action("站立")` begin at runtime frame 1 in `_initialize_fight`. |
| Intro start | First original `intro_poll` seq 43 at display 15; its state seq 44 observes P1/P2 frames 2/8. | Production `battle_intro.begin` is called from `_enter_current_fight`; the probe then calls `battle_intro.begin(..., true)` a second time (runner-only extra lifecycle). At probe intro tick 15 the observed frames are 1/1. |
| Ready / fight tick 0 | Original `ready` seq 2663 at display 452, then states seq 2665/2668: P1/P2 frames 7/2. | Probe logical tick 0 is recorded immediately after `_enter_current_fight`, before its first `_advance_fight`; it is not source display tick 0. |

Original first 15 fight ticks, `(fight_tick: P1 frame, P2 frame)`, are:

`0: 7,2; 1: 1,20; 2: 2,21; 3: 3,22; 4: 4,23; 5: 5,24; 6: 6,25; 7: 7,26; 8: 1,27; 9: 2,28; 10: 3,29; 11: 4,30; 12: 5,1; 13: 6,169; 14: 7,170; 15: 1,171`.

The source state rows report `paused=false` for fight ticks 0–15. There is no dedicated `rootpause` event in this capture, so the pause field is not inferred from `frame_state_enter/exit`. `battle_intro.begin` sets Godot `root_zhanting=true` during intro; after intro completion the runner state rows report `paused=false`.

The concrete boundary problem is therefore event/lifecycle alignment: source has a display/load/enterFrame phase through display 451 before Ready, while the current probe starts actors at runtime entry, omits the source load/display phase, and invokes `battle_intro.begin` twice. The first observed intro mismatch is already at source display 15 (source frames 2/8 versus runner 1/1). This evidence does not justify a production runtime fix by frame shifting or rootpause suppression.
