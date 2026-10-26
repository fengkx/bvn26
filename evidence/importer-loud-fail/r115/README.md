# r115 — independently revealed filtered origins explain the remaining bounded phase errors

Eight geometry/translation groups each create three fresh instances: cache-only, identity ColorMatrix, and a ColorMatrix mapping input alpha to255 with constant RGB offsets. All480 source texels, actual20-element filter properties and complete800x16 native ARGB images are retained.

**Identity filter versus cache-only:102400/102400 exact.** The alpha-reveal outputs are solid opaque rectangles, including transparent padding beyond the original shape. Their measured left edges are123/124/127/128/128/129/130/131 for the ordered groups; all span y4 through12 inclusive. These are observed alpha-support boundaries, not origins picked by matching RGB.

Using those independently measured left edges in the unchanged r112 arithmetic reproduces **2904/2904 cache-only interior samples**, including the four previous geometry counterexamples. This supports allocation-origin investigation rather than changing interpolation. It is an intermediate-boundary diagnostic: measured native origins are not a source-derived runtime algorithm, and identity-image equality alone does not prove identical hidden allocation for every filter/cache-only path.

A separate observation is retained: the constant-RGB ColorMatrix yields both native0xff254971 and0xff6e0071 in its opaque rectangle despite unchanged property readbacks. Alpha is255 throughout, so this does not invalidate the measured support; it is not claimed RGB matrix parity and remains a native arithmetic discriminator. No reference is rewritten to the mathematically expected constant.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-reveal-buffer --output /tmp/bvn-r115/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r115/native /tmp/bvn-r115/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_reveal_buffer --native evidence/importer-loud-fail/r115/native --output /tmp/cache-reveal.json
python3 -m unittest tools.tests.test_bitmap_cache_reveal_buffer
```

[Summary](summary.json), all source/filter/image bytes in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: independently sweep source geometry minima, sizes and scales while varying the reveal alpha coefficient. Compare globally fixed source-unit versus device-unit bounds-expansion/rounding constructions against the measured support, retaining zero-minimum, negative-minimum and binary-scale controls. Validate a common geometry rule on held-out cases before using it to predict cache-only origins; never select padding from a locally matching image. Keep the unexpected constant-RGB outputs as a separate matrix arithmetic control.

`cache_only_allocation_equivalence_proven=false`, `candidate_admitted=false`, `production_admitted=false`. Components historical9/54; no GPU/production advance. General affine/coverage and full AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.

Validation: full Python771 passed+2 skipped; caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production unchanged; full roster/Web export and fresh GPU/component renders not rerun.
