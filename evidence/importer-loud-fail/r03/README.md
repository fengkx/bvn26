# Filter color/order and importer guards, r03 (2026-10-23)

Draft PR #48 is still blocked. This checkpoint fixes observed cached raster,
opacity, outer glow composition and post-filter RGB CXFORM behavior. It does
not claim complete filter parity or complete AS semantic ownership.

## Native evidence and source-first answers

1. The checked-in isolated programs in tools/probes/flash_filters execute a
   stopped first frame, create fresh shapes, assign filters/CXFORM/cacheAsBitmap,
   draw to BitmapData, and emit samples. No enterFrame schedule is inferred.
2. Each sample uses a fresh object, removed after capture. The real-component
   harness copies the locked source's raw placement tag and dependencies; the
   21 source/sprite/frame/depth sites and hashes are in inventory.json. Root
   sprite 0 is explicitly supported for Jinye's frame-41 cache placement.
3. Isolated probes stay stopped and quit after done. Component clips retain
   source controls and are observed for 100 ticks; source frame counts and
   selected image ticks are recorded in each component cases.json. Full attacks
   and full-game visual parity are outside this component evidence.
4. Cached input quantization is checked against 36 native source color/alpha
   combinations. The 5 color groups and 4 RGB-CXFORM order groups use independently
   captured native rows. No tolerance or gameplay baseline was changed.
5. Adobe Flash Player Debugger 32.0.0.465/Rosetta and JPEXS 26.2.1 match the
   executable hashes in evidence/reference-environment.md. Each probe directory
   preserves raw trace, build hash and capture metadata. Godot 4.7.2 Compatibility
   generated the measured rows under godot/.

Flash getPixel32 returns straight ARGB; converting that back to premultiplied
RGBA loses low bits. r03 additionally draws the native result over opaque black
and reads RGB directly, retaining alpha from the transparent capture. The
comparator now rejects missing black-background samples. Earlier r01/r02 logs
and failing reports remain unchanged; this is a corrected measurement, not a
relaxed comparison.

The cached input uses integer `(channel * (alpha + 1)) >> 8`. Object opacity
truncates the filtered premultiplied RGBA. Outer glow composites with integer
source-over. RGB display-object CXFORM applies after filtering. The latter
fixes a conspicuous XG_mfdjx error: its source RGB multiplier is zero with blue
RGB offsets, but applying it before ColorMatrix produced orange. The generic
renderer now preserves the source order, with no character-specific branch or
new intentional stability deviation. Alpha-add and other unexercised combinations
are not certified by these tests.

## Strict comparisons

- Blur: all 242 cases / 37,280 alpha samples still exact.
- Cached raster: 36/36 cases, 144 channels exact (new regression).
- Canonical colors: 3/5 groups exact. Glow 100% and 50% now have strict GPU
  regression assertions (1,280 channels). Matrix 100% has 64 differing channels;
  Glow→Matrix has 128; both maximum error 1. Matrix 50% is exact. The overall
  colors-comparison.json deliberately fails.
- RGB-CXFORM order: Matrix 100% and 50% exact, with strict assertions on 1,280
  channels. Both Glow order cases retain one differing channel at maximum error
  1; order-comparison.json deliberately fails. No tolerance hides these edges.
- Real shipped components: all 21 placements captured across jiraiya, lanran,
  orochimaru, yijiao, yulong, main/XG_mfdjx and Jinye. All 4,242 observed clock
  samples match. Only 9/54 sampled images are pixel-exact; 45 still differ.
  strict-comparison.json deliberately fails. Maximum main-group mean absolute
  error fell from 3.30073194 to 0.23699583 after the order fix. Edge/vector/raster
  differences remain and have not all been attributed to a filter operation.
  components-before-order.json and main-before-order.png retain the prior result.
  Raw native traces and Godot clocks are gzip archives under components/;
  image comparisons and original captured PNGs are retained there as well.

The regression script's successful exit certifies only its explicitly asserted
subsets. Run both strict comparators to check the entire color matrix. A green
render script alone is not full filter acceptance.

## Final checks for this checkpoint

- Whole shipped roster: 227/227 cases, 130,334 states match the unchanged native
  traces after the final renderer changes (roster-report.json, roster.log).
- Python: 378 run, 376 passed, 2 skipped, 0 failures (python-tests.log).
- GPU: 7/7 scripts pass their asserted subsets; blend remains 38/38. See
  godot/results.json and individual logs. Full color comparisons remain red above.
- Headless Godot: player_controller, player_visual, retained_effect_clocks and
  clip_placement_once all pass, 4/4 (godot/smoke-results.json). An initial run
  lacked a writable default user-log path; rerunning with explicit log files
  removed that environmental error. No test expectation was changed.
- Protected function: PROTECTED_FUNCTION_OK, original 1,086 bytes/SHA-256.
- Integrity, handoff, contracts and runtime fingerprint: corresponding logs in
  this directory record checks after reviewed manifest hash updates.

The roster run used the existing scratch runner; tools/test_importer_roster.py
now packages that same pinned-index/hash/trace-comparison workflow for a fresh
output directory. Its CLI was checked; it was not separately run for another
227-case pass. Probe/component reproduction is documented in
[the fixture instructions](../../../tools/probes/flash_filters/README.md).

## Loud-fail audit and open work

Placement validation now rejects duplicate children, unknown MATRIX/CXFORM
fields, missing typed translation/alpha terms, malformed integer fields and
nonzero reserved bits with source locations. Mutation regressions cover these
paths. JPEXS's valid reserved=false encoding is accepted, not allowlisted.

The final rescan covers all 62 locked SWFs and retains the same 34 unsupported
placements with exact source locations in locked-swf-audit.json: blend 7 in
Kenshin (1); blend 13 in minrenx (1), qilabi (30), main (1); and main sprite 1504
frame 1 DropShadowFilter (1). These are hard errors, not harmless exceptions.
No new allowlist entry was added. Byakuya 631/985's exact hash/form scope remains
unchanged. The prior 88 cached-control / 26 context checks were not rerun here.

Still blocking merge: the color/order discrepancies above; exact real-component
pixels; Rukia gotoAndPlay(130), shunbuxg, exhaustive AS call/argument and clip-action
ownership; review of nine pre-existing compiled-context differences; handling
or explicit failing acceptance for the unsupported placements; complete shipped
content import acceptance. A 62-SWF placement scan is not a complete AS audit.
Future changes require final gates again. No new ports, merge or deployment.
