# Lee source control-flow audit: frames 62, 738, and 1149

This is a source-only reachability audit. It does not claim that a retained native capture executed any of these callbacks, and it changes no compiler or runtime code.

## Locked inputs and method

- Original input: `game/fighter/lee.swf`, SHA256 `2443dc112dbf2be696abb9d924831814ae01990536df8298fa2c1432f35c93d1`.
- Decompiled script bundle: `scripts/fighter/lee.json`, SHA256 `82230e0e97e0b2751ecba3e27b6f82e46c467ae956c51b0a2ba4d9c114c7e967`.
- Timeline/source-tag index: `godot/generated/fighters/lee/timeline.json`, SHA256 `4d0a4c5d6f50f9bdd636555a4b1ca9701c988cdb68c7e51d3e716099aaeba49e`; its embedded SWF hash matches the locked input. The indexed XML export is `lee.xml`, SHA256 `d729bc2ee1858be875af7e6275a801c71e996245a1719e7897d382ba5f251069`.
- Combat compilation index: `godot/generated/fighters/lee/combat.json`, SHA256 `b2e39de15cff390747f4a6906897ec3499aaa009f409eed26479974c082c5ef0`.

I enumerated the 183 script entries in the Lee bundle, the complete frame-label/change index for `DefineSprite_518`, numeric and named `gotoAndStop`/`gotoAndPlay` calls targeting that fighter timeline, plus `scripts/main.json` calls made on `game.p1.mc` and `game.p2.mc`. The only literal numeric gotos in the Lee bundle target the separate `AImain` child at frames 1/2. Fighter-root transitions use named labels; no target frame among 62, 738, or 1149 has a label.

## Frame 62

`DefineSprite_518/frame_62/DoAction.as` is unconditional: `gotoAndStop("落"); play();`. In the source timeline, frame 50 is label `落` and frame 66 is label `跳2`; frame 62 is twelve frames into the `落` segment. It has no PlaceObject/MOVE changes of its own. The display list inherited at 62 has the fall artwork at depth 27 and the active `PlaceObject2_18_36` enter-frame clip at depth 36, which was placed when label `落` began at frame 50. That clip calls `onJumping(3)`.

The source controller can enter `落` during a normal jump. In `DefineSprite_518/frame_1/DoAction.as`, the gravity branch with `jumped == 1` goes to `落` and resumes playback. In `DefineSprite_18/frame_1/DoAction.as`, the jump/air callbacks continue to read normal player keys. This establishes a normal-input route to the segment, but does not prove frame 62 will occur on every jump. `onJumping(3)` leaves the segment when `_parent.touch == true` and the appropriate step is 3 or 6, sending the fighter to `落地`; holding jump can also enter label `跳2`. The flag is the Lee root fighter's contact state, not a DOM touch event. Root frame-1 code sets it true at the floor, on a blocking-platform hit, or when clamping to the floor; it sets it false while airborne. Therefore frame 62 requires enough airborne, non-contact playback time to reach the twelfth tick after frame 50. The short/held-jump traces discussed in the task do not themselves establish that precondition. A useful source-valid capture would create a sufficiently long fall (for example, a source-observed high launch), then verify `touch == false` across the 50→62 interval and observe the exact frame-62 callback. Do not label a generic jump capture as frame-62 proof.

## Frame 738

`DefineSprite_518/frame_738/DoAction.as` is unconditional: `gotoAndStop("空中必杀1"); play();`. The timeline labels are frame 701 `空中必杀`, frame 723 `空中必杀1`, and frame 740 `空中必杀2`; 738 has no PlaceObject/MOVE change. The compiler's `timeline_fallthroughs` records the 701→723 air-super continuation.

There is a normal player-input route into this segment. `DefineSprite_18/frame_1/DoAction.as` defines `bishaAir`: it requires `ql >= 100` and, for a human controller, the fighter's `必杀` key; its airborne callback goes to label `空中必杀`. The player binding is I for P1 and N5 for P2. On frame 723 the timeline places character 381 at depth 34 with `DefineSprite_518/frame_723/PlaceObject2_381_34/CLIPACTIONRECORD onClipEvent(enterFrame).as`. That callback, while the root is not paused, calls `moveY(-20)` and only switches to `空中必杀2` if the parent fighter's `touch` flag is true. If contact remains false, it does not jump ahead; frame 738 is reachable in the 723→740 segment and its action loops back to 723. This is a conditional path, not an earlier unconditional skip. A source-observer fixture should start a real airborne special with at least 100 energy, preserve `touch == false` through the 723→738 interval, and record both the depth-34 callback and the root frame. An opponent placed out of contact range avoids conflating this with hit resolution.

## Frame 1149

`DefineSprite_518/frame_1149/DoAction.as` only performs `_root._y += 2`. Frame 1149 has no label and no PlaceObject/MOVE change. The adjacent labels are frame 1133 `起身` and frame 1158 `开场`.

The only ordinary source entry into `起身` found in Lee's fighter bundle is the clip action at `DefineSprite_518/frame_1098/PlaceObject2_18_29/CLIPACTIONRECORD onClipEvent(enterFrame).as`: it requires `gameRunning()` and `standup()`, then calls `gotoAndPlay("起身")`. For a human, `standup()` reads the normal `冲` key while `sw == false`. The `起身` timeline then reaches `DefineSprite_518/frame_1144/DoAction.as`, which unconditionally calls `gotoAndStop("站立"); play();` before frame 1149. This breaks the only sequential path from 1133 to 1149. No label resolves to 1149 and no numeric goto to 1149 appears in the Lee fighter bundle. Main-SWF calls on the actual fighter clip (`game.p1.mc`/`game.p2.mc`) use named labels such as `开场`, `站立`, `胜利`, and `失败`, not numeric 1149. `DefineSprite_1900/frame_5/DoAction.as` does contain `game.p1.gotoAndStop(p1frame)`/`game.p2.gotoAndStop(p2frame)`, but those calls target the outer player wrappers; the main's fighter clip is the nested `.mc` addressed separately by the named-label calls. Thus the retained source supports the conclusion that frame 1149 is not normally reachable through Lee's gameplay input/state paths. This is a static call/label/placement conclusion, not proof that no external debugger or synthetic forced-frame tool can invoke it.

## Acceptance boundary

Frames 62 and 738 have conditional, ordinary-input source paths, with additional contact/airtime constraints that need callback-level source observation for promotion. Frame 1149 has no normal gameplay path in the enumerated source control flow because the unconditional frame-1144 return intercepts the only sequential `起身` route. No runtime change is justified by this audit.
