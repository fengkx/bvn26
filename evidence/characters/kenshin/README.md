# Kenshin / 剑心 playable source port

Base commit: `e7876e6f7eb14625a973cc79aaffa52dea169a06`, branch `feat/kenshin`.
Coverage is **partial**. This is character-SOP evidence, not an oracle/native-debugger
capture or complete 1:1 certification. No deployment or merge is authorized here.
All six proof/admission flags remain false.

## Source-first answers

1. Source-select, catalog and coverage identify `剑心`, `Kenshin.swf`, no clone,
   between Kakashi and Byakuya. Root frame 1 mounts BODY Sprite 643 (1,165 frames).
   The original source hash is `648d781f59734e1b120b30c340685a74e223e5be49c186c31b796467db4f2e7f`.
   `source-first.json` inventories all three BODY timelines, frame scripts and
   display-list changes, including empty frames. Locked game/scripts inputs are unchanged.
2. Sprite 643 frame 1148 calls `wankai()`: wrapper transfer HP/energy, replace the
   root `feiint` interval when not wudi, then advance the wrapper. Root frame 2
   mounts Sprite 1473. Its frame 1503 repeats that lifecycle into root frame 3 /
   Sprite 2506. The old BODY continuation retires at replacement; it must not
   execute the following `_root._y = 0`. New BODY load/local state is initialized
   independently; HP/energy and wrapper-owned transfer survive.
3. `doWanKai()` enters each target's authored transformation label. Original root
   observations see the new, uninitialized frame 1 at ticks 33 and 188, followed
   by frames 1375 and 972 at ticks 34 and 189. `wankai_end()` at 1399/1019 checks
   wrapper 万解, calls cbsw, clears bs, then clears the wrapper flag. No invented
   end-frame recovery or fixed timer ticks are used. Compiled fallthroughs preserve
   the actual label flow.
4. Source invariants and corrected gaps:
   - Base frame 552 reads opponent body width **plus 100 pixels**, with mirrored
     signs. The compiled warp retains both terms. Runtime dimension reads retain
     double precision instead of passing through Vector2 before AS2 twip storage.
   - Third-form child Sprite 1568 retains `8 * (facing <= 0 ? -1 : 1)` grouping.
   - Third-form frame 600 unconditionally adds 350 HP, without an invented clamp.
   - Child Sprite 2274 forwards `showdow({R:255,G:0})`, including absent B.
   - Wrapper frame 3 also places Sprite 2581 at depth 45. Its independent 37-frame
     animation retains source matrix, color transform and blend mode 8, outside
     BODY color/transform/pause. The optional extractor rejects unowned sibling
     actions, callbacks and earlier placement lifetimes.
   - HIT_RECEIVE A–D uses the existing shared receiver and source gjlN/showFace
     compilation. The shared-source suite checks the common chain; live matching
     fixtures provide the scoped step-E state evidence.
5. Original Flash captures use the mandatory exclusive `flash_lock.py` helper,
   diagnostic AS2 observation/input fixtures, original RNG, and explicit Gaara/Kon
   helpers. No FDB or M0-02 capture is involved. Captures alone are never parity.
   Original timer entry/exit observations supply the external replay tape;
   callback intervals vary between 30 and 31 observed fight ticks. The same
   captured callback function follows the new BODY path. Second replacement
   cancels ID 1 and registers ID 2. The wudi fixture has an explicitly observed
   precondition and zero callbacks.

## Ownership and lifecycle

| State | Owner / initialization | Retention and removal |
|---|---|---|
| HP/energy transfer, 万解 | wrapper / wankai | persists across BODY replacement; consumed by doWanKai |
| Local hit flags/controller variables | each BODY load/frame 1 | old receiver retires; new locals do not inherit sentinel state |
| feiint handle | root / wankai | clear previous interval before registering replacement; round/menu teardown clears owner |
| feixue receiver | captured source function plus BODY path | resolves the current live mc; pause and hp > maxhp/5 guard remain authored |
| Sprite 2581 playhead | wrapper frame 3 / PlaceObject3 depth 45 | advances independently of mc, loops 37 frames; rollback restores clock |
| Body warp | ordered frame call / source invocation | reads current target dimensions at execution, not guessed attack geometry |

## Evidence scope and rejected runs

