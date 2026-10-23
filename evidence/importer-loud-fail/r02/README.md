# Filter parity and importer guards, r02 (2026-10-23)

Draft PR #48 remains blocked. This run fixes the measured small-object blur
mismatch; it does not claim complete Flash visual or importer semantic parity.

## Native source and implementation

The isolated programs now live in `tools/probes/flash_filters/*.as`, built by
`tools/probes/build_flash_filter_probe.py`. The old scratch-dependent scripts
were removed. [Reproduction commands](../../../tools/probes/flash_filters/README.md)
cover building, native capture, Godot rendering and strict comparison.

Source-first answers for this change:

1. Each checked-in probe executes its sole frame's DoAction, starts with stop(),
   creates a solid shape, assigns BlurFilter, draws its parent to BitmapData and
   reads getPixel32. There are no enterFrame actions or hidden timeline frames.
2. Each sample creates a fresh wrapper/shape and removes it afterward. There is
   no MOVE or retained instance state; runtime timeline scheduling was unchanged.
3. Playback stays stopped; after emitting done the probe calls fscommand("quit").
4. Assertions use the native alpha rows, not a convolution-generated baseline.
   The source programs independently fix the case matrix. Widths 1/2/4/8/12/16/32,
   blur 6/7/8/9/10/11/15/20/21/30, quality 1/2/3 yield 210 cases.
5. These exact programs were run in Adobe Flash Player Debugger 32.0.0.465 under
   Rosetta. Raw native logs, build/source hashes and capture metadata are stored
   in each case directory. This is a component oracle, not a full-game replay.
   Shipped placements remain listed in ../shipped-filters.json; real shipped
   component rendering still requires separate verification.

The 210-case native result supports limiting the BlurFilter kernel to
`min(blur, (padded_extent + 1) / 2)`, with padded extent equal to the source pixel
extent plus `2 * ceil(blur / 2) * quality`. Quality 1 exposed the limit on small
objects; quality 3 had enough padding. The generic filter group now updates this
limit with buffer geometry. It is applied to BlurFilter only: GlowFilter's
small-object limit has not been independently established. No character-specific
rule or intentional stability deviation was added. Fractional transforms,
vertical/two-axis combinations and real shipped components still need coverage.

## Results

- Blur large: 16/16, 2,560 alpha samples, exact.
- Blur small: 16/16, 1,120 alpha samples, exact after the fix. The previous
  3 failing cases (quality 1, blur 10/15/20) remain in
  blur-small-comparison.json; fixed results are separate.
- Blur bounds: 210/210, 33,600 alpha samples, exact on GPU (blur-bounds-godot.log).
- Color: all five cases still differ; max premultiplied RGBA errors 2/1/2/1/3.
  colors-comparison.json is a failing report; there is no parity tolerance.
- Existing blend regression: 38/38 passed with its existing unchanged assertions.
- Python: 376 tests, 2 skipped; see python-tests.log for final execution evidence.
- PROTECTED_FUNCTION_OK: 1,086 bytes and the original SHA-256, protected.log.
- Integrity, handoff, six schemas/six examples, and regenerated runtime/content
  fingerprint checks: see the corresponding logs.
- Whole-roster replay was NOT rerun in r02. The earlier 227/227, 130,334-state
  result predates the renderer changes and is not final acceptance.

## Audit and guard results

All 62 locked SWFs were rescanned. locked-swf-audit.json retains each source,
frame and rejected construct, plus the explicitly incomplete skip-site review;
large placement obligations remain in tools/importer/placement_requirements.json.
There are 34 rejected placements: mode 7 in Kenshin (1), mode 13 in minrenx (1),
qilabi (30) and main (1), and DROPSHADOWFILTER in main sprite 1504 frame 1 (1).
Numeric blend IDs are authoritative here; the earlier checkpoint's informal
"invert" label should not be used to interpret mode 13.

All 88 cached visual-control checks and 26 shipped fighter context compilations
passed. Seventeen context outputs match saved ai.json; nine pre-existing output
differences remain for review, and no AI output was regenerated. The production
cached-placement checks pass for current generated timelines. This does not
prove every AS statement has an owner or constitute full shipped import acceptance.

New tests ensure a truncated nested frame cannot bypass placement obligations,
and dropping filters/cache/blend/color-transform fields fails. Filter parsing
now rejects missing/invalid values, unknown or duplicate children, invalid RGBA,
unsupported glow flags and inconsistent IDs/reserved bits with source context.
A shadowed `source` loop variable previously replaced filter diagnostics with
"blendMode"; the importer now preserves the SWF/sprite/frame location. Synthetic
build tests use explicit empty requirements for their own fixture SWF instead of
relaxing production guards. No new harmless allowlist entry was added.

## Still blocking merge

Exact color/opacity/filter-order parity, real shipped components, numeric goto
and shunbuxg handling, complete AS/clip-action/skip-site ownership, review of the
nine compiled-context differences, full shipped import acceptance, and final
whole-roster/Godot acceptance after all changes. The narrow hash/form-pinned
Byakuya allowlist remains unchanged and requires review. New character ports
remain paused; nothing was merged or deployed.
