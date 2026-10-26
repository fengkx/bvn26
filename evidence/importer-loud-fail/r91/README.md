# r91 — independent clipped half-step rounding clears the held-out leaf

60 native scalar controls independently vary source widths60/256, six scales (including odd inverse half-step parity classes), and origins0/1/4/15/-4. Each destination pixel is drawn through its own1×1 clip; vertical scale1 and integer origin eliminate vertical interpolation ambiguity. All2528 source texels and matrix properties are explicitly read back. Original source bytes and native outputs are retained.

One global half-step rule is exact on all16377 fully covered scalar samples: **round the fixed-point inverse half-step to nearest even**. Ceiling matches16359; floor16358. No per-coordinate coefficient is fitted. Fractional/outside coverage readbacks are retained but excluded from this scalar initializer claim.

Only after that independent measurement, a separate CPU candidate applies the rule without changing repeat initialization or geometric span routing. It preserves all **71824/71824** r32 controls (including8736 transparent RGBA), clears the r90 independently clipped impulse/ramp samples **9360/9360**, and makes the unchanged original r89 Jiraiya leaf images **6/6 exact** (589824 RGBA pixels). All three original interior residuals are gone. Authored fillY16twips remains separate from draw initialization. No native reference, source shape, bitmap, mask, old sampler module or production file changed.

The old initializer was ceiling for clipped and even for repeat. The diagnostic now uses even for both, with the existing repeat period normalization intact. This is an independently constrained common arithmetic change, not RGB-selected routing. r90 compatibility lists remain rejection evidence and are never used as rendering selectors.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case clipped-half-step --output /tmp/bvn-r91/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r91/native /tmp/bvn-r91/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_clipped_half_step --native evidence/importer-loud-fail/r91/native --output /tmp/bvn-r91/scalar.json
python3 -m tools.probes.bitmap_half_even_candidate --output /tmp/bvn-r91/heldout.json
python3 -m unittest tools.tests.test_clipped_half_step
```

[Summary](summary.json), complete scalar and held-out results in `analysis.json.gz`/`heldout.json.gz`, [capture](native/native.log), [hashes](provenance.json), [acceptance](acceptance.json).

Next discriminator: port this one independently measured change into an isolated Godot sampler diagnostic; retain all71824 original GPU samples and render all six original r89 images with their raw texels/fill/mask metadata. Require exact RGBA, then move toward the complete authored filter component. Do not enable production from a leaf pass.

`cpu_bounded_candidate_passed=true`, `gpu_advance_allowed=true`, **`production_admitted=false`**. Fractional coverage is still unproven (all original leaf fringe samples transparent), as are JPEG3, general affine and implicit buffers. Full AS/clip-action ownership remains open.54-suite historical9/54. Draft only; no merge/deploy/Worker.

Fresh Python721 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web and54-suite not rerun (production unchanged).
