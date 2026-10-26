# r70 — actual GPU allocation isolates a fractional blur gap

The bounded r69 extent construction now runs through actual diagnostic FilterGroup nodes for all724 native cases from r62/r66/r68/r69. It keeps authored source bounds, uses `floor(kernel/2)+1` padding and extends the actual input/filter viewports by one far-end pixel. Every group verifies actual size, origin and pass count; the shared admitted CXFORM shader is unchanged.

| GPU/native gate | Exact RGBA pixels |
|---|---:|
| Input | **115840/115840** |
| Filtered before CXFORM | **115596/115840** |
| Final | **115678/115840** |

The strict render gate exits1. All244 filtered and162 final failures are at kernels **3.99609375 and7.99609375**, in r68, with maximum channel delta1. All other cases, including all r69 fresh small-kernel/alpha controls, are exact. The new differences already exist before CXFORM, so altering reciprocal arithmetic or geometry to absorb them would be incorrect.

The diagnostic subclass changes allocation only and retains the production filter passes. It does not replace source bounds, native rows, original textures, or choose a route by RGB. Twelve sequential batches use the same graphical Compatibility backend. Sources, native captures and aggregate readbacks are pinned in [provenance](render/provenance.json); per-batch fixtures/logs are retained under `render/batches/`.

## Reproduce

```sh
python3 -m tools.probes.run_integer_extent_gpu --godot /path/to/Godot \
  --output /tmp/bvn-r70/render
# Expected exit1 until every filtered and final pixel is exact.
python3 -m unittest tools.tests.test_integer_extent_gpu
```

[All measured sites](render/comparison.json), [lossless GPU rows](render/rows.json.gz), [acceptance](acceptance.json). No new Flash capture; the pinned native inputs are reused. No production runtime/shader edit, tolerance or allowlist.

## Next isolation

Capture independent one-axis and two-axis Blur/Glow responses near those integer kernels, with constant/impulse/ramp inputs and explicit source readbacks. Separate fractional edge-weight consumption from normalization and pass-by-pass truncation before changing any filter math. Test common constructions globally; do not add an epsilon or adjust CXFORM to hide a pre-transform mismatch. Preserve all existing exact blur, component, composition and arithmetic controls.

`production_admitted=false`. Component suite remains historical9/54; no real component improvement is claimed. Fractional destination positions, clipping/general affine eligibility and full AS/clip-action ownership remain open. Full roster/Web export and unchanged graphical suites were not rerun; their pinned regression readbacks are checked by Python. Draft only; no merge/deploy/Worker.
