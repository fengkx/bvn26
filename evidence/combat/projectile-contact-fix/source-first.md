# Projectile contact source gate

The saved fixtures and source traces are unchanged. The fresh Sakura read-only
hit-receive observation in `fresh-sakura/` matches all 602 saved fighter states
exactly. Final validation is recorded in README.md and regressions.json.

## Frame scripts and callbacks

- Kakashi bundle `scripts/fighter/Kakashi.json`, Sprite 710, label 招1:
  frame 420 writes 动作=1 and ql+=5; 452 writes 动作=0; 455 goes to 站立
  and plays. Other DoAction frames in 419–480 are empty. Four projectile
  placements at 425/depth32, 431/depth30, 437/depth27 and 443/depth32
  initialize played=0 and movspeed=speed*2. Each EnterFrame tests its own
  bounds against opponent bdmn/zh1atm/zh2atm/zh3atm/abcd, then conditionally
  sets played=1, movspeed=0 and gotoAndPlay(3), else moves by movspeed.
  Sprite 244: frame 1 stop, frame 3 this._name="abcd", frame 9 stop;
  frames 2 and 4–8 have no DoAction.
- Sakura bundle `scripts/fighter/Sakura.json`, Sprite 630, label 招1:
  416 writes 动作=1 and ql+=5; 440 writes 动作=0; 453 goes to 站立 and
  plays; other DoAction frames 415–467 are empty. The frame417/depth36
  callback moves the owner backward by speed while unpaused; 433/depth36
  permits skill1 cancellation. The frame442/depth28 projectile initializes
  played=0, movspeed=speed*2. Its collision branch is the same but jumps
  to child frame 5. Sprite275: frame1 stop, frame3 rename to abcd, frame9
  stop; other child frames are empty. Jumping to 5 does not run frame3.
- Shared receiver: DefineSprite_2/frame_1/DoAction.as getHitObj queries the
  opponent's current attack names, without an already-hit flag. The receiver
  goto and the projectile callback are independent source operations.

## Placement lifetime

The listed projectile placements have move=false. Kakashi removes depth32 at
438, depth30 at445, depth27 at450 and depth32 at455. Thus old/new authored
zh1atm overlap at437 and old/new zh12atm overlap at443–444. Their local variables,
playheads, offsets and queued rename scripts belong to distinct instances.
Sakura removes depth28 at452. New placements initialize locals; MOVE retains
instance state. EnterFrame eligibility begins after placement.

## Exit and invariants

The parent exits are the explicit gotos above; child playback follows stop/goto,
not parent label boundaries. A settled receiver hit cannot replace the child
callback's collision test. Old/new same-name placements must not share state.
Sakura's skipped rename frame cannot remove its attack name.

## Original same-input evidence

Kakashi fixture/source: evidence/characters/kakashi/projectile-runtime-r01/ground/.
Sakura fixture/source: evidence/characters/sakura-ino/original/
catalog-neutral-r01-batch01-remaining/sakura-415-magichit1-neutral/.
The fresh Sakura probe reproduces the original 602 states. Inside receiver
callbacks at fight ticks37 and53, zh12atm is at child frames1 and6 respectively,
and both hitTests are true. Root observations settle these at ticks39 and55.
The baseline native has 262/492 differing states. Tests must retain exact
comparison and full row counts; no hitbox/HP/input/tolerance adjustment is allowed.

## Other implicit receivers refreshed by the same compiler correction

The recorded EnterFrame paths in MinRen Sprite764/frame382/child260, YiHu
Sprite638/frame150,327,421/child99, RiFaGu Sprite638/frame154/child106 and
Byakuya Sprite631/frame148/child109 contain the same bare `hitTest` calls.
Only their query receivers are refreshed; placement lifetimes, parent and child
frame scripts, motion, stop/goto/rename rules and explicit child receivers are
unchanged. YiHu frame327 retains its explicit `hitmc` receiver for zh3atm.
Their 19 saved same-input comparisons are rerun after refreshing the metadata.
