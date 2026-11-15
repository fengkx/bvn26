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

The root timeline has one frame and no replacement edge was found. The body has no 万解 label. This is not permission to disable a controller key: ordinary strict controllers compile without disabled action overrides. Initial use of the replacement-package build helper produced incompatible parent initialization obligations; the failed guard is retained in `logs/strict-compile-r01.txt`. The build now uses normal strict compilation, with no shared compiler/runtime change. Fresh compilation must equal the cache, and deleting any individual frame call must fail the guard.

## Fresh original-player evidence

`comparisons.json` binds 19 same-input original/native cases (14198 actor states, 14 fields) to fixture, build and raw-trace hashes. All declared targets were observed. These are controlled diagnostic fixtures with declared energy/positions/helpers and Ichigo opponent, not canonical default initialization or OS-input proof. The continuous warp case enters three times with facing +100/-100/+100 and actual target position changes; the followup case contacts twice, not three times. Both 601-row root-position comparisons match. The static-input visibility probe matches 1202 visibility rows, including opponent hide/restore at ticks31/72 and301/342. A dynamic display probe was rejected for changing the root observation boundary; that rejection is retained and the guard was not weakened. Guard and interruption cases match, but interruption occurs before hide, not during hidden state. Rollback pause/reset evidence remains native-only.

## Remaining acceptance blockers

Seven original BitmapData root images and separately replayed native viewport images are retained in `visual-comparisons-r01.json`. Their 162 actor states match; their pixels do not. At tick43 the original has black flames around the opponent that differ from the native screenshot. Timer and foreground-stage images also differ. Source body frame805 places sprite368 as `bs2atm` at depth28, blend mode6; its nested name changes at46/50 and stops at69. This is a source lead, not an established root cause or a fix. No tolerance was relaxed. Audio has not been captured or accepted. Full visual/audio lifecycle acceptance and hidden-state interruption still require work, so this candidate is **not ready for a Draft PR**.

The coordinator released the priority window at19:40; captures subsequently ran under the exclusive Flash lock. Task-owned captures finished, our browser page closed and lock released. Existing PID24366 was never operated. The desktop-lock/queue blocker is no longer current.

The headed local Web build visibly rendered title, selection and a Sasuke-versus-Naruto training match on world. `web/training-snapshot-r02.json` proves actual fighter and build identity; `web/training-battle-r02.png` records the displayed match. Inputs used browser key dispatch including synthetic events, not OS-input proof. A prior attempt selected Kenshin and is excluded. `web/fight-r01.png` is actually a helper-selector screenshot, not fight evidence. A super input was attempted without retained action-phase diagnostics and is not counted. Full Web action/pause/focus recovery remains incomplete.

Build c894217bbc8c9489f7be9bbfb26adeb9ee169d97b60a01df156e5edc624b0ada, PCK187492ab9d5f1ce33e75a5c94dc55d560f13e8396290929fa4683570c1ca327d. `web-build-metadata-r01.json` records source commit9818773 and dirty snapshot provenance; this is not clean-tip acceptance. The local build previously passed11 metadata tests,8 manifest tests and headless lobby UI. No deployment occurred.

Thirty saved-roster cases /18300 states match retained originals, not the full288 matrix. The global frame audit still fails12 unchanged baseline contexts; candidate passes. Actual menu-font regeneration and coverage passed earlier. First-import editor-settings sandbox errors remain retained; later approved import was clean. Inherited RID/resources-in-use cleanup remains unaccepted; the current headed native visual log has no matching warnings. All six flags remain false.

Large raw artifacts are copied losslessly into `live-raw-r01.tar.gz` with verified per-file hashes in `live-raw-index-r01.json`. Original files remain in this worktree. Extract the archive at repository root before replaying evidence scripts in a fresh checkout. Failed probes and raw captures are included, not discarded.

## Subsequent visual investigation

`visual-investigation-r02.json` records two locked headed native experiments: three render waits, then derived display reconstruction without advancing source state. Neither removes the tick43 black-flame/foreground difference. Native frame805 already owns sprite368 at local frame1 and no hidden stage names. The independent source one-second timer is not driven by the same wall-clock tape in the bitmap captures, so timer parity is unproven. Sound trigger/lifecycle validation is required and still missing. The next buffer-inspection experiment was stopped before Godot launch by `DESKTOP_LOCKED_OR_UNKNOWN_STOP`; no further foreground attempt was made. Browser completion remains pending. No runtime/compiler correction or acceptance claim is made from these diagnostics.
