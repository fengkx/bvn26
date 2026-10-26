# Runtime source boundaries (r13)

## Root slot ownership

- Per-frame scripts: Sasuke sprite603 frames1228/1229 assign root p1bs/p2bs, store HP/energy on the wrapper, and replace feixue with a slot-specific callback. Frame1230 starts its root interval then writes wrapper 万解=true; frame1232 gotoAndStop(2).
- Placement: frame2 PlaceObject2 sprite1019 replaces the body at depth1; replacement load and initial frame precede the next body advancement.
- Leaving: explicit parent gotoAndStop; no label-end inference. Target doWanKai jumps to 开场1016, yielding1017 at the next observed phase.
- Invariants: root p1bs/p2bs are initialized from selected source names by main frame8 initFight, then only the selected slot is overwritten. Full retained script inventory contains no readers of these two properties; do not alter character menu/session selection as an invented consumer. Root maxhp controls the captured slot callback threshold; the callback ignores wudi and crosses the threshold by exactly10.
- Native comparison: native-sasuke-slot1/2 retain all child definitions/non-action tags. Both record replacement gap undefined HP, next671/234, body1017, live old reference, damage671→661, floor300 unchanged,301→291, pause291 unchanged at root maxhp1500. Observer aliases game.p1/p2 to its wrapper and explicitly seeds pn; this is a focused ownership probe, not whole-match image parity.

## Post-opening observation

Main DefineSprite1991/frame1 goStep(4) clears kcint; renderSkip does too. Later body replacement opening labels do not restart the match opening callback. BattleIntro therefore stops observing fighter frame tables when inactive. Looking up replacement directory names in initial-form tables was an invalid extra consumer, exposed by the real input smoke.

## Input activation

Generated source wankai predicates require energy>=300 and the authored attack+jump keys. The development disabled_actions guard is removed only after a source-bound complete profile manifest passes runtime preflight. Unsupported graphs remain blocked. Input smoke traverses natural match opening and real key/controller dispatch, not forced source frames.

Initial slot binding: Sasuke DefineSprite603/frame1/DoAction.as line909 assigns `pn = _parent._name != "p1" ? 1 : 2`. The source-validated initialization contract now executes this for admitted initial bodies as well as replacement bodies. Natural Main input tests assert the binding before transfer; no missing HP/energy default is used.
