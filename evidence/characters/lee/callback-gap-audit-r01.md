# Lee callback inventory offline gap audit r01

This is a read-only audit of the locked Lee callback inventory and retained source/native traces. It does not change the compiler or runtime and does not promote callback coverage from state-frame observations.

## Inventory facts

- `evidence/characters/lee/source-callback-inventory-r01.json` contains 167 Lee callback entries: 111 compiled frame dispatches, 44 player-controller hooks, 10 receiver hooks and 2 player-body hurt hooks.
- 118 entries have a source exact-frame observation marker; 49 remain `source_observation_pending`.
- The pending classification is 49 entries: summon 1, KO/recovery 13, audio callback-frame 2, native/source trace 21, round lifecycle 6 and special continuation 6.
- The pending set has 48 unique source frames. Its selected state-cover cases cover only 12 of those frames. State-frame presence is not callback-observer evidence.

## Target frame audit

- `DefineSprite_518/frame_29/DoAction.as` (`瞬步`) is compiled as `compiled_frame_dispatch`, but remains `native_source_trace_pending`. Retained Lee traces contain the state frame in 23 files, while no retained file contains the exact callback-observer event for this path. This is compile/static plus state coverage, not callback execution proof.
- `DefineSprite_518/frame_1017/DoAction.as` (`招换`) is compiled and `mapped`, but has no retained fixture state-frame observation and remains `summon_pending`. It has no source callback-observer promotion.

## Valid source-observer scope

Three immutable observer captures are explicitly Lee-slot filtered:

- `lee-callback-observer-recovery-r01`: Lee `p2`, 2,136 Lee observer events; observed exact enter-frame paths at 1088, 1098 and 1133. Promotion remains pending because source callback path/state preconditions are not mapped to Godot.
- `lee-callback-observer-kill-r01`: Lee `p1`, 2,032 Lee observer events; observed paths at 366, 605, 653, 681 and 688. This is a kill-negative observer run and is not proof for frame 29 or 1017.
- `lee-callback-observer-hp1-r01`: Lee `p2`, 2,210 Lee observer events; observed paths at 1075 and 1076. Its source preconditions and horizon differ from the current validated 625 pair, so it is not promoted as a general callback result.

All three captures report `body_call_scope_events=0` and retain `promotion=pending`. The observer inventory is filtered to `fighter/lee#`; it does not use the earlier mixed P1 一护/P2 小李 interpretation as Lee callback evidence.

## Acceptance boundary

Already supported by actual same-input evidence: current Lee 602-state action matrices, clean 625 kill/dead 802-state comparisons, and the explicitly listed observer paths above. Compile/static mapping covers the remaining inventory entries, but exact callback entry/placement/lifetime evidence is still missing for the 49 pending entries, including frame 29 and frame 1017. No runtime change is justified by this audit.
