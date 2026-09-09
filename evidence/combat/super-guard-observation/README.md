# Super attacks against guard: observed differences

Status: two reproduced differences; no production runtime changes in this audit.
Scope: base Naruto and Ichigo, the current native Vs Com scene, original Flash
Player as reference. This is a controlled behavior fixture, not a complete
same-key/random-tape match or visual/Web parity acceptance.

## Fixture and evidence

Both sides start each case at 1000 HP, 300 energy, X=400/450 and the same floor
height (-25 in the captured source coordinates), facing each other. At case tick
10 the defender enters guard and the attacker enters the requested source label.
P1 holds down when defending. P2 retains CPU control; its random interval is
canceled and its sample fields are fixed (defran=0, other four samples=500).
The controller still decides when to remain in guard. Neither collision bounds
nor damage/receiver functions are replaced. Each case records 300 display ticks.

The original fixture is injected into a separate copy of the existing r15
instrumented main SWF; its fighter files retain the original instrumentation.
`original-fixture.as` is the complete root frame-10 replacement. All game/scripts
inputs remain unchanged. `probe.json` identifies source/runtime hashes and the
instrumented main hash. Temporary build workspace:
`/tmp/bvn-super-guard-observation/`; parent instrumentation builder:
`tools/probes/build_ai_reference.py` with match-flow/body-boundary instrumentation.

`original.log` has one SG2_DONE and 1800 SG2 snapshots. `native-probe.gd` injects
the corresponding fixture at `_advance_fight`'s root-observer phase, so source
goto target scripts drain after observation and before the next callback batch.
`native.log` has an explicit success marker, process exit 0 and no SCRIPT ERROR.
`native.json` contains all 1800 snapshots. `comparison.json` retains the first
mismatch and all damage events; field indexes are defined in `probe.json`.
AS2 trace coordinates have limited printed precision; matching those values is
not a binary-coordinate proof. HP values in these cases are exactly representable.

Two discarded experiments are not used as reference evidence: a P2 keyboard
fixture did not control the native CPU predicate compiler; an injection before
the next main tick deferred the initial guard state too late. The retained
fixture uses CPU predicates and the measured root-observer phase on both sides.

## Results

| Attack | Original remaining HP | Native remaining HP | Compared snapshots |
| --- | ---: | ---: | --- |
| Ichigo normal super | 940 | 940 | 300/300 equal |
| Ichigo up super | 975 | 975 | 300/300 equal |
| Ichigo ultimate | 730 | 730 | 300/300 equal |
| Naruto normal super | 999 | 971 | First difference at case tick 44 |
| Naruto up super | 970 | 942 | First difference at case tick 120 |
| Naruto ultimate | 523 | 523 | 300/300 equal |

The comparison includes both source frames, defender HP/hits/action, both
positions, and pause state. It does not compare every gameplay field or pixels.

### Naruto normal super: blocked contact incorrectly starts the follow-up

Original `scripts/fighter/minren.json`,
`DefineSprite_764/frame_538/DoAction.as` requires opponent HP > 0 AND action == -1.
At tick 43 both versions correctly block the starter: defender HP=999, hits=0,
action=2. At tick 44 the source stays at attack frame 538; native is already at
543 (the follow-up). Native then applies six 3-HP blocks and one 10-HP block,
ending at 971 instead of 999. The defender remains in guard; these are not
successful combo hits.

`godot/fighter_runtime.gd::_run_frame_actions` runs after `_apply_ai_source_frame`.
Its old special-transition fallback uses `_hit_instances` as the source-condition
substitute. `apply_attack_contact` also marks blocked contacts. Consequently the
fallback takes the branch even when the compiled source condition correctly
rejects it. This path also runs through `AiCpuDriver.run_target_frames`; it is not
isolated from current Vs Com. The earlier static audit's suggestion that this
legacy branch was outside the current mode was incorrect.

### Naruto up super: two additional guarded finishing hits

Both versions first block four 40-power contacts (4 HP each), then one 140-power
finisher (14 HP), reaching 970 at tick 111. At tick 120 both attackers are at
source frame 713 and the defender X is 525, but native re-enters guard-hit frame
726 while original advances to frame 730. Native settles another 14 HP at tick
121 and again at tick 131, ending at 942. Original remains at 970.

The first observable divergence is the receiver's contact/transition, preceding
extra damage and extra pause effects. Original receiver paths are
`DefineSprite_638/frame_729/PlaceObject2_2_28/...enterFrame` (fangyu), frame 727
(onDefence), and frame 731's defence controller. Root cause is not yet proven:
inspect the actual sbs2atm/bdmn bounds and callback/placement lifetime at this
boundary. Do not remove legitimate repeated contacts or globally suppress hits
on a blocked attack; Ichigo's ultimate legitimately blocks six times.

### Naruto ultimate: guarding the starter does not prevent later guard break

The source and native both block 1.5+1.5+2+2 HP first, then take nine 30-HP
contacts and the final 200-HP launch, ending at 523. First true hit is tick 147;
the hit count reaches 10. This observed sequence confirms the distinction
between blockable starter packets and the later zl=14 guard-breaking packet.

## Visual observation and limits

The original player window was inspected through CUA. Native rendered keyframes
were captured through an analysis SceneTree and inspected. The rendered repeat
preserves the reported damage outcomes but has one different defender timeline
snapshot (Ichigo up-super tick 121: 992 vs headless 991); render/timer repeatability
is not accepted. Screenshots illustrate native appearance, not paired pixel proof.

Keep the two findings open. No hitbox enlargement, per-character patch, changed
baseline, or tolerance relaxation was made. No complete M2/M3 parity claim.
