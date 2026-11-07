# s352 — AFTER-s344 rank #8: Button2009 UI

Base: `26cbf097` (s351 #229 squash). Branch: `feat/s352-button2009-ui`.
Authority: [unchanged AFTER-s344 rank #8](../next-fix-priority-after-s344.md).
Ranks 1–7 delivered; rank 9 planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero mechanism/product obligations closed. Evidence-only delivery.

## Independent attempt and result

This cut uses **System Events process/window queries**, independently of s342's
exact-path CUA selection. The retained scripts are repo-relative. Raw stdout,
stderr, exit codes and measured subprocess costs are retained separately:

1. [Name query](window-query.applescript) under the sandbox exits 1 with `-10827`.
   This is an execution error, not a permission-denial diagnosis or dispatch event.
2. The same read-only query outside the sandbox exits 0, `matching_processes=0`.
   This matches the literal name `Flash Player`, not all possible player names.
3. One `open -a` request launches the receipt-hash-matching app with locked
   `game/main.swf`; exit 0 means launch-request acceptance only. The app path is
   derived from [s343's binary receipt](../s343/lookup-candidates.json).
   No instrumented movie was launched and no candidate was compiled.
4. The post-launch name query still reports zero. Reading the app's Info.plist
   identifies `Flash Player Debugger` and its bundle ID. The independent
   [bundle query](bundle-window-query.applescript) exits 0 and returns **two rows
   with the same PID 50810**, both `frontmost=false`, and **no window rows**.
   These are not two independently identified processes. Absence from this query
   does not establish that no native window exists or that no input was dispatched.
5. CUA inventory independently reports two running entries for the same bundle ID.
   CUA selection by that observed ID returns an explicit ambiguity between the
   installed receipt path and `/Volumes/Flash Player/Flash Player.app`.
   The mounted copy was not selected or hash-qualified. No permission prompt was
   observed. [CUA receipt](cua-attempts.json) retains the relevant output; unrelated
   application inventory is omitted. No exact-path CUA retry was made.

**Actual target-window/input control remains unproved.** No keyboard/mouse input
was sent. No original-menu Enter/release, no-input/frame1 controls, handler
entry/return, listener order, live placement lifetime or observer perturbation
was observed. No native behavior capture was produced. The movie's actual
execution and activation remain unknown; no process was killed because this
route did not establish exclusive ownership of it. The new process/window-query
results and bundle ambiguity are facility observations, not native behavior proof.
There is no timeout in the new route and no silence-as-nondispatch inference.

Compilation and full original opcode/control-flow preservation remain deferred
behind actual window/input control, as required by the rank's ordering. Compiler
unavailability is not claimed. Existing six candidate patch hashes and historical
s263 combat events are only revalidated by complete locked s342 replay; neither
is new progress. No forced frame, AS call as input, assumed listener order,
combat tape change, runtime edit or widened validator/threshold is introduced.

## Reproduction and gates

Portable re-check (Python standard library; no macOS/UI dependency):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s352/diagnose.py --output /tmp/s352.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s352 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

The base diagnosis exits **0**, with both admission flags false. Each of
`--require-native-ui`, `--require-opcode-qualification`, `--require-thin-coverage`
and `--require-full-as` exits **1**; the combined proof gate also exits 1.
[Gate receipts](gates.json) and [project checks](project-checks.json) record exact
commands, expected/actual exits and durations. The unit tests reject invented
window/input/dispatch claims and compare the entire retained s342 diagnosis.
The retained Button2009, sampling and import-guard tests are run unchanged.

For a fresh macOS facility observation, run `osascript` with either checked-in
`.applescript` path and record its new output separately. The name and bundle
queries intentionally remain separate so zero name matches cannot hide the
bundle rows. The [host receipt](host-tools.json) pins the system interpreter,
player executable and Info.plist; paths from the player receipt are host hints,
not portable dependencies of the diagnosis. New host observations require new
analysis; a future window/control success must not simply flip this report's
false flags. Do not run UI inputs against an unbound target.

[Input pins](input-sha256.json) cover raw route receipts, authority and complete
s342 files; s342 recursively validates the retained Button tooling.
[Artifact pins](artifact-sha256.json) cover all top-level s352 files except that
index. [Scope audit](scope-audit.json) records zero prior/protected diffs;
[manifest audit](manifest-audit.json) records only reviewed tracking hashes.
[Timing](session-timing.json) records measured work/check costs, not person-days.

## Source-first boundary and next discriminator

1. Locked s276 preparation, retained through s342, identifies Sprite2010 stops at
   frames 1/10; no new per-frame behavior is inferred.
2. Root56 places menu depth157; menu10 newly places Button2009 depth5. This static
   placement is not a measured continuous native lifetime.
3. Both original handlers explicitly `gotoAndStop(1)`; no forced frames are used.
4. Tests protect evidence boundaries and source patch reproduction, not assumed
   observer neutrality, listener ordering or implementation behavior.
5. Same-input original-menu execution is still absent. No runtime change or
   mechanism completion follows.

Next disambiguate the receipt-pinned running player and bind an actual visible
window and input target; process rows/launch success are insufficient. Then
compile isolated candidates outside the source tree, qualify complete opcode
projection, observer-off/on and live placement/timeline bracketing before
original-menu Enter/release and observed no-dispatch controls. Delivery of this
slice does not close that proof gap. No merge, ready-for-review or deployment.

Validation: **115 tests pass**; verify.py, check_handoff.py and diff whitespace
checks exit 0. Base diagnosis exits 0; four individual proof gates and their
combined gate exit 1. These successful audit checks do not prove native behavior.
