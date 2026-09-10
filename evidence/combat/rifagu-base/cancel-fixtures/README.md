# Calibrated cancellation fixtures

These 69 inputs are derived from retained original observations. Each fixture
retains its baseline case ID, event hash, root observation frame, input tick,
source callback path and destination label interval. The input prefix remains
the calibrated path; the follow-up lasts one tick. The original's subsequent
result is measured, never inferred from the expected destination.

The observation phase matters: keys are published at the root observer for
callbacks in the following display. Thus `at_end` names the observed root frame,
not an assertion that a callback still exists on the next display. Source
placements begin callbacks after placement; a root-frame match must not be
reported as full within-display boundary acceptance. The audit reports these
as `root_input_phase_matched` separately from untested callback-phase edges.

The 19 uncalibrated nominal edges remain listed. Several occur after an
unconditional source goto (112 to standing, 131 to falling, 246 to standing,
379 to standing, 883 to standing, 896 to standing). The generator rejects an
unrelated action that merely shares the next numeric frame. It does not force
an unreachable source playhead or treat a missing frame as a passing test.
`uncalibrated-source-evidence.json` retains the exact exit scripts and hashes
for 18 such nominal edges; the pre-knockdown frame still requires runtime
calibration. The last live callback edge is a separate obligation.

The case files describe test input only. Acceptance requires complete fresh
original traces and exact comparison with the current native implementation.
