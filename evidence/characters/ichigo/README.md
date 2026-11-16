# Ichigo Zero / 一护2 candidate port

Base: `a3b479414546250b7d0cd6e35cbc3ae52b3169d1`; branch `port/ichigo-base`.
This is an independent author lane for `game/fighter/ichigo.swf`, including
White Ichigo / 白一护. It is not the existing `yihu.swf` fighter or its forms.
Targeted draft review only; no merge, production deployment or admission.
The source-controlled matchmaking catalog is in scope; production Worker
configuration and network changes are not part of this port.

## Identity and source-first answers

1. `selection-audit.json` compares the actual main SWF Sprite 1477 placement
   order with all 40 source selector cards. After available fighters, their
   generated internal forms, and in-progress Temari are excluded, the order is
   仙鸣, 一护2, 佐助须佐. This lane takes only the second. 石田 is already available.
   The source SHA-256 is
   `21bf68e942d417b0b39e8702ae388b8146a9c275510d83125d51a4f08dd9723f`.
   Sprite 274 has 907 frames; replacement Sprite 632 has 1,108 frames.
   `source-first.json.gz` retains scripts and display changes, including empty
   frames; the extracted timelines retain original transforms and placements.
2. BODY owns combat locals and the playhead; the parent wrapper owns the form
   transfer and the source root interval owns `feiint`. Base frame 844 starts
   the 300-energy transformation; frame 886 calls the original `wankai`.
   Wrapper replacement transfers HP/energy, clears the old interval, registers
   the new source interval and replaces BODY. New BODY locals do not inherit
   an old sentinel. `doWanKai` jumps to 开场 968; the first observed post-advance
   state is 969, as both Flash and native traces show. The form resumes at 1015.
3. Base normal super starts at 383 and checks the opponent action at 415.
   The complete source `!= -1` block preserves gotoAndStop followed by play;
   no end-of-label recovery was added. White upper attack's placed child moves
   the wrapper by 25 until it crosses the opponent, calls `setDirect(±1)` and
   enters 砍技22. Both calls remain in generated controllers. The retained
   source has no method definition; fresh before/after Flash observations in
   both directions show undefined return and unchanged facing. The compiler
   admits this exact reviewed SWF/sprite only and fails on a new binding.
4. Both packages use the existing body/controller/hit/sound/form runtime.
   There is no character-specific runtime branch. White Shape 309 is a pair
   of adjacent source fills: exact reversed shared edges are removed to form
   one boundary. Islands, duplicate edges, branches and crossings still fail;
   no bounding-box substitute or dropped call is used. The 31 prior base
   context compiler outputs are byte-identical to the pinned baseline.
5. Fresh diagnostic Flash captures use distinct movie processes under the
   approved `bvn-lane3-next-port` lock. PID 24366 is untouched. Instrumentation,
   input fixtures, source hashes, timer observations and raw logs are retained.
   Native form replay delivers the recorded timer callbacks; it does not
   invent a fixed 30-Hz schedule for wall-clock timers. Source-only archives
   may contain historical files named `native.json`; these are not Godot proof.

## State lifecycles

| State | Owner and writes | Retention and reset | Evidence |
|---|---|---|---|
| BODY locals / playhead | Sprite 274 or 632 load and frame scripts | MOVE retains; wrapper replacement creates fresh BODY | Full source timelines; lifecycle rollback test |
| HP / energy | BODY; wrapper transfer during wankai | Explicit transfer survives replacement | Natural input and replacement checkpoint tests |
| feiint | Root interval, registered by wankai | Old handle cleared; callback tests pause and HP > maxhp/5 | Observed timer tape; pause/threshold test |
| Form HP drain | `feixue` calls `loseHp(10)` | 201 becomes 191, then stops; paused callback does nothing | Source and lifecycle test |
| Upper-attack child | Source placement at form frame 300 | Placement instance owns callback; authored goto controls exit | Mirrored repeated fresh Flash/native cases |
| Next round | Source nextfight/chushi | Health restored on current form; no invented base reset | Lifecycle test |

## Validation scope and residuals

`comparisons.json` and `checks.json` are the authoritative executed counts.
The initial 15 fresh targeted cases matched 10,830 actor states across 14 exact
fields. Five additional White Ichigo action cases match another 3,610 states:
20 cases / 14,440 states in total, as recorded in `targeted-summary.json`.
The additional form cases declare a single energy refill after natural
transformation; they are controlled action evidence, not a full natural match.
The final batch exited 0 with no script/resource-loader errors or exit residuals.
The initial saved-roster run completed 25/300 cases (17,810 states), all matched.
The remaining 275 cases completed with unchanged source/fixture hashes.
All 300 cases match 189,400 actor states (`saved-roster-full-results.json`).
Five retained negative/overlap/interruption fixtures do not reach their target;
they are not counted as five covered moves. The saved Jianba ultimate reports
two ObjectDB instances and one resource still in use at exit, still unaccepted. The initial partial output remains in
`saved-roster-partial.tar.gz`, and is not presented as a full-roster pass. Initial failed importer, output-directory, resource-import and
incorrect capture-frame runs remain diagnostic, not passing evidence. Tests
must inspect script errors as well as exit codes: Godot assertions can return
from a function while the runner later prints a success marker.

The actual menu font importer ran successfully with Sarasa UI SC TTC index 199;
coverage passed. The regenerated font is retained with its hashes. Only the
font timestamp differed, so the shared runtime font was restored byte-for-byte.
Selection and base/form native screenshots were inspected; they are visual
observations, not a Flash pixel or audio-waveform parity claim.

