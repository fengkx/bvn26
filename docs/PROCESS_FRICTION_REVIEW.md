# Process friction review (2026-11-16)

Review only. Base is `master` at `3dcd40c7a`. This document does not change
runtime behavior, flip any admission flag, merge a pull request, or deploy.

The port is slowed less by missing source rules than by applying the strictest
bar — full 1:1, sampler admission, or a green complete-ownership audit — to
work whose own SOP already allows a narrower claim. Several of those stricter
bars are real and should stay. They should stop being the gate for landing the
narrower claim.

Flags named below stay false. Nothing here admits production sampling, native
parity, M0-02, M2-04, or M6.

## What is a real bar

Keep these. They are correctness, not ceremony.

- Do not invent hitboxes, MATRIX components, gravity, or per-character branches.
  [SOURCE_FIRST.md](SOURCE_FIRST.md) and [HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md)
  steps A–D exist because those guesses already shipped wrong behavior.
- Do not call a slice 1:1, or mark M2-04 / M6 done, without the evidence that
  page names. [CHARACTER_PARITY_SOP.md](CHARACTER_PARITY_SOP.md) §5 already
  allows reporting a source-invariant regression while withholding the
  same-input claim.
- `production_admitted` and `native_parity_proven` stay false until a sampler
  receipt actually proves them. [IMPORTER_KNOWN_GAPS.md](IMPORTER_KNOWN_GAPS.md)
  already says the flag is an evidence record, not a runtime kill switch, and
  not a reason to pretend FilterGroup is disabled.
- The full `audit_importer.py` inventory stays nonzero while scripts still
  require owner review. Emptying that list to get exit 0 would hide scope.
- A Computer Use timeout is a facility failure. It is not proof that a key was
  not dispatched. [evidence/sampling-upgrade/s361/README.md](../evidence/sampling-upgrade/s361/README.md)
  states that correctly.
- Canvas blur must release held keys. The training P2 sticky-dash bug was a
  real lost `keyup`, not a tab-hidden pause. See
  [evidence/combat/training-p2-investigation/README.md](../evidence/combat/training-p2-investigation/README.md).
- Do not rewrite golden tapes, widen thresholds, or treat schema JSON as
  behavior acceptance.

## Findings

### 1. Targeted character SOP is still written as if it cannot merge

Impact: finished ports sit in draft language until a person repeats an
authorization the repository already recorded.

On 2026-11-16, Temari, Ichigo Zero, and Sage Naruto merged with all six
proof/admission flags false. The merge notes say so in one sentence and then
leave the opposite sentence in the same file:

- [evidence/characters/shouju/README.md](../evidence/characters/shouju/README.md)
  opens with “Draft handoff only; no merge or deployment” and later says
  “The user authorized merging these targeted character ports” while “Six flags
  remain false.”
- The same split is in
  [evidence/characters/ichigo/README.md](../evidence/characters/ichigo/README.md)
  (“Targeted draft review only; no merge”) and
  [evidence/characters/minrenx/README.md](../evidence/characters/minrenx/README.md)
  (header still points at Draft PR #296; the merge section records the
  authorization).

[docs/STATUS.md](STATUS.md) copies both policies forward. The 2026-11-15
Kenshin line still ends “无合并或部署” after 22 Flash/native fixtures and
16,964 matched actor states. The 2026-11-14 Killer Bee and Mayuri lines still
say “no merge” after 15,162 and 8,664 matched states. The six names being
checked are not character-SOP criteria. They are defined, always false, in
[tools/probes/helper_observation_profile.py](../tools/probes/helper_observation_profile.py)
`flags()`: `production_admitted`, `native_parity_proven`, `oracle_accepted`,
`certified_global_tick`, `os_input_join_proven`,
`native_initialization_complete`.

[tools/sampling_native.py](../tools/sampling_native.py) `seal()` writes both
sampler flags false, and `validate()` rejects a receipt if either is true.
That is the right fail-closed rule for a capture adapter. It is the wrong
merge rule for a character port that already matched its focused fixtures.

