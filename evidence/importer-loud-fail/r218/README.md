# r218 — independent JPEG row route and original bitmap exact

864 independently encoded constant YCbCr controls vary widths7/8/9,15/16/17,23/24/25, both subsampling formats and independently varied luma/chroma. Actual decoded planes equal the authored constants. Geometry-derived eight-pixel prefixes using r213 contribution-floor arithmetic, with nearest-total conversion for the remainder, clear **110592/110592 native RGB pixels**. Whole-row floor clears95616; group4 clears103104; group16 clears85632. Routing never inspects RGB to choose a path.

Held-out unchanged original JPEG3 and six coefficient-preserving width controls now clear **494424/494424 RGBA pixels**. The original bitmap is **70308/70308 exact**, including all four former residuals. Raw-plane hashes exactly retain r217; no IDCT, source bytes, alpha, reference image or per-coordinate adjustment changed. Source alpha is independently extracted. This is bounded decoder evidence, not an assertion of native SIMD implementation or permission for global production use.

[Independent row comparisons](summary.json.gz), [native controls](native/native.log.gz), [held-out counts/hashes](heldout.json), [held-out decoded planes](heldout-planes/), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_jpeg_row_partitions --output /tmp/jpeg-rows --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jpeg-rows /tmp/jpeg-rows/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jpeg_row_partitions --native /tmp/jpeg-rows --dump /tmp/jpeg-planes --output /tmp/jpeg-row-analysis
python3 -m tools.probes.validate_jpeg_row_route --planes evidence/importer-loud-fail/r218/heldout-planes --output /tmp/jpeg-heldout.json
```

Next discriminator: bind source-derived decoded bitmap340 to an isolated complete Orochimaru wrapper diagnostic, retaining the authored fill67, mask, transforms, Blur20 and source cache bounds. First compare unfiltered/local/input boundaries to pinned native; only then compare complete images. Do not upload native reference pixels as source textures. Keep all sampler/matrix/decoder controls exact. Production_admitted remainsfalse, complete component diagnostics still36/54 until remeasured; historical production9/54; AS ownership open. Draft only; no merge/deploy/Worker.

Checkpoint stopped at the user's request. Focused tests2/2, caches26/26, fingerprint, integrity, handoff, contracts and PROTECTED_FUNCTION_OK pass. Full Python963 passed/2 skipped is retained r209 evidence, not rerun in r218; full roster/Web and production54 were not rerun. The pursuing goal is paused; r219 and the next wrapper discriminator have not started.
