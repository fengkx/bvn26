# Susanoo Sasuke source-first candidate

Status: offline candidate; **not ready for a Draft PR**. All six proof/admission flags remain false.

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
| Special pause | Existing source-compiled bsd/cbsd/bsw/cbsw calls | Source resume boundaries; rollback/round reset still need execution | BODY727 frames777,802,884,921,997,1022,1094,1138 |
| Child instances | Source PlaceObject/MOVE/remove timelines | Native shared lifetime interpreter; no per-character reset or offset patch | Complete timeline and nested scripts in inventory |

The root timeline has one frame and no replacement edge was found. The body has no 万解 label. This is not permission to disable a controller key: ordinary strict controllers compile without disabled action overrides. Initial use of the replacement-package build helper produced incompatible parent initialization obligations; the failed guard is retained in `logs/strict-compile-r01.txt`. The build now uses normal strict compilation, with no shared compiler/runtime change. Fresh compilation must equal the cache, and deleting any individual frame call must fail the guard.

The source five-question record is incomplete until original-player observation: scripts and placement history are retained, authored exits remain compiled, source invariants have tests, but live same-input behavior has **not run**. The 13 fixtures declare intended source action ranges; they do not assert observed target coverage. Repeated same-instance casts, actual side crossing, hide/restore interruption, pause/reset and render/audio comparisons remain required. No full parity, default initialization, OS-input, pixel or audio acceptance is claimed.

## Execution and blockers

Desktop was reported locked at 17:32 Asia/Shanghai. Foreground is suspended without repeated lock checks; Sage Naruto has first claim after unlock, then this lane. `probe-r01` is built, not run. No Flash process has been started by this task and PID24366 is untouched.

The first headless Godot import retained editor-settings sandbox write errors and is not a clean exit. A normally approved second headless import writes the standard editor settings; its result is tracked separately. Prior headed RID/resources-in-use failures remain unaccepted inherited residuals; this candidate has no headed acceptance evidence yet.

Tests and evolving results are recorded in `checks.json` and `logs/`. Font rebuilding actually ran through `build_menu_font.py`; font coverage passed. Portrait export initially failed because Pillow was absent; the successful retry used a temporary uv environment. No dependency/toolchain reinstall or production deployment occurred.