[docs/IMPORTER_KNOWN_GAPS.md](IMPORTER_KNOWN_GAPS.md) already recorded the
2026-10-26 decision that sampler admission, production54, and full AS
ownership are follow-ups, not merge blockers. Character status lines did not
inherit that decision. Each new port re-litigates it, and the next agent
reading the top of STATUS or the character README will refuse again.

Slowdown: a port that has source-first notes, focused Flash/native rows, and
an explicit residual list still waits on a fresh “you may merge this one”
sentence. Kenshin, Mayuri, and any similar residual on master stay described
as unmerged even when the accepted bar for Temari / Ichigo Zero / Sage Naruto
was the same shape of evidence.

Recommended change, wording only:

- In [CHARACTER_PARITY_SOP.md](CHARACTER_PARITY_SOP.md) §7, state two outcomes.
  `targeted_sop_matched` may be merged when the focused fixtures, source
  paths, and residuals are in the character record. `production_admitted`,
  `native_parity_proven`, M2-04, and M6 stay false.
- Stop appending “no merge” to a STATUS line whose only unmet condition is
  those flags. Say “merged as targeted SOP; flags false; residuals: …”, or
  “not merged because &lt;concrete residual&gt;”.
- After a merge, replace the README header. Do not leave “Draft / no merge”
  above a paragraph that records authorization.

Do not set any flag to true as part of that wording change.

### 2. “Do not claim 1:1” is written as “do not land the runtime slice”

Impact: shared hit-chain work and the next character cannot move while step E
is open, which it still is.

[HIT_RECEIVE_SOP.md](HIT_RECEIVE_SOP.md) lines 7–8 forbid editing
`godot/fighter_runtime.gd` and forbid marking M2-04 done when the five
questions, compiled fields, or same-input trajectory are missing. Section 3
then says the previous step must be green before runtime edits. Step E is the
fixed Flash trajectory (Naruto vs Ichigo, seven scripted situations) and is
still pending at line 302 and lines 343–359. Read literally, steps C and D
cannot land while E is red, and E cannot turn green until a capture program
that this repository keeps refusing (finding 3).

The same page already warns against that stall. Section 1.4 says not to
repeat “仍不是一比一” in place of doing the next verification. Section 6’s
completion list is the right bar for the words “这条链已落地”. It is not the
right bar for merging a compiled `gjlN` / `showFace` slice that names what E
still lacks.

[SOURCE_FIRST.md](SOURCE_FIRST.md) lines 27–28 and question 5 do the same
collapse: incomplete answers forbid both the runtime edit and calling the
task done. [CHARACTER_PARITY_SOP.md](CHARACTER_PARITY_SOP.md) §5 is the
clearer rule and is not the rule STATUS follows: without an original-player
trace, report the source-invariant regression and do not call it same-input
acceptance.

[tools/audit_move_acceptance.py](../tools/audit_move_acceptance.py) cannot
say the narrower thing. `audit()` always returns `status: not_accepted` and
appends a standing list (hitbox tangency, KO, focus loss and browser
recovery, form switch) even when the requested rows matched. The acceptance
rule only says that an empty row must not be called parity. A matched focused
set still prints as not accepted, so the tool output and the SOP completion
paragraph look the same.

Slowdown: agents either refuse the runtime edit that steps B–D ask for, or
they do the edit and then refuse to merge it because the completion paragraph
is red. Both burn a cycle that does not add Flash evidence.

Recommended change:

- Split the sentences. “Do not mark M2-04 / do not say 1:1” stays. “Do not
  edit the shared runtime” applies only when step A failed or the edit would
  be a character branch / guessed box. A step B–D slice with source paths and
  the §D table may merge as partial.
- Teach `audit()` to emit `targeted_cases_matched` plus the unmatched
  boundary list, and reserve `not_accepted` for a row that was in scope and
  failed. Do not treat the extra boundary list as a failed assertion.

