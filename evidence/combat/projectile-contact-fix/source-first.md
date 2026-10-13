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


## PR review: complete contact locals and post-contact motion

The previous refresh only updated query receivers for Naruto/Hitsugaya/Ichigo.
The same `build_combat_model.build_model` compiler now regenerates the entire
`projectiles` field in both action and runtime artifacts, including load locals,
one-shot grouped writes, child frame counts, and source provenance. Controller
hooks use the same `parse_projectile_motion`/`parse_projectile_initialization`
functions. No production runtime code changes are required. Kakashi's rebuilt
`motion_windows` exactly match the runtime's existing 12 windows (the action
artifact had only 10); no manual window is added.

- Naruto Sprite764, 招1 375–411: frame376 writes action=1/ql+=5; frame401
  writes action=0; frame408 gotoAndStop(站立)+play. Other DoAction frames are
  empty. The depth36 callbacks at385 allow bisha/magichit2; at401 they also
  allow rush. Depth28 is a new PlaceObject of Sprite260 at382, removed at404.
  Its load initializes played=0 and movspeed=speed*2. Its next-frame callback
  queries bdmn/zh1atm/zh2atm/zh3atm/abcd, guarded by !zhanting. On contact,
  played==0 groups played=1, movspeed=0, gotoAndPlay(5); otherwise X+=movspeed.
  Child260 stops at3 and11, renames to abcd at5; other child frames are empty.
- Hitsugaya Sprite638, 跳招 136–185: frame137 writes khit=1/jump=1/action=1,
  ql+=5; frame154 calls shine(4312815); frame180 gotoAndStop(落2)+play.
  Other DoAction frames are empty. The depth36 callback at144 shifts parent
  X by -facing while opponent.sw==false and shifts Y by -1, unless paused.
  Depth28 is a new Sprite106 at154, removed at175. Load initializes played=0,
  movspeed=speed. Its hit branch matches Naruto; the else branch adds
  movspeed to both X and Y. Child106 stops at1 and15 and renames at5;
  other child frames are empty.
- Both new placements have move=false and start EnterFrame on the following
  root frame. The numeric child goto, stop frames and explicit parent exits
  determine playback; label end frames do not return to standing.
- Source invariant: after the guarded contact sets movspeed=0, losing the
  collision cannot restart motion. Compare the child's frame/X/Y/played/
  movspeed at the same root observation used for fighter states, including
  after its rename. The probe follows authored depth and ignores unrelated
  decorations without a played local. It never writes gameplay fields.
- Same-input source evidence: `projectile-states/` retains original Flash
  Debugger captures for Naruto neutral ranged and Hitsugaya guarded air ranged.
  The inputs/setup are copied from the saved corpus; only the read-only
  projectile observation configuration is added. Full fighter and child
  comparisons, red traces and reproduction commands are recorded there.
