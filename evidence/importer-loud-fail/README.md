# Importer loud-fail (Draft PR #48)

The PR is not merge-ready. Current progress and evidence are in
[r14](r14/README.md); probe reproduction is documented in
[the fixture instructions](../../tools/probes/flash_filters/README.md).

Implemented: placement/finite-number/selected call guards, source-pinned nested
control requirements, cached-timeline validation, locked-SWF scanner, initial
Blur/Glow/ColorMatrix/cacheAsBitmap rendering, and strict native blur regressions.
The small-object BlurFilter mismatch is now fixed: 242 cases / 37,280 alpha samples
match native Flash exactly. Cached raster, outer Glow and post-filter RGB CXFORM now have exact native
regressions. Two canonical color groups and two order groups still differ by
one level; real components match 9/54 images and 4,242/4,242 clocks.

The latest scan lists 34 rejected placements across all 62 locked SWFs, including
unsupported blend IDs 7/13 and a DropShadowFilter. See r13/locked-swfs.json
for every source and frame. Shipped filter sites are in shipped-filters.json.
The only harmless allowlist entry is still Byakuya sprite 631 frame 985 in base
form: exact source/SWF hashes and form scope pin the historical transformation-disabled
case. The r13 graph compiles its real conditional even with that exception disabled. Juggo child controls and main KO controls have separate source-pinned
records delegating to existing native consumers. No new exception was added.

Source-verified shunbuxg/colored shine and conditional stop/play compilation now
feed build-time cached frame-call obligations. r05 refreshed 21 valid caches and
imported XG_rush. r06 implements retained, same-label numeric goto and refreshes
Rukia: **22/26 caches pass**. Its original 141→130 loop matches 31/31 native
playhead samples. The stricter r09 audit later exposed three additional wankai paths. r12 wires Daitu; r13 adds Sasuke, Byakuya, rifagu and rukia. r14 adds the complete Minren graph, including authored initial filter clearing. Current cache acceptance is **25/26**; Yihu still blocks build/fingerprint.
Expression, missing-target and cross-label numeric jumps remain hard errors.

Remaining blockers include color/filter-order and real component parity,
parent/form switching, XG_rush pixels, complete AS/clip-action ownership, deferred
context-field differences and complete shipped import acceptance. The original
game/ and scripts/ inputs remain unchanged. No new intentional stability deviation
was introduced; new character ports remain paused. See r13 for current acceptance and the existing online simulation-clock deviation.

The r07 parent-replacement probes record native field reset and observable old
MovieClip-reference equality for all four sources. Target compilation exposes
additional parent-scoped 万解 condition blocks at minren 1293/996 and Sasuke
1019/1024. Strict load-dependency records and precise errors are implemented;
the runtime consumers are not. Cache acceptance remains 22/26, build remains red.

The r08 parent-flag owner now executes the reviewed conditional super-end/body-write
blocks, matching 2/2 native source cases and 6/6 observations, with rollback coverage.
Target contexts improve to 3/4; minren's frame timers and subsequent parent-frame-3
replacement remain errors. Full replacement consumers are still missing: 22/26
caches and failing build/fingerprint. See r08 for the precise scope and diagnostics.

The r09 audit rejects previously dropped wankai calls and wrapper transfer writes.
Seven source contexts are now correctly blocked (19/26 cache acceptance). Native
probes establish live old-reference reads/writes and retirement of an installed
old callback; full body replacement is still unimplemented. See r09 for exact
source sites, the newly exposed three fighters, and acceptance failures.

The r10 compiled initial feixue callback resolves current body state and methods;
48/48 native callback observations match across four sources. Repeating timers
retain captured functions and support strict rollback. This is a component, not
full form replacement: seven caches remain blocked, root interval ownership and
target profiles remain unfinished. See r10 for exact scope and acceptance.
