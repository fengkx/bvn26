# Transformation start call — source-first audit

Scope: interpret the previously dropped `wankai_start()` call, not form replacement.

1. `scripts/fighter/yihu.json::DefineSprite_638/frame_967/DoAction.as` calls `wankai_start()` then `showFace`. The complete function at `DefineSprite_638/frame_1/DoAction.as#wankai_start` writes action=3, bs=1, subtracts 300 ql, sets jump=1, then calls cbsd(pn), in that order. Frame 963 already subtracts 300; the second subtraction must remain even when ql becomes negative.
2. This repair introduces no placement. Existing frame 967 display-list entries and lifetimes remain as extracted in `data/slices/yihu-base.timeline.json`; the function does not create or move a clip. Its root cbsd call uses the existing shared source super service.
3. Neither the call nor its function changes the playhead. Playback continues through the same timeline; later wankai/form replacement is a separate unresolved operation.
4. Assert source statement order and exact energy/pause values, not a gameplay assumption that energy cannot go negative. Reject any unrecognized statement in this admitted function.
5. The retained neutral original recording first differs at tick 16: original ql=-300 and both actors paused, versus native ql=0 and unpaused. Keep that recording and the pre-fix trace unchanged; compare the repaired prefix and retain the later form-exit failure.
