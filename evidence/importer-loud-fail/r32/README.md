# r32: Godot diagnostic sampler and fresh production component measurements

**Diagnostic GPU/native samples 71824/71824 exact. Production admission is false.**
No production placement is bound to this sampler. No runtime/generated production
content, locked input, native reference, allowlist or tolerance changed. Full
AS/clip-action ownership proof remains a separate merge blocker.

## What the Godot fixture actually exercises

`godot/tests/bitmap_sampler_diagnostic.gd` independently ports clipped/repeat
coordinate initialization and row partitioning from r27/r30/r31 into GDScript.
It retains the two half-step rounding rules, integer repeat normalization,
256-pixel work chunks, texture-period splits, four-pixel bulk prefixes, footprint
checks and scalar tails. Python supplies transforms, source patterns, clip bounds
and **native expected bytes only**; it does not compute coordinates, modes or
predicted pixels for Godot.

The GDScript fixture packs the four source texels and geometry-derived mode/phase
into nearest-filtered data textures. `bitmap_sampler_diagnostic.gdshader` performs
byte-weight, vertical-first or horizontal-first interpolation on the actual
Compatibility GPU. Native expected values are used only after GPU readback.
This validates GDScript metadata generation and GPU arithmetic together. It is
not yet a production Sprite2D/Polygon2D scan-conversion or texture-binding test.

`run_bitmap_godot_fixture.py` regenerates inputs from pinned traces, rejects
nonzero exits, engine errors, missing completion markers/reports, wrong input
hashes, missing suite coverage and **any** mismatching sample. `gpu.png` is the
actual GPU readback atlas; `gpu.json` contains per-suite counts; `provenance.json`
pins source/fixture/native/player-binary/readback hashes and the executed command.
The generated fixture is reproducible scratch data, not an expected-output rewrite.

## GPU/native results

Tested on Godot 4.7.2 Compatibility, Apple M2/OpenGL 4.1 Metal 90.5. Environment and
engine identification are in `gpu.log` and `provenance.json`.

| Native suite | Exact / total |
|---|---:|
| r22 base bitmap phase |1536/1536|
| r22 extended non-power-of-two phase |4096/4096|
| Distant clipped |1008/1008|
| Single clipped |1008/1008|
| Continuous clipped scan |6048/6048|
| Distant repeat |1008/1008|
| Single repeat |1008/1008|
| r30 short repeat spans |5376/5376|
| r31 interval controls |11256/11256|
| r31 long/chunk controls |30744/30744|
| New transparent target, constant alpha 128 |4368/4368|
| New transparent target, varying alpha |4368/4368|
| **Total** |**71824/71824**|

The 63088 old samples draw on opaque black: their premultiplied RGB is compared
exactly and the destination alpha is 255. New samples genuinely exercise transparent
RGBA, rather than inferring transparency correctness from the black-background suite.
The full older CPU scalar/clipped/span regressions were also rerun, with no changes
to their candidate implementations. Not every older independent CPU control is
repeated on GPU; the directly executed GPU suites are listed above.

## New native RGBA probe and readback encoding

`bitmap-transparent-rgba.as` uses a transparent BitmapData destination and emits
`getPixel32` words. It covers clipped/repeat modes, scales 3/5/8/1.7, starts 3/4,
lengths 1/4/8/260, and two 2x2 primary-color/white sources: constant alpha 128, or
corner alpha 0/64/128/255. There are 128 ordered trace rows and 8736 RGBA samples.
The parser preserves signed 32-bit AS trace words by bit reinterpretation, rejects
out-of-range/fractional words, and requires every identity and completion marker.

For these native controls, the GPU readback adapter uses the single integer rule:

```
reciprocal = floor(65280 / alpha)
straight_channel = floor((premultiplied_channel * reciprocal + 127) / 256)
```

Alpha 0 yields RGB 0. This is a measured `getPixel32` encoding candidate, **not a
production framebuffer blending rule**. Simple floating nearest division failed 856
samples; floor division failed 5231; exact nearest/ties-down division fixed constant
alpha but left 542 varying-alpha responses. The 8-bit reciprocal rule matches all
8736. `rejected-readback-models.json` retains the rejected counts and examples.
No per-pixel choice, reference rewriting or ±1 tolerance is used.

This does not establish arbitrary PNG upload premultiplication, arbitrary source
colors/alpha patterns or every Flash readback case. Production texture decoding
and compositing must still be validated on the real path.

## Fresh 54-component remeasurement

Reused the hash-pinned r03 native captures and r21 case definitions, then rendered
all 54 images freshly through the **unchanged production renderer**. Source hashes
were rechecked by the inventory tool. Results remain:

- exact images **9/54 → 9/54**; 45 still differ;
- playhead observations **4242/4242**;
- 21 filter/cache placements covered; strict comparator exits 1 as required.

`component-pixels.json` lists every fighter, clip, source frame/depth, tick,
per-channel changed counts/maxima and worst coordinates. `components/` contains
fresh Godot PNGs/clocks and case definitions. `component-comparison.json` retains
the complete strict comparison. Pinned native images remain in r21/r03; no new
native production baseline was written.

Color/order/matrix/rush use separate harnesses and were not rerun here. Their
historical results remain 3/5, 2/4, 20/24 and 234/5103 differing RGB channels. They are
not newly green because the sampler diagnostic passed.

## Admission boundary and next work

The bounded GDScript+GPU arithmetic fixture passes. Production pixel suites do
not, so `production_admitted` remains false and there is no placement binding.
The real renderer still needs covered-row metadata and effective transform/fill
mapping, plus proof for source upload/premultiplication, actual masks/coverage,
fractional fill-matrix composition, affine/negative scales and real varying-alpha
textures. Unsupported domains must not silently reuse a convenient sampler.

Next bind only a source-proven eligible diagnostic component, preserve its actual
fill metadata and masks, and require exact native image parity before enabling
that path in production. No intentional stability deviation was introduced.

## Reproduction / acceptance

```sh
python3 tools/probes/run_bitmap_godot_fixture.py --godot "$GODOT" --output "$OUT/sampler"
# Requires an actual GPU; --headless does not prove GPU/native rendering.
python3 -m unittest tools.tests.test_bitmap_godot_fixture
python3 tools/probes/build_flash_filter_probe.py --case bitmap-transparent-rgba \
  --output "$OUT/rgba" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/rgba" "$OUT/rgba/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
```

For components, follow r21 reproduction using its pinned r03 native traces and
`render_components.py`, then run `compare_filter_components.py` (required exit 1)
and `inventory_component_pixels.py`. Fresh logs are included here.

Fresh checks/counts: `acceptance.json`, `checks/`. Caches 26/26. Runtime unchanged;
full battle replay, other GPU/Godot runtime suites and Web export were not rerun.
This turn ran the new GPU sampler fixture and the full 54-image production component
harness. Draft PR #48 remains not merge-ready. No merge/deploy/Worker.
