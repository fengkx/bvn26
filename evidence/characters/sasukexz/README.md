# Susanoo Sasuke source-first candidate

Status: targeted behavior candidate with unresolved audiovisual acceptance; **not ready for a Draft PR**. All six proof/admission flags remain false.

The source selector's index 27 is 佐助须佐, an independently selectable `sasukexz.swf` entry (BODY727, root frame 1), not the base Sasuke WKframe variant. `selection-order.json` retains the source order and exclusion of pending Temari, Sage Naruto and Ichigo2. This branch starts at a3b479414546250b7d0cd6e35cbc3ae52b3169d1. `dependencies.json` records pending-port integration and the unavailable source-default Sage Naruto opponent. No unreviewed assets were copied from those branches.

## Source and lifecycle coverage

`source-inventory.json` retains all 1609 body frames, including frames without scripts, display-list changes/events, all 171 source scripts and 82 compiled-call frames. The source SWF SHA256 is fd634abbcefbcf50bac507e85e116038be0f63316b8d483a131597e2757bf20f. The script bundle SHA256 is 30d6b62fe925bb51e6a2193cd4ca178501a6149f63706e23880f9e434f7fbd20.

| State | Owner and initialization | Retention / release | Source |
| --- | --- | --- | --- |
| Facing and position | Fighter wrapper; upper attack frame 493 reverses facing, copies opponent Y and offsets X by 50 | Ordinary wrapper state until another authored write | BODY727/frame493 |
| Opponent visibility | Opponent wrapper, hidden at 638 after conditional followup | Restored explicitly at 679; interruption before restoration still needs original observation | BODY727/frame624,638,679 |
| Followup entry | Body playback head; requires opponent HP > 0 and action == -1 at 624 | Explicit gotoAndStop + play enters 招21; no synthetic forced followup | BODY727/frame624 |
| Combo recovery | Body action field and source callbacks | Authored recovery writes and explicit return functions; label ends are not synthetic returns | BODY727 frames236–386 |
| Opening | Body kcplayed | 1 at1431, 3 at1433, 2 at1510 with explicit return | BODY727 opening scripts and intro.json |
| Special pause | Existing source-compiled bsd/cbsd/bsw/cbsw calls | Source resume boundaries; native rollback/round reset passed, original reset not compared | BODY727 frames777,802,884,921,997,1022,1094,1138 |
| Child instances | Source PlaceObject/MOVE/remove timelines | Native shared lifetime interpreter; no per-character reset or offset patch | Complete timeline and nested scripts in inventory |

The root timeline has one frame and no replacement edge was found. The body has no 万解 label. This is not permission to disable a controller key: ordinary strict controllers compile without disabled action overrides. Initial use of the replacement-package build helper produced incompatible parent initialization obligations; the failed guard is retained in `logs/strict-compile-r01.txt`. The build now uses normal strict compilation, with no shared compiler change. The later shared render correction is described below. Fresh compilation must equal the cache, and deleting any individual frame call must fail the guard.

## Fresh original-player evidence

`comparisons.json` binds 19 same-input original/native cases (14198 actor states, 14 fields) to fixture, build and raw-trace hashes. All declared targets were observed. These are controlled diagnostic fixtures with declared energy/positions/helpers and Ichigo opponent, not canonical default initialization or OS-input proof. The continuous warp case enters three times with facing +100/-100/+100 and actual target position changes; the followup case contacts twice, not three times. Both 601-row root-position comparisons match. The static-input visibility probe matches 1202 visibility rows, including opponent hide/restore at ticks31/72 and301/342. A dynamic display probe was rejected for changing the root observation boundary; that rejection is retained and the guard was not weakened. Guard and interruption cases match, but interruption occurs before hide, not during hidden state. Rollback pause/reset evidence remains native-only.

## Remaining acceptance blockers

Seven original BitmapData root images and separately replayed native viewport images are retained. Their 162 actor states match; whole-frame pixels do not. The missing tick43 black flame and foreground were traced to the shared shine backdrop and corrected (below). Timer inputs are not aligned and wider raster differences remain unaccepted. No tolerance was relaxed. One original BODY StartSound trigger now matches native stream creation, but sound pause/cleanup and continuous audiovisual lifecycle are not accepted. Hidden-state interruption is also not covered. This candidate is **not ready for a Draft PR**.

The coordinator released the priority window at19:40; captures subsequently ran under the exclusive Flash lock. Task-owned captures finished, our browser page closed and lock released. Existing PID24366 was never operated. The desktop-lock/queue blocker is no longer current.

The latest local Web export completed with11 metadata tests,8 manifest tests and the headless lobby UI runner passing. `web-build-metadata-r03.json` records build d38ff4da0e2eabd28cca004a28526bee47dc22fe5159453f64c195f9157e3fbf, PCK e29b0c844b01e0b193eb2cb998cedfe5c5cc0393c510c2bbc388ce6eeba907c8, source commit52dcf4b and dirty snapshot provenance. This is not clean-tip acceptance or deployment. Raw import/export logs are retained compressed.

`web/lifecycle-r04.json` records Sasuke-versus-Naruto training, complete normal super followed by standing, stable paused actor snapshots, and cleared pause flags after resume on that post-fix build. `web/repeat-super-r04.json` records later casts and pauses at source838 and811 in the same match. Screenshots retain the actual rendered page, but these pause images are not frame43 original/native visual parity. Inputs are programmatic. The DevTools focus attempts did not establish an actual OS/window visibility transition. The native browser connector failed; accessing Chrome through the native app was then rejected by automatic review because of unrelated private windows. Specific approval was requested; no bypass or focus-recovery pass is claimed. Earlier wrong-selector and incomplete-action attempts remain excluded.

