# Placement and clip metadata checkpoint (r11)

The fresh scan re-exported all **62 locked SWFs** with JPEXS 26.2.1. The
34 unsupported placements remain hard errors: difference blend 7 (1), overlay
blend 13 (32), and DropShadowFilter (1). None is treated as harmless. The compact
`locked-swf-inventory.json` preserves every source SHA, source/frame/depth and
rejected XML placement. The checked-in placement requirements now contain these
same exact diagnostic records. Existing filter/transform obligations were compared
against the prior catalog and are unchanged.

The scan additionally pins **2,407 clip-action lifetime ranges**. The build guard
checks event names and ActionScript byte hashes on every retained source frame,
including inherited MOVE frames and nested clips. New placements and removals end
the previous obligation. It rejects a cache that removes or changes an action on
a later frame, even when the placement-entry metadata remains intact. This closes
a cache-validation hole; it does **not** prove that every event body has a complete
runtime consumer. That separate AS/clip-action ownership audit remains open.

The extractor rejects malformed or unknown clip-action metadata, missing flags,
reserved bits, invalid action byte encoding, inconsistent aggregate event flags,
and KeyPress/keyCode metadata that its output cannot represent. Known event names
remain source evidence for the body/controller compiler. A numeric1 no longer
passes a source booleantrue cache obligation through Python's `True == 1` rule.
No runtime, shader, locked source, allowlist or tolerance changes were made here.

`tests.log` records **34/34** focused Python tests, including new mutation guards
and source range/reset behavior. `closures.json` and `closures.log` record the
**89/89** shipped cached timeline result; a nonzero audit exit remains mandatory
while any of the34 source issues remain unresolved.

Reproduce from the repository root:

```sh
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/audit.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/closures.json"
python3 -m unittest tools.tests.test_clip_action_fields tools.tests.test_import_guards tools.tests.test_timeline_geometry
```

The compact inventory excludes repeated full-frame obligations and unrelated AS
inventories. The complete placement/clip obligations are the reviewed source-hash
catalog at `tools/importer/placement_requirements.json`; raw temporary exports are
not committed. Source-first scope is serialization/audit only: no new gameplay
mechanism or claim of native rendering parity is introduced.
