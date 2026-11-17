# Temari / 手鞠 — partial targeted candidate

Base: `a3b479414546250b7d0cd6e35cbc3ae52b3169d1`.
Branch: `port/shouju-base`.
Worktree: `/Users/fengkx/me/agent-code/bvn2_6-shouju`.

This is committed, playable native WIP with partial targeted evidence. Targeted SOP evidence is recorded below; full character admission remains
unaccepted. Merged as a targeted port in PR #294 on 2026-11-16; full admission
remains false. The original handoff below does not certify production deployment.
The source selector, manifest catalog and coverage order confirm 手鞠 from
`game/fighter/shouju.swf` immediately after 小乌. See `selection-order.json`.
Standalone form variants remain deferred. No other character is started.

## Source and lifecycle

The locked SWF SHA-256 is
`71749a25bd0cab546e89a09c2aa37ca455a725e4c1fd4e388f63b6babe03eb5d`.
Root frame 1 places BODY 541. `source-first.json` inventories all 1,279 BODY
frames (including empty frames), scripts, placement/MOVE/removal changes,
sound events and wrapper scripts. No replacement BODY is activated by this work.

- Standing frame 2 clears hits. New controller placements initialize local
  fields; MOVE preserves instances. The existing compiler retains this distinction.
- Combo controller windows start at 226, 256 and 294. They retain authored
  predicate ordering, including cancellation to ranged attacks and supers.
- Normal super costs 100 at 600, starts presentation at 601, resumes at 617,
  and explicitly returns at 652. Upper super costs 100 at 688, starts at 689,
  resumes at 708, and returns at 741. Ultimate costs 300 at 790, starts at 792,
  resumes at 822, and returns at 934. All use the source face label 手鞠1.
- The normal-super controller placed at 618 calls moveX(30) when unpaused.
  Its lifetime comes from the timeline, not a guessed duration.
- Defence/hurt/flying callbacks are at 1035/1047/1060. Receiver rules are shared;
  no character-specific runtime patch was introduced.
- Source frame-call checks compare fresh strict compilation with the cache and
  reject deletion of every compiled call. The new requirements entry is pinned
  only to this SWF hash and BODY. No key or guard was disabled.

Fresh original/native comparisons cover **17 primary fixtures, 12,634 actor
states and 14 exact fields**, with no differences: 16 action scenarios and one
absent-label negative/no-op. `comparisons.json` covers the first 16 fixtures;
`crossing-r04-comparison.json` adds the 540-frame continuous crossing run.
All fixtures declare their target and reach it. Probe/build metadata, locked
SWF hashes, instrumentation diffs, initial conditions, input and raw captures
are retained. Runs use diagnostic controlled initialization and key injection;
they are not global initialization, AI, OS-input or production certification.

`continuous-lifecycle.json` retains both failed fixture designs and the accepted
same-instance sequence. Three upper supers enter at ticks 11, 281 and 421;
P2 jump/left input moves the target from x=350 to x=122, while Temari stays at
x=300 and changes facing from +100 to -100. Initial energy is 300, then 200 and
100 at entry, without mid-run refill/reposition. Tick 540 has recovered to
standing frame 4. The prior 722-state crossing *attempt* also matches but never
crosses; it is supplementary evidence, excluded from the primary count.

| State owner | Initialization / persistence | Exit / reset | Source |
|---|---|---|---|
| BODY playhead | Authored label entry; continued source frames | Explicit return, stop, or timeline fallthrough | BODY 541 full frame inventory |
| Controller instance | New PlaceObject initializes fields; MOVE retains them | Display-list removal/replacement | `source-first.json` placement/change records |
| Super pause and energy | Costs at 600/688/790; pauses at 601/689/792 | Resumes at 617/708/822; returns at 652/741/934 | BODY frame scripts |
| Receiver/hit state | Shared receiver and body hurt callbacks | Source standing/recovery frames; round reset smoke | BODY 2, 1035, 1047, 1060 |

## Build

Use Python 3.11+ (the system Python 3.9 attempt failed and is retained):

```sh
python3 tools/importer/export_swf_xml.py \
  --ffdec-jar /Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec-cli.jar \
  --output-dir /private/tmp/bvn-shouju-export game/fighter/shouju.swf
/opt/homebrew/bin/python3 evidence/characters/shouju/build_port.py \
  --workspace /private/tmp/bvn-shouju-export \
  --ffdec /Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec-cli.jar \
  --ffmpeg /opt/homebrew/bin/ffmpeg
```

