# Selected forms live audit — 2026-11-17

## Repairs

- Naruto One Tail upper-special solid paint now follows the original curved edges and round stroke. Production Web reproduced the red rectangle; repaired native and Web builds display the circular effect. See [source and render evidence](red-block/README.md).
- Recompile numbered frame actions in selected forms, including Hitsugaya Bankai's ultimate face/pause call, Ichigo Bankai's screen flash, and Naruto One Tail's authored vertical resets.
- Preserve undefined operands in Hitsugaya Bankai's partial ultimate hit packet. Its natural-intro checkpoint restores and replays identically.

## Validation

The matrix contains 97 unchanged 360-tick input fixtures for Hitsugaya Bankai,
Rukia release, Ichigo Bankai, Naruto One Tail and Sasuke Curse Mark. Scenarios
cover attacks, guarding, receiving guard breaks, mirrored attacks, simultaneous
attacks and insufficient-energy input. Contact coverage is recorded separately;
a move's name alone does not establish that it hit.

`matrix.tar.gz` retains fixtures, original logs, probe metadata, random/clock
tapes, native output and per-case comparisons. `matrix-sha256.json` records the
archive input hashes. Comparisons use all 14 actor fields and root positions
without tolerances. The original failed capture/comparison is retained when a
repeat is made.

The native matrix completes all 97 fixtures without script errors. All 97
scenarios match the source actor states and root positions, including the
unchanged-input repeat below. Ten original/native guard pose samples are captured and reviewed; see
[guard visual observations](guard-visual/README.md) for remaining presentation
differences.

The first Sasuke air-attack capture ran long enough to reach the real-time
60-second round timeout. Its 36 differing actor rows (only `sw`, ticks 343–360)
remain in the matrix archive. The fixed-frame native runner does not deliver
that external countdown. Repeating unchanged input with the browser test closed
matches all 722 actor states and 361 root positions; see
`sasuke-airhit-repeat/comparison.json`. No runtime change or comparison filter
was used for this repeat.

Additional checks: 24 source/package tests; shared PvP/training each match 602
actor states; 126 hit-state transfers and 10 gates; selected-form flow, player
controller/visual and form graph references; Web export and asset fingerprints.

## Remaining audit items

The existing long-match r15 round-reset mismatch reproduces identically with the
pre-change runtime; see `long-match-regression.json`. Full audiovisual acceptance
continues separately from these measured repairs.
