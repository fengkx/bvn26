# r44 — held-out amplified alphas reject common normalization sequences

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`.
The analysis exits **1**. No production/GPU code, row routing, native reference,
channel tolerance, coefficient lookup or per-pixel formula choice changed.

## Native experiment

Reuse the exact r43 width32 input/transform grid: requested RGB
`(117,120+x%16,240)`, gains2/4/8 with adjacent−1/256,0,+1/256,
centered negative offsets `−(gain−1)*128 + {-1,0,1}`, opacity33/67/100.
The alpha set is the47 old unit-space `estimate_quotient` rejections, including
14/135, plus the retained146/197/206/244: **51 alphas,4131 rows,132192 pixels**.
The alpha list is frozen in the checked-in AS source and checked against r43.
All inputs/results have transparent and black readbacks; source bytes, alpha,
order and completion are validated. The retained **10368/10368** source/output
pairs match r43 exactly.

Keeping the same grid at low alpha exposes input quantization: alpha7 has
**864** samples whose actual premultiplied input reaches green clipping under
the exact rational transform. All are retained and explicitly listed in
`analysis.json.gz`; no clipping samples are removed to improve scores. The other
**131328** samples remain strictly inside the rational clipping bounds. Alpha2
also demonstrates that a quantized output byte can be zero without the
prequantized transform being clipped. We do not use output-zero as a clipping
selector. The experiment does not claim all51 alphas are clamp-free.

## Independent arithmetic measurements

`cxform_input_normalization.c` measures, for every byte1–255, the binary32 input
normalizations and reciprocal estimates independently of native pixels:

1. `f(c/255)` and `E(f(a/255))`;
2. `f(c*f(1/255))` and `E(f(a*f(1/255)))`;
3. `f(c*E(255))` and `E(f(a*E(255)))`.

Here `f` is binary32 rounding and `E` is the independently measured reciprocal
estimate. The helper is compiled for x86_64 with contraction disabled and run
under Rosetta; source/executable/output hashes and commands are pinned in
`normalization-environment.json`. These are mathematical comparators, not claims
about Flash's ISA or SIMD implementation.

Direct evaluation retains the normalization rounding before multiplying by the
alpha reciprocal. It then applies the green/RGB multiplier, offset divided by255,
clamp, and the three existing alpha/opacity multiplication orders. These direct
sequences are **not assumed equivalent** to factorizing one common coefficient
`f(normalizer*reciprocal)`. Factorized candidates are checked separately against
all old coefficient intervals; direct sequences are checked against all actual
old RGB controls instead of misusing those intervals as an equivalence proof.

## Intersections and exact failures

All old bounds remain; every new bound has a native witness. Combined RGB
constraints increase **661248→1057824**. All three combined space models retain
255 nonempty intersections, but none of the seven old or three additional
factorized common constructions satisfies every interval.

Unit-space coverage for the seven old constructions is now
**50,107,119,208,46,107,179 /255**, respectively. In particular, the previously
locally exact quotient construction remains only208/255. The added factorized
divide/rounded-multiply/estimated-multiply constructions give208/208/179 of255.
The maximum coverage in the other spaces is209/255, still rejected.

Direct normalization sequences (RGB channels, not image counts):

| Sequence | Old exact /661248 | New exact /396576 | Max delta |
|---|---:|---:|---:|
|divide|645182|391172|1|
|multiply rounded1/255|645181|391174|1|
|multiply estimated1/255|640282|391434|1|

All three alpha/opacity orders give the same scores and predictions for these
sequences on these controls. This is not proof of a general operation order.
Every mismatch remains a failure; no new sequence is admitted.

The first two normalization paths **are distinguishable**: one old channel and
46 new channels differ between them. Native observations do not select one path
universally. Examples with the actual premultiplied green input:

| Native row/x | Alpha | Green | Multiplier | Offset | Opacity | Native | Divide | Rounded multiply |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1291/13|49|26|2049/256|−896|67|23|23|24|
|1367/0|51|24|8|−895|100|12|12|13|
|3602/9|204|103|4|−385|100|104|103|104|

At these alphas, both normalizations produce the **same measured reciprocal
bits**; source normalization differs by one binary32 step. Thus these examples
isolate input normalization within the tested sequences, not a change in their
reciprocal estimate. Opposite local matches do not authorize switching formulas
by alpha or pixel. `normalization_discriminators` records all witnesses and
occurrence counts. Grouped mismatch records retain first coordinates, exact
operands, native/actual bytes and multiplicity; raw traces retain every coordinate.

## Reproduction and regressions

```sh
python3 tools/probes/build_flash_filter_probe.py --case cxform-amplified-rejected \
  --output /tmp/r44-native --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py /tmp/r44-native \
  /tmp/r44-native/native.log --player-app "$FLASH_PLAYER" --allow-window-activation
python3 -m tools.probes.analyze_cxform_rejected \
  --root evidence/importer-loud-fail/r44 \
  --output /tmp/r44-analysis.json.gz  # expected exit 1
python3 -m unittest tools.tests.test_cxform_rejected
python3 -m unittest discover -s tools/tests
```

`provenance.json` pins analysis/source/reference hashes. Fresh checks are archived
in `checks/` and `acceptance.json`: Python606 tests (604 passed,2 skipped);
cache/build-manifest26/26, fingerprint8/8, protected, integrity, handoff and
contracts pass. r36 composition4032/4032 and complete Yulong4/4, r37 nested
124416/124416, leaf6/6 (69120), isolated Glow4/4, GPU sampler71824/71824 and
CPU sampler regressions remain exact. Existing Python tests retain scalar3072,
three-alpha25920 and both held-out span8652 controls. Full roster replay and
Web export were not rerun for this probe-only change.

## Remaining blocker

No common construction/sequence clears the old controls, so no new candidate is
advanced to the pinned filter buffers or GPU. Historical native-buffer result
remains43006/43200 and GPU nested-filter remains67774/72576. Production components
remain historical9/54; full AS/clip-action ownership is a separate merge blocker.

The next useful controls are adjacent source green bytes at the distinguishing
49/51/204 sites, retaining the same transform and row geometry, with independently
varied input alpha. Retain explicit source readbacks and compare fixed operation
sequences globally; do not choose the locally matching normalization. The current
measurement separates two input paths but still does not explain Flash's common
reciprocal/operation construction.

Draft only; no production admission, merge, deployment or Worker change.