The comparison index records **22/22 matching cases, 16,964 actor states and 14 exact fields**.
The independent wrapper/BODY/effect clock comparison has **722 matching rows**.
The 204-case saved roster replay matches 119,008 states; the 62-case recent
Juugo/Karin/Mayuri/Killer Bee replay matches 44,764 states. Both original
source hashes and fixture hashes are checked before replay.
The clean final native batch reports `MOVE_CASE_BATCH_OK 22`, exit 0, with no
script/runtime errors. `native-final` supersedes diagnostic batches.
The final checks record completed results and explicit residuals. Source
`events.jsonl`, build metadata, instrumentation diffs, input/clock/random tapes
and capture summaries are retained. Large raw files are losslessly gzip archived; `archive-index.json` maps original
paths and uncompressed hashes. Saved-roster raw runs are retained in tar.gz, with
readable reports alongside them. Raw captures may contain original absolute
scratch paths; they are provenance, not a claim those scratch directories persist.

- `combo-r01` is the preserved earlier **original-only** capture, not a pass.
- `r02` initial capture had an invalid single-element target range; diagnostic only.
- Native r01 preserved the missing warp and transformation-end differences.
- Native r02 exposed the one-twip warp loss; failed outputs remain diagnostic.
- `forms-r01/transform-invulnerable` did not contain the wudi precondition because
  the shared dynamic probe was built without it. It is **not** an invulnerability
  negative case. `invulnerable-r01` uses a dedicated build and supersedes it.
- `wrapper-r01` queried dynamic depth 45 and returned undefined. `wrapper-r02`
  observes authored timeline depth 45 at AVM1 depth -16339 and supersedes it.
- A first saved-roster replay used relative output paths; file writes failed.
  Those are execution failures, not gameplay mismatches or passes. The absolute
  output-path run is retained separately.

The compiler impact report compares all 38 prior BODY packages. Expression/body
and controller compilation remain unchanged for those inputs. Newly recognized
wankai_end calls change recompiled contexts for Lanran and five existing form
packages; their shipped packages are not rewritten by this port. This existing
uncompiled-source coverage remains separately visible in the frame-call audit.
Kenshin's cached context and complete three-node form contract must pass that audit.

## Export resource preflight

The first actual Web J+K path remained in a black super background. The exported
log and screenshot are retained as a failed run, not a pass. An isolated PCK
check identified `Missing replacement asset: 606.png`: `FileAccess.file_exists`
cannot validate remapped exported textures/scripts. `SourceFormProfile` now uses
`ResourceLoader.exists` for resources while retaining file/JSON/content checks.
No missing asset, controller or lifecycle guard is bypassed. The standalone
`web/packed_profile_check.gd` must run from an empty project with only the PCK,
so source files cannot mask an export defect. The Kenshin natural J+K activation
check and seven existing form input paths pass after this change.
The rebuilt PCK passes both replacement profiles from an empty project; a missing
profile still fails. Actual headed Chrome then completed selection, natural opening
and both J+K replacements. Snapshots show `kenshin-2` and `kenshin-3`, standing,
released pause, and third-form HP drain. Screenshots show both costumes and the
wrapper effect. `web/browser-check.json` binds observations to the exported build
and PCK hashes. These are programmatic keyboard/UI checks, not OS input proof.

## Remaining acceptance scope

Targeted exact actor states and wrapper clocks do not establish full pixel,
waveform, AI, every cancel boundary, all maps/opponents or full browser lifecycle
parity. Native screenshots show rendered content and the actual selection path;
they are not a Flash pixel comparison. Third-form assets and executable replacement
lifecycle are included; untested form actions remain unaccepted. Source timers are
external recorded inputs in deterministic replay, not a claim of identical OS timer
scheduling. PR #37 protected interrupted-super recovery is unchanged.

## Reproduction

Use the pinned Godot 4.7.2/JPEXS 26.2.1 under the restored toolchains directory.
`build_port.py` rebuilds all three slices/assets/controllers from a separate JPEXS
workspace. Then run `prepare_form_graph.py` with targets 2 and 3. Audit and update
only reviewed frame-call contracts. `build_timer_probe.py` adds observations to a
separate original-game copy. Build precondition-specific probes separately.
Every launch must remain under the exclusive Flash helper. `prepare_replay.py`
creates a native fixture from observed callback delivery, without rewriting the
source fixture or trace. Run `move_case_reference.gd`, then exact comparison.
The UI font was regenerated using `build_menu_font.py`, Sarasa UI SC index 199,
and the existing license; the non-ASCII coverage test must execute without skip.
