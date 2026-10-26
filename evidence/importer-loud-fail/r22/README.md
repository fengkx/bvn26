# r22: isolate component input rasterization before changing filter math

Draft PR #48 remains blocked. **No production pixel-count improvement is claimed.**
No runtime, generated asset/cache, locked source, tolerance or allowlist changed.

## Fresh production measurements

| Gate | r21 | r22 |
|---|---:|---:|
| Exact component images | 9/54 | 9/54 |
| Component playheads | 4242/4242 | 4242/4242 |
| Color groups | 3/5 | 3/5 |
| Filter/CXFORM order groups | 2/4 | 2/4 |
| Scalar ColorMatrix | 20/24 | 20/24 |
| Rush entered frames | 21/21 | 21/21 |
| Rush differing RGB channels | 234/5103 | 234/5103 |

`component-pixels.json` pins each source hash, owner/child clip, source frame,
observed local frame, tick, changed channels, maxima and worst coordinates.
The color/order/arithmetic/rush comparison JSON files retain all remaining
failures. Native references are the same hash-pinned r03/r05/r11 captures as r21;
Godot outputs were freshly measured. One incomplete Yulong capture exited 0
without a completion marker; the strict image comparator rejected it and a
complete rerun replaced it. The component render launcher now also rejects
missing completion markers and any engine ERROR.

## Remove only the tested outer filter/cache, retaining fractional transforms

`build_filter_components.py --raster-input-only` builds a **separate diagnostic**
from the same locked definition and placement tags. It clears the tested child’s
filters/cache before each native observation; Godot receives the same placement
without those two fields. The native child is resolved by authored depth, including
anonymous children, and emits `raster_input,<case>,0,false`. Missing children,
missing/duplicate removal observations, or a still-filtered Godot placement are
rejected. Nested child behavior and other fields are retained; this is not a claim
that every descendant filter has been removed.

All 21 removals were observed. **The same 45 image identities still fail**, with
9/54 exact and 4242/4242 clocks matching. Thus correcting the tested outer filter
alone is insufficient; substantial input-raster/transform differences precede it.

| Source | Exact unfiltered-input images | Maximum R/G/B delta |
|---|---:|---|
| Jinye | 1/4 | 159 / 137 / 159 |
| Jiraiya | 0/4 | 158 / 151 / 156 |
| Lanran | 0/4 | 209 / 209 / 209 |
| main / XG_mfdjx | 6/12 | 190 / 159 / 247 |
| Orochimaru | 0/10 | 176 / 169 / 174 |
| Yijiao | 2/6 | 158 / 158 / 158 |
| Yulong | 0/14 | 80 / 106 / 114 |

`raster-inputs/` retains native trace gzip, exact generated harness AS, source and
SWF hashes, native launch metadata, cases, native/runtime PNGs and clocks.
`raster-input-pixels.json` gives the complete measured list. These images do not
replace the authored-filter parity gate.

A separate rejected diagnostic snapped Godot normalization translations down to
1/20 pixel and scale down to 16.16 while keeping pinned native captures unchanged.
It also remained 9/54. `snap-diagnostic.py` reproduces this hypothesis; it is not a
reference correction or a production change.

## New isolated smooth-bitmap sampling evidence

Two new native probes use a 2x2 RGBA basis bitmap, smooth bitmap fill, and an
interior sample (no shape edge), drawn over black. Their AS, built SWF hashes,
run IDs and raw native logs are retained. There is no filter or timeline state
in these probes. Native environment is Flash Debugger 32.0.0.465/Rosetta.

The first probe varies horizontal translation in 1/256 pixel increments with
scales 2/4/8 and alpha 255/128. The observed output changes at quarter-screen-pixel
phases. A diagnostic CPU candidate truncates destination translation to quarter
pixels, floors source phases to 1/256 texel, floors the first three bilinear
weights to bytes, assigns the residual to the fourth, and truncates the weighted
premultiplied RGB. It matches **1536/1536** calibration samples exactly.

The independent extended probe includes negative and two-axis translations and
scales 2.5/3/5/8. That same candidate matches **3393/4096**, with **703 failures,
maximum channel delta 2**. It is explicitly NOT admitted to production:

| Alpha | Scale | Exact / 512 | Max delta |
|---:|---:|---:|---:|
| 255 | 2.5 | 257 | 2 |
| 255 | 3 | 384 | 1 |
| 255 | 5 | 383 | 1 |
| 255 | 8 | 512 | 0 |
| 128 | 2.5 | 385 | 1 |
| 128 | 3 | 448 | 1 |
| 128 | 5 | 512 | 0 |
| 128 | 8 | 512 | 0 |

`analyze_bitmap_phase.py` validates full capture coverage and exits 1 on any
candidate mismatch. This is a CPU arithmetic experiment, **not Godot parity**.
The full per-phase failures are in `bitmap-phase-extended-comparison.json`.
Next experiment: isolate inverse-affine/fixed-point coordinate stepping at
non-power-of-two scales using independent red/green basis pixels, with both
translation signs. Only after those interior samples match should edge coverage,
rotation, clipping and authored bitmap-fill smoothing be composed into a shader.
Do not reuse the DropShadow phase rule without this additional proof.

## Acceptance and remaining blockers

See `acceptance.json` and logs for this turn's counts. Runtime preservation is
recorded separately. Cached fighters remain 26/26; online-manifest/fingerprint
checks pass. No runtime changes means roster/GPU regression suite and full Web
export were not repeated; the last complete runtime acceptance is r20 and last
successful full Web build is r21. These are historical results, not fresh r22 runs.

Still blocking merge: 45 component images, color/order/ColorMatrix/rush differences,
and full AS/clip-action ownership proof. Placement errors remain cleared (34/34);
no placement admission changed here. This checkpoint advances diagnosis and probe
coverage, not production rendering parity. No merge or deployment performed.

## Reproduction

```sh
python3 tools/probes/build_filter_components.py --raster-input-only \
  --output "$OUT/inputs" --ffdec "$FFDEC"
BVN_REVIEW_DIR="$OUT/inputs" BVN_FLASH_APP="$FLASH_APP" \
  python3 evidence/characters/pain/visual-parity/review/probes/capture_components.py
BVN_REVIEW_DIR="$OUT/inputs" BVN_GODOT="$GODOT" \
  python3 evidence/characters/pain/visual-parity/review/probes/render_components.py
python3 tools/probes/compare_filter_components.py --output "$OUT/inputs"
python3 tools/probes/inventory_component_pixels.py --directory "$OUT/inputs" \
  --output "$OUT/raster-input-pixels.json"
# The two comparators above intentionally exit 1: parity remains incomplete.
python3 tools/probes/build_flash_filter_probe.py --case bitmap-phase-extended \
  --output "$OUT/bitmap-phase-extended" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/bitmap-phase-extended" \
  "$OUT/bitmap-phase-extended/native.log" --player-app "$FLASH_APP" \
  --allow-window-activation --timeout 40
python3 tools/probes/analyze_bitmap_phase.py --extended \
  --native-log "$OUT/bitmap-phase-extended/native.log" --output "$OUT/extended.json"
# Exit 1 is required for the rejected candidate. Omit --extended and build
# bitmap-phase for the 1536/1536 calibration probe.
python3 -m unittest tools.tests.test_component_raster_inputs tools.tests.test_bitmap_phase_analysis
```
