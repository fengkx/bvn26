# r31: continuous repeat spans match the captured native arithmetic suites

**CPU arithmetic gates are green. Production admission remains false.**
The r30 scalar initializer and r27 clipped sampler are byte-identical to the
previous tip. No runtime/generated data, locked source, reference, tolerance or
allowlist changed. Components were not remeasured:9/54 remains the historical
baseline, not a new render result.

## Native controls and coordinate/weight inference

`bitmap-repeat-span-intervals.as` captures the requested size2 cases:
scale5/origin0 and scale3/origin-15 (draw translation is minus origin). Clip starts
2 through8 preserve overlapping destination coordinates while lengths4 through16
vary individually; lengths1/3 are scalar controls. Six textures provide four
independent corner impulses plus horizontal and vertical ramps. Green/blue are
constant113. There are11256 RGB responses,1876 six-response groups.

The analyzer inverts each six-response signature across *all* byte coordinates
in a two-texel period, separately for byte weights, vertical-then-horizontal and
horizontal-then-vertical interpolation. Independent ramp responses bound the
search; the byte-weight residual is included. Each recovered byte denotes a
half-open coordinate interval of width1/256. All compatible coordinates/families
are retained in `comparison.json`, including reflected-coordinate ambiguity.
These are intervals conditional on the tested interpolation families, not proof
of native implementation internals.

**All1876 groups admit the unchanged r30 scalar coordinates.** No endpoint-derived
coordinate adjustment is required by these observations. Some signatures admit
multiple families; no such ambiguity is used to pick a per-pixel runtime path.

At scale5/start4/offset1, length4 gives corner responses(96,142,6,8) and rampX152;
length8 gives(95,142,6,9) and the same rampX152. At the fixed scalar coordinates,
the former is vertical-first and the latter horizontal-first. This independently
separates an interpolation-order change from changing the source coordinate.

## Geometric span model

`bitmap_repeat_span_candidate.py` uses only the transform, source size and
covered destination interval. No native RGB enters partitioning:

1. Intersect geometry and destination clip; start at the first fully covered
   pixel. Coverage-fringe rasterization is outside this model.
2. Split the interval into256-pixel work chunks anchored at that start.
3. Within each chunk, split when the unwrapped scalar source coordinate crosses
   a texture period (`floor(sourceX/width)` changes).
4. For each run, take the largest prefix whose length is divisible by4. The tail
   uses the unchanged scalar byte-weight interpolation.
5. If the **entire bulk prefix's** bilinear footprints avoid the repeated right
   and bottom texture edges, interpolate vertically then horizontally. Otherwise
   interpolate horizontally then vertically. Each stage truncates to bytes.

The positive monotone axis transform allows checking the last bulk X footprint
and the row's Y footprint. Mode applies to the whole bulk prefix, explaining why
increasing clip length changes earlier pixels. Four-pixel grouping alone was
insufficient because it omitted both period segmentation and bulk footprint tests.

For scale5/start4, length4 stays within the safe neighbor region, but length8
crosses it: VVVV becomes HHHHHHHH. For scale3/origin-15/start4, a one-pixel prefix
precedes the period boundary; length5 gives BHHHH. These choices are made from
geometry before sampling any texel.

Without the256-pixel work boundary, the corrected model gets938/1008 on the old
distant suite. Reinstating the independently observed clipped-work boundary
clears1008/1008. An additional held-out probe, `bitmap-repeat-span-chunks.as`, then
captures lengths255/256/257/513 at shifted starts3/5, across both cases and all
six textures:30744/30744 exact. This checks boundary anchoring independently of
the old sparse positions255/511.

## Exact counts

| Native suite | r30 | r31 | Max channel delta |
|---|---:|---:|---:|
| Distant repeat |571/1008|1008/1008|0|
| r30 four-corner short spans |4789/5376|5376/5376|0|
| r27 independent repeat boundaries |not admitted|2016/2016|0|
| New lengths1/3/4–16, shifted starts |—|11256/11256|0|
| New long/chunk-boundary controls |—|30744/30744|0|

All scalar controls remain exact: translation1200/1200, pixel-step960/960,
single-pixel1008/1008, negative168/168, binary matrix routes280/280,
rounding288/288, independent scalar4032/4032, scalar lengths1/3:768/768.
All clipped regressions remain exact: base1536,extended4096,single1008,distant1008,
scan6048,widths24080,axes4032,origins1632,boundaries2016.

## Production integration remains unfinished

This closes the captured continuous arithmetic counterexamples. It does **not**
claim GPU or production image parity. `timeline_preview.gd` currently emits
nearest-filtered Sprite2D/Polygon2D nodes around lines998–1030. Merely replacing UV
sampling cannot reproduce the scan-start/chunk/period context established here.
The production binding must supply actual covered row intervals and effective
transforms, preserve the authored fill smoothing/repeat mode, and verify the
integer interpolation stages against native on Godot's render path.

The demonstrated domain is positive axis transforms, known full coverage,
identity fill matrix (plus the old constrained binary-route controls), and the
captured opaque/constant-alpha sources. General affine/negative scales,
fractional fill-matrix composition, coverage edges and varying-alpha texture
composition are not established by these CPU tests. No broad runtime fallback
or unsupported-domain exception was added to hide that gap.

Next: port the bounded sampler and span metadata into a Godot diagnostic fixture,
require exact native RGB/RGBA before binding eligible production placements, then
remeasure the54 component images. The remaining production integration is work
still to do, not an intentional Flash-fidelity deviation or a product decision.
Full AS/clip-action ownership proof also remains a separate merge blocker.

## Reproduction and acceptance

The raw traces, source/SWF hashes and Flash Player Debugger32.0.0.465/Rosetta
capture environment are retained in `intervals/` and `chunks/`. Build each fixture
with `build_flash_filter_probe.py --case bitmap-repeat-span-intervals` or
`bitmap-repeat-span-chunks`, then use `capture_native_player.py` as inr30.

```sh
python3 tools/probes/analyze_bitmap_repeat_spans.py --output /tmp/r31-comparison.json
# Exit0 means arithmetic_passed=true; production_admitted remains false.
python3 -m unittest tools.tests.test_bitmap_repeat_spans
```

Fresh counts/logs are in `acceptance.json` and `checks/`. Caches26/26. Production
is unchanged; full roster/GPU/Godot/Web export were not rerun (historical full
runtime:r20; Web:r21). Components/color/order/matrix/rush were not remeasured:
9/54,3/5,2/4,20/24,234/5103 differing RGB channels respectively. Placement34/34
clearance is unchanged. Draft PR#48 is still not merge-ready. No merge/deploy/Worker.