### 3. Sampling slices re-prove a closed negative and cannot close their own question

Impact: the sampler’s time goes into nested replays and another Computer Use
bind, not into the next character fixture or a live oracle.

From s345 onward, `diagnose.py` imports the previous slice and fails if
`diagnose()` is not byte-identical to the stored `diagnosis.json`. The chain
is recursive: s366 loads s357, s357 loads s350, s350 loads s341, and those
files do the same. Running the newest diagnosis re-executes the whole prefix.
Each slice’s base path exits 0 only by printing
`production_admitted=false native_parity_proven=false`. Every `--require-*`
proof gate exits 1, including gates the slice was not trying to prove.
[evidence/sampling-upgrade/s366/diagnose.py](../evidence/sampling-upgrade/s366/diagnose.py)
is the pattern. [docs/SAMPLING_UPGRADE.md](SAMPLING_UPGRADE.md) repeats it
for every cut: “零机制/产品义务关闭”, “不重排”, runtime unchanged.

[evidence/sampling-upgrade/next-fix-priority-after-s362.md](../evidence/sampling-upgrade/next-fix-priority-after-s362.md)
still ranks the Button2009 Computer Use bind as work item 7 after three
recorded facility failures:

- r01: `Sky Computer Use native pipe startup failed`, including after kernel
  reset, with an empty flashlog
  ([evidence/oracle/native-fight-r01/PROPOSED_PR.md](../evidence/oracle/native-fight-r01/PROPOSED_PR.md),
  [evidence/reference-environment.md](../evidence/reference-environment.md)).
- s342: exact-path selection `timeoutReached`.
- s352: bundle selection returned an explicit two-path ambiguity.
- s361: the same path returned `timeoutReached` after 10.9543s and a binding of
  `undefined` after 3.1263s.

r02 already left that bind. It drives the movie by PID with AX/CG and System
Events and records “No CUA app-string selection.” r24’s adapter still says
“No CUA app-string binding” and then blocks the next live capture on review
and merge of the offline slice
([evidence/oracle/native-fight-r24/README.md](../evidence/oracle/native-fight-r24/README.md),
“no new live should precede review/merge”). The offline slice is not mergeable
under finding 1, because its flags are false by construction. The live run
that could change the evidence cannot start until that merge.

Slowdown: each new sampling number replays history, spends another attempt on
a bind that has not succeeded, and is forbidden to reprioritize toward a
character fixture or the physical-PID path that already reached a fight.
Transport and window-selection failures become “proof gate exit 1” instead of
`facility_blocked`.

Recommended change:

- A disk or disassembly slice exits 0 when its own question is answered, and
  names the unanswered question in a field. It does not import and re-execute
  every ancestor `diagnose()`. Pin the ancestor digest if a byte lock is
  still wanted; do not walk the chain.
- Delete Computer Use app-string selection from the next-rank table until the
  r01 pipe failure is gone. Further UI work uses the r02 PID path or stops
  with `facility_blocked`. A timeout remains “not a dispatch observation”,
  which is already written; it does not schedule the same call again.
- An offline adapter may be reviewed and merged as a tool, flags false,
  without a live receipt. The live run is the next task, not a precondition
  of merging the adapter that the live run needs.

### 4. Page hide, “not frontmost”, and OS focus-loss are one error

Impact: recoverable capture and browser conditions abort the run or enter
online recovery, and the write-up then looks like a gameplay focus bug.

Three different events are collapsed:

