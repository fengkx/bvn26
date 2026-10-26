# r234: reject display-first footprint phase transfer

One independently defined phase construction: compute the admitted minimum-norm/ties-even offset from the display-only inverse, project its two components through the exact inverse-fill linear matrix, then ties-even round once to16.16. Retain each declared/legacy-quarter/scaled-quarter full inverse coefficient and translation unchanged. This tests nonlinear phase order; no local coefficient or RGB-selected sequence is introduced.

Pinned r232/r233 native captures are reused. Every old full-phase score, histogram and complete failure payload reproduces exactly, as do geometry point sets. All three global projected variants reject:

|Translation construction|r232 exact/18216|r233 exact/436000|
|---|---:|---:|
|declared|14383|347686|
|legacy child/draw quarters|13363|320342|
|scaled child then draw quarters|13419|321250|

Projected maxRGBA delta is2,6,0,0. The unchanged scaled/full-phase baseline remains17077/18216 and409816/436000. No projected construction qualifies for old nearest/smooth advancement. Phase-only transfer is insufficient; this does not identify a hidden allocation or precision stage.

## Reproduce

```sh
python3 -m tools.probes.analyze_jinye_factored_phase --native-fill evidence/importer-loud-fail/r233/native --output /tmp/bvn-r234/analysis.json
python3 -m unittest tools.tests.test_jinye_factored_phase_analysis
```

Focused3/3, mandatory gates in acceptance.json/checks. Prior exact axis controls retained at r229; fullPython1011pass/2skip retained at r227. No native recapture, GPU or production change. No new roster/Web/54production run. Diagnosticcomplete46/54, historicalproduction9/54. Candidate/GPU/production admission false; AS/clip-action ownership open.

## Next discriminator

Use independently representable synthetic source-tag controls to hold the complete bitmap-to-stage matrix and stage mask fixed while moving a predeclared dyadic linear factor S between fill and display: F'=S F, C'=C inverse(S), mask'=S mask. Prove equivalence from actual raw tag coefficients and display property readbacks, not requested matrices or RGB. Retain identical coordinate-coded bytes, both cache states, and explicit original Jinye counterexamples. Compare native images before adjusting arithmetic. A cache-state or factorization difference would constrain pipeline ownership without choosing a model from matching pixels.
