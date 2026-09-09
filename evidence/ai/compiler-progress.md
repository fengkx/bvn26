# Source compiler progress

Date: 2026-09-08. The fixed VS COM battle is not implemented or accepted yet.

## Native predicate compilation

`tools/importer/compile_ai_predicates.py` specializes the explicit player branch
out of the retained Sprite 16 controller and compiles 27 predicate functions to
native GDScript. It retains ordered guards, strict combo checks, scalar comparison
semantics, local variables and rush's facing writes. Unsupported expressions,
assignments and statements fail compilation. Generated code contains no source
parser or AVM interpreter. It is currently generated outside the game project;
the battle context adapter and ordered dispatch are still required.

The context ABI uses numeric, boolean and string fields. JSON null in the test
fixture denotes an absent AS2 value, not explicit AS2 null. It does not claim
general ActionScript coercion compatibility. Sensors are supplied outcomes;
MovieClip geometry and missing-instance lookup are not verified by this test.

```bash
python3 tools/importer/compile_ai_predicates.py \
  --output /tmp/bvn-ai-compile/predicates.gd
python3 tools/probes/check_ai_predicates.py \
  --godot /absolute/path/to/Godot \
  --output /tmp/bvn-ai-predicate-check
```

The independent reference executes the retained functions in Node with a fixture
object graph. Godot executes the generated native functions against the same
scalar inputs. 52,650 cases match both return values and facing writes. This is
translation evidence, not proof of AVM1 scheduling, RNG timing, geometry or a
complete fight. See `predicate-translation.json` for source and artifact hashes.
The retained `predicate-native.log` also records sandbox-denied macOS user-data
directory creation and certificate access; the fixture writes its results under
the temporary project and all 52,650 native results were produced and compared.

## Parent goto removes the executing clip

The native Adobe FP32 debugger produced `parent-goto.log` from
`tools/probes/as2/ai_parent_goto`. The root stops at frame 1. Its child's first
enterFrame jumps the parent to frame 3, whose display list removes that child.
The source then contains two trace calls and a second goto, but neither trace
nor frame 2's script executes. Frame 3's trace does execute.