| Event | What the code does | What it is not |
|---|---|---|
| OS / canvas focus loss | [godot/render_surface.gd](../godot/render_surface.gd) `focus_exited` releases held keys. It does not pause the match. | Not `document.visibilityState`. The training bug was canvas blur inside a visible page. |
| Tab or isolated browser hidden | [godot/web/shell.html](../godot/web/shell.html) forwards `visibilitychange` only. [godot/authority_match.gd](../godot/authority_match.gd) `_visible()` treats `visibilityState !== 'visible'` as both “send neutral input” and “authority_stall” recovery (`process_tick`). | Not OS focus-loss, and not the player opening the pause menu. |
| Owned Flash window not frontmost | [evidence/oracle/native-fight-r02/capture_menu.py](../evidence/oracle/native-fight-r02/capture_menu.py) `bound_window` raises `Owned movie is not visible and frontmost` when `frontmost_pid` mismatches or the window is offscreen. The test is named `test_rejects_focus_loss_and_offscreen`. | Not proof that the movie lost the user, and not a reason to discard a trace that was otherwise pinned. |

[docs/ARCHITECTURE.md](ARCHITECTURE.md) states the collapsed rule in one
sentence: focus loss pauses the match and clears held keys. The implementation
does not pause on focus loss. The authority path does drop keys and start
recovery on page hide. [docs/CHARACTER_PARITY_SOP.md](CHARACTER_PARITY_SOP.md)
§6 and `audit_move_acceptance.py` then list “失焦恢复” / “focus loss and
browser recovery” as one extra boundary, so a move case stays short of
acceptance until both are tested.

[godot/main.gd](../godot/main.gd) `_diagnostic_watchdog_step` treats
`page_visible == false` as “do not report a stall”. That part is the right
separation. The authority path and the native binder do not share it.

r03 stopped a live capture on focus loss after S. Later merge validation
reran captures under an exclusive foreground lock
([evidence/characters/shouju/README.md](../evidence/characters/shouju/README.md)
merge section). A certificate popup or another agent window fails the same
check as a real lost-focus sticky key.

Slowdown: isolated-browser pauses and “another window is in front” become
hard capture failures and online recovery. The next attempt repeats the bind
instead of recording `not_frontmost` or `page_hidden` and continuing, or
retrying once.

Recommended change:

- Name three results in the capture record: `os_focus_lost` (keys must
  release; match pause only if a source or FR-10 rule says so), `page_hidden`
  (isolated tab / visibility; do not zero local-play keys; do not call it
  focus-loss), `not_frontmost` (retry or skip the input sample; do not fail
  the whole receipt when the PID, title, and hash still match).
- In `authority_match.gd`, page hide may pause the *send* and surface a
  waiting state. It should not be the same branch as `paused` and should not
  be reported as focus-loss. Whether hidden-tab input must go neutral is a
  product choice; write it down separately from the canvas-blur fix.
- Correct the ARCHITECTURE sentence so it matches the code that is supposed
  to remain: key release on focus exit; no claim that the match pauses.

### 5. A later commit is treated as voiding an already reviewed head

Impact: review work is redone, or a frozen good head waits forever, because
the branch tip moved.

[docs/PR48_REVIEW.md](PR48_REVIEW.md) already has the rule that should be
used: judge the product and guard source at the reviewed SHA; later
documentation-only commits do not change that source; deferred audits stay
deferred rather than being relabeled passed. The surrounding practice does
not follow it.

- Sampling READMEs and [docs/STATUS.md](STATUS.md) attach “no merge” to the
  tip, not to a named product SHA. A docs or evidence commit after review
  puts the pull request back in the “unreviewed, do not merge” bucket even
  when the runtime diff is the one that was reviewed.
- [evidence/importer-loud-fail/root-frame-review/README.md](../evidence/importer-loud-fail/root-frame-review/README.md)
  correctly says old 26/26 evidence is not a pass for a tip that made the
  guard stricter. That sentence is then easy to copy onto a tip whose new
  commits are notes. The new failing check and a docs commit are not the
  same event.
- Oracle slices add a second deadlock. r24 will not run live “before
  review/merge”, and the slice will not merge without the live receipt and
  with flags false. There is no frozen head that is allowed to land.

[tools/importer/audit_importer.py](../tools/importer/audit_importer.py)
`audit_exit_code` returns 1 whenever `source_scripts` is non-empty, and
`source_script_inventory()` marks every locked script
`requires_complete_owner_review`. Combined with “do not merge on red”, no
character port can merge on this command’s exit code. PR48 already decided
that this exit stays red and does not block that merge. The character lane
still needed a separate user sentence to get the same treatment.

