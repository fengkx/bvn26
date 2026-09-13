# Controlled Sakura helper / super overlap

This is a controlled test, not a natural no-intervention replay. The fixture keeps Sakura and the selected `松本` helper alive in one fight. It summons at tick 10 and begins down+special at tick 55. At tick 55, the instrumented original and GameWorld harness set Sakura's energy to 300 at their root observation boundary so the source 300-energy super gate can be tested while the helper attack instance remains active.

The source root frame 804 summons `松本` at fight tick 15. A `resource_intervention` event at tick 55 records source ql 200→300. Sakura enters `防御` at 56, `防御2` at 57, and `超必杀` at 58. The same helper instance is still attacking and its source `atm1` field is 1 through tick 68. P2 loses 60 HP at tick 56 (hits 1) and another 60 at tick 60 (hits 2); its pause begins at tick 61. The sequence is retained to verify actual overlap rather than an energy rejection.

`comparison.json` reports all 722 fighter observations exactly matched across the 14 source fields. `helper-comparison.json` reports all 722 helper observations matched across frame, position, orientation, action, and attacking; source-only helper `hits` and `atm1`–`atm3` remain visible in the retained source events and are not included in that six-field comparison. The two independent GameWorld replays produced byte-identical fighter, helper, and intervention outputs.

The first GameWorld harness pass is preserved in `port-first-pass-harness-phase/`. It applied ql after its tick-55 state row and therefore differed in that row only; the source intervention precedes the source tick-55 row. The corrected harness applies the intervention at the start of the matching root observation stage. No input tick, source trace, or original output changed.

This case validates the controlled scenario only. It does not claim natural overlap behavior without the documented energy change, nor full Sakura acceptance.
