# r150 — indexed continuous spans differ from BitmapData spans

Direct native readback verifies all **2275 source texels**. The valid indexed tag retains its explicit long header, authored rectangle/fill transform, and before/after source-materialization controls. All **37248/37248** overlapping output pixels remain unchanged across those epochs.

A fixed byte-weight calculation for every indexed sample is **36832/36832 exact** on fully covered pixels; the unchanged positive-axis bulk sampler is **36832/36832 exact** for AS BitmapData. Applying the bulk sampler to indexed input only matches15620/36832 (max delta2). Indexed and AS native output agree8018/18624 per epoch. The API/storage distinction is measured independently of output-selected arithmetic.

The grid crosses scales1/3/5, independent quarter-pixel X/Y draw offsets, two X/Y clip origins, and lengths1/3/4/5/7/8/9/12/16/32. Four globally fixed candidates are retained. **832 fringe/outside samples are excluded from arithmetic admission**, not silently replaced; raw readbacks remain in the native log. This is not a general coverage or affine proof.

[Summary](summary.json), [all counterexamples](failures.json.gz), [native input and properties](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_indexed_bitmap_spans --output /tmp/indexed-spans --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/indexed-spans/components/lanran /tmp/indexed-spans/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_indexed_bitmap_spans --native evidence/importer-loud-fail/r150/native --output /tmp/indexed-spans.json
python3 -m unittest tools.tests.test_indexed_bitmap_spans
```

Next discriminator: apply this single indexed byte-weight rule to the unchanged original Lanran format3 source and pinned cache/filter boundaries. Preserve the frame5 fractional-coverage hard error. Only a source-proven storage distinction may route arithmetic; no per-pixel selection. Require held-out source component images before GPU binding.

`indexed_continuous_sampler_admitted=false`, `production_admitted=false`. Eight source-backed live original images are exact; production54 remains historical9/54. Full AS ownership, general affine/coverage, and remaining components are still merge blockers. Draft only; no merge/deploy/Worker.
