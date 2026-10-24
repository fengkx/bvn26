# r36: integer normal composition, diagnostic admission only

**The same pinned Yulong wrapper images now pass 4/4 (previously 0/4), with
zero channel difference. Production admission remains false.** New native vector
and bitmap controls each pass 2016/2016; the shared GPU implementation passes all
4032/4032 RGBA observations. No production compositor, sampling binding, assets,
reference pixels or thresholds were changed.

## Shared arithmetic and source-first evidence

`normal_composition.gdshaderinc` defines premultiplied **integer byte** source-over:

```
out = front + floor(back * (256 - front.alpha) / 256)
```

This applies to all four channels, including a transparent destination. It uses
neither the hardware floating point normal blend nor a per-pixel choice of formulas.
The GPU control fixture and final wrapper diagnostic include this same function.

The controls independently vary four color palettes (black, white, gray, colored
backgrounds), background alpha {0,1,64,128,254,255}, front alpha
{0,1,2,63,127,128,254,255}, object opacity {0,1,25,50,99,100} and inner opacity
{25,50,100}. Three authored display-list topologies separate front-only, middle
outside inner, and middle inside inner. Child depths and cached flags are explicit
in the two AS fixtures. All actions execute synchronously on frame 1 and the probe
stops; no timeline MOVE, exit-label assumption or enterFrame scheduler is involved.
The existing Yulong source-first answers remain those recorded in r34/r35.

Inputs are measured separately from the composed result. Black-background
BitmapData readback supplies stored premultiplied RGB; transparent readback supplies
alpha. Multiplying the lossy straight RGB readback by alpha is **not** used.

The native observations distinguish opacity ownership:

- Bitmap pixels: scale stored premultiplied bytes by the 8.8 alpha multiplier.
- Vector fills: transform alpha first, then compute RGB as
  `floor(authored_color * (transformed_alpha + 1) / 256)`.
- Compose parent/child 8.8 multipliers before applying them to the leaves; preserve
  the captured group's isolation and composition order. In these draw controls,
  `over(back, over(middle, front))` is exact. Flattening that into
  `over(over(back,middle),front)` is not generally byte-equivalent.

For example, palette 0/front alpha63/outer99% on transparent black produces
vector `[17,48,58,62]` versus bitmap `[16,47,57,62]`. These differ because their
input rasterization semantics differ, not because of a selected output-dependent
blend formula. A rejected initial model that multiplied already-rasterized vector
bytes and treated every cached hierarchy as an already-materialized opacity group
passed only 1281/2016 vector and 1575/2016 bitmap observations. The final model is
selected by authored source type and hierarchy only, and passes every observation.

Scope: these are synchronous `BitmapData.draw` hierarchy controls. Setting
`cacheAsBitmap` does not itself prove that the display renderer materialized every
nested cache before that draw. Do not generalize this result into an arbitrary
production cache/filter scheduling or isolation rule.

## Actual wrapper composition

`integer_wrapper_diagnostic.gd` inherits the unchanged r35 diagnostic. It keeps
production PNG loading, timeline traversal, authored Glow, 38x8 buffer allocation,
texture decoding and intermediate readbacks. At the final Composite node only,
it installs an explicit destination copy and the integer normal-composition
function with hardware blending disabled. Source bytes are reconstructed from the
existing composite shader's output; no image patch, background constant, native
image lookup or per-fighter color correction is used.

This diagnostic retains the actual sampled destination and actual final filter
texture. `run_normal_composition.py` stops before rendering wrappers if either
native arithmetic controls or GPU controls fail. Complete image comparisons use
the unchanged pinned r03/r21 native images, including alpha255. A missing sample,
unexpected event, shader error, wrong source hash, buffer change or any differing
channel fails. A one-byte mutation is covered by a regression test.

| Fresh check | Result |
|---|---:|
| Native vector controls / CPU | 2016/2016 |
| Native bitmap controls / CPU | 2016/2016 |
| GPU controls vs native RGBA | 4032/4032 |
| Complete wrapper with diagnostic integer composite | **4/4** |
| Loaded PNG premultiplied texels | 102/102 |
| Input + Glow buffer pixels | 1216/1216 |
| Existing leaf diagnostic | 6/6, 69120/69120 RGBA |
| Existing isolated Glow wrapper | 4/4 |
| Existing GPU sampler | 71824/71824 |
| Existing CPU clipped/repeat/scalar suites | all exact |
| Unchanged ordinary production composite, freshly rerun | **0/4**, max delta1 |

The old entry point still exits 1. The new candidate exits 0 only for its exact
bounded diagnostic. Neither sets `production_admitted=true`. The 54-image
production suite is not remeasured and remains historical **9/54**; no diagnostic
pass has been added to its score.

## Admission and next experiments

The integer operation is now validated for the measured operands and the bounded
Yulong production-path diagnostic. This is sufficient to eliminate the r35 final
114-pixel/+1 discrepancy in that diagnostic, but not to replace ordinary blending
globally. Remaining proof before production binding:

1. Actual multiple cached/filter SubViewport layers on transparent destinations,
   non-unit opacity and destination-copy ordering. The GPU control computes the
   measured nested arithmetic in one diagnostic shader; it is not an end-to-end
   rendering of every native nested display list through production buffers.
2. Partial-alpha PNG upload/premultiplication and formats beyond this source bitmap
   (its 99 opaque and 3 zero-alpha texels are proved).
3. General fractional/nonrectangular coverage, arbitrary affine/negative transforms,
   fill-matrix composition and source eligibility beyond this bounded rectangle.
4. Remaining component/color/order/matrix/rush pixels and full AS/clip-action
   ownership audit remain independent merge blockers.

Next discriminating experiment: materialize nested source buffers explicitly in
native Flash, then render the same two layer boundaries with actual production
buffer nodes, varying destination alpha and parent/child opacity independently.
Keep these 4032 controls and the pinned four complete images as strict regressions;
do not infer cache materialization from the `cacheAsBitmap` flag alone.

No intentional stability deviation, allowlist or tolerance. Draft PR #48 remains
**not merge-ready**. Production runtime unchanged, so full roster/Web export and
unrelated production GPU/Godot suites were not rerun. Repository checks and their
counts are recorded in `acceptance.json` and `checks/`.

## Reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case normal-composition \
  --output "$SCRATCH/vector" --ffdec "$FFDEC"
python3 tools/probes/build_flash_filter_probe.py --case normal-bitmap-composition \
  --output "$SCRATCH/bitmap" --ffdec "$FFDEC"
# Capture both builds using capture_native_player.py and the pinned native player.
python3 tools/probes/run_normal_composition.py --godot "$GODOT" \
  --native evidence/importer-loud-fail/r36 --output "$SCRATCH/composition"
python3 -m unittest tools.tests.test_normal_composition
python3 tools/probes/run_production_wrapper.py --godot "$GODOT" --output "$SCRATCH/baseline"
# The unchanged baseline remains exit 1, 0/4; the integer diagnostic exits 0, 4/4.
```
