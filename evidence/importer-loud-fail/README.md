# Importer loud-fail (Draft PR #48)

The PR is not merge-ready. Current progress and evidence are in
[r02](r02/README.md); probe reproduction is documented in
[the fixture instructions](../../tools/probes/flash_filters/README.md).

Implemented: placement/finite-number/selected call guards, source-pinned nested
control requirements, cached-timeline validation, locked-SWF scanner, initial
Blur/Glow/ColorMatrix/cacheAsBitmap rendering, and strict native blur regressions.
The small-object BlurFilter mismatch is now fixed: 242 cases / 37,280 alpha samples
match native Flash exactly. Glow/ColorMatrix still differ by 1–3 color levels.

The latest scan lists 34 rejected placements across all 62 locked SWFs, including
unsupported blend IDs 7/13 and a DropShadowFilter. See r02/locked-swf-audit.json
for every source and frame. Shipped filter sites are in shipped-filters.json.
The only harmless allowlist entry is still Byakuya sprite 631 frame 985 in base
form: exact source/SWF hashes and form scope pin the transformation-disabled
case. Juggo child controls and main KO controls have separate source-pinned
records delegating to existing native consumers. No new exception was added.

Remaining blockers include color/filter-order and real component parity, numeric
gotoAndPlay(130), shunbuxg, complete AS/clip-action ownership, nine existing
context-output differences and final whole-roster acceptance. The former
227/227 / 130,334-state replay predates the renderer work and is not final evidence.
The original game/ and scripts/ inputs remain unchanged. No new intentional
stability deviation was introduced; new character ports remain paused.
