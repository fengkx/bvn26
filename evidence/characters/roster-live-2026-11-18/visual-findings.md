# Visual observations from the first roster pass

These are same-input native Flash/Godot snapshots, not full move-set acceptance.
Native checkpoint sampling was separately calibrated against terminal replay;
all actor states matched and only the real-time countdown differed in that
calibration. The production HUD and particle differences below still require
individual terminal replay and recorded-random checks before narrowing causes.

| Case | Ticks | Observation | Status |
|---|---|---|---|
| Sage Naruto | 175, 205 | Wind arcs were painted as a large white/cyan rectangle | Fixed; 842 actor states and 421 root positions still match |
| Obito | 205, 240 | Original opponent is in front of the statue; native opponent is occluded | Open: source hit/guard `swapDepths` chain and render depth |
| Deidara | 145 | Native smoke has hard pixel edges where original is blurred | Open: filter/raster sampling |
| Deidara | 205, 240 | Explosion fragment positions/scales differ | Recorded-random and child-clock check pending |
| Gaara | 205 | Blood/hit effect orientation differs | Confirmed: source XG_kanx frame 1 calls `this._rotation = random(180)`; compiler omits this integer-random rotation |
| Itachi | 175, 240 | Opponent is tinted/occluded by Susanoo; top HUD absent | Open: blend/depth versus sampling |
| Sage Naruto / Jiraiya | 205 / 240 | Top HUD absent in native sample during effects | Open: terminal replay and blend ordering |
| Multiple fighters | after 175 | Original 1P/2P markers visible, native absent | Check real-time presentation callbacks |

The test freezes native external timers for checkpoint sampling. Countdown digits
and energy-bar flash phase therefore are not synchronized visual baselines.
Most cases have not replayed their recorded random streams. Gaara was separately
replayed with both recorded streams; see the follow-up below. The missing AVM
integer-random rotation is source-confirmed, while other particle phase/position
differences remain observations.

Reviewed: all 40 selectable fighter/form contact sheets (eight frames each),
all six helper sheets (eight frames each), and four dense Ichigo Bankai frames.
The main case exercises two guard sequences and one ultimate; this is not an
exhaustive review of every move, every stage or online presentation.

Additional findings from the completed sheet review:

| Case | Ticks | Observation | Status |
|---|---|---|---|
| Ichigo Bankai | 149, 151, 155, 160 | Purple bounds rectangle obscures the authored crescent | Fixed and visually rerun; 362 actor states and 181 root positions match |
| Susanoo Sasuke | 145, 175 | Opponent partly covered by Susanoo in native | Same depth-swap investigation |
| Ikkaku / Temari / Gin / Uryu | 175–420 | Hit sprites have different orientations | Shared integer-random rotation missing; exact sampled rotations not in old tape |
| Kenpachi / Gaara / Orihime helpers | 30 | Source black backdrop is present, native still shows stage | Timing observation; independent terminal/clock check pending |
| Orihime helper | 45 | Native black backdrop remains after source returns to stage | Timing observation; independent terminal/clock check pending |
| Yoruichi helper | 45 | Top health HUD absent in native | Same HUD investigation |

The HUD disappearance survives an independent terminal replay and a replay that
renders every simulation tick (Itachi, tick 175). Raising the HUD z-index from
110 to 2000 in a temporary diagnostic does not restore it. No guessed z-index
patch was applied; `hud-followup/` retains the experiments.

`depth-swap-source.json` records 49 source onBeHit functions across 35 fighter
bundles. The source receiver/attacker depth swap is absent from native hit
settlement. Existing hurtSkill swap support does not cover this shared chain.


Gaara follow-up: `particle-followup/` retains both recorded-stream checkpoint and direct terminal renders. Both recorded streams consumed completely without divergence; the orientation difference remains. The probe explicitly records Math.random only, not AVM random(n). The missing rotation is in `scripts/main.json`, `DefineSprite_125_XG_kanx/frame_1/DoAction.as`; runtime `HitEffectRuntime` currently has no rotation event. All 842 actor states and 421 root positions still match.

The missing integer-random rotation also occurs in XG_kan, XG_ice and XG_fire frame 1. The native compiler currently recognizes Math.random offsets only.

All 35 dedicated guard-break sheets reviewed also show the receiver
in front of dust/effects in native where the original places it behind. The
source break branch and combat rows match; this reinforces the depth-swap
finding rather than indicating a different guard-break state.

Static follow-up outside the 40 selectable-entry matrix: replacement form
`yihu-3` (BODY 1672) also references solid shapes 1034/1037 without compiled
curves. Its transformation/move path needs a separate original/native live
fixture; it was not regenerated on the strength of the other form alone.

Local Web keyboard follow-up reproduced neither repaired rectangle. Browser logs
contain two viewport lifecycle errors (`is_input_handled` / `push_input`); trigger
not isolated, retained in `web/browser-errors.json`.

Follow-up repair: frame 1 now applies the source integer rotation for XG_kanx,
XG_kan, XG_ice and XG_fire. Gaara's tick-205 terminal replay is retained as
`particle-followup/gaara-rotation-fixed-205.png`. Through this frame, all
412 actor rows and 206 root rows match the previous same-input terminal run.
The integer draw has a checkpointed generator because the existing Flash tape
only records Math.random. Individual sampled Flash angles remain unrecorded.

Receiver depth follow-up: the source swaps the receiver behind the opponent on
settlement when it was in front. In onDefence(xgtype) this precedes checkDead;
in onBeHit(flying) it follows hurtVoice and the wall check. Both operate on the
two existing fighter wrappers and preserve their playing frames. Godot now reads
and swaps the rendered wrapper depths for both settlement and hurtSkill.
A fresh match uses the original stage placements.

The graphical terminal replay used the retained Flash inputs, random draws and
clock reads. All 35 base guard breaks through tick 32, Obito through tick 205,
and Susanoo Sasuke through tick 175 matched 3,074 actor rows and 1,537 root
positions. The rerun also identified incorrect case in Renji and Sasuke hurtVoice
consumer IDs; the compiler now uses the SWF path stored in the source bundle.
See [frame comparisons](depth-followup/comparison.png) (Flash, prior native,
fixed native) and [per-case counts](depth-followup/results.json). The images show
the receiver/attack overlap correction; HUD parity remains open.