- Player SHA-256: `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
- Probe SWF SHA-256: `7c3d6944805a5cdd934c9d1fb775cdbb66d81d14e7cdb804f53cf8aec9a2d17c`
- Build: `tools/probes/build_schedule_probes.py` with JPEXS 26.2.1.
- Capture: opened `/tmp/bvn-ai-parent.swf` in the native debugger and extracted
  only the `AI_PARENT_GOTO` lines from its shared trace log.

The corrected `ai_parent_function` probe defines its function in the child
Sprite's own DoAction, matching the controller's lexical scope. The native log
in `parent-function.log` shows the retained jump reaches parent frame 2 and the
function continues. The jump to frame 3 removes the clip: neither the function's
next trace nor the caller's next trace executes. Root frame 2 and frame 3 scripts
then execute in that order, followed by DONE. Probe SWF SHA-256:
`b1763f0ad774ff1c7906062e376d0bc8d7af2d64c25fbc96dc2e705a9028bb6a`.
The log was preserved from the tool's observed trace output before the player's
shared log was reused. An earlier draft defined the function on the root and
therefore had the wrong lexical `_parent`; it is not evidence for this rule.

`tools/importer/compile_ai_controller.py` now compiles eight dispatch functions
and all 30 Sprite 16 placement callbacks of base Ichigo. It preserves source
order and propagates instance removal through generated calls. The adapter must
apply display-list changes immediately and queue every target DoAction. It must
also resolve body calls, live fields, sensing and lexical scope; these interfaces
are not yet connected to the battle runtime.

`tools/probes/check_ai_controller.py` compared 3,960 cases against retained source,
including three callbacks per surviving instance, ordered writes/gotos, body-call
arguments and local variables. The removal adapter follows the native probe;
body effects and geometry are test doubles. All cases matched. Results are in
`controller-translation.json`, with engine output in `controller-native.log`.
This narrows AI-U05 but does not establish the full game callback ordering.

## Fixed original easy fight

`fixed-easy-r01/summary.json` records a completed original-game capture: P1 Naruto,
P2 CPU Ichigo, AI=5, the source introductions and 600 display frames after ready.
The fixture uses the original loader with instrumented copies, not isolated
fighter playback. `build.json` and `instrumentation.diff` retain source/output
hashes and exact instrumentation. `events.jsonl` preserves the contiguous event
sequence, and `random-tape.json` retains the 350 observed Math.random draws.

There are 7,157 events, including 67 samples and 3,889 predicate returns. Twenty-nine
samples precede ready. Intervals in this instrumented run range from 498 to 541 ms;
this does not prove a timer implementation formula, but rules out treating this
capture as a fixed 15-display-tick sequence. The sample's `this` prints undefined;
its lexical random fields still have numeric values. Do not derive the timer's
receiver solely from `this`.

The capture is not a complete oracle yet: random(n), predicate reads, sensor
matrices and target-frame DoActions need additional instrumentation, and Godot
has not replayed it. The CPU mode remains unconnected. Next work is the source
state/geometry adapter and timer lifecycle, followed by fixed-input/tape parity.


## Runtime context integration and geometry discrepancy

`compile_ai_context.py` now compiles frame-state writes for both base forms (35
Naruto source frames, 32 Ichigo source frames), the unconditional onBeHit0 writer,
and the authored 11 sensor placements. `AiSourceState` and `AiSenses` are connected
to FighterRuntime. Source numeric 动作 is not inferred from the visible action
label. Target frame state writes are queued in order, and declarations without
an initializer do not erase existing values when frame 1 repeats. Conditional
BODY writers and the CPU dispatch adapter remain unconnected.

`ai_context_smoke.gd` passes source-state, declaration, queued-target, immediate
hit-writer and mirroring checks. The existing `combat_smoke.gd` also passed with
no script errors. Context output is retained in `context-native.log`; the first
fixture attempt omitted hitstun_ms and was corrected before claiming this pass.
The engine's sandbox certificate warning is unrelated to these assertions.

The original r02 capture records getBounds and hitTest at one fixed loaded frame.
The missing absmian yields undefined bounds and hitTest. `check_ai_geometry.py`
recreates the observed player positions/source frames in Godot. All 12 hit or
missing outcomes match, but exact local bounds differ for all 11 real sensors;
maximum component difference is 0.061765 source pixels. The comparator exits
nonzero and retains the failure in `geometry-comparison.json`. No tolerance was
widened. This is an unresolved AI-U09 precision issue, not a passed geometry test.

The r03 capture additionally records actual local/concatenated matrices and each
sensor's own-space bounds. All own-space rectangles are (0,0)-(65.95,40.5), while
actual coefficients match the authored fixed-point matrices. Original getBounds
results lie on 1/20-pixel coordinates. Further isolated transform/rounding probes
are required to identify the correct rounding stages; do not round or offset
boxes merely to fit this one sample. Full build provenance and event streams
are retained under `geometry-r02/` and `geometry-r03/`.

## Native timer and controller instance host

`AiRandomClock` consumes the compiled interval, difficulty multiplier and ordered
five random sites. `SourceRandom` supports strict recorded consumption; missing
values or a different consumer fail instead of silently drawing replacements.
Stage music can use this shared service. `ai_random_smoke.gd` passed initialization
without an immediate draw, all five difficulty scales, shared music consumption,
invalid/exhausted tapes, and timer operation while the scene tree is paused and
time scale is reduced. This does not establish Flash timer phase parity.

`AiControllerInstances` now owns native controller identity independently of an
action label. It preserves instances across retained display-list membership,
invalidates removed generations, and suppresses callbacks on the placement tick.
The caller supplies callback order; no whole-game callback order is inferred here.
`ai_instances_smoke.gd` passed retention, removal/replacement, and removal of a
pending callback followed by replacement at the same authored path. Source basis:
compiled hook membership and `parent-function.log`; new placements begin callbacks
on the following display tick. The host is not yet wired into FighterRuntime.
CPU field adaptation, conditional BODY logic, and full recorded combat comparison
remain required before enabling or claiming source-equivalent Vs Com.

## Live predicate field context

FighterRuntime now owns `AiPredicateContext`, which maps wrapper coordinates,
facing fields, energy, root pause and opponent source state to the generated
predicate ABI. Numeric action and missing fields remain source state values;
they are not inferred from action labels. Source xscale and scale_X writes stay
separate. The current context covers base forms only; helper action and gravity
must be supplied by the eventual match host. Existing sensor precision limits
still apply, and conditional state writers remain incomplete.

The context compiler now retains the base body's onClipEvent(load) assignments,
including spd/jumpPower/fall, and the frame-1 `speed = spd` field read. Load is an
explicit event, not folded into configure: its scheduling relative to DoAction
must be driven by the source lifecycle. The base gjl1 strength table is extracted
for isPoFangAct. The expanded context smoke passed the separate load/frame events,
live energy/position/facing access and source strength/undefined lookup. CPU
dispatch is still not enabled by this change.

## BODY compilation and real fighter controller bridge

`compile_ai_body.py` now compiles eleven retained BODY functions: hurtSkill,
dash, doDashX, onDashing, fangyux, beidax, updateDirect, on_enterframe, initWudi,
isHitBan and doHurtSkill. It also extracts both hurt-skill timeout closures into
named native methods with their original 800/600 ms registration arguments.
The code preserves alias reads, later assignment overrides, pre/post increments,
the chained wdFrame assignment, ascending ban2..ban30 lookup, and the original
stage-hit parameter object. Colors/effects/stage attacks and actual timers still
require the runtime host. Both base form sources compile successfully.

`check_ai_body.py` passed 3,488 source/native cases with zero differences. It
checks returned values, ordered writes/calls, boundary combinations, and manually
fired timeout callback contents. Geometry inputs and external effects are test
doubles; this is not a Flash timer or combat acceptance result. Results are in
`body-translation.json` and `body-native.log`. After extending the scalar emitter,
the existing 52,650 predicate and 3,960 controller cases also passed again.

`AiControllerHost` bridges compiled controller instances to actual FighterRuntime
coordinates, sensors, target labels and queued frame-state writes. It requires
explicit scope/effect/BODY bindings and caller-provided callback order. The live
host smoke passed a retained walk controller moving twice by source speed, then
an attack goto removing that controller before its later movement statements.
The first run found that JSON floating-point frame numbers did not match integer
playheads through Array membership. Converting membership to PackedInt32Array
fixed that integration defect; the successful output is `host-native.log`.

This bridge is not invoked by the main battle loop yet. Its target-label adapter
still uses the existing FighterRuntime action entry path; remaining immediate
side effects must be audited against target DoAction timing. BODY host wiring,
remaining source state writers, effect/stage-hit services, callback scheduling,
and full recorded combat comparison remain open. No Vs Com acceptance is claimed.

## BODY host and timeout service

`AiBodyContext` maps the compiled BODY ABI to real fighter coordinates, health,
energy, collision velocity, depth and source state. Platform inputs retain their
authored ban indices, so missing indices are not compacted. Its smoke test passes
ban8 lookup/landing, paused guard movement, clamp-before-pause, and Ichigo's
energy debit plus deferred burst command. The initial-state compiler now includes
htx/yup/tdtime/hitNear/_lastX/_initwudi; this adds one Naruto frame with literal
writes (36 total). Conditional initialization and received-hit field binding are
still not complete.

`AiSourceTimeouts` provides independent one-shot registrations using milliseconds,
with explicit recorded firing and cancellation. Live timers ignore scene-tree
pause and engine time scale. Tests pass delayed execution, nested registration,
exactly-once firing, cancellation and cleanup. The BODY host test also schedules
the actual compiled Ichigo callback, explicitly fires its recorded registration,
and observes bsw and the original XG_baoqi parameter object. External visual/stage
attack services are recorded by the test, not implemented by this test double.
Outputs are `body-context-native.log` and `timeouts-native.log`.

The timer service does not prove Flash's dispatch phase. Main battle integration,
source-ordered initialization, hit reception fields, effects/stage attack service
bindings and complete same-tape parity remain open.

## Received packet fields

`compile_ai_hit_state.py` compiles Sprite 2's beida/fangyu state transfer into
`ai_hit_state.gd` for both fighters. The transfer retains its requested target
as data; it does not execute collision tests, damage, effects or target frames.
`check_ai_hit_state.py` passed 124 source/native packet cases, covering ordinary
guard, guard break, absent hit, missing duration and fractional frame durations.
Evidence is `hit-state-translation.json` and `hit-state-native.log`.

FighterRuntime now applies these compiled packet writes at its receive_attack
entry. BODY can read the actual received htx/yup/tdtime/jhp/bdzl fields. Guard
keeps the prior time counter and clears yup; normal hits reset time, and the
guard-break strength encoding is subtracted once. tdtime remains fractional.
The expanded context smoke passed these real receive-entry assertions. This
does not complete onBeHit's conditional hitNear/facing/depth effects or resolve
the existing target-frame scheduling limitations.

## Composed CPU driver and persistent runtime services

`AiCpuDriver` assembles controller instances, native BODY, timeout service and
random-clock registration. The caller supplies controller ordering and separate
display/body/controller/target-frame phases; the driver does not invent an
ExecutionProfile. Effect/stage services and unresolved controller scope must be
bound explicitly. Stop clears timeouts, its random registration and actor-bound
callables. The driver is not yet called by the main battle loop.

The driver integration test found a real lifetime defect: TimelinePreview's
render replacement queued the fighter's AiRandomClock for deletion, causing a
native crash when the driver later initialized it. RuntimeServices now survives
render replacement alongside SoundLayer; it is still destroyed with its owning
actor. The successful regression advances source frames, changes action, awaits
render cleanup and fires a recorded random sample through the surviving clock.
It also verifies movement/BODY composition, the actual deferred hurt-skill callback
and driver shutdown. Output is `cpu-driver-native.log`. The existing combat smoke
passed after the persistent-service change. This is not whole-game parity.

## Hit eligibility before candidate lookup

The original Sprite 2 checkHit() exits for !gameRunning() and !canhit before
looking up fighter, helper or stage attack objects. The first two guards are now
compiled into a boolean eligibility predicate. The fighter and helper contact
paths call that predicate before reading or consuming an attack instance.

The source comparison passes 124 transfer cases and 10 eligibility combinations.
`ai_hit_gate_smoke.gd` verifies real fighter and helper contacts: undefined/false/
zero canhit prevents damage; after canhit becomes true the same unconsumed attack
instance can hit. Root pause also blocks direct contact lookup. Output is
`hit-gate-native.log`. Existing combat smoke passes; its two existing ObjectDB
exit warnings remain. Stage attacks are not connected yet, so their future
lookup must use the same gate rather than bypassing it.

## Burst stage-hit timeline and runtime

`build_ai_stage_hit.py` resolves XG_baoqi through the original ExportAssets entry
(Sprite 514), verifies the pinned XML and selected asset hashes, and materializes
its 20-frame timeline plus the explicit frame-20 removal script. The authored
`mian` exists only on frames 3..15. No guessed or enlarged hit rectangle is used.

`StageHitRuntime` snapshots the caster's position/visual facing when configured,
queries the current mian against an eligible defender, and returns the original
hit packet through the established receive path. It does not mark the effect
as consumed: getStgHitObj contains no such flag. The copied visual facing is
separate from reception direction, which reads the current opponent wrapper.
The smoke test passes inactive/active/removed frame windows, snapshot position,
canhit rejection, packet damage/reaction and explicit removal. Output is
`stage-hit-native.log`; registry naming and full candidate priority integration
remain open, so this is not full stage-hit or Vs Com acceptance.

Rebuild from a verified JPEXS workspace:

```bash
python3 tools/importer/build_ai_stage_hit.py --workspace /tmp/main-pinned --output godot/generated/effects/XG_baoqi
```

## Stage registry and incoming candidate priority

The burst compiler now extracts root stgi initialization, post-attach wrap and
receiver lookup names. Native registration preserves names 1..11 then 2..11: the
source lookup list contains only 1..10, so name 11 is intentionally unreachable.
The registry accepts an explicit lookup permutation; Flash array enumeration and
duplicate-name restoration after removal remain unverified. Clearing scene
effects preserves the root counter.

CombatResolver.resolve_incoming implements fighter, helper, then stage candidate
priority for one defender callback. It is not yet connected to the main battle
loop. ai_stage_registry_smoke verifies wrap, unreachable name 11, replacement
identity, fighter-before-burst damage, burst fallback and counter persistence.
The second lookup explicitly resets the receiver to an eligible standing clip;
reusing the preceding hit reaction had incorrectly assumed unchanged eligibility.
Output: stage-registry-native.log, AI_STAGE_REGISTRY_SMOKE_OK. Verbose shutdown
reports 15 audio objects (MP3 streams/playbacks) and two resources still in use;
this is not a clean lifecycle acceptance. Full Vs Com integration remains open.

## CPU subtree callback phase

AiCpuDriver.run_enter_frame now consumes the measured ExecutionProfile ordering:
controller placements in descending display depth, then BODY on_enterframe.
AiControllerInstances still snapshots identity and excludes placement-tick calls.
This covers only the compiled BODY subtree, not other effect children, the second
fighter, timers or the complete main loop. The driver smoke no longer invokes
BODY before the controller. It checks that BODY's source _lastX stores the X
produced by child movement in the same tick, in addition to movement, timeout,
random-clock survival and cleanup. Output: cpu-driver-native.log. Main battle
integration remains pending: old input/motion callbacks must not run alongside
the compiled equivalents, and external effect services still need bindings.

## Compiled escape to combat services

AiCombatServices binds compiled BODY bsd/bsw calls to the existing SuperRuntime
and addStgHit to StageHitRuntime plus StageHitRegistry. The caller supplies the
shared presentation runtime, effect parent and helpers; other service names
require an explicit handler rather than silently succeeding. Stage timeline
advance and target scripts remain separate caller-controlled phases.

ai_combat_services_smoke executes the compiled Ichigo doHurtSkill and recorded
600 ms callback against real fighters: energy 200 -> 100, opponent stopped,
XG_bsq requested, pause released, 招换 entered, stgk1_P2 spawned on frame 1,
frame-3 authored mian deals 80 damage, and frame-20 script removes the effect.
Output: combat-services-native.log. This does not measure the wall-clock delay
or render the super presentation. Two audio ObjectDB instances and one resource
remain at shutdown. Main menu/battle routing, other effect service bindings,
full callback coverage and whole-game source comparison are still pending.

## Authored receiver callbacks in CPU scheduling

compile_ai_controller now extracts eight Sprite 2 receiver placements from
Ichigo Sprite 638. Each callback must consist exactly of beida() or fangyu();
unknown bodies fail compilation. receiver_hooks carries source path, method,
depth, placement frame and display-list membership. AiControllerHost merges
these with its 30 Sprite 16 controllers and applies the same lifetime/snapshot
rules. A reception-induced goto synchronizes the display list before the next
callback. AiCombatServices uses the authored method to choose guard reception
and the existing fighter/helper/stage priority resolver.

The CPU driver test verifies scheduled beida callbacks alongside movement. The
combat service test additionally demonstrates no hit on placement tick and a
real Naruto hit on the next callback. This fixture explicitly clears the prior
escape's wdFrameX and puts its floor at the aligned receiver position; leaving
these from the escape scenario correctly blocked the contact or caused a fall.
Outputs: cpu-driver-native.log and combat-services-native.log. Audio shutdown
warnings persist (four ObjectDB objects, two resources in the latter run).
Main battle routing and projectile child callback integration remain pending.

## Ichigo projectile initialization correction

The source audit found Sprite 99 frame 1 contains stop(), movspeed=18 and
played=0 in one script. parse_clip_timeline previously recognized only a script
consisting entirely of stop(), and projectile motion fell back to fighter speed
6. It now compiles this bounded initialization form with its source hash and
includes frame 1 in stop_frames. Rebuilt projectile records for frames 150, 327
and 421 carry initial_speed=18. After the source impact jump, the movement speed
stays zero even when collision ends. No character-name branch was added.

ai_projectile_source_smoke passes all three directions, stopped initial clip,
impact jump to 5, no resumed movement after separation and stop at frame 10.
It invokes explicit callbacks; placement-tick and cross-child scheduling are
not covered. Current collision lookup still lacks the source's other projectile
targets and frame-327 hitmc distinction. Full original same-input acceptance
remains pending. COMBAT_SMOKE_OK also passed; that run reports 10 audio-related
ObjectDB instances and four resources at exit. Outputs: projectile-source-native.log
and projectile-combat-native.log. No matching Python combat unit tests exist
(the attempted discovery ran zero); this is not claimed as unit coverage.

## Projectile collision query chain

The projectile compiler retains the source hitTest receiver/target sequence in
collision_queries and rejects partial query recognition. Ichigo's source queries
bdmn, zh1atm, zh2atm, zh3atm, abcd in order; at frame 327 the zh3atm query uses
hitmc rather than the whole projectile. Native lookup tests those current bounds
in order. The target lookup recognizes projectile frame-script renames so the
old authored zh1atm name does not mask the new abcd name.

The source smoke passes a projectile-only overlap with the target body far away,
the ordered extracted query list, and the post-rename abcd lookup. It also checks
that the current Sprite 99 display list has no child named hitmc. This empty child
lookup does not prove Flash's unqualified hitmc scope resolution; that remains
a minimal-probe question. Exact bounds rounding and cross-child callback phases
remain unaccepted. Output: projectile-source-native.log.

## Projectile placements in the CPU driver

The controller compiler now includes three projectile_hooks for Ichigo's
Sprite 99 placements. Together with 30 controller hooks and eight receiver
hooks, they cover the 41 direct BODY placement enterFrame scripts. Projectile
initialization requires the compiled fixed-speed frame-1 form; unknown child
callbacks/initializers fail explicitly. This does not cover every nested
descendant script or complete BODY frame actions.

AiControllerInstances advances surviving child playheads before callbacks.
New projectile instances initialize offset and local playhead; placement-tick
callbacks are excluded. AiControllerHost uses the same descending-depth callback
list for projectiles and other children. FighterRuntime's projectile callback
is shared with the older player path, while playback advancement is separate
for the CPU path. Main must not additionally call the old combined update.

ai_projectile_driver_smoke passes no movement on placement tick, 18-pixel
movement next tick, collision jump to 5, advance to 6 on the later tick, no
double advancement for the same tick, and fresh state after same-tick removal/
replacement. It uses a no-op receiver service to isolate projectile scheduling;
full simultaneous hit timing remains pending. Output: projectile-driver-native.log.
Main fight/menu integration and remaining effects are still unfinished.

## CPU sequential BODY playback

AiCpuDriver.advance_timeline now calls a source-frame advance path. It advances
one frame (or wraps at the source frame_count), uses authored labels to update
the native action identity, queues frame state writes and preserves child
instance data. It does not call the legacy action-end stand/guard/hurt fallback.
Only native event bookkeeping resets at a crossed label; source frame writes
remain in their frame-action phase. Missing source frames or unsupported labels
fail explicitly. Existing player playback remains on its current path.

The driver smoke verifies stopped playback stays at 725 and sequential playback
continues 725 -> 726 (防住), rather than restarting guard/stand; a separately
positioned playback test verifies 737 -> 738 (被打). These isolate the playhead:
normal guard callbacks can pin 715, and the normal frame-735 script explicitly
jumps to stand. Those scripts are not bypassed in the production frame phase.
Movement, timer registration and random-clock checks still pass. Output:
cpu-driver-native.log. Explicit goto still uses the existing start_action path
and needs its own retained-instance/target-action audit before full parity.
Main routing and complete original comparison remain pending.

## Explicit CPU goto and target writes

AiControllerHost now uses goto_ai_label, which changes playhead/play state and
queues target writes without start_action's immediate stand/guard/hurt resets
or blanket child-state clearing. Host synchronization still applies removal
before the caller survival check. Native hited/beida/bs/sw mirrors update when
the compiled frame writes execute, only for AI-controlled actors; stopping the
driver releases that ownership.

The host smoke verifies hited/beida remain unchanged during the goto caller and
become zero when stand's frame script runs. AImain's retained frame-2 state
survives the goto. Driver, combat-service and projectile tests pass. Enabling
source-state mirrors on the legacy player path initially stalled combat_smoke
in its super sequence: that path still has its own event ordering. Restricting
ownership to AI-controlled actors restored COMBAT_SMOKE_OK. This documents an
integration boundary, not proof the old player path is source-identical.

Outputs: host-native.log, cpu-driver-native.log, combat-services-native.log,
goto-combat-native.log. Full target-frame side-effect ordering, including
compiled super events and damage timing, remains to be integrated; main battle
routing and whole-match parity remain pending.

## Ordered super services in target frame actions

compile_ai_context now records top-level bsd/cbsd/bsw/cbsw/showFace calls with
source line positions. The AI frame phase merges these with scalar writes by
line number; it does not group all assignments before all calls. Naruto frame
530 explicitly calls bsw before bs=0. Original functions/other frame statements
are still outside this bounded extraction and must not be assumed compiled.

AiCpuDriver routes frame services through AiCombatServices into SuperRuntime,
then emits the existing presentation notification. bsd and showFace remain
separate calls: the effect request precedes the face selection. Root super
services synchronize bs into the source-state adapter after execution.

ai_super_frames_smoke passes Ichigo 450/463, 530/542 and 585/601: pause/stop,
XG request before face, face_p2 label, super focus, resume, no duplicate event
on a second drain. It separately observes Naruto frame-530 call-before-write.
Output: super-frames-native.log. Driver, context, combat-service and combat
smoke also pass. This checks presentation state, not rendered frame parity;
main entry integration and full target-script coverage remain pending.

## Top-level frame playback commands

compile_ai_context now retains top-level literal gotoAndPlay/gotoAndStop and
play/stop in the ordered frame call list. AiCpuDriver executes these through
the source goto path. The frame queue pops commands explicitly and drains
new targets appended during a target script; it no longer relies on iteration
behavior while appending to an Array. Conditional playback and other BODY
function calls are not automatically covered by this extraction.

The driver smoke verifies Ichigo 738 play, 744 stop (no further playhead advance),
and frame 748's assignments/goto/play followed by frame-1 writes in the same
phase. The queue is empty afterward, jumped=1 and hited=0. Super, escape-service
and projectile driver regressions pass. Output: cpu-driver-native.log. Main
integration and complete frame function coverage remain unfinished.

## Vs Com main-scene entry

The MENU slice now exposes VS COM (source modo=2, p1cpu=false, p2cpu=true).
It follows map selection into fixed Naruto P1 / Ichigo P2 with source AI=5.
The main scene creates AiCpuDriver/AiCombatServices, initializes both fighters'
source load state (CPU predicates read the player's sw), binds indexed ban
platforms and uses the shared SourceRandom. P2 ignores keyboard input; P1 keeps
its existing player input path. The CPU subtree receives source timeline, child
callbacks, BODY and target-frame phases without also running legacy P2 input,
movement or a second incoming-hit resolver. Inactive helpers are excluded from
the incoming helper branch until activated and assigned an owner.

Stage-hit effects advance and expire through their source phases. Returning to
MENU cancels the CPU random interval and timeouts, clears stage effects and
releases CPU ownership. Entering modo=3/4 also stops any preceding CPU driver.
ExecutionProfile is copied into generated/main for the exported runtime. The
existing inter-fighter callback order and explicit stage lookup list remain
provisional; this entry is not full same-input parity.

vs_com_smoke drives menu -> map -> fight -> complete intro, supplies one known
five-draw random sample, injects and flushes P1 keyboard input, then advances
240 combat ticks. P1 moves; CPU moves and attacks (player HP 1000 -> 840 in this
fixture); exit cancels the timer and switching to versus leaves no CPU driver.
Output: vs-com-native.log. MENU and INTRO smoke pass. The pause test now waits
for the existing intro before opening pause, including after scene reload;
PAUSE_MENU_SMOKE_OK passed. No test expectations for combat damage were relaxed.

Remaining visual services (resColor/applyColors, jump/landing effects, shadow
and generic child effects) are explicit warning-on-first-use placeholders in
the main adapter, not complete implementations. The tested random sample did
not invoke them. Other frame functions, helper AI state, initialization phase,
hit reception timing, geometry rounding and full original comparison remain
open. Do not mark M5-03 or source parity complete on this smoke result.

Web export to /tmp/bvn-vs-com-web completed with exit 0 and a savepack record
for generated/main/execution_profile.json. The exporter reports sandbox-denied
editor settings writes under the user's Library; browser execution was not
performed in this step. Export alone is not Web acceptance.

### Helper action input

The helper compiler now retains root DoAction assignments to 动作: woailuo
frame 13 writes 1; kon frame 12 writes 1 and frame 67 writes 0. New helpers
retain undefined until an assignment; main frame 8 removeFZ clears the value
and yfgj does not reset it on reuse. Main CPU context reads the P1 helper.
AI_HELPER_STATE_SMOKE_OK verifies these states and the generated defence
predicate at defran 129/130 with opponent action 0. This is a source invariant
test, not a whole-display-list scheduling comparison.

VS_COM_SMOKE_OK also passed after this change (P1 HP 840 in this run). The earlier note
claiming a retained HP 920 result was not supported by the current log; both
retained main-smoke logs report HP 840. This is not evidence of nondeterminism.
The smoke only proves movement and damage, not original parity.

### Main smoke repeatability diagnostic

`BVN_AI_SMOKE_TRACE=/tmp/trace.json` enables 240 per-tick snapshots in
`godot/tests/vs_com_smoke.gd`: both fighter snapshots/Y, helper action values,
pending timeout count and random sample count. Two independent headless
processes produced byte-identical snapshots (SHA-256
`2e54d674766ed564325a01c2af11119067b02ac3d65a69d347bc1fe855b3eef3`),
both with VS_COM_SMOKE_OK and no SCRIPT ERROR. Pending timeout counts were
zero throughout; this does not exercise live timeout ordering. The snapshot
fields are diagnostic, not a complete state serialization or an original
Flash comparison. No runtime timing behavior was changed for this test.

### Missing jump/landing linkage names

`compile_ai_visual_services.py` resolves main frame 8 jumpxg/luodixg wrappers
against all 62 retained SWF ExportAssets tables. Neither XG_jump nor XG_luodi
is exported by any retained SWF; the wrappers pass zero X/Y offsets. Source
search finds these names only in main.json. The main adapter now treats the
missing linkage as no created clip instead of reporting an unimplemented
visual service. No substitute artwork is introduced. Generated metadata
retains each wrapper source hash and all inspected SWF hashes.

VS_COM_SMOKE_OK checks that both calls add no world child and no unresolved
service. XG_tishen2 is different: it is exported as Sprite 94 and remains a
real missing import/adapter, as do color and shadow behavior. This inventory
does not establish complete Flash display scheduling or visual parity.

### Ichigo escape effect

The fixed Ichigo CPU's doHurtSkill non-Naruto branch calls bsd with XG_bsq.
Imported ExportAssets Sprite 493 from pinned main.xml using
`build_ai_effect_assets.py --workspace /tmp/main-pinned --clip XG_bsq
--output godot/generated/effects/XG_bsq`. The importer checks SWF, XML and
asset hashes and rejects scripts other than a single root unloadMovie call
or nested sprite timelines requiring another audit. The effect's source
DoAction unloads at frame 17; HitEffectRuntime now consumes local effect.json
events rather than waiting for generic frame-count overflow.

AI_ESCAPE_EFFECT_SMOKE_OK exercises the main CPU bsd service, imported
17-frame timeline, source default Y offset -25, mirrored facing, survival
through frame 16 and unload at 17. Native exit still reports one retained
resource, so this is not clean lifecycle acceptance. Full pause/display
ordering and original same-input comparison remain open. XG_tishen2 belongs
to the Naruto branch and was not imported as a substitute for Ichigo.

### Element color source compilation

Compiled main frame 8 bdxg color operations into both shared hit_receive
artifacts: ordered two-entry offset palettes for strengths 7/8/9, and the
20-entry grayscale matrix for strength 10. Exact source-value and delivered
artifact checks pass in ElementAndSuperClipTests. Renderer and CPU
applyColors/resColor remain unimplemented; extraction is not visual parity.
The full test_effect_clip_inventory module has two unrelated StageMusicTests
failures because expected dictionaries omit the existing random_site fields.
Those music expectations were not changed in this color work.

### CPU color lifecycle and renderer adapter

AiColorState follows BODY colors/_csn/_cgap: setColor replaces the palette
without resetting index; applyColors selects then increments/wraps; resColor
clears palette/filter, restores identity transform and sets gap=1 without
resetting index. Main CPU services now call these operations. AI-owned
FighterRuntime receives compiled bdxg color operations before hit effects;
new Vs Com initialization creates fresh color state. Legacy P1 color behavior
is not covered by this adapter.

TimelinePreview composes source RGB transform outside authored placement
transforms and supplies the compiled matrix to a filter shader. Alpha-changing
source transforms remain explicitly unsupported. This path retains the
existing texture/CXFORM blending behavior; Flash pixel clamping, transparent
edges, overlapping-child filter compositing and pause callback ordering are
not accepted as exact. Current implementation renders the filter per drawn
child rather than a composited BODY surface, so full filter parity remains
open. Do not use uniform checks as pixel-level evidence.

AI_COLORS_SMOKE_OK covers actual element receive, palette ordering, preserved
index on replacement/reset, shader matrix uniforms and filter clearing.
VS_COM_SMOKE_OK passed with the color service adapter. Source numeric JSON
values are floating-point in Godot; tests compare the matching numeric types.

### CPU hit-pause callback dispatch

Main frame 8 pauseGame sets root zhanting and calls conditional stopMc; it
does not suppress enterFrame. CPU mode no longer takes the whole-battle
hit_fx_pause_count early return. The adapter sets root pause, stops eligible
actors, and keeps compiled callbacks running. P1 legacy body-pressure
resolution is skipped while root-paused, matching BODY's pause return.
Repeated hit pauses use a boolean state in CPU mode; resume calls playMc
with its source hited/sw conditions and resumes black stage presentation.

AI_HIT_PAUSE_SMOKE_OK holds Ichigo at source frame 740 with the retained
beidax controller: color index alternates on paused ticks while position and
source time do not advance. P1's eligible timeline stops, and resume does not
force the hited CPU timeline to play. Vs Com and pause-menu smoke pass.
The full koPause writer/guard chain is still missing, and non-CPU mode
retains its legacy hit-pause adapter. These tests do not accept full pause
parity, helper scheduling, or timer order. Exit reports retained audio/resource
objects; lifecycle acceptance remains open.

### Complete KO source inventory before pause-guard implementation

`tools/analyze_ko.py` locates the KOstart caller in retained scripts, then
checks all root DoAction frames against the original SWF tag inventory.
`ko-source.json` records Sprite 1858: 394 frames, 11 root scripts, labels
winner=93, drawgame=240, next=384, all empty root-script frames, source hashes
and the eight KO/pause lifecycle functions. No player execution is required.

The chain is larger than a koPause guard: KOplay starts the clip and, when called by checkDead(pn), focuses
the dead fighter; frame 3 calls KOstart; frame 30 calls KOend; frame 74 fades HUD;
frame 84 branches on equal HP; frame 94 increments the winning side's count;
227/376 goto next and play; draw frame 270 pauses root; 388 closes transition;
394 either returns to character selection when the source counter reaches 3 in modo 2/3 (two actual wins) or
registers nextfight at 1000 ms. The callback initializes the next round and
plays ready. Current death handling lacks this full chain.

Do not add a disconnected koPause boolean and claim KO complete. Required
next work: audit KO root placement and nested scripts, materialize its assets,
compile branch/round operations, then route checkDead through the timeline.
The temporary pinned XML/JPEXS paths from earlier steps are no longer present
on disk; this inventory reads the retained SWF directly. Full asset import
will require restoring the export tooling/workspace, not trusting old paths.

### KO display-list import and nested script audit

Restored official JPEXS 26.2.1 under /tmp/bvn-ffdec-26.2.1 and re-exported
retained main.swf to /tmp/bvn-main-ko with export_swf_xml.py. The normal
generator/XML version checks and SWF/XML/asset hashes pass.

`build_ko_assets.py` now imports the root KO placement (Sprite 1858, depth
115, original matrix), 394 frames and all 8 reachable bitmap/sound assets.
Every bitmap fill reference is materialized. The audit retains 17 scripts
across sprites 1843/1844/1857/1858; source text is evidence only, not an
interpreted production payload. ko.json explicitly says assets only and not
behavior compiled. The root placement matrix is separate from its local
timeline to avoid applying the wrapper twice.

Nested behavior matters: Sprite 1843 stops at 1 and 15; the frame-20 placed
child in 1844 tests perfect HP while at frame 1 before play; 1844 frame 40
sets root pause; both 49 and 50 goto the winner's victory label, and 50 stops.
These must survive compilation, including both consecutive goto calls.
No KO runtime or round-completion acceptance is claimed by asset import.

### Native KO script compiler

compile_ko.py translates all 17 audited root/child script entries and the
nextfight callback into native GDScript. The bounded expression/statement
compiler rejects unknown syntax, preserves conditional order and both
gotoAndStop/play calls, and checks source entry hashes against the retained
bundle. Production code calls an explicit adapter ABI: read/write state,
root services, target clip goto/play/stop and interval registration. It does
not evaluate AS2 in production. controller.json remains compiled_not_connected.

KO_CONTROLLER_SMOKE_OK executes generated code with a recording adapter:
equal HP versus winner branches; both winning sides and victory positions;
consecutive frame 49/50 victory gotos; perfect-health callback only at child
frame 1; modo 1/2/3 terminal targets at source counter 3 (two actual wins); nextfight interval
1000 ms, timer id retention, round increment and reset/ready call order.
These validate branch output, not placement lifetime, wall-clock timer order,
real scene navigation or a complete KO match. Main integration remains open.

### KO instance scheduler

KoTimeline now owns the root and nested KO clip frames, playing flags,
placement identity, generation and local winmc X override. Snapshot-based
advancement excludes newly placed children from their birth tick; stopped
clips retain enterFrame dispatch. Metadata now distinguishes source frame
actions from the parent-sprite/placement-frame/depth child callback. Gotos
apply display-list membership immediately and queue destination actions;
source next/play sequences remain ordered. KO source winmc is placed at root
93 and removed at 226, with no intervening MOVE at its depth, so its frame
94 scripted X override survives this authored interval.

KO_TIMELINE_SMOKE_OK runs complete root paths for both winning sides and
a draw with the compiled controller and real extracted display lists. It
checks KOstart at frame 3, KOend, win counters, child perfect animation stop
at source 15, winmc positioning, and eventual nextfight interval registration
followed by root frame 1 stop. The service boundary still records external
operations; no real match reset or menu navigation is claimed. Descending
child callback order uses the existing measured profile, while full KO
creation/action ordering against original Flash remains unverified.

### KO visual playhead binding

KoClip renders the imported timeline using KoTimeline's live child frame
values, rather than elapsed-age modulo animation. It applies the original
root placement matrix once and reads winmc's scripted X override. Ambiguous
repeated sprite placements fail explicitly; the audited KO graph has one
live occurrence of each child symbol.

KO_CLIP_SMOKE_OK checks root position (96.35,115.6), original scale, P2 winmc
X=120, perfect child frame 15 and winner child frame 50 remaining stopped,
and loaded textures on rendered sprites. This headless check does not prove
pixel output or source audio timing. Main scene services and death signal
remain unconnected.

Service tracing for the next integration step found updateWins assigned to
_root in HUD Sprite 1814 frame 1; it addresses captured p1xt/p2xt.win clips.
clearint is a function expression in main frame 8 that clears nine named
interval IDs, so it must not be approximated as only stopping AI randomness.
The current HUD has no win-clip playback and only five opening placement
frames; KO's fadoutXuetiao/out timeline also needs compilation. These are
concrete remaining dependencies for a complete round transition.

### HUD out timeline and win-counter initialization correction

Compiled all ten Sprite 1815 HUD placements, labels in=2/out=6, and explicit
stop frames 1/5. BattleIntro now advances an explicit HUD playing state:
in stops at 5; out advances 6..10 then naturally wraps to the stop at 1.
HUD_TIMELINE_SMOKE_OK verifies each source Y translation and wrap/stop;
INTRO_SMOKE_OK and three source intro tests also pass.

Source initialization was previously omitted from the KO fixtures. Main frame
7 and Sprite 1991 frame 1 initialize p1ws=p2ws=1, rounds=1. Thus terminal
ws==3 means TWO actual wins, not three. Sprite 1785's HUD win frames confirm
this: frame 1 empty, frame 2 one marker, frame 3 two markers. Corrected the
prior written claim and full KO timeline test initialization. The compiler
now emits root_initializers with the original initializer path/hash; these
belong to match entry, not every nextfight round. KO_TIMELINE_SMOKE_OK passes
with source initial values. Win-marker rendering and the full main adapter
remain open.

### Source win-marker HUD rendering

build_health_presentation.py now imports Sprite 1785's three display-list
frames and rasterizes its actual Shape 1784. HealthHud draws the selected
frame's markers under the authored bar/win matrices, with no guessed pip
positions or replacement artwork. set_wins takes source counter frames 1..3;
health reset preserves them and new match entry sets both to source frame 1.

WIN_HUD_SMOKE_OK covers all nine pairs of counter frames, source marker
counts 0/1/2, imported texture presence and preservation through health reset.
VS_COM_SMOKE_OK passed with the expanded HUD. This does not validate raster
pixels against Flash or connect KO updateWins to a main-scene root adapter.

### Ordered lethal-state publication and KO request

The combat compiler now retains checkDead's ordered bdzl=0/sw=true writes
and the source pn binding (_parent._name == p1 selects 2; otherwise 1). Both
base action models and generated combat models carry these fields. Native
_check_dead publishes them to AiSourceState before emitting ko_requested;
the event precedes the non-flying death goto. The CPU goto uses the source
stop-then-play timeline path instead of legacy start_action side effects.

KO_REQUEST_SMOKE_OK covers both fighter slots, training exclusion, once-only
request, opponent AI observing sw=true, cleared bdzl, signal-before-goto and
correct pn values. VS_COM_SMOKE_OK passes. The request still needs a main
KO service adapter before it drives a real KO round transition. Also corrected
the earlier focus description: pn is the opponent number, so KOplay's mapping
focuses the dead caller; the winner focus comes later at KO frame 94.

### Main-scene KO and next round integration

Fixed modo 2 now instantiates KoTimeline/KoClip at match entry and connects
both fighters' ordered KO requests. The root adapter binds live HP, source
fields, focus, compiled win/round initializers and default time values; it
executes KOstart/KOend, conditional pause/play, HUD out and updateWins, actor
victory/stand gotos, qjxg/ready playback, chushi and nextfight registration.
KO pause guards ordinary hit-effect resume. Ready's source frame-2
clearInterval(kcint/nxtfht) is now compiled and emitted, stopping the native
nextfight Timer after its callback starts the next round. clearint dispatches
its source list; six unimplemented interval consumers have no registrations
in this slice, rather than being treated as implemented clock behavior.

The requested fixed-fighter flow still skips character selection: the source
terminal selection goto cleans up the fight and returns to map selection.
This is the existing slice restriction, not a port of the original selection UI.
The default gametime/maxtime values are source compiled; countdown/options
coverage is not established by this adapter.

VS_COM_KO_SMOKE_OK covers P1 and P2 each winning two consecutive rounds via
actual receive_attack lethal events, KO pause protection, win HUD counters,
nextfight blood/round reset, Ready interval cleanup, and final CPU/KO/Timer
cleanup on map return. Timer timeout is explicitly delivered in the test;
real-time phase is not verified. Vs Com, intro, hit-pause and three Python
intro source regressions pass. The two-match run reports 16 ObjectDB objects
and 6 resources at exit; resource lifecycle is not accepted. Whole-root
ordering, P1 legacy mechanics, filters/audio and original battle trace
comparison remain open.

## Menu sound cleanup source correction

The proposed immediate actor SoundLayer cleanup on `_goto_menu` was removed:
its smoke test only asserted the proposed implementation, not source timing.
Locked `scripts/main.json`, `DefineSprite_666/frame_2/DoAction.as`, explicitly
executes `stopAllSounds()`. Main XML places Sprite 666 at root MENU frame 10,
depth 1; its other DoActions are clearint at frames 4 and 20, and stop at 72.
Character selection instead places Sprite 1506 at root frame 46, depth 7;
its `frame_3/DoAction.as` executes stopAllSounds. Removing the battle instance
alone does not establish the timing or scope of event-sound termination.

A faithful implementation must compile these destination timeline events and
apply global sound stopping at those events, including cached actor sounds.
Current title menu is a native placeholder and has no such source playhead.
The fixed KO path also skips selection, so it cannot establish the original
selection sound timing. This remains open. The prior cleanup smoke printed
MATCH_SOUND_CLEANUP_SMOKE_OK but still reported 5 ObjectDB instances and 2
resources at exit; neither that test nor the earlier intermittent warnings
establish a leak cause. No original sound-lifecycle probe was run here.

## BODY frame-1 color state restoration

Source review of minren Sprite 764 and yihu Sprite 638 frame_1/DoAction.as
found unconditional resColor(), followed later by var _cgap=0 and var _csn=0.
The context compiler now emits those ordered calls/writes for both base
forms. AiCpuDriver consumes them on the source frame-event path; returning
to standing no longer keeps the previous hit palette/filter/index. The
existing resColor service itself continues to preserve index, as in source.

AI_COLORS_SMOKE_OK now covers two consecutive colored/filter-bearing returns
to standing through the real controller goto and target frame dispatcher.
VS_COM_SMOKE_OK also passes (P1 final HP 840). The main smoke reports 3
ObjectDB instances and 1 resource at shutdown; it does not prove leak-free
cleanup. P1 still uses the legacy frame adapter, and full filter composition,
initialization inited/doWanKai, and same-input original comparison remain
unaccepted. This change does not claim those paths complete.

## First-load movement state

The previous BODY adapter test manually seeded _lastX=0, hiding a missing
source initialization prefix. Both retained base BODY frame-1 scripts guard
inited=true and _lastX=0 with if(!inited). compile_ai_context now extracts
that prefix with source location and refuses a changed guard or conflicting
unconditional writer. AiSourceState applies its scalar projection once per
configuration; re-entering frame 1 preserves the updated previous X.

AI_BODY_CONTEXT_SMOKE_OK passes without a manually seeded previous X. New
checks exercise both base models, frame-1 revisits and fresh configuration;
the native BODY subsequently updates previous X to its actual position.
VS_COM_SMOKE_OK passes with P1 HP 840; this run has no shutdown resource
warning, unlike the prior color regression run. Both generated context files
reproduce byte for byte. Initialization call ordering, transformations and timer phase are not
covered by this scalar projection, and full original replay remains open.

## Ready-boundary discrepancy against retained original

`tools/probes/check_ai_ready.py` now validates the fixed capture configuration,
all locked source hashes, unique Ready marker, absent pre-Ready input and
absent pre-Ready predicate calls. It runs the native main scene through its
normal intro and records both fighters before the transition tick, at the
Ready signal, and after that tick. This diagnostic cancels the native AI
random clock and is deliberately not a full random/timer replay.

The retained FP32 capture has both actors on source frame 3 at fight tick 0.
The native signal has P1 frame 8 / P2 frame 7; end-of-tick has P1 frame 9 /
P2 frame 1. Positions, HP, energy and source action agree apart from X float
representation; pause differs at the pre-transition snapshot as expected.
`ready-boundary-comparison.json` records all raw differences without a frame
shift or tolerance. Two diagnostic executions reproduced these frame values.

This narrows the next investigation to intro completion, stand-loop playback
and actor/root scheduling before comparing attacks. Do not force frame 3 at
Ready or shift the reference to pass. Original snapshots are root enterFrame
observations; neither native signal nor end-of-tick has yet been established
as the equivalent phase. Full original parity remains unverified.

Reproduce:

```sh
python3 tools/probes/check_ai_ready.py --godot <godot-binary> --reference evidence/ai/fixed-easy-r01 --output /tmp/ready-boundary.json
```

## Standing frame-8 exit restored

Both base BODY scripts have unconditional gotoAndStop("站立"); play() at
frame 8. build_combat_model had explicitly excluded the stand-to-stand pair,
so the legacy player path looped across the label range through frame 9.
Removed that exclusion and regenerated only the new standing action_exits
entry in both base combat models and runtime copies. Other existing
augmentations were preserved. No character-specific runtime branch was added.

STANDING_LOOP_SMOKE_OK verifies three seven-tick loops for both actors through
advance_timeline/run_frame_actions, including while root pause is true.
VS_COM_SMOKE_OK passes with P1 HP 840. The original pre-Ready state sequence
shows frame 7 -> 1 -> 2 -> 3, consistent with this source frame-8 goto.
The post-fix Ready diagnostic remains divergent: signal frames P1=5/P2=7,
end-of-tick P1=6/P2=1, original both=3. The previous report is preserved;
ready-boundary-after-stand.json is a separate post-fix artifact. This is one
confirmed missing source exit, not full intro scheduling or P1 lifecycle
acceptance. Legacy start_action still has broader instance-reset behavior
than source goto, which this loop-frame test does not establish as faithful.

## Ready play does not advance immediately

Locked main DefineSprite_1991/frame_1/DoAction.as, goStep case 4, calls
_root.ready.play() followed by clearInterval(_root.kcint). BattleIntro
previously implemented this as goto(currentframe+1), executing Ready frame 2
and its HUD/interval effects immediately. It now enables playing without
moving the clip; polling is stopped as before. Frame 2 executes on the next
normal intro timeline advance. No Ready frame number was forced to match
the reference.

READY_PLAY_SMOKE_OK verifies frame 1 is retained by goStep(4), no HUD or
frame-2 interval signal occurs yet, and the following tick enters frame 2
with HUD in and kcint/nxtfht clear events. INTRO_SMOKE_OK and VS_COM_SMOKE_OK
pass. Ready diagnostic now reports signal P1=6/P2=1 and end tick P1=7/P2=2;
original root callback still reports both=3. Prior reports remain untouched.
This resolves a source API semantic error, not the remaining phase mismatch.

## Original intro timer capture r01

Added analysis-only entry traces to kaichang() and goStep(step) in locked
main Sprite 1991's script when building an instrumented copy. Function
signatures must match uniquely. No locked input is edited. Built a fresh
copy with pinned JPEXS and ran Adobe FP32 through Ready plus 30 fight frames;
the collector retained 1619 contiguous events ending in done.

`intro-phase-r01/phase-analysis.json` records 22 intro polls: adjacent calls
span 15 display ticks 12 times and 16 display ticks 9 times, with measured
500-536 ms intervals. The native fixed-15-tick interval is therefore not a
replay of this run's timing. goStep sequence is 1,2,3,3,4. The first step 3
at display 260 is followed by another at 275; step 4 occurs at 338. Ready
occurs at display 465 with both fighters at source frame 3, reproducing the
previous capture's boundary values.

The duplicate step 3 is direct evidence that the original retry branch
matters. Its cause is not yet proven: inspect queued frame actions and
first intro goto completion before changing runtime ordering. Do not hardcode
a retry or tune a timer to force frame 3. The capture includes source hashes,
random tape and instrumentation diff; full native replay remains pending.

## Original intro r02: boundary is not a fixed frame invariant

Extended the analysis copy with P2 goto-before/return and BODY frame-script
entry/exit records at retained frames 1, 8, 823 and 883 (822 has no script).
The fresh FP32 run completed 1935 contiguous events through fight tick 30.
This run executed steps 1,2,3,4 with no retry. P2's goto-before frame is 6,
goto-return frame is 822, and the next root snapshot is also 822.

Crucially, original Ready now observes P1 frame 3 / P2 frame 2 rather than
both frame 3. `intro-phase-variation.json` preserves the three original
boundaries and instrumentation limits. The Ready diagnostic's raw difference
is not sufficient evidence of a runtime bug without matched timer phase;
never impose a universal Ready frame value. Source-confirmed standing-loop
and ready.play fixes remain justified independently by their scripts.
The r01 retry's exact overwrite chain remains unproven because r02 did not
reproduce the same phase. Full timer/event replay is the next prerequisite.

## Explicit intro interval replay entry

BattleIntro can now start in recorded polling mode. Visual advancement no
longer also synthesizes kaichang calls in that mode; the replay host supplies
one ordered sequence/timestamp per recorded callback. Existing source branch
logic is reused. Repeated/backward event order latches an error, and cleared
or cancelled polling does not execute callbacks. Fresh begin resets replay
bookkeeping. Default runtime polling has not been switched or declared to
match the Flash timer.

INTRO_POLL_REPLAY_SMOKE_OK covers no implicit callbacks over 31 display ticks,
explicit deliveries separated by 536 ms, invalid sequence/time rejection,
cleared/cancelled delivery and reset/default mode. INTRO_SMOKE_OK still passes.
This verifies the delivery boundary only: loading state, real recorded
callback phases and complete original tape consumption remain unconnected.

## Queued standing script versus intro goto

INTRO_QUEUED_GOTO_SMOKE_OK exercises the actual AiCpuDriver frame queue and
BattleIntro's recorded poll entry. With BODY frame 8 already advanced and
queued, delivering kaichang before target DoAction processing calls the
source goStep(3) path and immediately reaches 822. Draining the existing
frame-8 script then executes its explicit goto stand, ending on frame 1.
The next recorded poll naturally takes the source currentframe<10 retry
branch; frame 823 then sets kcplayed=1. At frame 6 the same delivery reaches
822 and continues to 823 without a retry. No retry behavior was added.

This proves the existing native components can express the conditional
overwrite sequence. It does not prove the r01 trace's exact cause: that
recording lacks frame-script entry markers at the failed callback. r02's
goto-before=6 / return=822 matches the successful case. Main currently polls
before actor advancement by default; full recorded callback placement and
loading/timer playback are still required before whole-run comparison.

## Recorded intro callback delivery in the main scene

The fixed fight's advance method now accepts explicit after_actor_advance
intro poll records and delivers them before actor callbacks/target DoActions.
The interval callback executes outside assert expressions so release builds
do not strip its side effect. Default advancement passes no events.

VS_COM_INTRO_POLL_SMOKE_OK exercises actual main-scene stepping with two
controlled source phases: frame 6 reaches intro 822 then 823, while queued
frame 8 overwrites intro with stand and the next poll retries successfully.
VS_COM_SMOKE_OK remains passing. These are controlled phase regressions, not
a replay of the entire captured session. Loading checkpoints, all recorded
interval phases and random consumers must still be replayed before claiming
whole-match alignment.

## Observed loading gate and 21 poll branch comparisons

BattleIntro now models kaichang's initial p2loaded=false return via its
loaded argument/state. The normal fixed native scene defaults to loaded; a
replay can keep polling inert until the source load event. Analysis-only
intro_poll_state records capture curStep, p2loaded, both kcplayed values and
both source frames without guessing them from the rendered animation.

Fresh FP32 capture intro-phase-r03 completed 1812 events through 30 fight
frames. It contains 21 poll input records, including 11 before loading.
extract_intro_poll_inputs.py reproduces poll-inputs.json byte for byte.
INTRO_POLL_REFERENCE_OK cases=21 compares each observed input with the actual
BattleIntro branch and captured goStep call list; all match. This is an
independent per-call input comparison, not continuous battle replay or
proof of timer phase. Loading-gate and main phase-delivery smoke tests pass.

## Continuous post-load intro segment matches 267 frame pairs

Main now emits a read-only observation signal immediately before recorded
intro poll delivery. intro_continuous_reference.gd consumes r03's actual
poll sequence/display ticks without per-poll state replacement. It seeds
only the initial loaded standing checkpoint (P1=5/P2=4 at the first poll),
then advances the normal main scene. The checkpoint is represented one
frame before that phase; both preceding standing frames have no relevant
state action. Random refresh is cancelled and input stays empty for this
pre-Ready segment.

All 10 loaded poll inputs match (step, kcplayed and both source frames).
All 267 subsequent root snapshot frame pairs match continuously through
Ready. Ready is display 453, P1 frame 1 / P2 frame 2 in both the source and
native replay. A final rerun reproduces the match. End-of-native-tick maps
to the next original root snapshot tick because the source observer increments
aiDisplay in root enterFrame. No later frame or state is overwritten to fit.

Evidence: intro-continuous-r03.json records source events hash, all comparisons,
checkpoint/phase limits and original_parity_verified=false. This validates
only post-load intro frames and poll inputs under the supplied callback
phases. It does not validate full loading, all fields, random sequence,
pixel/audio output or subsequent combat. M5-03 remains pending.

Reproduce with Godot headless, script res://tests/intro_continuous_reference.gd,
then -- <absolute events.jsonl> <absolute output.json>.

## First continuous state difference at Ready

Expanded the same one-checkpoint replay to compare hp, ql, action, sw, touch,
touchFloor, hits, root pause, hstm and hurtSkling for both actors at every
root snapshot. Undefined is represented explicitly as null; no tolerance or
state overwrite is applied. The first 266 frame pairs and their 20 state
fields match. At display tick 453 (Ready), source P2 touchFloor is undefined
but native is true. All recorded frame pairs still match through that tick.

This isolates a callback-order concern: native BattleIntro currently applies
startFight before BODY on_enterframe, allowing its floor-contact write in
the Ready tick. The original snapshot retains undefined at that boundary.
The next change must examine deferred intro DoActions versus actor callbacks,
not seed touchFloor or suppress its valid floor-contact assignment. Previous
frame-only success evidence remains valid for its narrower scope.
Report: intro-state-first-difference-r03.json. Full parity remains pending.

## Deferred intro DoActions resolve the Ready state difference

Separated intro clip frame advancement from its queued frame event execution.
Main now drains intro DoActions after actor callbacks, so Ready 127's source
startFight does not enable BODY's floor-contact update in the earlier callback
phase of that same display tick. This uses an ordered event queue rather than
a touchFloor override or a special-case delayed assignment. HUD placement is
refreshed after frame effects execute.

The unchanged r03 continuous input now matches all 267 frame pairs, all ten
state fields per actor per frame, all ten poll inputs and the Ready boundary.
The original first-difference report remains preserved separately. Ready play,
main poll-phase, Vs Com and both-winner KO regressions pass. The comparison
starts from the same partial post-load checkpoint; full random sequence,
loading, subsequent combat and visual/audio parity remain unverified.

## Random refresh replay reaches first post-Ready state difference

Continuous probe combat mode now seeds the last original random sample at
the single initial checkpoint, supplies subsequent original draw sites and
values to SourceRandom, and delivers refreshes in event order alongside intro
polls. No live AI timer runs. The record preserves original global indices
and the seed sample; the initial music/loading random prefix is not replayed.

85 subsequent draws are consumed in order before the first difference at
display 454, the first post-Ready frame: original P1 touchFloor=true while the
legacy player source-state mirror remains undefined. P2 matches. This is the
next unresolved player BODY/state integration issue; do not hide it by skipping
the field. The remaining tape is unconsumed because comparison stops there.
267-frame intro state regression and VS_COM_SMOKE_OK still pass. Captured
random decimal precision, full callback phase and later combat remain open.

## Player exact main-floor state and first 30 fight-frame comparison

Compiled the exact main-floor equality branch from each base BODY instead of
hardcoding its field values. After player body pressure, the native adapter
now writes touch/touchFloor through the compiled data when unpaused and at
exact floor Y; the existing dash early return bypasses it. No physics or
collision threshold was changed. The other player floor branches remain open.

PLAYER_FLOOR_STATE_SMOKE_OK checks both models and the source root-pause/dash
early returns. VS_COM_SMOKE_OK passes. The unchanged r03 tape now completes
297 root snapshots (post-load intro plus Ready and 30 fight frames): all
source frames, ten compared state fields per fighter and poll inputs match;
all 95 post-checkpoint random draws are consumed by their recorded sites.
This reference segment has no held player input. Position/geometry, all other
state, music/loading prefix, full timers and visual/audio outputs are not
part of this match claim. Evidence is combat-first30-fields-r03.json; previous
first-difference reports remain intact. Full requested parity is unfinished.

## Geometry deltas and a 600-frame input capture

The continuous probe now records raw X/Y/xscale deltas separately from its
state match result. Over r03's 297 snapshots per actor, Y and xscale deltas
are exactly zero. X deltas are constant: P1 +0.0000061035156022626325 and
P2 -0.000024414062522737368. Relative-to-start X/Y displacement deltas are
exactly zero. No tolerance, rounding or baseline offset was applied to make
the raw coordinates equal. Absolute coordinate parity remains unproven.

Fresh original combat-input-r04 includes 600 fight frames and the authored
movement/attack/jump/special/helper input schedule. It retains 7878 events
through done, 353 random draws, 67 samples and 4256 predicate observations.
The terminal root snapshot has P1 HP 140 and P2 HP 1000; no native match is
claimed for this longer capture yet.

Two queued BODY frame records followed done within the same display tick.
Collector now retains them in post-done-events.jsonl after validating global
sequence/time order and a unique terminal marker, while rejecting later
display ticks. Three collector regressions cover preservation, later display
and duplicate done rejection. The new full capture is ready for input replay;
all previous captured baselines remain intact.

## Player input delivery and first r04 hit-settlement difference

The continuous probe now translates each recorded input_next_display state
into key transitions through Input.parse_input_event/flush_buffered_events,
using the session's actual action-slot bindings. It applies these before the
next native display step, holds keys without repeated press events, records
transitions, and releases them at exit. REPLAY_INPUT_SMOKE_OK verifies all
seven captured controls, held-state continuity, release and P2 CPU isolation.

The 600-frame r04 replay stops before the first nonempty player input, at
original display 469 (90 post-checkpoint random calls consumed). Both actors'
source frames still match: Naruto is on 1014, Ichigo on 372. Original Naruto
has hp=1000/ql=0/hits=0/action=0; native already has 920/8/1/-1. Original
frame 1014 only plays; frame 1015 calls onBeHit, and the original snapshot
at display 470 then contains those changed fields. Thus collision/goto is
not one frame late: native receive_attack applies settlement too early.

The fix must separate receipt/goto from source-frame onBeHit settlement, not
delay the whole collision or waive compared fields. The input adapter has
separate coverage but the continuous run has not yet reached held-input
frames; no 600-frame native parity claim is made. Prior reports are retained.
