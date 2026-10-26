# Placement and wrapper audit (r12)

Fresh exports of all62 locked SWFs still produce34 unsupported placement errors:
blend7 (1), blend13 (32), and DropShadow (1). No renderer support, allowlist or
pixel tolerance was added. The scanner now recognizes every `PlaceObject*` tag
as a placement: unsupported legacy/future revisions fail with the source/frame
and depth instead of disappearing from extraction or inventory. Existing source
placement records, field obligations and clip-action ranges match r11 unchanged.

A separate real silent drop was found in wrapper extraction. Child filters are
supported, but `TimelinePreview` only consumes a wrapper's matrix and blend group.
The importer previously discarded wrapper filters without an error:

- **Yulong body345, root frame1 depth1**: BlurFilter0×0, passes1. Zero blur is not
  assumed harmless: a filter can change the cached raster boundary. This is a
  shipped wrapper and now fails its cache validation.
- **Minren body1821, root frame3 depth1**: red GlowFilter7×10, passes3,
  strength1.1367188. This is the follow-on transformation target. It now fails
  extraction rather than dropping its filter.

`wrapper-fields.json` includes exact source SHA, original placement XML and
extraction errors for these two sites. Wrapper filter, color-transform,
cache-as-bitmap and clip-depth fields require a consumer and currently fail.
Source obligations are keyed by source hash and character ID, so removing the
cached `wrapper` object cannot bypass the check. The full scan pins138 initial
root-placement field records;57 contain fields unsupported **when extracting that
character as an independent wrapper**. These are not57 new shipped bugs: root
helper timelines consume their child placements normally, and many characters
are not selected as wrapper slices. The inventory retains them for future slice
validation instead of declaring them harmless.

A DefineSprite wrapper's `ratio` is preserved as metadata. It is not a morph
shape; the existing source audit still rejects actual DefineMorphShape ratio
interpolation. The regression distinguishes those cases. No global ratio rejection
or character-specific exception is used.

Focused tests: **39/39** (`tests.log`). Cached shipped placement acceptance:
**88/89**, with Yulong the only new failure (`closures.json`, `closures.log`).
Overall source/import acceptance remains failed. Neither wrapper filter rendering
nor new native Flash/Godot pixel parity is claimed in this track.

Reproduce:

```sh
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/audit.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/closures.json"
python3 -m unittest tools.tests.test_placement_tag_guards tools.tests.test_clip_action_fields tools.tests.test_import_guards tools.tests.test_timeline_geometry
```

The compact locked-source inventory omits repeated full-frame obligations and
unrelated AS inventories; complete reviewed obligations are in
`tools/importer/placement_requirements.json`. Source-first scope is extraction
and rejection of missing consumers. Production gameplay/rendering is unchanged.
