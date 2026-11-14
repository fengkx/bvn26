# Integrating Karin master into Killer Bee

Merge base update: `bf4b7a43f9cf648b0ad874bd5399a302433da3a5` (Karin #289).
The previously reviewed Killer Bee commit `f3acf16f49f7d2909c1108c80c855d280e3070b9`
is retained as the first parent. No history rewrite, Flash capture, merge to
master, ready-for-review transition or deployment is performed.

Conflicts preserve both fighters in selection, portraits/footer, opening,
service catalog, coverage and task history. Source evidence, original tapes and
native baseline files for both ports remain byte-identical. The online manifest
is regenerated for 28 fighters, 5 helpers and 10 stages. Test inventories now
include both names and the 28-entry count; no assertion is weakened.

The shared projectile parser uses Karin's generic literal initialization, which
also covers Killer Bee's stopped `played = 0` initialization. Killer Bee's X-only
facing warp parser remains. Both runtime changes are retained: source property
creation and Karin's variable-driven projectile name lookup.

Karin's compiler now reads additional DoAction tags in the same frame. Rebuilding
Killer Bee's AI metadata adds exactly the source `_root.shine()` at
`DefineSprite_766/frame_556/DoAction_2.as`, a white screen flash. No other generated
Killer Bee behavior field changes. Existing traces are replayed offline; no
original capture or expected state is regenerated.

The initial 32-test focused run had one failing full-roster cache audit. Using
master's unmodified compiler in a separate temporary directory reproduces the
same prior-27 results against unchanged caches. Ten prior cache entries fail;
these inherited failures remain visible and unmodified. After refreshing the
new frame call, Karin and Killer Bee both pass that audit. The other 26 focused
tests pass. The editor import has only the sandbox editor-settings write warning;
no script error. Final replay and verification results are in checks.json.

Historical port receipts remain evidence for their recorded heads. They do not
claim same-head Web/preview validation for this integration. That preview and
review are left to the coordinator. Coverage remains partial; all six admission
and proof flags remain false. Weekly remaining allowance was 26% at entry and
24% at the latest pre-finalization check, above the required 20% floor.
