# Importer loud-fail (Draft PR #48)

The PR is not merge-ready. Current progress and evidence are in
[r06](r06/README.md); probe reproduction is documented in
[the fixture instructions](../../tools/probes/flash_filters/README.md).

Implemented: placement/finite-number/selected call guards, source-pinned nested
control requirements, cached-timeline validation, locked-SWF scanner, initial
Blur/Glow/ColorMatrix/cacheAsBitmap rendering, and strict native blur regressions.
The small-object BlurFilter mismatch is now fixed: 242 cases / 37,280 alpha samples
match native Flash exactly. Cached raster, outer Glow and post-filter RGB CXFORM now have exact native
regressions. Two canonical color groups and two order groups still differ by
one level; real components match 9/54 images and 4,242/4,242 clocks.

The latest scan lists 34 rejected placements across all 62 locked SWFs, including
unsupported blend IDs 7/13 and a DropShadowFilter. See r06/locked-swf-audit.json
for every source and frame. Shipped filter sites are in shipped-filters.json.
The only harmless allowlist entry is still Byakuya sprite 631 frame 985 in base
form: exact source/SWF hashes and form scope pin the transformation-disabled
case. Juggo child controls and main KO controls have separate source-pinned
records delegating to existing native consumers. No new exception was added.

Source-verified shunbuxg/colored shine and conditional stop/play compilation now
feed build-time cached frame-call obligations. r05 refreshed 21 valid caches and
imported XG_rush. r06 implements retained, same-label numeric goto and refreshes
Rukia: **22/26 caches pass**. Its original 141→130 loop matches 31/31 native
playhead samples. Four parent/form goto errors continue to block build/fingerprint.
Expression, missing-target and cross-label numeric jumps remain hard errors.

Remaining blockers include color/filter-order and real component parity,
parent/form switching, XG_rush pixels, complete AS/clip-action ownership, deferred
context-field differences and complete shipped import acceptance. The original
game/ and scripts/ inputs remain unchanged. No new intentional stability deviation
was introduced; new character ports remain paused. See r06 for current acceptance.
