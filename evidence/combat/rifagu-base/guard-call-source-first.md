# Guard callback call scope

The native scope probe confirms the call is undefined; compilation now preserves its no-op behavior.

1. Base Sprite 638 frame 887 places Sprite 14 at depth 30 with an enterFrame
   callback containing `fangyux();`. Sprite 14's own frame-1 controller does
   not declare this function. The body Sprite 638 declares it in frame 1:
   it returns during root pause, otherwise calls `_parent.moveX(-htx)`.
   Naruto and Ichigo base callbacks explicitly call `_parent.fangyux()`.
2. The instance remains through frames 887..891 and is replaced by a new
   Sprite 14 placement at frame 892. New callbacks first execute on the
   display after placement. Frame 888 invokes `onDefence()`.
3. Frame 892's replacement callback returns to `防御2` while defence is held.
   Source timeline placements, not the label's last frame, govern lifetime.
4. The two source spellings must not be silently compiled into the same
   body call. No receiver impulse or hitbox may be changed to compensate.
5. The retained guard-receive fixture starts P1 holding down and gives P2
   one normal attack. Original P1 X remains 300 at observations 16 and 17;
   the port moves to 297 and 294. Frame/action/energy and root shake match
   at the first difference. A dedicated probe records `typeof(fangyux)`
   and `typeof(_parent.fangyux)` from the original callback before deciding
   how to compile the call. Original and generated inputs remain unchanged.

The dedicated original records four callbacks with `undefined,function` for
`typeof(fangyux),typeof(_parent.fangyux)`. The compiler now distinguishes explicit
parent calls from unqualified calls and verifies that no controller or main
script supplies the unqualified function before emitting a no-op. It records
the source call site and root-scope bundle hash. Arguments on an unresolved
call and newly defined scope bindings are rejected instead of guessed.

After this compiler repair, both held-guard and guard-release routes match all
602 actor and 301 root-position observations each. The same four-route native
rerun also matches the normal-second-hit release and knockdown/recovery paths.
See [scope recordings](guard-call-scope/) and [route red/green comparisons](routes/).
