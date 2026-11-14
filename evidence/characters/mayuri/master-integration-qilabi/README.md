# Killer Bee master integration

Merged master 117e641f (parent bf4b7a43) into Mayuri 7759d483, preserving both
histories and all three ports. Catalogs, portraits/footer, openings, task history,
source evidence and Mayuri's corrected partial coverage note retain all roles.
Roster expectations now cover 29 fighters. No original trace or fixture changed.

Qilabi's source property creation, placement-local controller calls and facing
assignment parsing coexist with the earlier Karin and Mayuri compiler/runtime
rules. Same-input compilation is unchanged for 28 prior bases. Qilabi's four
JSON artifacts were rebuilt to retain Sprite256 frame 6's `played = 1` after
rename; this is the only semantic artifact delta. Controller code is unchanged.
See qilabi-delta.json for source lifecycle and the retained failed source checks.

All 50 retained original comparisons match 36,100 actor states on 14 fields:
49 positive cases and one source-authored energy rejection. The negative must
not enter its target move; the initial harness assumption and its failure are
retained. Nine Godot checks pass, including all three character rollback checks,
Karin projectile rollback, Mayuri projectile state, shared projectile locals,
protected recovery and player input/visual checks. Forty Python tests pass.

The existing menu font pipeline was actually run with Sarasa UI SC index 199;
the static UI coverage test passed without skip. Online consistency passes for
29 fighters / five helpers / ten stages. Exact results, caveats and measured
smoke durations are in results.json and logs. No Flash/live/FDB or production
deploy occurred. All six flags stay false and coverage stays partial. The new
head needs its own coordinator review and preview; the prior review is not a
pass for this integration. Keep PR #290 Draft.