The initial compatibility mismatch is resolved after the user clarified that
in-repository catalog wiring is required. `catalog-integration-resolved.json`
records preservation of all 31 previous fighters, addition of only `ichigo`,
and successful strict manifest generation. `serial-integration-blocker.json`
is historical evidence of the earlier failed gate, not a current dependency.
No other author lane's worktree or character assets were changed.

Headed form capture reports resources still in use and material/shader/texture
RID leaks on exit. These are unaccepted residuals; they are not hidden or fixed
by unrelated renderer cleanup. Exhaustive audiovisual, browser focus/input recovery, AI, maps,
opponents and input/cancel boundaries remain unverified. No complete 1:1 claim.
All six proof/admission flags remain false.

## Additional White Ichigo action coverage

The fresh form-action reports cover held combo, sequential neutral/down/up
ranged inputs, guarded normal super, upper super and ultimate. The original
combo attempt exhausted its 120-second wall budget at fight tick 231; it is
retained as incomplete. Its retry keeps the exact fixture and completion checks
and increases only the wall budget to 360 seconds. All five complete Godot
replays exited zero without script or resource errors.

Observed source/native outcomes include 650 damage / four receiver hits for
the ultimate, 280 damage / one hit for upper super, and 96 guard damage with
zero hits for normal super. These values describe the retained fixtures, not
all opponents or range conditions. The form returns to source standing frames
in each completed case; no end-of-label recovery was invented.

## Local Web evidence

The standard staged Web build passed clean import/export log scans and strict
manifest checks. The final PCK cold-load check resolves White BODY 632 and
rejects a missing profile. `web/build-metadata.json` binds the exported PCK
SHA-256 to build ID `9752865ebb97b40ba2fc87db184a35744e3f14f8bd5cf8c5f1388814c68c3289`.
The snapshot reports the pre-evidence commit plus dirty staging import UID and
export-template paths honestly; it is not a clean-commit or deployed build.

Headed Chrome r04 observed the source selection card/footer, natural J+K
replacement, White standing with the global pause released, HP 1000 -> 990,
and a natural jump. `web/browser-check.json` verifies the browser build ID and
PCK hash against the sidecar; the final console contains no script/resource
errors and no JS exceptions were recorded. `form-jump-early.png` shows the airborne body. The later supplemental
screenshot does not show the body and has no simultaneous source-frame
snapshot, so it does not establish rendering parity; the main `form-jump.json` observes
frame 90, but its later screenshot already shows landing. Screenshots and
snapshots are not asserted to be simultaneous or pixel-equivalent to Flash.

Earlier browser attempts are retained under `web/failed-r01` through `r03`.
They used premature menu input or insufficient source navigation intervals.
The successful r04 additionally uses `training_confirm_supplement.mjs` for
the two omitted P1 confirmations (training uses P1 for both players/helpers),
and `jump_capture_supplement.mjs` for the airborne screenshot. All operate the
same isolated browser while this lane holds the approved foreground lock.
Training recovers HP every second; the diagnostic eventually observed HP 990,
not a sustained loss. No runtime state was assigned by browser automation.
Programmatic CDP inputs are not physical OS-input proof. No production deploy.

## Capture teardown follow-up (2026-11-16)

The capture harness now closes the existing rollback adapter, stops combat
drivers (including KO callback unbinding), frees the scene and waits for audio
mixer retirement before reporting success. This removes the retained snapshot
resources and KO dispatch reference cycles in the reproduced headless path.
`--check-shutdown` explicitly skips images and records that fact in metadata;
it cannot serve as visual acceptance. Original capture targets, inputs and
energy interventions remain unchanged.

`shutdown-r01/checks.json` and compressed raw logs record the executed base/form
checks, source frames, script hashes and measured process durations. All listed
checks exit zero with no script, resource, RID or ObjectDB diagnostics. The first
sandbox attempt had a macOS certificate-access error; a normal-permission rerun
produced the retained clean results. Headed renderer exit cleanup, historical
saved-roster exit warnings, full audiovisual/AI/boundary acceptance and all six
proof/admission flags remain pending/false. No merge or deployment.

## Merge validation (2026-11-16)

The existing Compatibility renderer capture targets were rerun under the
exclusive foreground lock. All lane cases exit zero without script errors,
RID/ObjectDB leaks or resources-in-use warnings. Selection and combat PNGs
and raw compressed logs are retained in `merge-validation-r01`. Fighter and
required replacement images were inspected. This closes the capture-harness
headed exit residual for these runs; historical saved-roster warnings and full
aligned audiovisual/AI/exhaustive acceptance remain unresolved. Six flags
remain false. The user authorized merging these targeted character ports.

Pre-merge roster tests exposed stale hand-maintained expectations in inherited
selection/opening checks. Current admitted base entries are added explicitly,
with opening intervals and kcplayed assignments verified against pinned source
bundles. Source audit records retain timeline changes and exact script paths.
No gameplay fixture, source output or comparison tolerance is changed.

Serial integration now retains 33 selectable base fighters. The combined
original-input replay passes 37 cases / 27074 exact actor
rows; see `merge-validation-r01/integrated-replay.json` and its raw archive.
Menu font was actually rebuilt with available-roster coverage (502 characters).
Godot resources were imported before the accepted replay; an earlier attempt
before importing the newly merged assets is retained separately as failed.
No gameplay/compiler behavior was changed during this integration.

Local standard Web export, packed replacement-form loading and Chromium boot
passed; see `merge-validation-r01/web/` for build identity, PCK hash, raw
logs and browser screenshot. Snapshot dirty provenance is explicitly retained.
