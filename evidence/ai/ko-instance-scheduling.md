# KO instance scheduling and round continuity

Status: the retained r13, r14 and r15 captures match the currently compared
fighter fields. Full gameplay, geometry, presentation and Web parity remain pending.

## Source-first basis

- Frame scripts and empty timeline frames: `ko-display-source.json`,
  `godot/generated/main/ko/timeline.json` and `controller.json` retain the
  KO root (1858), winner (1844) and nested clips. Scripts remain compiled by
  `tools/importer/compile_ko.py`; this change adds no character or frame-number
  exceptions to the runtime.
- Placement: root frame 56 creates the HUD and KO before asynchronously loaded
  fighters. KO frame 93 creates a new winner instance. Retained placements keep
  their registration; removed instances cancel callbacks and queued scripts.
  `match-timeout-source.json` retains root/HUD ancestry. The native
  `../probes/schedule/effect-order/comparison.json` confirms that instance order
  interleaves callbacks and frame scripts across subtrees.
- Exits: compiled goto/play/stop operations remain authoritative. KO root frame
  30 resumes after the actor phase; winner frame 40 pauses before older actors.
  Both observations occur in r15, source sequences 49224–49228 and around 49810.
- Invariants: an older root and a newer child cannot be represented by moving
  the whole KO tree before or after fighters. Tests use real compiled KO clips,
  exercise both sides of an intervening actor callback, and cancel a removed
  child's queued winner script. The previously failing resume fixture is now
  `godot/tests/vs_com_ko_resume_smoke.gd`.
- Original input: `match-flow-r15/events.jsonl` is unchanged. r13/r14 inputs and
  random tapes are also unchanged. Native replay does not overwrite per-frame
  fighter state or adjust expected outputs.

## Runtime changes

`KoTimeline` registers each live instance independently with the shared callback
registry. Its playhead still advances separately; each registration executes its
own callback and pending frame scripts. Registration targets have weak owners,
and teardown releases their registrations and retained targets. The standalone
KO timeline API remains available for source fixtures.

`AiCpuDriver` executes the captured initial frame batch at its BODY registration,
then leaves callback-generated target scripts in the shared deferred FIFO. P1
uses the same driver. This retains both original short reference runs while
allowing KO root and child instances to interleave at their actual positions.

Round reset is separate from fresh-match allocation. `scripts/main.json`,
`frame_8/DoAction.as`, `chushi` restores HP, spawn transforms, input/roster data;
it does not clear energy, hits or pause. Native `chushi` no longer runs the
fresh-match action/presentation reset. KO actor goto uses source timeline control
for either player slot. Repeated goto to the current frame only changes playing
state; it does not enqueue another copy of that frame's script. The source
`nextfight` calls standing twice for each actor, but r15 sequences 50449–50456
execute each frame-1 script once, in P1 then P2 order.

The source `hitlosehp` and `onDefence` use direct `ql +=` operations for both the
receiver and attacker. Native settlement no longer uses the legacy energy-cap
helper. BODY's later callback owns the cap. r15 sequence 68883 preserves
305.46666666666493 energy at the receiver boundary. The shared receiver audit
now retains `hitlosehp` across all 35 main fighter bundles as one source group;
this is source reuse evidence, not acceptance of the other characters.

Root exit releases battle drivers, callbacks and timers before the root observer,
then follows the already-authorized fixed-selection bypass to map selection.
The replay verifies driver removal and the hidden battle world before recording
absent actors as frame 0. Post-exit display ticks do not advance battle logic;
a recorded callback surviving teardown fails the replay. This checks battle
absence, not the original character-selection UI.

## Reference timer delivery

The existing generated `nextfight` callback can use its live Timer or an explicit
recorded delivery. Recorded mode suppresses the wall-clock Timer start and
requires a live interval before emitting its timeout. r15 sequence 50444 is
replayed before the next root observer, after initial actor scripts. Deferred
standing scripts execute after that observer, as the source boundaries show.
The replay never substitutes recorded HP, energy or action state.

The countdown's 123 recorded callbacks are still NOT replayed or compared here.
Neither countdown/timeover gameplay nor all fields in `match` observations are
covered by the fighter comparison status. The timeout branch needs its own
original capture and implementation.

## Validation

See `ko-instance-validation/checks.json`: 12 focused native tests pass with
success markers, exit 0 and no SCRIPT ERROR. Historical intermediate first
failures are summarized in `progress.json`; the `ko-energy` experiment also
exposed a nil-geometry diagnostic error when original actors disappeared.
The final replay handles actual battle teardown rather than doing arithmetic
on absent source geometry.

| Capture | Fighter boundaries | Root frame pairs | Actor state snapshots | Result |
|---|---:|---:|---:|---|
| r13 | 1166 | 897 | 1794 | Compared fields match |
| r14 | 1084 | See report | See report | Compared fields match |
| r15 | 4158 | 6281 | 7096 | Compared fields match |

r15 spans both KO rounds, the nextfight delivery, battle exit and the retained
6000-fight-tick capture window. All 1202 post-checkpoint random calls and 19
clock reads are consumed. Exact geometry remains separately reported without
rounding or correction. The capture begins at a partial post-load checkpoint;
it does not certify boot/loading. Audio logs still report unimplemented
SOUNDINFO in/out points. No new Web/browser or pixel/audio acceptance is claimed.