Generated assets, intro, portraits and footer are activated in the 32-fighter
selection and matchmaking catalogs. Native headed selection/combat screenshots
are retained under `visual-resume`.
The source compiler accepts the package without shared runtime changes.
Reference fixtures explicitly select the existing Gaara/Kon helpers on both ends;
the Web run selects Kon/Gaara. The independent Temari assist is not part of this
base-fighter port, and canonical default-helper initialization is not certified.

The UI font was actually regenerated from Sarasa UI SC collection index 199,
using `build_menu_font.py`; the non-ASCII coverage test ran and passed. The first
attempt failed on the default uv cache permission. The second used a writable
temporary dependency cache; it did not install or replace the restored toolchains.

## Validation and remaining scope

The earlier desktop-lock blocker is resolved. Previous fresh captures completed
and released the exclusive Flash lock. The t342 capture used renewed user permission and the exclusive external lock.
It completed and released the lock; unrelated PID 24366 is untouched.

- Exact primary actor-state comparisons: 17 cases, 12,634 states, 14 fields,
  including actual continuous side-switch and complete recovery.
- Native rollback: natural intro, ultimate, guard, round reset and late input.
  Missing-label test passes with `disabled_actions` empty; no key suppression.
- Saved roster: 30 representative fixtures, 18,300 matched states; not the full
  288. One legacy overlap case has no target observation and is counted only as
  a state regression. No shared runtime behavior was changed; SOP section 6
  prescribes checks by impact, not automatic full-project replay.
- This resume: 30 source/receiver/import-guard tests and one non-skipped font
  coverage test passed. The actual font rebuild from the earlier turn remains
  recorded; no new UI strings or font modification required another rebuild.
- Previous Web export and 32-fighter manifest passed. Its PCK hash is
  `b2b22bdb51ae22d5da5b6c0c15e00163acae8392d2d1df7aac05e5ff468af592`.
  It was a dirty snapshot, including unused generated portrait files subsequently
  removed before preservation. It is not an exact-current-HEAD package.
  Isolated headless Chrome input attempts are retained in `web`; completion
  markers alone did not establish Temari selection/combat. Subsequent explicit
  screenshots and `web/validation.json` establish actual Temari selection,
  natural intro, Vs Com receiving hits, and training special entry, source pause,
  contact and recovery. Seven repeated normal-special entries are recorded.
  This is not a headed-browser or physical-keyboard acceptance claim.

Final t342 export also passed import/export (exit 0), strict log scans, eight
online-manifest tests, the online UI runner and the post-export fingerprint check.
`web/final-build-metadata.json` records source commit `004dceb8`, build ID
`f121dbc04f3107750f136fd6395cef0578727bb4a9861c067dc9b1e5ef691530`, and PCK
SHA-256 `b2f515f136575b45276f59917b71c5a9722eac6185a234a06df987b4fb2b8f2c`.
The snapshot honestly reports dirty: 176 generated UID files plus the bound export
preset and derived online manifest. No clean-HEAD claim is made. The final package
browser identity matches both sidecar and runtime. The same final package also
records seven normal-special entries, pause/contact and recovery after natural
intro in training (`web/final-package/validation.json`). See its
[selection](web/final-package/browser-select.png) and
[battle](web/final-package/browser-super.png) screenshots.
The frozen product inputs are unchanged by the later evidence/document commits.
Expected negative lobby-fixture warnings remain in `web/final-export-logs`.

Headed native capture exited with five resources still in use and shader,
material and texture RID leaks. These remain unaccepted, as do prior saved-roster
exit warnings. The earlier editor-settings sandbox write failure is retained as
a non-clean exit, not runtime acceptance. Pixel-aligned original/native visuals,
waveforms, exhaustive AI/cancellation and global initialization are not proven.
All six proof/admission flags remain false. M6 remains pending.

The t342 resume first preserved 1,146 dirty files in
`/Users/fengkx/me/agent-code/shouju-wip-20261115.tar.gz` (SHA-256
`4ec34d820852c5680a35635a7057ec3b1c2d212225f2d2a012d908c2abc2ffc7`),
then committed task evidence as `be5ab318`. Generated untracked UID files are
also preserved in that archive. No live weekly quota percentage/reset is exposed
by task tools; the user reports quota restored. The previous hard cutoff is
recorded, not confused with a new hard block. No extra quota was purchased.

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

The retained pre-fix diagnostic copy only bypasses screenshot rendering. Its
raw log reproduces 24 ObjectDB leaks, three CanvasItem RIDs and five resources
still in use; the fix reaches the same super source frame 618 without leaks.

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