Thirty post-fix saved-roster representatives /18300 states match retained originals. The full saved corpus also completed:300 cases /189400 actor states matched in998.28 seconds. 10 cases emitted exit warnings/errors; these remain unaccepted, not clean passes. `saved-roster-full-summary-r03.json` lists them. The complete replay output is archived with verified member hashes in `saved-roster-full-r03.tar.gz` and `saved-roster-full-index-r03.json`. This is state regression, not audiovisual acceptance. The global frame audit still fails12 unchanged baseline contexts; the candidate passes. Actual menu-font regeneration and coverage passed earlier. First-import editor-settings sandbox errors remain retained; later approved import was clean. Inherited RID/resources-in-use cleanup remains unaccepted. All six flags remain false.

Large raw artifacts are copied losslessly into `live-raw-r01.tar.gz` with verified per-file hashes in `live-raw-index-r01.json`. Original files remain in this worktree. Extract the archive at repository root before replaying evidence scripts in a fresh checkout. Failed probes and raw captures are included, not discarded.

## Subsequent visual investigation

`visual-investigation-r02.json` records two locked headed native experiments: three render waits, then derived display reconstruction without advancing source state. Neither removes the tick43 black-flame/foreground difference. Native frame805 already owns sprite368 at local frame1 and no hidden stage names. The independent source one-second timer is not driven by the same wall-clock tape in the bitmap captures, so timer parity is unproven. At that stage, sound trigger/lifecycle validation was still missing. The next buffer-inspection experiment was stopped before Godot launch by `DESKTOP_LOCKED_OR_UNKNOWN_STOP`; no further foreground attempt was made. Those failed diagnostics did not justify a runtime/compiler correction or acceptance claim; the later isolation result below did.

## Shared shine backdrop correction

The missing frame43 flame and foreground are now explained and corrected: ScreenFlash read the earlier BackBufferCopy inserted by the lower darken-blended object. A copy directly behind ScreenFlash supplies all completed lower layers. `shine-backdrop-source.md` records source lifecycle, failed hypotheses and the confirming experiment. `visual-fixed-r12.json` preserves fresh corrected native images against the retained original, including unresolved whole-frame pixel differences and unmatched timer inputs. No fighter depth, blend formula, source call or key was changed. The same synthetic lower-copy regression fails without the refresh and passes with it. The initial harness leaked its unattached diagnostic node; its log remains, and the corrected harness exits cleanly. This does not accept inherited product cleanup residuals.

Post-fix checks:30 saved-roster representatives /18300 states matched, rollback smoke passed,26 source/import tests passed. Pre-fix Web evidence remains in `web/lifecycle-r03.json`; the rebuilt post-fix browser evidence is described above.

## Targeted sound observation

`sound-comparison-r03.json` compares fresh, independently inserted original StartSound markers against native AudioStreamPlayer creation/playing observations. One normal-super BODY727/frame776 sound331 occurs once in each. The source marker precedes its next root observation at tick14; native creation precedes that same observer. No blanket tick offset is applied. All722 actor states still match after instrumentation. The instrumentation proves original scripts, normalized XML and sound bytes unchanged apart from marker insertion. Earlier overwrite/path-binding and incompatible mode refusals are retained; no guard was relaxed.

This does not measure original waveform, device latency, nested/global/helper voices, real-time envelope output, or sound pause/cleanup. Raw source/native captures and failed probes are losslessly archived in `sound-raw-r03.tar.gz`, indexed by `sound-raw-index-r03.json` (130 files, every member verified). Extract at repository root; preserved originals remain untracked. No Draft PR yet.

## Bounded transport repair and independent audio investigation

The21:28 limited authorization allowed only establishing/verifying this task window. Native Chrome selection reached Sasuke and the map selector; the following screenshot timed out, so this run does not prove fight entry or focus recovery. `web/native-chrome-attempt-r05.json` retains that boundary. The later public provider-list health query failed before page discovery; a task-local JS reset followed by exact-URL binding also failed with Broken pipe(os error32). `web/transport-diagnosis-r07.json` records the attempts and public issue references. No whole-Chrome reread, internal API, raw CDP, restart or process kill was used. The deeper transport root cause remains unknown.

Independent native sound investigation reached source776 naturally and observed one sound331 player. Source stopMc is conditional: at this boundary bs=1, so the initial test assumption that pause always stops the fighter timeline was wrong. The initial assertion log remains. The corrected source-predicate test observes the event stream playing across pause/resume without restart and its node freed with the scene. This used the Dummy driver and exited with2 leaked ObjectDB instances /1 resource still in use, so neither audible output nor clean exit is accepted. See `sound-pause-cleanup-r02.json` and retained logs. No product code changed.

A fresh original Flash probe inserted read-only Sound.position/duration observation after source StartSound331. All69 reads returned undefined for both fields. The probe therefore supplies no playback-progress acceptance; all722 actor states still match the same-fixture retained native result. No sound attach/start/stop substitution was made to manufacture a readable result. `sound-position-comparison-r04.json` records the failed observation; raw probe/capture/collector output is archived losslessly in `sound-position-raw-r04.tar.gz` with verified member hashes. Task-owned Flash completed and the exclusive lock was released. Actual OS focus recovery, continuous audiovisual comparison and original sound pause/cleanup remain unaccepted; no Draft PR.
