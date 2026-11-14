# Ulquiorra / 小乌 — source-bound base and required replacement

Base commit: `32ab99eecde34730fc2d6a5a7d26a403bd08faf5`.
Branch: `port/weqal-base`. Worktree: `/Users/fengkx/me/agent-code/bvn2_6-weqal`.
This is in-progress work, not an admitted character or a complete parity port.
All six proof/admission flags remain false. No merge or deployment.

## Verified selection

`selection-order.json` records the original source selector, matchmaking catalog
and coverage order at the base commit. The next unported base is `小乌`, displayed
as `乌尔奇奥拉`, from `game/fighter/weqal.swf`. It precedes `手鞠` / `shouju.swf`.
Sage Naruto (`仙鸣` / `minrenx.swf`) and other form variants are deferred by the
user. A `not_started` coverage row alone does not establish an unported fighter:
several previously implemented fighters retain that full-acceptance status.

## Source-first findings

1. Root frame 1 mounts BODY Sprite 387, 1,187 frames. The SWF hash is
   `ea72662bcb9c2a4c7ee9e9a81bb92c1beb1323f3982de86aa8e24a23286dc171`.
   `source-first.json` inventories every frame, including empty frames, scripts,
   placement/MOVE/removal changes and the source wrapper. Locked inputs are unchanged.
2. Controller placements at 166, 185 and 201 implement normal continuation and
   cancellation. At 201 the source tests ultimate, normal super, low attack,
   then ranged attack. The original combo reaches source frame 201 at tick 44;
   the cancellation fixture is calibrated from that observation.
3. Normal exits are 176/193/215. `必杀` at 468 has no terminating script and
   falls through into `空中必杀` at 469. Cost is applied at 470, super starts
   at 471, resumes at 492 and returns at 527. Upper super starts at 529,
   resumes at 553 and returns at 586. Ultimate starts at 632, resumes at
   715 and returns at 768. No guessed label-end recovery is introduced.
4. Low attack frame 233 reverses facing, places X at the opponent's X ±100,
   and copies opponent Y. It is a source warp, not a guessed dash. Shared
   hit/receive source tests cover the 35 fighter and 26 helper bundles.
   Guard/hurt calls are 825/837/850; standing frame 2 clears hits. Source
   super face label is `小乌1`. No character-specific runtime patch was added.
5. Fresh original Flash runs use the mandatory external lock with holder
   `bvn-next-base-port`. These are diagnostic key-injection/source-state
   captures with explicit Gaara/Kon helpers, not OS-input/oracle/M0-02 proof.
   Per-case source/build hashes, fixture encodings, instrumentation and raw
   logs are retained. Captured-source-only is not a native parity pass.

| State | Owner and initialization | Lifetime |
|---|---|---|
| Placement callbacks/local fields | Authored new PlaceObject/load | MOVE retains instance; removal/new placement replaces it |
| Combo/hits | BODY state and shared receiver | Standing frame 2 resets; guard does not increment |
| Super pause and face | Root bsd/cbsd/showFace | Authored bsw/cbsw frames release it |
| Low attack warp | BODY frame 233 | Reads current opponent position and facing on each invocation |
| Transformation transfer | Wrapper and wankai function | Transfers HP/energy, replaces BODY with 808; new load resets local fields |

## Required replacement graph

The base-required graph is `parent 1 / BODY 387 → parent 2 / BODY 808`.
Standalone selector variants remain deferred; this replacement belongs to 小乌.
`form-graph.json` audits both complete executable packages, load declarations,
source-bound functions, frame calls and dependent resources. The frame-call
requirements entry was added only for this source hash/BODY; no guard is weakened.
The original failed audit and manifest logs remain as historical evidence.

- Base failure `1061–1099` has no terminating goto/stop and naturally enters
  `万解` at 1100. Cost at 1101 and presentation at 1103 remain source-driven.
- At 1148 `wankai()` stores HP/energy in the wrapper transfer object, starts
  the authored root interval, calls parent nextFrame and removes the old BODY.
  The pending replacement is not a usable BODY until its next display tick.
- Parent frame 2 loads BODY 808 with fresh declarations (including `khit=0`),
  executes source initialization, binds the opponent slot and enters its opening.
  The observed replacement tick reports undefined BODY state; next tick is 968.
- Base frame 1152's explicit parent goto remains compiled and guarded. The
  earlier natural replacement normally removes that BODY before 1152; a controlled
  direct entry verifies that the explicit edge can still install the same target.
- BODY 808 frame 1023 executes `wankai_end`, releasing the source super pause.
  No second form node is reachable from BODY 808's frame-call graph.
- The old closure's `feixue` interval dereferences the current BODY. The fresh
  Flash probe records callback boundaries without altering delivery or callback
  bodies; native replay receives these recorded external events. This is not a
  certified global clock or OS timer parity claim.

`source-first-form2.json` retains every target frame/script/placement. Native
checkpoint coverage includes restore before replacement, redo, restore after
replacement, fresh-field reset, live interval callback, natural failure fallthrough,
and the explicit parent goto. These controlled entries are source/lifecycle tests,
not original same-input captures. Natural J+K activation is separately tested.

## Build and validation notes

`build_port.py` builds the source-bound candidate with the existing form-aware
compiler; this is compilation, not admission. Use Python 3.11+, pinned JPEXS
26.2.1 and Godot 4.7.2. Export workspaces are external scratch directories.
The UI font was actually rebuilt with `build_menu_font.py`, Sarasa UI SC index
199 and the retained OFL license. The non-ASCII coverage test ran and passed.
The first two font attempts failed due to missing fontTools / restricted cache;
those logs remain. The successful run used an isolated uv dependency environment.

The first native batch overlapped newly generated sound segments before their
Godot resource import. Its resource-loader errors are retained and that batch
is diagnostic only, even where actor-state comparison matches. The clean imported replay in `native-final` completed all 12 cases without
script or resource-loader errors.

Full audiovisual/AI acceptance and exhaustive boundaries remain unclaimed. See `checks.json` for final executed
results and remaining work. No Draft PR is opened while the admission blocker
or other required checks remain unresolved.

## Scoped validation

The retained 12 base Flash cases matched 8,664 actor states on 14 exact fields.
They are replayed again after graph activation. Fresh transformation and target
form cases extend this matrix; final counts and execution results are recorded in
`checks.json` and comparison reports. Target form resource refills are explicitly
recorded fixture interventions, not natural full-match input proof.

The UI font was regenerated by the real importer and its coverage test passes.
Selection/full footer and base super frame 493 were inspected. The headed renderer
reports exit-time resource/RID leaks: this remains an open cleanup residual.
Graph tests do not clear that renderer residual. Global pixel/waveform, all AI,
all maps/opponents and exhaustive input/cancel boundaries remain unaccepted.
All six proof/admission flags remain false; M6 stays pending. No deployment/merge.

Large originals and failed runs remain retained (lossless gzip where applicable).
Capture metadata contains historical scratch paths; it is provenance, not a claim
that those temporary builds remain available. See `checks.json` for current scope.
