# Down-ranged projectile correction

The retained `mayuri-ranged` input first diverged at tick 164: Flash P2
entered frame 751 while Godot remained at frame 5. At tick 165 Flash HP
was 740 and Godot HP was 890. The original failed native trace remains in
`diagnostics/`; neither the source trace, input nor comparison tolerance changed.

## Source-first answers and lifecycle

- Root `DefineSprite_487/frame_395/PlaceObject2_220_28` creates `abcd`.
  Its source lifetime is root frames 395–443. The new placement starts a
  new local state; retained MOVE records keep the current instance.
- Sprite 220 frame 1 initializes `movspeed=15`, `played=0` without stopping.
  The callback tests the authored opponent body/attack instances before movement.
  On contact while `played==0`, `gotoAndStop("hit"); play()` selects frame 15,
  as confirmed by the extracted SWF `frame_labels.hit` value.
- Frames 15 and 16 rename the clip `zh2atm` and set `played=1`.
  The separate `if(played==0)` movement branch remains after the collision
  branch; it is not an `else`. Frame 48 stops the local timeline.
- The previous compiler silently omitted this non-stopping initialization,
  named stop/play pair and movement guard. Consequently the runtime used the
  fighter movement fallback and reached the renamed hit clip too late.
- Existing Flash same-input capture supplies the behavioral baseline. The
  first corrected replay matches all 722 actor states and all 14 fields with
  complete tick/slot alignment. It proves this fixture, not all projectile
  boundaries, audiovisual parity or an unlocked capture environment.

| State | Owner | Writes / preservation | End |
|---|---|---|---|
| `movspeed` | placed Sprite 220 instance | frame 1 sets 15; retained while placed | instance removal |
| `played` | same instance | frame 1 sets 0; frames 15/16 set 1 | instance removal |
| local playback | same instance | natural advance; collision selects `hit` 15; frame 48 stops | instance removal |
| source name | same instance | placed as `abcd`; frames 15/16 rename to `zh2atm` | instance removal |
| local X | same instance | callback adds movspeed only while played is zero | instance removal |

The common compiler resolves the label against the actual child definition,
preserves initialization and guarded motion, and emits the frame-local write.
The shared runtime executes that compiled write in the existing child-frame
queue. There is no Mayuri-specific runtime branch, enlarged collision box,
fixed hit delay or altered input. Unknown label targets fail compilation.

The source also has color flashes at Sprite 220 frame 17 (`8978176`) and
Sprite 464 frame 42 (`4580164`). These compile into the existing screen-flash
event handler. This wiring is source-derived; visual equivalence remains
unaccepted without aligned original-player images.

The ultimate's Sprite 464 separately initializes only `played=0` at frame 1,
renames to `cbsatm` and writes `played=1` at frame 40, and stops at frame 45.
Its root-871 callback adds X=10 only while played is zero. The same generic
compiler now preserves this scalar-only initialization and movement-only
guard. A diagnostic rollback run exposed the initially missed scalar-only
initialization; it is retained as a failed intermediate run, not counted as
acceptance. A complete original ultimate capture is still required.
