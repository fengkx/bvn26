# r90 — single-pixel impulses reject a routing-only explanation

252 independent native controls use60×58 four-corner impulses and horizontal/vertical ramps, the r89 authored non-binary scales,16-twip fill translation and draw X4/4.25. All **41760 source texels** are explicitly read back and verified before drawing. Clip starts4..7 and ends76..80 vary independently; a separate path isolates each sample with a1×1 clip. The full source-readback sequence and filter-free fill/draw matrix getters are retained.

The unchanged r89 fixed-coordinate sampler matches **9045/9360 full-coverage interior RGBA samples**. Four-corner plus two-ramp signatures fit at least one old interpolation order at1455/1560 groups, but **105 groups fit none**. All105 are drawX4/sampleX75; five are single-pixel clips, one at each tested Y20/21/26/27/28. Therefore choosing another bulk/tail route cannot alone explain these counterexamples.

Separately,283/480 overlapping native sample groups change with clip geometry, confirming that span behavior still matters elsewhere. The compatibility lists are **rejection diagnostics**, never a selector used to render pixels.3240 clipped-out/coverage-fringe samples are retained separately and not counted as interior success.

At x75 the old initializer's rounded inverse is53137 and its ceiling half-step yields a coordinate exactly on a1/256 boundary. This suggests a discriminating **half-step rounding** experiment, not permission to change the initializer: compare ceiling versus even half-step on independently chosen odd inverse coefficients, both parity classes, with zero vertical fraction and scalar clips. Include neighboring pixels/origins and the original source width before testing any common construction against all old suites. Do not fit a coefficient from the observed response.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case jiraiya-span-controls --output /tmp/bvn-r90/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r90/native /tmp/bvn-r90/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_jiraiya_span_controls --native evidence/importer-loud-fail/r90/native --output /tmp/bvn-r90/recheck.json
python3 -m unittest tools.tests.test_jiraiya_span_controls
```

[Summary](summary.json), complete signatures/failures/fringe readbacks in `analysis.json.gz`, [capture](native/native.log), [hashes](provenance.json), [acceptance](acceptance.json). No old sampler/reference changed; no GPU or production binding.

`routing_admitted=false`, `production_admitted=false`. r89 still5/6 leaf images;54-suite historical9/54. Nontransparent fractional coverage, JPEG3, general affine/implicit buffers and full AS/clip-action ownership remain open. Full roster/Web/54 component renders not rerun. Draft only; no merge/deploy/Worker.

Fresh Python:718 pass +2skip. Caches26/26, fingerprint, protected, integrity, handoff and contracts pass.
