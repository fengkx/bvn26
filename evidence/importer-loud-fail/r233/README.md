# r233: independent raw-fill and draw translation controls

Keep original shape56/57 geometry and linear fill coefficients. Patch only the active bitmap55 fill mode to nearest67 and selected signed translation bits by exact integer twips. Source bytes remain R=2x,G=6y,B73,A255. Thirteen fill variants independently move X or Y by -20,-10,-1,+1,+10,+20twips; baseline additionally brackets draw translation around quarter boundaries. Both cache states and original/scale1 draws remain explicit. Parsed fill metadata is not an AVM property readback.

200nativeimages/1843200RGBA;47840source pixels and100display matrices verified. Unchanged baselines reproduce r232 **73728/73728** pixels. All **436000/436000** geometry-common nearest samples retain compatible source codes; no incompatible output is removed from the denominator.

Seven global coordinate models all reject. Existing scaled-child/minimum gives409816/436000; the new combined-fill-and-child quarter hypothesis gives401594/436000 (maxRGBA delta2,12,0,0). The report retains every failure and all prior r229/r231/r232 evidence hashes. No offset is fitted from output.

Independent input-defined comparisons sharpen the rejection:

- 64draw pairs sharing toward-zero quarter units have **139520/139520** identical native pixels.
- The new model collapses104fill pairs to identical fixed coordinate rows, but102pairs differ natively (11270/144868 compared pixels). Quantizing combined fill+child translation discards observable distinctions. Both cache states remain in the report.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_fill_translation_controls --output /tmp/bvn-r233/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
# Capture fill0 through fill12 sequentially with capture_native_player.py.
python3 -m tools.probes.analyze_jinye_fill_consumption --native evidence/importer-loud-fail/r233/native --output /tmp/bvn-r233/analysis.json
python3 -m unittest tools.tests.test_jinye_fill_translation_controls tools.tests.test_jinye_fill_consumption_analysis
```

Focused9/9 and mandatory gates are recorded in acceptance.json/checks. FullPython1011pass/2skip retained from r227; exact axis controls retained from r229. No production/GPU changes or new roster/Web/54production run. Diagnostic complete coverage46/54; historical production9/54. AS/clip-action ownership remains open. Candidate/GPU/production admission false.

## Next discriminator

Separate footprint-phase order from translation without new coefficients: compare globally applying the proven display-inverse minimum-norm phase before inverse source-fill mapping against applying that nonlinear phase after composing the full inverse. Identity fills cannot distinguish these sequences; authored rotated fills can. Preserve separately constrained quarter draw consumption and exact raw fill twips. Reject both sequences against r232/r233 and all old nearest/smooth controls before admission. Never select a sequence from local RGB; add independent native factorization controls only if needed to distinguish the hypotheses.
