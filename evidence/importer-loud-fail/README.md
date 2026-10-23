# Importer loud-fail (Draft PR #48)

The PR is not merge-ready. Current progress and evidence are in
[r05](r05/README.md); probe reproduction is documented in
[the fixture instructions](../../tools/probes/flash_filters/README.md).

Implemented: placement/finite-number/selected call guards, source-pinned nested
control requirements, cached-timeline validation, locked-SWF scanner, initial
Blur/Glow/ColorMatrix/cacheAsBitmap rendering, and strict native blur regressions.
The small-object BlurFilter mismatch is now fixed: 242 cases / 37,280 alpha samples
match native Flash exactly. Cached raster, outer Glow and post-filter RGB CXFORM now have exact native
regressions. Two canonical color groups and two order groups still differ by
one level; real components match 9/54 images and 4,242/4,242 clocks.

The latest scan lists 34 rejected placements across all 62 locked SWFs, including
unsupported blend IDs 7/13 and a DropShadowFilter. See r04/locked-swf-audit.json
for every source and frame. Shipped filter sites are in shipped-filters.json.
The only harmless allowlist entry is still Byakuya sprite 631 frame 985 in base
form: exact source/SWF hashes and form scope pin the transformation-disabled
case. Juggo child controls and main KO controls have separate source-pinned
records delegating to existing native consumers. No new exception was added.

Source-verified shunbuxg/colored shine and conditional stop/play compilation now
feed build-time cached frame-call obligations. r05 refreshes 21 valid caches and
imports XG_rush: **21/26 caches pass**, up from 0/26. Its 21 entered source frames
match native, but pixels still differ. Five numeric/parent goto errors continue
to block fingerprint/build acceptance. Only audited frame_calls and the source
XG_rush assets were refreshed; other context fields remain under review.

Remaining blockers include color/filter-order and real component parity, numeric
gotoAndPlay(130), parent/form switching, XG_rush pixels, complete AS/clip-action
ownership, deferred context-field differences and complete shipped import acceptance. The latest
whole-roster replay after renderer changes passes 227/227 / 130,334 states.
The original game/ and scripts/ inputs remain unchanged. No new intentional
stability deviation was introduced; new character ports remain paused.
