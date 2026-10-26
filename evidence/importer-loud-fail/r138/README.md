# r138 — original rotated Yulong source input and Glow reproduce pinned images

Source bitmap148 raw premultiplied bytes, both authored fill slots, shape266 contour/matrix and wrapper267 raw tags remain pinned. The active unit quarter-turn is inverted directly; no pre-rotated texture substitutes for the source matrix. Child translation and outer draw translation retain their independently measured separate consumption. Effective origin is `(298.5,182.75)` plus the three integer offsets, derived without reading reference pixels.

The source-derived input is **720000/720000 exact** against r131 cache boundaries. Unchanged admitted Glow arithmetic is **720000/720000 exact**. Normal composition matches the two original full54 pinned images **480000/480000 exact**. All222 fractional fringe samples match, but area coverage here is still only component-tested: `floor(sample × exact rectangle area)`, with no epsilon. No target image supplies rendering input.

[Summary](summary.json) includes all source fill metadata, origins, fringe samples and pinned image hashes. Full candidate inputs/Glow are under `images/`. [Provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_yulong_rotated_source --output /tmp/yulong-rotated-source
python3 -m unittest tools.tests.test_yulong_rotated_source
```

Next discriminator: independently capture constant raw-byte sources with alpha0/1/2/31/63/64/127/128/254/255 and independent quarter-pixel X/Y positions. Compare normal and quarter-turn fills to isolate coverage from interpolation. Require exact edge/corner byte consumption before GPU binding; component-specific agreement does not establish general coverage.

`source_derived_input_verified=false` pending independent coverage; `production_admitted=false`. This CPU diagnostic is not a new production54-suite count. Six previous bounded live Blur images exact; historical production54 remains9/54. Other components, arbitrary affine/coverage and AS ownership remain open. Draft only; no merge/deploy/Worker.
