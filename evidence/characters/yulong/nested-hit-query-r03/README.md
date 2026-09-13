# Yulong getHitObj packet alignment r03

This capture instruments an isolated player build. The locked source SWFs and retained source bundles were not changed. The receiver probe captures one `hitTest` result, reuses it in the original branch, and writes a log only on the original first-hit return path. The separate child markers preserve source frame 7 rename and frame 8 StartSound order.

The native receiver selected `zh2atm`/20 damage/被打 at attacker frame 468, `zh2atm`/20 damage/被打 at attacker frame 472 before frame 7's rename, then `zh21atm`/100 damage/击飞 at attacker frame 476. Mapping each native `fight_tick` to the next Godot state tick (`fight_tick + 1`) aligns the same attacker frames, instance names and packets with the stable Godot contact log. Godot's current case also matches all 602 native state rows exactly.

The frame 8 native sound marker follows the fight 48/root 472 state observation. It does not directly log the parent playhead, so root 473 at the event is inferred from the source's within-tick advance and the following root 473 state. Godot records frame 8 at fight tick 49/root 473, consistent with that phase. This evidence does not support a one-tick runtime correction.

`events.ai-ref` is the raw native trace. `packet-alignment.json` preserves selected source/Godot observations and runtime hashes. The three Godot state/playhead/sound files are the final rerun and match the previously accepted stable outputs byte-for-byte after JSON parsing.
