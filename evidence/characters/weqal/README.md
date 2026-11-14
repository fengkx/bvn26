# Ulquiorra / 小乌 base candidate — blocked, no PR

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
| Transformation transfer | Wrapper and wankai function | Requires BODY 808 replacement; unresolved in this base-only task |

## Blocking admission contract

The normal compiler rejects `DefineSprite_387/frame_1148/DoAction.as: wankai()`.
The existing form-aware compiler can preserve the operation and its target
BODY 808, and also preserves the explicit parent goto at frame 1152. However,
`frame_call_guard.py` requires a reviewed, complete executable replacement graph
for a package containing these operations. No such graph is present, because
the user deferred form variants. `frame-call-audit.json` retains the failure;
`logs/online-manifest-check.log` retains the missing reviewed requirements failure.
No requirements entry, source call, assertion or gate was removed to bypass it.

The source also naturally falls from `失败` into `万解` at frame 1100. Disabling
the J+K action alone is not evidence that all entry paths are unreachable.
Consequently this candidate must not be presented as a completed base-only
production package. Resolving the blocker requires a source-backed design for
explicit deferred-form boundaries, or separately authorized form implementation
and parity. This task does not implement the deferred variant.

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

Full audiovisual/browser/AI acceptance, exhaustive boundaries, and complete
saved-roster regression remain unclaimed. See `checks.json` for final executed
results and remaining work. No Draft PR is opened while the admission blocker
or other required checks remain unresolved.

## Final scoped results

All 12 fresh original/native cases match 8,664 actor states on the 14 existing
exact fields, with complete tick/slot coverage and all declared targets seen.
The original cancel enters the selected super window; this does not establish
all cancel boundaries. Natural opening/ultimate rollback/late guard/round reset
passed. Three saved combo fixtures (Kenshin, Juugo, Killer Bee) match; the full
saved roster was not run. Nine source tests and actual font rebuild/coverage
passed. Selection/full footer and super frame 493 were visually inspected.
The headed renderer reports exit-time resource/RID leaks, retained as a
lifecycle residual. These results do not remove the form-graph/manifest blocker.

Large original logs and event streams are losslessly gzip archived.
`archive-index.json` records their uncompressed hashes and paths. Scratch
`game` symlinks were removed from capture-build records; input encodings, build
metadata, instrumentation diffs and original logs remain in this worktree.
Locked-input verification and handoff checks passed. The online manifest gate
remains failed; no online catalog/fingerprint is represented as updated.
