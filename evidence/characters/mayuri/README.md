# Mayuri / 涅茧利 base-form port

Base: `b905eb5f9441c94bf3c75d87e6c8d8fa73ed0563`, branch `feat/mayuri`.
Rebased onto `147155cb3ecd6387dfd9ae60b3e3522dfbb02f78`.
Status: **targeted parity matched, partial coverage**. No merge or deployment.

## Source-first review

1. Locked `game/fighter/mayuri.swf` (SHA-256
   `b13277fdf268be9a0a6863d73d5cd17347cc2d0863365fa6757c62c34a891f81`)
   and `scripts/fighter/mayuri.json` select Sprite 487, 1,257 frames.
   `source-first.json` inventories every root frame, including empty frames,
   scripts and display changes. The extracted timeline preserves authored
   matrices, depths, creation frames and MOVE flags.
2. Controller placements at root 199 and 220 govern normal continuation and
   super cancellation; callbacks begin after placement. Root 395 places
   projectile `abcd`; root 871 places `cbs1atm`. Their source callbacks and
   nested timelines use the controller compiler. The resumed source audit found
   missing local initialization, hit-label jumps and movement guards; see
   [ranged-fix.md](ranged-fix.md). New
   placements and retained MOVE instances use the shared runtime lifetimes.
3. Normal returns are 210/230/272. Frame 220's controller allows `bisha`,
   `skill2`, then `nornalhit`; the native combo trace reaches 220 at tick 37
   after the heavy-hit pause. Frame 623 conditionally enters 必杀2 only while
   the opponent is alive and action is -1; 632 otherwise returns to standing.
   The continuation returns at 735. Upper super starts at 494, resumes at
   522, flips facing and copies opponent-relative X/Y at 528, then returns
   to falling at 563. Ultimate starts at 743, resumes at 871 and returns
   at 975. No end-of-label recovery is invented.
4. The receiver is byte-identical to Juugo's Sprite 2. Guard and hurt calls
   are 1045, 1057 and 1070; standing hurt recovery is 1066. Compiled gjl1,
   hits reset and super events reuse the shared hit/receive chain. The source
   intentionally uses `cbsw` at normal-super frame 600 and spells its face
   labels `涅浊利1` / `涅浊利2`; both are preserved. Tests assert those source
   facts, not guessed durations or geometry.
5. Native Flash captures use diagnostic copies of main.swf, the source
   input-read injection and explicit fixture setups. Completed source traces
   are distinct from Godot parity. Early 120-second incomplete captures are
   retained; later captures may wait 600 seconds without changing logical
   tick count, inputs or comparison precision. Flash launches only through
   the external lock with holder `bvn-mayuri`; lock waiting is not a failed
   capture. No live M0-02 or historical r-series capture is performed.

## Selection and scope

The source manifest has no Mayuri `fzurl`; default helper `鼬` uses the
already imported `you` helper. Source portraits, footer and opening use the
existing import tools. Opening writes kcplayed=1/3/2 at 1142/1144/1186.
Focused fixtures explicitly select existing Gaara/Kon helpers.

All six admission/initialization flags remain false. Full audiovisual,
browser, AI, exhaustive boundaries, G0, weak-machine, two-machine, TURN and
Internet acceptance are not claimed. Executed checks and remaining gaps are listed below; none establishes full admission.

## Executed focused results

On 2026-11-14 the console session was logged in and no longer reported locked.
All twelve unchanged fixtures were captured in the original Flash Player under
the exclusive `bvn-mayuri` lock (`--wait -1`), with approved foreground activation.
**12/12 cases, 8,664 actor states, all 14 fields, complete slot/tick alignment**
match the Godot port. The fields are frame, x, y, xscale, action, hp, ql, sw,
touch, touchFloor, hits, paused, hstm and hurtSkling.

The new captures resolve the five previously red comparisons and four source
capture gaps. Yesterday's locked-session failures and intermediate runs remain
in `diagnostics/`; old traces are not overwritten. No input, source timer,
comparison precision or threshold changed. See `capture-environment-20261114.json`,
`comparisons.json` and the dated `source-builds/20261114-*` directories for exact
encoded fixtures, source/build hashes, instrumentation diffs, tapes and logs.
The original `summary.json` is a capture-only record; `comparisons.json` records
the subsequent native comparison.

