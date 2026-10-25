# r152 — independently measured non-tie twip rectangle coverage

Spatially constant bitmap inputs isolate coverage from sampling. Native transparent/black paired readbacks preserve24 actual premultiplied source values, crossing eight alpha values and three colors. Authored mask X/Y offsets independently cover0/.05/.1/.15/.25/.35/.5/.75/.85/.95; draw translation remains integer.2400 native images retain all geometry and inputs.

Ideal unquantized rectangle area fails16497 fringe pixels, max channel delta49. A single geometry rule — round each rectangle edge to its nearest quarter pixel, then floor each source byte times exact covered area — matches **153600/153600 pixels**. This retains quarter-grid controls inside the grid. No output-selected arithmetic or tolerance is used. Exact rational geometry avoids floating-point epsilon.

These authored twip offsets contain **no nearest-quarter ties**. Python's even-tie convention is not evidence for Flash ties; midpoint behavior remains unproven. Constant input also does not independently prove the order with varying-texture sampling. The candidate must next pass original source images without changing references.

[Summary](summary.json), [ideal-area counterexamples](failures.json.gz), [native readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-twip-coverage --output /tmp/twip-coverage --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/twip-coverage /tmp/twip-coverage/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_twip_coverage --native evidence/importer-loud-fail/r152/native --output /tmp/twip-coverage.json
python3 -m unittest tools.tests.test_twip_coverage
```

Next discriminator: retain original Lanran format3 texels, use the independently established indexed sampler and quantized geometry together, and compare all four original cache/filter/complete images. Reject ties, non-unit scales and unsupported affine rather than extrapolating this bounded coverage result. If exact, only then attempt live GPU binding.

`general_coverage_admitted=false`, `production_admitted=false`. Full AS ownership and production component parity remain open. Draft only; no merge/deploy/Worker.
