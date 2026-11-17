# Live audit: incomplete hit packets and stale form frame calls

The full input matrix found a native error in Hitsugaya Bankai's down-special.
The baseline is PR #302 (`cffb4ea767ea4a3f2dead44c3620a467178b819d`).
Original/native traces are retained under the task capture directory pending archive.

## Five source questions

1. `scripts/fighter/rifagu.json`, `DefineSprite_951/frame_749/DoAction.as`
   flashes, followed by `DoAction_2.as` calling `cbsd(pn)` and `showFace`.
   The existing compiler supports ordered multiple DoAction tags, but the cached
   form AI omitted the second tag. Fresh compilation also identifies omitted
   numbered tags in Ichigo Bankai (243) and Naruto One Tail (588, 589, 1085).
   The source inventory archive retains all BODY frame/clip scripts and timelines
   for the five forms; empty frames remain explicit in their locked timelines.
2. `cbs2atm` is an authored placement in the second down-special section. The
   original `getHitObj` reads each packet field directly from `gjl2`. Wrapper
   `frame_1/DoAction.as` supplies only `cbs2pw=0` and `cbs2tm=5000`; missing
   `zl/up/x/dz` values are undefined, not a default hit reaction or impulse.
   Receiver Sprite 2 and the BODY retain their existing instance/state lifetimes.
3. Sprite 2 `beida` writes the packet to BODY fields then calls
   `gotoAndPlay(htype)`. A missing target is not an invented `被打` target.
   The original reference preserves the current receive animation while the
   undefined movement operands prevent another displacement. Explicit source
   `cbsd/cbsw` boundaries continue to control the later freeze and recovery.
4. Assertions must preserve packet absence, source tag order, the current receiver
   frame and original movement/pause state. No zero impulse, synthetic hit reaction,
   larger hitbox or character-specific runtime branch may stand in for the source.
5. The original `rifagu-2-bishaSuper-hit` input was captured before runtime edits.
   Native first diverges at tick 14 because the cached frame 749 omitted `cbsd`.
   At tick 106 original Sprite 2 records a packet with undefined strength/target;
   native raises an invalid `horizontal_impulse` dictionary access. The original
   subsequent receiver Y is -85, while the failed native continues to -90.
   Preserve the full baseline and compare the same input after repairs.

Shared receive-chain source tests: 35 fighters, 26 helpers and observer invariants
pass (9 tests). Original ordinary block, incoming break and mirrored incoming break
for Hitsugaya Bankai already match all recorded actor/root fields with the real
source guard branch observed. The rest of the matrix remains in progress.

## Repair observations

The first repair retained undefined packet fields but exposed a second mismatch:
converting a NaN transform to native integer twips reset the receiver to the
origin. Original tick 106 and subsequent samples retain the preceding coordinate
when an undefined impulse participates in the BODY movement expression. Both
source coordinate setters now ignore NaN assignments before twip conversion.
The corrected down-special and mirrored down-special each match all 722 actor
states and root positions. All 20 Hitsugaya fixtures currently match.

The battle checkpoint stores the owned Variant graph as packed bytes, preserving
undefined source fields and NaN derived movement caches. The dedicated
`rifagu_partial_hit_rollback_smoke.gd` observes the authored incomplete packet,
saves at that boundary, restores and replays the remaining fight, and checks an
identical final checkpoint. This passed without changing serialization rules.
Player controller, visual smoke and Ichigo nested transformation graph regressions
also passed; the full remaining original matrix and browser UI check are pending.
