# r82 — non-white source composition across native API boundaries

576 fresh paired controls retain explicit non-white premultiplied source readbacks, a separate native Blur output, applyFilter output and actual filtered bitmap-display output. Both paths use identical authored source/color/filter properties. All **73728/73728 source RGBA pairs** agree; all **73728/73728 independently blurred alpha samples** match the admitted grouped/consumed-kernel model.

The unchanged r80 gain/color construction plus common source-over byte composition clears **73728/73728 applyFilter** and **73728/73728 display** samples. The source component is the explicitly read native RGBA, not an inferred straight-color reconstruction. Source alpha is independently checked against the authored rectangle/ramp; RGB is required to remain bounded by alpha. This isolates filter/source composition without claiming PNG decoding or a general source-premultiplication model.

Coverage: source colors1137375/16712064; alpha25/135/254; constant and horizontal ramp; kernels3.99609375/8.25; quality1/3; angle/distance(0,0),(0,-0.501953125),(135,1.25); filter alpha0.5/0.75 and strength0.75/2.5. Property getters and original bytes are retained in native.log.

Native outputs across APIs agree **73162/73728**. The566 differences all occur at the half-phase offset; preserving applyFilter ties-even versus display ties-away explains all of them. Using one API's output as the other's reference would be wrong. Neither API nor arithmetic is selected from observed RGB.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case shadow-colored-paths --output /tmp/bvn-r82/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r82/native /tmp/bvn-r82/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_shadow_colored_paths --native evidence/importer-loud-fail/r82/native --output /tmp/bvn-r82/recheck.json
python3 -m unittest tools.tests.test_shadow_colored_paths
```

[Exact comparisons](analysis.json), [capture](native/native.log), [hashes](provenance.json), [acceptance](acceptance.json). The separately requested native Blur is an independent alpha control, not a readback of an inaccessible internal shadow cache.

Next run these same non-white controls through the r81 GPU nodes, retaining actual raw source bytes and source texture identity. Do not synthesize source RGB from final output. Require both API routes separately exact; then add explicit post-filter opacity/transparent-destination composition boundaries. General PNG upload, fractional coverage, affine transforms and nested scene composition remain separately unproven.

`passed=true`, `production_admitted=false`. No production or GPU modification in this round. Historical components9/54 unchanged; full AS/clip-action ownership remains open. Full roster/Web and54-component renders not rerun. Draft only; no merge/deploy/Worker.
