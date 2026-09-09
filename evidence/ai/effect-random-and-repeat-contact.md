# Effect random calls and repeated source hit queries

Status: source-derived fixes and focused validation; full parity is still
unproven. This supersedes the missing `XG_qdj` random-call frontier in
[the preceding report](player-controller-and-binary-trace.md).

## Source chain and lifecycle

`scripts/main.json → frame_8/DoAction.as` defines `bdxg`: impact strength 2
calls `addChildXG(selfmc._parent,"XG_qdj")`. `addChildXG` attaches a new clip at
the next effect-layer depth, then assigns parent coordinates and X scale.
Offsets default to X=0, Y=-25. No existing effect instance is reused.

The imported main Sprite 256 timeline has 19 frames. Its only parent
DoAction scripts are frame 1 (root X write and two random offsets), frame 2
(root X/Y reset), and frame 19 (`this.unloadMovie()`). Frames 3–18 have no
parent DoAction and advance naturally. The sprite's graphics change on the
authored frames; its lifetime is not inferred from the next label.

Frame 1 expressions are `_X += random()*10 - random()*10` and
`_Y += random()*20 - random()*30`, written in expanded assignment syntax in
the source. The compiler now emits two `random_offset` events with ordered
consumer sites `main#DefineSprite_256_XG_qdj/frame_1/DoAction.as:1` through
`:4`. Unsupported `Math.random()` expressions fail compilation instead of
silently disappearing. The runtime uses the shared source random stream and
applies the resulting offsets in parent coordinates. Events are identified
by their compiled index, so two operations with the same name on one frame
are not collapsed.

The minimal [native attach probe](../probes/schedule/effect-attach/comparison.json)
verifies that the attach caller completes its coordinate assignments before
the new clip's frame-1 script executes. Four stubbed 0.25 draws produce
`(100,197.5)` from `(100,200)` even with `_xscale=-100`; uppercase `_X/_Y`
write the built-in coordinate properties. The next root callback observes
the completed four calls. The stub controls only this minimal probe and is
not a modification of the original game or its random tape.

```sh
python3 tools/probes/build_effect_attach_probe.py --ffdec /tmp/bvn-ffdec-26.2.1/ffdec-cli.jar --output /tmp/bvn-effect-attach-new
```

Main now queues newly attached effects' initial scripts until the caller
frame work finishes. Existing effect frame scripts run after actor playheads
advance and before actor callbacks in fixed Vs Com. The latter placement
removes the r13 display-742 extra movement before `pauseGame`; it remains a
partial scheduler integration, not a fully verified world event order.
Other source root-snapshot differences remain visible below.

## Repeated guard contact

`scripts/fighter/minren.json → DefineSprite_2/frame_1/DoAction.as` and the
corresponding Ichigo script define `getHitObj` as an ordered current-instance
lookup and hitTest. They do not maintain a per-attack hit-consumed flag.
`checkHit` still requires gameRunning and canhit. The defender's receiver
clip placement determines when this query runs.

In r13, Naruto's new frame-1005 guard receiver queries Ichigo's still-placed
attack again. Original sequences 6672–6678 return to frame 1002 and settle
another guard hit at 1003. The legacy attack cache suppressed that query in
native code, allowing the player guard controller to return to frame 991.
The source receiver path now performs a fresh current hitbox query and does
not use legacy cached contacts or consumed-instance filtering. The legacy
manual resolver retains its prior behavior; helper/stage lookup fidelity is
not established by this fighter-contact test.

## Comparison results and remaining differences

The original r13 input/random/clock files are unchanged. Reports and logs are
retained in [effect-random-validation](effect-random-validation/).

| Report | Result |
|---|---|
| r13-effect-init | Random failure removed; first differing boundary is 685, player expected 1002 versus actual 991 |
| r13-repeat-contact | All 1,166 expected boundaries match; all 298 post-checkpoint random calls and clock tape consumed; extra native boundary after reference end; first substantial X difference at display 742 |
| r13-effect-phase | Same boundary/random/clock coverage; first substantial X difference moves to display 785; extra end boundary remains |

The final report is still `first_difference`, not a passing golden trace.
It retains 35 root frame-pair mismatches and 24 per-actor state mismatches.
Boundary-order agreement does not establish that those scripts ran on the
same side of each root observer callback. The native report reaches display
1084, but emits an additional P1 frame-1 boundary absent from the captured
reference. This must be resolved against original termination/observer
ordering; the comparator has not been relaxed or truncated to hide it.

P1's maximum relative X difference is `4.000030517578125`; P2 relative X
matches. Neither actor has a Y or facing difference in this segment. Small
single-precision position differences also remain. Root shake assignment
semantics, full effect transform/visual comparison, all helper/stage behavior,
full boot and complete match/round/Web acceptance remain open.

## Checks

- [Five native checks](effect-random-validation/checks.json): random offsets
  and four calls once per attached instance, authored frame-19 unload,
  repeated source contact with canhit/pause gates, fixed effect clock,
  Vs Com entry and KO flow. Each expected marker was present without script
  errors. Resource-exit and macOS certificate warnings remain in logs.
- [Fourteen Python tests](effect-random-validation/python-tests.log): effect
  source inventory, random expression rejection and existing music contracts.
  Two old music expectations lacked already-generated random consumer sites;
  they were updated after checking both lexical calls in source
  `DefineSprite_1900/frame_1/DoAction.as`, without changing music behavior.
- Shared hit-effect sections in both base action and generated combat models
  were refreshed through the same compiler function as the main model.

No new Web/browser acceptance was performed. M5-03 remains pending.
