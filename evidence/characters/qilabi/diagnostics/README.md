# Retained failed and superseded checks

The first full Python run executed 1,532 tests (24 failures, 5 errors, 2 skips).
Nine failure records belong to new roster expectations or the projectile parser
loaded before its fix. All 27 targeted tests pass after the source fix and
explicit roster additions; see `../logs/source-final3.log.gz`.
The remaining 15 failures pin historical renderer hashes; five errors concern
two old diagnosis resource pins and three shadow-catalog tests. Their affected
files are byte-identical to base 147155cb; `inherited-failures.json` records the
hash comparison. Historical proof hashes and expected results were not changed.

`superseded-inputs/` retains early down inputs too short to dispatch and a cancel
after its source window, plus an earlier repeat. They are diagnostics, not extra
coverage. `upper-before.json` records the upper-U divergence at tick 16 before
compiling the source frame-one stop/played declaration and allowing its authored
movspeed assignment. Final source/native traces are separately retained.
The first extended rollback test tried to restore a checkpoint already pruned
by confirmation; it was corrected to use an independent retained checkpoint.
No runtime workaround was made for that test error.