Observed outcomes include 2 HP normal guard chip and 5 HP super guard chip,
zero guard hits, incoming guard/break ending at 916 HP, and normal interruption
ending at 960 HP. Air ranged deals 180 damage / two hits. Ultimate deals
500 damage / eleven hits. Upper super deals 250 damage / two hits; its repeated
fixture enters at ticks 11 and 181 with opposite facing and deals 500 total.
Cancel enters super at tick 38 and deals 380 total damage / eight maximum hits.
These observations describe the selected fixtures, not exhaustive boundaries.
The ranged tick-164/165 collision divergence was fixed from source before this
recapture; [ranged-fix.md](ranged-fix.md) retains its causal evidence.

Godot selection and natural-opening/source-frame-616 battle images were rendered
and inspected in [visual/](visual/README.md), including the full source footer.
Aligned Flash pixel/audio, browser, AI and exhaustive boundary acceptance remain
unclaimed, consistent with the Juugo partial-coverage bar. No full admission,
G0, weak-machine, two-machine, TURN, Internet or OS-input proof is asserted.

The final Mayuri production rollback check passed with natural opening,
ultimate pause snapshot/replay, late guard input and round reset. Protected
recovery, player input/visual controllers, four projectile regressions,
controlled Mayuri repeated-placement invariants and CJK font loading passed.
An intermediate rollback run exposed missing scalar-only projectile
initialization; that failed run remains in `diagnostics/`. A four-case batch
also hit its wall-clock timeout; all four individual reruns then completed
722 states and reached their target actions. They were native-only evidence at that time; the dated 2026-11-14
original captures now complete their targeted comparisons. See `godot-checks.json` and retained logs.

The source/compiler Python group passed 41 tests, followed by all eight final
Mayuri tests (including missing-label rejection). Selection/opening passed six
tests; font provenance/coverage passed three; six contract schemas/examples
passed. The current versions of PR #44's 65 Python test modules plus three
related modules ran 383 tests: 377 passed immediately, two lacked historical
capture data, and four failed/errored. All four passed in the seven-test
correction rerun. The portrait count now includes Mayuri; the shadow audit
reads catalog-owned stage directories instead of obsolete frame directories,
without changing audited hashes, depth checks or compiled shadow output. See
[python-tests.json](python-tests.json). The unrelated historical-sampling test
inventory is not claimed as passed. Shared modes matched 602 PvP and 602 training-timer states;
post-rebase matchmaking typecheck and 31 server tests passed; the local
Wrangler test passed separately with approved sandbox escalation. Those historical results are not new network/Internet acceptance.

Shared projectile compilation/execution changed; prior generated fighters
were not rewritten. Compiler impact is checked against the original compiler,
including final parser contexts and full output checks for existing renamed
flash clips. The PR #37 recovery function is byte-identical: 1,086 bytes,
SHA-256 `9da62022432d7093b22b265b9e411db392ede4cbb1656fec21fe244f93f274ed`.
The resumed saved-roster replay passed all **204 cases / 119,008 actor states**,
using the same Juugo cohort and all 14 fields. After reducing concurrency,
67 already-completed cases were re-compared and the remaining 137 executed
with two workers. Source/fixture hashes, per-case results and measured process
times are in `regressions.json`; interrupted attempts remain diagnostic evidence.

The online compatibility manifest has now been regenerated and its full
consistency check passed (27 fighters, five helpers, ten stages). `online-fingerprint-delta.json` records the inventory delta,
including local import fingerprints; the pre-rebase baseline inventory audit is
retained in diagnostics.
No authority implementation or unrelated import/UID cleanup was performed.
Fingerprint generation is not online matchmaking or browser acceptance.

The work remains on `feat/mayuri`; only a Draft PR is authorized. Final post-rebase
checks are recorded in `checks.json` and `post-rebase-checks.json`: all twelve
replays remain byte-identical, all six Godot checks pass, 28 Python tests pass,
and the static UI font coverage gate executes without skip. The rebase did not
change the simulation/compiler used by the retained 204-case roster replay. No merge/deployment, admission-flag change,
timer workaround, shortened comparison window or font/parity gate bypass is used.