Slowdown: reviewers re-read merged product diffs because a STATUS paragraph
landed on top, or they refuse a head that was already accepted. Authors add
another evidence round to make the tip “clean” instead of merging the
reviewed range.

Recommended change:

- Record the reviewed product SHA on the PR. Merge that SHA, or merge the
  tip only when the extra commits are docs, evidence, or a listed fix.
  Re-review the extra range, not the frozen range.
- A new failing product check invalidates the old green run. A documentation
  commit does not.
- `audit_importer.py` keeps exit 1 for the complete-ownership mode. Callers
  that mean “ship the targeted port” must not use that exit as the merge
  bit. Add an explicit `--ownership-inventory` mode whose nonzero status is
  labeled inventory, if a separate exit code is needed. Do not make the
  inventory empty.

### 6. Environment failures inside capture are stored as invalid evidence

Impact: a timeout, a foreign focus blip, or a missing live receipt deletes
the diagnostic value of the run and forces a full recapture before anyone
can read what did happen.

[tools/sampling_native.py](../tools/sampling_native.py) `validate_capture`
raises on timeout, a foreign run id, a short trace, or the wrong posture, and
the CLI turns that into exit 1 with no receipt. That is right for admitting
the trace. It is harsh for keeping a classified failure: the partial log is
not a first-class `environment_blocked` artifact, so the next slice cannot
point at it without re-running.

Native-fight analyzers go further. r24’s two CLI modes exit 1 with “no live
receipt” even though the adapter under test is offline by scope. Historical
incomplete HP rows are retained, which is good, and then both modes still
fail closed, which makes “the adapter is ready to try” look like “the
evidence package is invalid.”

[docs/VALIDATION.md](VALIDATION.md) already says a publishable prototype may
exist without being called a finished 1:1 port, and that AT-01–16 are the
release-candidate matrix. Capture scripts and STATUS lines treat any missing
AT row, or any false flag, as a hard stop for the incremental port.

Slowdown: one foreground steal or one timed-out Computer Use call costs a
whole slice, and the slice’s exit code is indistinguishable from a wrong
gameplay result.

Recommended change:

- Exit 2 (or a written `status: environment_blocked`) for timeout, pipe
  failure, certificate popup, and not-frontmost, with the raw log retained.
  Exit 1 stays “this trace contradicts its claimed identity.”
- An offline tool package exits 0 when its unit tests pass and prints
  `live_receipt=absent` as data. It does not exit 1 merely because it was
  not allowed to launch Flash.

## What would actually speed the port

In order, without calling unfinished work finished:

1. Write the merge rule that 2026-11-16 already used. Targeted SOP with
   focused Flash/native rows and a residual list can merge. The six flags
   stay false. Put that in CHARACTER_PARITY_SOP §7 and stop writing “no
   merge” when that is the only gap. Update Kenshin / Mayuri / Killer Bee
   status lines to the same vocabulary so the next agent does not undo the
   exception.
2. Stop the sampling chain from gating character work. No more nested
   `diagnose()` replays, no more Computer Use retries, and no “merge the
   offline adapter before the live run it exists to perform.” Next sampler
   work is either the r02 physical-PID path or a character fixture.
3. Split page-hide, not-frontmost, and OS focus-loss in the capture record
   and in `authority_match.gd`, and fix the one ARCHITECTURE sentence that
   currently describes a pause the focus path does not implement.
4. Merge reviewed product SHAs even if later commits are notes. Re-review
   only the new range. Keep `audit_importer.py` red for ownership, and do
   not use that exit as the character merge bit.
5. Leave step E, M0-02, M2-04, M6, and both sampler flags exactly as open as
   they are. Say “partial” in the status line instead of blocking the merge
   that the partial evidence was gathered to justify.
