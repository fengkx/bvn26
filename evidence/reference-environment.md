# Original reference environment

Status: usable for native-player boot and isolated AVM1 scheduling probes. A fixed
Naruto-versus-Ichigo gameplay replay has not yet been captured, so `M0-02` remains
pending.

## Runtime

- Player: Adobe Flash Player Debugger `32.0.0.465`, standalone macOS application
- Bundle identifier: `com.macromedia.Flash Player Debugger.app`
- Team identifier: `JQ525L2MZD`
- Executable architecture: `x86_64`, run through Rosetta on Apple Silicon
- Executable SHA-256: `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
- Installer URL: `https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa_debug.dmg`
- Installer SHA-256: `7a9a043e1481768d58ed9de8ff8644aa95d73ea7a0f5ba59b77fd4e71f7c25fd`
- JPEXS: `26.2.1`; CLI jar SHA-256:
  `23c1e70ff2b08388e35de10afd97a2875386cbfdc2ef99c8176d40b4f8a3ada9`

The locked `game/main.swf` was opened directly from its original directory on
2026-09-07. It reached the BVN 2.6 main menu and displayed the Normal single-player
selection and keyboard-help overlay. No file under `game/` or `scripts/` was
modified. This establishes a working native reference player, but not yet a
repeatable gameplay oracle.

`trace()` capture uses the two settings in `tools/probes/mm.cfg`. Probe SWFs are
built in a temporary/output directory and are not production dependencies.

## Known limitations

- The debugger is an end-of-life reference runtime and must never ship with the Web build.
- The initial full-game navigation was visually observed; its input stream and frame trace
  have not yet been normalized into an oracle replay.
- Ruffle is not used for scheduling conclusions because the full game did not provide a
  stable reference run there.

## Filter probes, 2026-10-23

The packaged filter probes were rebuilt with JPEXS 26.2.1 and recaptured with
Adobe Flash Player Debugger 32.0.0.465 through Rosetta. The executable and JPEXS
hashes match the locked values above. Probe programs, reproducible commands,
raw traces and per-run metadata are recorded in
[filter probe instructions](../tools/probes/flash_filters/README.md) and
[filter r02 evidence](importer-loud-fail/r02/README.md).
Godot 4.7.2 Compatibility ran on Apple M2/OpenGL Metal; a fresh signed official
app was used because the older scratch app failed signature verification.
No source file under game/ or scripts/ was changed.

## Filter color and shipped components, r03 (2026-10-23)

The same locked Flash Debugger/JPEXS executables and Godot 4.7.2 Compatibility
environment captured the color/opacity/order diagnostics and 21 shipped filter
or cache placements. Raw captures, source hashes and per-run metadata are in
[the r03 evidence](importer-loud-fail/r03/README.md). Native capture used
tools/probes/capture_native_player.py (component harness delegates to it).
Direct black-background RGB avoids lossy getPixel32 premultiplication recovery.
45/54 real component images still differ; these captures do not certify parity.

## XG_rush asset probe, r05 (2026-10-23)

The same Flash Player Debugger 32.0.0.465/Rosetta and JPEXS 26.2.1 captured the
original XG_rush definition tags through capture_native_player.py. No original
definition bytes changed during probe import. Native logs, actual probe scripts,
player executable hash and capture metadata are in
[r05 evidence](importer-loud-fail/r05/README.md). Godot 4.7.2 Compatibility
matches 21 entered source frames, but sampled RGB still differs. The timer-based
phase experiment is explicitly not used as the native frame oracle.

## Rukia numeric goto, r06 (2026-10-23)

The locked Flash Player Debugger 32.0.0.465/Rosetta and JPEXS 26.2.1 captured
an isolated Rukia body with its original definition tags and frame actions.
Godot 4.7.2 matches all 31 sampled playheads across the original 141→130 loop.
This is a paused-movement playhead experiment, not whole-combat equivalence.
Build hashes, source, raw trace and capture environment are in
[r06 evidence](importer-loud-fail/r06/README.md).

## Parent form replacement, r07 (2026-10-23)

Four original fighter SWFs were captured with the same Flash Debugger 32/Rosetta
and JPEXS 26.2.1 through capture_native_player.py. The root probe initializes the
required pause flag before original startup and then forces the original body
frame containing the parent goto. All non-DoAction root tags and original nested
definitions are byte-identical. The captures record native behavior only; there
is no matching Godot form-switch consumer yet. See
[r07 evidence](importer-loud-fail/r07/README.md) for raw traces and environment hashes.

## Parent conditional owner, r08 (2026-10-23)

The same Flash Debugger 32/Rosetta and JPEXS 26.2.1 captured the original minren
1293/996 and Sasuke 1019/1024 parent-flag conditional blocks. Root instrumentation
sets the parent flag and intercepts cbsw to record pre-write bs; original nested
actions and non-DoAction root tags remain byte-identical. Godot 4.7.2 matches both
conditional cases (six observations); this is not complete form-switch parity.
Actual programs, native logs and environment hashes are in
[r08 evidence](importer-loud-fail/r08/README.md).

## Parent live references, r09 (2026-10-23)

The same Flash Debugger 32/Rosetta and JPEXS binaries captured four isolated
fighter movies with `build_parent_goto_probe.py --live-references`. Only root
DoAction instrumentation changes; definition and non-action tag hashes remain
identical. Old-reference writes reach the replacement body, while old fields,
methods and the installed old enterFrame callback disappear. These are native
observations, not a Godot replacement parity claim. Programs, hashes and capture
environments: [r09 evidence](importer-loud-fail/r09/README.md).

## Saved form callbacks, r10 (2026-10-23)

The same Debugger32/Rosetta and JPEXS binaries captured the original initial
feixue function before/after parent replacement in four fighter movies. Root
instrumentation controls pause/HP/wudi, temporarily rebinds loseHp, and registers
a diagnostic repeating delivery wrapper; original definitions/non-action tags
are unchanged. Saved functions resolve the replacement's current loseHp method.
Programs,56 observations and per-capture environments are in
[r10 evidence](importer-loud-fail/r10/README.md). Godot matches48 callback results,
not full transformation, MovieClip identity or timer phase/cadence parity.

## BODY form transfer helpers, r11 (2026-10-23)

The same Flash Debugger32/Rosetta and JPEXS binaries captured seven original
fighter movies using `build_form_helper_probe.py`. Root-only instrumentation
invokes original BODY wankai with movement paused and useAI undefined; original
nested definitions and non-action root tags remain unchanged. All seven expose
immediate old-function retirement at parent.nextFrame; the trailing root_y write
does not run. Captures, hashes and environment records are under
[r11 form helpers](importer-loud-fail/r11/form-helpers/README.md). Godot compares
28 helper observation groups across seven cases, not full form replacement or
target frame coordinate/callback phase parity.

## ColorMatrix scalar arithmetic, r11 (2026-10-23)

The same Debugger32/Rosetta and JPEXS binaries captured the packaged
`color-arithmetic.as` fixture: 24 isolated coefficient/combined-row cases and a
completion event. Godot Compatibility matches20/24 cases exactly; four channels
still differ by1. Capture metadata, binary/probe hashes and the strict failing
comparison are in [r11 pixels](importer-loud-fail/r11/pixels/README.md). This is a
filter arithmetic diagnostic, not a fresh full shipped-component parity capture.

## Replacement lifecycle and absent scalar fields, r12 (2026-10-23)

The same Flash Player Debugger 32 under Rosetta and JPEXS binaries were used
for fresh original-body replacement observations and the packaged
`build_missing_form_fields_probe.py`. Five missing-field captures contain 26
observations and five completion events. Original Sasuke 1019/128 increments
absent khitn to NaN; its original 135 callback does not jump until khitn is
explicitly seeded to zero. Original Yihu 1180/143 uses Less2 followed by Not:
absent nn satisfies the compiled >= branch and the original callback reaches
frame 151. The captures preserve original nested scripts and placement tags;
root instrumentation and paused/controlled inputs are recorded in
[r12 missing fields](importer-loud-fail/r12/missing-fields/README.md).

The additional packaged ColorMatrix arithmetic ramp recorded 2,048 channel
samples (17 events). It narrows the rounding investigation but does not establish
a replacement shader algorithm or close the remaining pixel differences; see
[r12 pixel measurements](importer-loud-fail/r12/pixels/README.md). No parity
tolerance was changed.

Fresh Daitu `--observe-frames` sampling establishes the two distinct replacement
paths: real wankai reaches parent/body 2/1292, while the direct parent goto with
the flag false reaches 2/2. The production consumer, Main activation and rollback
checks are documented in [r12 forms](importer-loud-fail/r12/forms/README.md);
[capture environment](importer-loud-fail/r12/forms/native-daitu/capture-environment.json)
records the native run. This is lifecycle/state evidence, not pixel parity.

## Special aliases and additional form helpers, r13 (2026-10-23)

The same Adobe Flash Player Debugger 32.0.0.465 under Rosetta and pinned JPEXS
binary captured eight fresh root-only probes; nested definitions and root
non-action placement tags remain unchanged. Per-capture player, source, probe
and build hashes are saved with the native logs.

- [Special cost](importer-loud-fail/r13/special-cost/README.md): Yihu third-form
  537→538→539 and Rifagu second-form566→567→568 preserve ql234 until their
  original unconditional subtraction of100. Two captures, eight observations,
  ten events. Playback is forced at the source label and movement is paused.
- [Replacement helpers](importer-loud-fail/r13/form-helpers/README.md): original
  Byakuya, Rifagu and Rukia wankai reach parent/body2/1046,2/1204 and2/1122 at
  the next observation, with original transfer and key binding. Three captures,
  fifteen observations, eighteen events; useAI is undefined, movement paused.
- [Yihu graph](importer-loud-fail/r13/yihu-graph/README.md): first and second
  wankai edges reach2/872 and3/1004. An isolated original frame390 callback,
  with a true hitTest diagnostic and body enterFrame no-op, changes xscale75
  to-75 before reaching frame399. Three captures, ten observations, thirteen
  events. Body replacement/rollback checks pass, but exact root displacement
  remains native12 versus Godot17 at the first replacement: original nested
  sprite1027/frame1 subtracts5 from `_root._y`. The strict diagnostic fails;
  Yihu candidates remain unpublished. These captures do not certify pixel
  parity or full combat behavior.

### r13 Sasuke root-slot callback observations

Adobe Flash Player Debugger32, Rosetta, same player application and capture tool as the r12 form observations. Two root-observer probes retain the original child action/definition bytes and PlaceObject tags; explicit pn seeds select each original slot branch. `game.p1/p2` alias the diagnostic wrapper, so these are focused source ownership observations, not full-match equivalence claims. Captures use the standard windowed LaunchServices launch via `tools/probes/capture_native_player.py`.

- [Slot1 capture](importer-loud-fail/r13/forms/native-sasuke-slot1/capture-environment.json): 13 events, complete.
- [Slot2 capture](importer-loud-fail/r13/forms/native-sasuke-slot2/capture-environment.json): 13 events, complete.
- [Source bounds and reproduction](importer-loud-fail/r13/forms/source-first.md): parent2/body1017 after initialized replacement, root slot selection and transfer671/234, live reference rebinding, captured direct-health callback ignores wudi, uses root maxhp1500 threshold, and obeys pause. The probe clears the real interval then explicitly invokes the captured original function to isolate callback semantics; it does not measure interval wall-clock phase.

## r14 Minren transfer and initial filter retirement

Native Flash Player Debugger32 (Rosetta), source minren.swf unchanged; root-only probes for both player slots. Capture environment/player hashes are retained in `importer-loud-fail/r14/native-slot1/` and `native-slot2/`. Capture used `tools/probes/capture_native_player.py --allow-window-activation`; reproduce via `tools/probes/build_minren_form_probe.py`. Wrapper GPU comparison used Godot4.7.2 OpenGL/Metal on Apple M2; the exact1,280-channel Glow check is in r14/wrapper.log. No native wall-clock timing claim or new stability deviation.

## 2026-10-24 Yihu nested stage reference (PR48 r15)

The same Adobe Flash Player Debugger32.0.0.465/Rosetta and JPEXS26.2.1
executed the original Yihu wankai helper with unchanged child definitions and
placement tags. The extended root observer records23 consecutive post-replacement
body/root-position samples, including the16-frame nested loop. Build hashes,
launch environment and raw trace are in `importer-loud-fail/r15/native-stage/`.
The probe is isolated, not a complete transformed combat/image parity claim.

## r16 Yulong wrapper initialization probe

The same Adobe Flash Player Debugger32.0.0.465 (Rosetta) and JPEXS26.2.1 were used via `tools/probes/capture_native_player.py` with window activation authorized. Root-only instrumentation preserves original child definitions and non-action root tags. Evidence: [r16 native log](importer-loud-fail/r16/native.log) and [build hashes](importer-loud-fail/r16/native-build.json). This adds bounded filter lifecycle observations, not full-game pixel parity.

## r17 placement candidate probes

The same Flash Player Debugger32.0.0.465 under Rosetta and JPEXS26.2.1 captured30 difference/overlay cases and12 DropShadow cases. Blend input and output pixels are recorded separately; premultiplied RGB comes from drawing the captured BitmapData onto opaque black, not reconstructing lossy straight-alpha values. Shadow probes sample the entire32×32 image. Both candidates fail exact parity and remain outside production. [r17 evidence](importer-loud-fail/r17/README.md) retains captures, build hashes and rejected patches.

## r18 placement arithmetic isolation

The same Flash Player Debugger32.0.0.465 under Rosetta and JPEXS26.2.1
captured a complete256×256 opaque overlay grayscale grid and two12-case
DropShadow mask probes (strength1, hidden source, blur3 or blur0).
[Captures and build hashes](importer-loud-fail/r18/README.md) distinguish
opaque integer blend parity from unresolved alpha compositing/fractional
sampling. Godot4.7.2 Compatibility matches all262,144 opaque-grid channels
in an isolated candidate; the candidate still fails12/30 mixed-opacity cases
and is not admitted to production. No reference environment change.

## r19 integer blends and fractional shadow impulses

The same Flash Player Debugger32.0.0.465/Rosetta and JPEXS26.2.1 captured
3,072 alpha-ramp cases,336 half-alpha boundary cases,192 layered compositions,136 impulses and256 expanded
DropShadow cases. Pre-blend alpha and premultiplied RGB are measured directly;
GPU inputs use observed byte alpha rather than the requested beginFill percentage.
Godot4.7.2 Compatibility matches all admitted difference/overlay samples exactly.
The expanded shadow candidate remains unadmitted at232/256. Raw captures, build
hashes and launch metadata are in [r19 evidence](importer-loud-fail/r19/README.md).
No reference environment change or production Flash dependency.

## r20 DropShadow phase capture

Native Flash Player Debugger32.0.0.465 (Rosetta), same player/FFDec/Godot binaries and hashes as r19/reference-tools.json. Fresh windowed captures: shadow-phase (48 cases) and shadow-phase-sweep (520 cases); run IDs, SWF hashes and launch metadata are in importer-loud-fail/r20/. GPU uses Godot4.7.2 Compatibility on Apple M2.
Additional r20 captures: shadow-phase-ties (48 impulses) and drop-shadow-ties (256 full images), with the same binaries and capture settings. Raw captures are retained beside the phase sweep.

## r22 component input and bitmap phase captures

Same Flash Player Debugger32.0.0.465/Rosetta, FFDec26.2.1 and Godot4.7.2
Compatibility/M2 binaries as r20. Seven fresh raw-definition component harnesses
remove only the tested outer filter/cache, with native removal observations;
54 images and4242 playhead observations are retained under importer-loud-fail/r22/.
Two additional smooth-bitmap probes capture1536 calibration and4096 extended
samples. The candidate fails703 extended samples and is not in production.
Build hashes, run IDs, generated harnesses and launch metadata are retained.
No reference-environment change or production Flash dependency.

## r23 bitmap inverse/scanline captures

Same Flash Player Debugger32.0.0.465/Rosetta, FFDec26.2.1 and host as r22.
Fresh native fixtures: bitmap-inverse(1008), bitmap-inverse-clipped(1008),
bitmap-size(240), bitmap-row(6048). Ordered raw captures, source/SWF hashes
and launch metadata are under importer-loud-fail/r23/. Reused r22 phase captures
are unchanged. These compare a diagnostic CPU model, not Godot pixels; remaining
channel differences reject production admission. No reference-environment change.

## r24 bitmap span and single-pixel clip captures

Same Flash Player Debugger32.0.0.465/Rosetta and FFDec environment as r23.
Fresh native bitmap-spans (96 rows), bitmap-scalar-clipped (1008 points),
bitmap-scalar-repeat (1008 points) captures retain build hashes and launch
metadata under importer-loud-fail/r24/. Only destination width/clip context
changes in the span controls. CPU hypotheses remain rejected; no runtime
Flash dependency or reference-environment change.

## r25 short-span captures

Same Flash Player Debugger32.0.0.465/Rosetta and FFDec environment as r24.
Fresh bitmap-short-spans fixture:1896 ordered rows,4248 RGB samples, source/SWF
hashes and launch metadata in importer-loud-fail/r25/short/. No environment or
production runtime change; the CPU hypotheses remain diagnostic and rejected.

## r26 isolated axes and corner impulses

Same Flash Player Debugger32.0.0.465/Rosetta and FFDec environment as r25.
Fresh bitmap-axis-ramps (1728 rows/8064 samples) and bitmap-weight-impulses
(864 rows/2880 samples) captures, source/SWF hashes and launch metadata are in
importer-loud-fail/r26/. No environment change or production Flash dependency.

## r27 source boundaries and independent origins

Same Flash Player Debugger32.0.0.465/Rosetta and FFDec environment as r26.
Fresh bitmap-boundary-spans (1344 rows/4032 samples) and bitmap-origin-sweep
(1632 rows/samples) captures retain source/SWF hashes and launch metadata under
importer-loud-fail/r27/. Older r22–r26 captures are reused unchanged and hashed in
comparison.json. CPU clipped candidate is exact on listed suites; repeat still
rejects production admission. No environment or production runtime change.

## r28 repeated bitmap matrix routing

Same Flash Player Debugger32.0.0.465/Rosetta and FFDec environment as r27.
Fresh bitmap-repeat-matrices:2940 single-pixel corner responses across draw/fill
translation routes. Original trace, source/SWF hashes and launch metadata are in
importer-loud-fail/r28/matrices/. Reused reference hashes are in comparison.json.
The signed-byte hypothesis is diagnostic only; no environment/runtime change.

## r29 repeat affine controls (2026-10-24)

Flash Player Debugger 32.0.0.465 under Rosetta, same native capture tool and player as r28. Three unmodified raw captures and individual environment records are under `importer-loud-fail/r29/{coefficients,step,negative}/`. Fixtures use separate integer draw translations and destination-pixel movement, plus negative off-grid scale controls. No old reference was regenerated.

## r30 repeat rounding and spans (2026-10-24)

Flash Player Debugger 32.0.0.465 under Rosetta, same capture tool/player as r29. Original traces, source/SWF hashes and environment records: `importer-loud-fail/r30/{rounding,half,spans}/`. Captures separate source width, draw origin, target pixel and clip length. Old references are unchanged.

## r31 repeat span intervals and chunks (2026-10-24)

Flash Player Debugger 32.0.0.465 under Rosetta, same player/capture tool as r30. Raw traces and individual capture records: `importer-loud-fail/r31/{intervals,chunks}/`. Probes independently vary clip length and start, with four impulses and two ramps. Old references and production rendering remain unchanged.

## r32 Godot sampler diagnostic and native RGBA (2026-10-24)

New transparent BitmapData capture uses the same Flash Player Debugger32.0.0.465/Rosetta; environment and hashes are in `importer-loud-fail/r32/rgba/`. GPU diagnostic runs Godot4.7.2 Compatibility on Apple M2/OpenGL4.1 Metal90.5; `r32/gpu.log` and `r32/provenance.json` pin engine/source/input/readback.54 production components were freshly rendered against unchanged r03 native references. No native production baseline was rewritten.

### r33 source-bound bitmap leaf

Reused Adobe Flash Player Debugger 32.0.0.465 under Rosetta and Godot 4.7.2 Compatibility on Apple M2/OpenGL 4.1 Metal 90.5. The new source-tag leaf capture is pinned in `importer-loud-fail/r33/native/capture-environment.json`; GPU command, executable/source/readback hashes are in `importer-loud-fail/r33/render/provenance.json`. No player configuration change.

### r34 complete Yulong wrapper diagnostic

Reused the pinned r03/r21 Flash Player Debugger 32 native component references without recapture. Actual GPU rendering remains Godot 4.7.2 Compatibility on Apple M2/OpenGL 4.1 Metal 90.5; command, executable/source hashes and output evidence are in `importer-loud-fail/r34/wrapper/`. No Flash player or environment configuration changes.

### r35 production-path wrapper diagnostic

Reused pinned native Flash component images without recapture. Godot 4.7.2 Compatibility / Apple M2 / OpenGL 4.1 Metal 90.5 ran the production texture loader and filter/composite code through an opt-in test subclass. The actual PNG import configuration is archived at `importer-loud-fail/r35/production-path/texture-import.txt`, with executable/source/asset hashes in `provenance.json`. No import or player configuration was changed.

### r36 ordinary composition controls

New bitmap and vector captures use Adobe Flash Player Debugger 32.0.0.465 under Rosetta, unchanged from r33. Original traces, build/source/SWF hashes and environment records are under `importer-loud-fail/r36/{bitmap,vector}/`. Each capture has 2016 observations plus an explicit completion event. Godot 4.7.2 Compatibility / Apple M2 / OpenGL 4.1 Metal 90.5 runs the shared integer shader and the production-path wrapper diagnostic. Commands, source/engine/native/readback hashes are in `r36/composition/provenance.json`. The r03/r21 native component images are reused unchanged. No player/import configuration change.

### r37 explicit nested materialization

Adobe Flash Player Debugger32.0.0.465 under Rosetta explicitly allocated and drew nested BitmapData sources. The final capture includes source-input readbacks and all child/parent/final pixels: `importer-loud-fail/r37/native/` contains source/SWF hashes, original trace and capture environment. Godot4.7.2 Compatibility / Apple M2 / OpenGL4.1 Metal90.5 ran actual production BlendGroup nodes, with correct and deliberately stale destination-copy ordering. Commands, source/engine/native/readback hashes are in `r37/{fresh,stale}/provenance.json`. No player settings, old references or import settings changed.

### r38 nested filter and materialized CXFORM controls

Reused Flash Player Debugger32.0.0.465 under Rosetta. New original traces/source/SWF hashes/environment records are under `importer-loud-fail/r38/{native,cx,dense,spans,varied}/`. Native explicitly allocates BitmapData and applies filters; no cache flag inference. Godot4.7.2 Compatibility / AppleM2 / OpenGL4.1 Metal90.5 runs actual FilterGroup allocation/passes through opt-in diagnostics. The initial and fixed-candidate source/readback provenance are in `r38/{render,integer}/`; baseline shader snapshot preserves the initial code. No old references, player settings or PNG imports changed.

### r39 independent long-row CXFORM controls

Flash Player Debugger32.0.0.465 under Rosetta captured810 completed row controls; original trace, source/SWF hashes and capture environment are in `importer-loud-fail/r39/native/`. Apple clang21.0.0 compiled an independent x86_64 reciprocal-estimate helper, executed under Rosetta; source/executable/output hashes and command are in `r39/reciprocal-environment.json`. Agreement is not evidence of Flash instruction selection. No player settings, references, GPU shaders or production runtime changed. Existing Godot diagnostic regressions use the same4.7.2 Compatibility environment.

### r40 all-alpha CXFORM / source-intersection controls

Flash Player Debugger32.0.0.465 under Rosetta captured all-alpha rows, nonbinary-opacity rows and long/source-boundary rows. Source/SWF hashes, completion records and losslessly compressed original traces are in `importer-loud-fail/r40/{alpha,opacity,extents}/`; raw/compressed hashes are recorded separately. Apple clang21.0.0 with `-arch x86_64 -O2 -ffp-contract=off` built the independent reciprocal-precision comparator, run under Rosetta. Commands and source/executable/output hashes are in `r40/reciprocal-environment.json`; no inference about Flash instruction selection. Existing Godot4.7.2 Compatibility regression environment is unchanged. No player settings, GPU shaders, production runtime, pinned references or texture imports changed.

### r41 residual CXFORM coefficient intervals

Flash Player Debugger32.0.0.465 under Rosetta captured2760 completed32-pixel rows, including exact premultiplied residual inputs. Source/SWF hashes, lossless raw trace archive and completion environment are in `importer-loud-fail/r41/native/`. Apple clang21.0.0 (`-arch x86_64 -O2 -ffp-contract=off`) built seven independent reciprocal constructions; source/executable/output hashes and commands are in `r41/reciprocal-environment.json`. Measurements do not imply Flash instruction selection or SIMD. Prior native references and Godot4.7.2 Compatibility regression environment are unchanged; no player settings, production/GPU code or texture imports changed.

### r42 channel identity and explicit materialization

Flash Player Debugger32.0.0.465 under Rosetta captured green identity/adjacent multipliers, five explicitly materialized stages, and zero-green offset isolation. Source/SWF hashes, complete lossless traces and environment records are in `importer-loud-fail/r42/{native,stages,zero}/`. Independent coefficient measurements from r41 are reused unchanged and hash-checked; no inference about Flash instruction selection. Godot4.7.2 Compatibility regression environment remains unchanged. No production/GPU code, earlier native references, player settings or texture imports changed.

### r43 amplified reciprocal controls

Flash Player Debugger32.0.0.465 under Rosetta captured324 width32 rows with explicit source/output readbacks. Source/SWF hashes, complete lossless trace and environment are in `importer-loud-fail/r43/native/`. r41 independent coefficient measurements and r42 bounds are reused unchanged and hash-checked. Existing Godot4.7.2 Compatibility regressions use the unchanged environment. No instruction/SIMD inference, production/GPU change, earlier-reference rewrite or texture-import change.

### r44 held-out amplified alpha and normalization controls

Flash Player Debugger32.0.0.465 under Rosetta captured4131 width32 rows with explicit source/output readbacks. Source/SWF hashes, full lossless trace and environment are in `importer-loud-fail/r44/native/`. Independent x86_64 input-normalization/reciprocal measurements use Apple clang with contraction disabled; commands and source/executable/output hashes are in `r44/normalization-environment.json`. No native pixels enter that helper and no Flash instruction/SIMD inference is made. Existing references and Godot4.7.2 Compatibility regressions remain unchanged; no production/GPU or texture-import change.

### r45 adjacent source-byte and alpha controls

Flash Player Debugger32.0.0.465 under Rosetta captured459 width32 rows, independently varying one requested source green byte and input alpha at three fixed r44 transforms. Complete source/output readbacks, lossless trace, build hashes and player environment are in `importer-loud-fail/r45/native/`. Independent r44 normalization measurements and prior bounds are reused unchanged and hash-checked. Existing Godot4.7.2 Compatibility regressions are unchanged. No instruction/SIMD inference, production/GPU change, native-reference rewrite or texture-import change.

### r46 fixed-source transform brackets and signed offsets

Flash Player Debugger32.0.0.465 under Rosetta captured1200 fixed-source multiplier/offset bracket rows plus75 independent signed fractional-offset rows with ColorTransform property readback. Complete readbacks, lossless traces, source/SWF hashes and environment are in `importer-loud-fail/r46/{native,offset}/`. r44 independent normalization measurements and old bounds are reused unchanged and hash-checked. Existing Godot4.7.2 Compatibility regression environment is unchanged. No instruction/SIMD inference, production/GPU change, old-reference rewrite or texture-import change.

### r47 fine multiplier and signed consumption controls

Flash Player Debugger32.0.0.465 under Rosetta captured624 fixed-source fine-multiplier rows plus195 independent signed/zero-centered rows, with explicit ColorTransform multiplier property readbacks. Complete lossless traces, source/SWF hashes and environment are in `importer-loud-fail/r47/{native,signed}/`. Independent normalization measurements and old bounds are reused unchanged and hash-checked. Godot4.7.2 Compatibility regressions use the unchanged environment. No instruction/SIMD inference, production/GPU change, old-reference rewrite or texture-import change.

## r48 signed constraint analysis

Reused the pinned r47 Flash Player Debugger 32/Rosetta source readbacks and signed controls; no new native capture or environment change. Direction-correct CPU interval analysis does not infer an ISA implementation. The existing Godot diagnostic composition, nested, leaf, Glow and sampler regressions were rerun with unchanged native references. See importer-loud-fail/r48/provenance.json and acceptance.json.

## r52 independent rounding-mode experiment

No new Flash capture. The checked-in x86_64 SSE intrinsic probe ran under Rosetta with explicit MXCSR nearest/down/up/toward-zero readbacks for each input. Source/executable/input/output hashes and compiler/host details are in importer-loud-fail/r52/environment.json. This measures independent constructions and does not infer Flash instructions. All native references and production rendering remain unchanged.

## r56 exhaustive reciprocal output image

No Flash capture or rendering change. An independent x86_64/Rosetta intrinsic probe enumerated every float32 input in the fixed normalized-byte domain [1/256,1], recording nearest-mode CSR and contiguous output runs. Compiler/host/source/executable/output hashes are in importer-loud-fail/r56/environment.json. This is a bounded hardware image, not an inference about Flash instructions or a fitted reciprocal table.

## r58 static native-byte candidate and bounded CPU gate

No new Flash capture. The current installed Flash Player Debugger32 Mach-O was read only; its hash, constant addresses and instruction-span bytes are pinned in importer-loud-fail/r58/static-binary.json. Static inspection is not execution evidence. LLDB/Rosetta startup did not yield a verified breakpoint hit; logs and process cleanup limitations are recorded in r58/debugger/status.json. An uninterruptible new C helper produced no output and is not used. Successful arithmetic reproduction uses Python float32 operations and previously hashed r56/r57 hardware image measurements. No fitted coefficient or changed native reference.

## r59 actual FilterGroup GPU diagnostic

No new Flash capture or rewritten reference. Pinned r38 native buffers reused. Godot4.7.2, OpenGL4.1 Metal90.5 on AppleM2; executable hash and commands in r59/render/provenance.json. RF reciprocal upload is checked byte-for-byte. Production remains disabled. The r58 uninterruptible helper PID24123 was still in U state at this round; its output is not used.

## r60 broad GPU arithmetic controls

No new native capture. All old/signed inputs and outputs are reused with unchanged consumed operand rules. Godot4.7.2, OpenGL4.1 Metal90.5, AppleM2, same executable as r59. RGBAF/RF upload bytes are asserted equal on readback; output RGBA8 is compared exactly. Shared shader helper unchanged from r59. Production remains disabled.

## r61 native filter rectangle capture and color-order diagnostic

Fresh Flash Player Debugger32 capture via capture_native_player.py/LaunchServices:65 events, done=true; launch metadata in r61/native/capture-environment.json; binary/OS hashes in player-environment.json and source hashes in build.json. The original r03 color-order pixel reference is unchanged. Godot4.7.2 OpenGL4.1 Metal90.5 on AppleM2. Logical diagnostic span metadata uses independent API rectangles; production buffers remain unchanged.
