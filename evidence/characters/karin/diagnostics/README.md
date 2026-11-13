# Retained pre-fix diagnostics

`initial-capture/` preserves the first original attempt and the following
interrupted attempt. The air-ranged capture timed out after the original
runner's 120-second wall-clock limit, at fight tick 116, with `done=false`.
It is not an accepted reference. The batch scheduler was stopped while its
own capture runner cleaned up its own player; the external lock was released
only after that cleanup. No other session's player was controlled.

Subsequent attempts allow 600 wall-clock seconds through the existing
capture runner's `--timeout` option. The required 360 logical ticks, complete
done marker, actor fields and exact comparison remain unchanged.

The initial fixtures incorrectly used lists of individual target frames;
the harness expects a two-element source interval. Those diagnostic build
records are retained, and final fixture target metadata uses the source
action span. This metadata does not inject input. The initial cancel input
also targeted a window without a super cancel; the final dash-to-super input
is instead based on Sprite 427's frame-26 callback. Its actual trigger must
still be observed, not inferred from the fixture name.

`before-runtime.json` binds the unmodified runtime and initial Karin context
used by the first Godot batch. Neither the missing healing frame writes nor
the second DoAction follow calls have been inserted into that baseline.

The first completed 900-HP capture (`health900-source-r02`) took 180.769
seconds after ready. With the unchanged 60-second match setting, both
actors changed `sw` at tick 184 and entered the round-ending path. The
move harness does not record countdown callback phases, so this trace is
retained as a timing diagnostic, not accepted fighter parity. No timer
setting, input, duration or comparison threshold was changed. Repeating
the same fixture with this session's heavy Godot jobs stopped took 53.502
seconds and matched all 722 actor states on all 14 fields.

The ranged baseline reports undeclared projectile locals and first diverges
at tick 16. Compiler repair preserves frame-1 declarations, the guarded
string-local assignment, frame-5 variable rename and frame-8 random rename.
The initial compiled metadata incorrectly recognized `atm_name = ...` as
`_name = ...` and omitted the declaration block. The first expanded source
test run records 12 failures against stale Karin packages; recompiling those
packages makes all 12 tests pass. Prior packages are not rewritten.

The initial projectile rollback check sampled root frame 448 before the
child-local initialization had become observable and failed its assertion.
The next diagnostic replay passed state restoration, but its old print
marker claimed two crossings without asserting them; the native positions
showed no crossing. Neither attempt is accepted mirror coverage. The final
check reads the retained final fixture, waits for live local state, and
asserts the three cast facings `[1, -1, 1]`; only the `-final.log` and final
`godot-checks.json` entry establish this scope.

Files named `native.json.gz` inside `*-source-*` diagnostic directories are
the capture-only harness's decoded Flash rows, not Godot output. Final
comparisons use explicit `.original.jsonl.gz` and `.native.json.gz` paths
and decompressed hashes in `comparisons.json`.

The pinned editor successfully imported the six new selection PNGs. It could
not save the account-wide editor preferences inside the sandbox; that is
retained in the import log. A fresh desktop capture subsequently loaded the
portraits/footer without ResourceLoader or SCRIPT ERROR failures. Desktop
exit resource/RID cleanup messages are retained and are not pixel parity.
