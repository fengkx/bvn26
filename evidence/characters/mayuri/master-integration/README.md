# Karin / Mayuri master integration

Merged master `bf4b7a43` into Mayuri `906b949f`, preserving both histories.
Catalogs, portraits/footer, natural openings, frame-call requirements, task
history and evidence retain both roles. Mayuri coverage wording is unchanged.

The compiler retains Karin's general literal declarations and variable-name
rename, plus Mayuri's source flash, named hit jump and rename-local writes.
The runtime retains both variable-name lookup and local writes. These source
patterns do not overlap in the shipped models. All 28 base fighter combat,
player-controller and CPU-controller outputs equal their corresponding parent
compiler results on identical inputs; no fighter artifacts were regenerated.
Roster tests now expect both roles and 28 portraits.

All 29 retained original-player cases match 20,938 actor states on 14 fields.
Both character rollback checks, Karin projectile rollback, Mayuri projectile
invariants, protected recovery, shared projectile locals and player input/visual
checks pass (eight Godot checks). The 33-test source/registry suite and static
UI font gate pass. Online fingerprints cover 28 fighters, five helpers and ten
stages. See results.json and logs for exact results and measured durations.

No Flash/live/FDB launch, fresh original capture, admission, merge to master or
deployment occurred. Full audiovisual/browser/AI and exhaustive boundary scope
remains partial. The existing Draft PR is left for coordinator review.
