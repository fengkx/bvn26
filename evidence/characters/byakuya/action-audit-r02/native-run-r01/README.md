# Byakuya Base Attack/Guard — Source/Native Paired Evidence

This is a focused hit/guard sample for the currently open Byakuya base form. It is not full move-set parity. No production combat code, shared geometry code, or shared test runner was changed for this run. The raw Flash and native traces remain next to the summaries.

## Same-input setup

All cases use P1 Byakuya / P2 Ichigo, helpers Soul/Soul, stage 现世, both fighters initially at 1000 HP and 300 energy, and both on the same Y plane.

- Down+U mirror: P1 starts at x=350, P2 at x=300. P1 holds down+ranged on ticks 10–12; P2 holds down from tick 1 through 299.
- Down+I mirror: same reversed positions and P2 guard tape; P1 holds down+special on ticks 10–12.
- Ordinary J: P1 x=300 attacks on ticks 10–12; P2 x=350 holds down from tick 1 through 299.

Source and native fixture JSONs are byte-semantically equal after removing only the native `geometry_probe` field. Fixture SHA-256 bindings are in `../prepared-cases.json` and this directory's `archive-manifest.json`.

## Paired results

- **Down+U (`zh2atm`):** source observed the actual P2 `bdmn` hit test at `display_tick=466`, `fight_tick=24`, Byakuya parent frame 388. `hitTest=true`; source attack game AABB was `[153.8, -117.1, 350.65, -17.1]`, receiver body AABB `[297.75, -78.3, 328.3, -26]`. Source packet was `zl=15`, `pw=100`, `htype=击飞`, branch `break`. Current native reached the same attack frame and contact with matching bounds to the accepted one-twip precision; P2 ended at 900 HP with one hit.
- **Down+I (`cbsatm`):** source observed actual P2 `bdmn` contact at `display_tick=490`, `fight_tick=45`, parent frame 736. Its rotated matrix had `b=-3.5914154`, `c=10.374527`; source game AABB was `[193.2, -221.8, 613.4, 15.05]`, receiver body AABB `[297.75, -78.3, 328.35, -26]`. Source packet was `zl=15`, `pw=450`, `htype=击飞`, branch `break`. Current native reached the same frame/contact; the AABB differs by one accepted twip at the left edge. P2 ended at 550 HP with one hit.
- **Ordinary J (`k1atm`):** current native produced a real contact at source frame 173 while P2 held down. The guard settlement was `防住`, HP 1000→997, hits 0. This is a current-runtime native result; this run did not take a new same-fixture source contact capture for J.

The two mirrored cases show the same hit and break outcomes on original and native, with no observed gameplay-result difference. The original contact records and native event use different tick labels (source `fight_tick` versus native runner/global tick); no timing cause is inferred from that label difference. The prior normal-orientation cbs evidence remains separately archived at `validation/hit-receive-r02-source/` and `action-audit-r01/`.

Original evidence details and hashes:

- `../source-run-r01-zh2/summary.json`: source hit seq 3528 / guard seq 3529; `hitTest=true`, `zl=15`, `break`. Captured run reached `done`; capture output was recovered read-only from the shared Flash log because the initial destination directory had not been created. The recovery procedure and raw hash are recorded in that source directory.
- `../source-run-r01-cbs/summary.json`: source hit seq 3679 / guard seq 3680; `hitTest=true`, `zl=15`, `break`; the normal capture tool wrote the run output.
- `archive-manifest.json`: per-file hashes and current-runtime provenance for all three native runs and fixture bindings.

The measured ~0.05 px (one-twip) differences are preserved in raw records and accepted for this comparison; no gameplay threshold or tolerance was changed.
