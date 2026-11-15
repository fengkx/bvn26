# Ichigo Zero / 一护2 candidate port

Base: `a3b479414546250b7d0cd6e35cbc3ae52b3169d1`; branch `port/ichigo-base`.
This is an independent author lane for `game/fighter/ichigo.swf`, including
White Ichigo / 白一护. It is not the existing `yihu.swf` fighter or its forms.
No Draft PR, merge, deployment, Worker modification or production admission.

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
All 15 fresh targeted cases matched 10,830 actor states across 14 exact fields.
The final batch exited 0 with no script/resource-loader errors or exit residuals.
The saved-roster run completed 25/300 cases (17,810 states), all matched, then
was stopped at the serial integration blocker; 275 remain unrun. Its raw partial
output is retained in `saved-roster-partial.tar.gz`. This is not a full-roster pass. Initial failed importer, output-directory, resource-import and
incorrect capture-frame runs remain diagnostic, not passing evidence. Tests
must inspect script errors as well as exit codes: Godot assertions can return
from a function while the runner later prints a success marker.

The actual menu font importer ran successfully with Sarasa UI SC TTC index 199;
coverage passed. The regenerated font is retained with its hashes. Only the
font timestamp differed, so the shared runtime font was restored byte-for-byte.
Selection and base/form native screenshots were inspected; they are visual
observations, not a Flash pixel or audio-waveform parity claim.

The compatibility gate currently rejects `service and Godot fighters catalogs
differ`. `serial-integration-blocker.json` records this required serial step.
The Worker catalog is unchanged as instructed. Local candidate registrations
and required future catalog entry are separate, reviewable changes in this
worktree; no other lane's worktree was written.

Headed form capture reports resources still in use and material/shader/texture
RID leaks on exit. These are unaccepted residuals; they are not hidden or fixed
by unrelated renderer cleanup. Exhaustive audiovisual, browser, AI, maps,
opponents and input/cancel boundaries remain unverified. No complete 1:1 claim.
All six proof/admission flags remain false.
