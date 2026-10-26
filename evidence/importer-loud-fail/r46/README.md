# r46 — fractional offset consumption explains contradictory bounds

No production or GPU implementation changed. Both raw and adjusted diagnostics
retain `candidate_admitted=false`, `gpu_advance_allowed=false`,
`production_admitted=false`; analysis exits **1**. No epsilon, tolerance,
per-alpha/pixel splice or interval-derived coefficient is used.

## Fixed-source multiplier/offset brackets

Select the union of r45's target counterexamples under the three fixed sequences,
plus all center/neighbor alpha controls (`delta_green=0`), deduplicated by actual
source RGBA and site: **48 sources**. This selects diagnostic inputs only, not a
rendering rule. The exact selection is frozen in the AS fixture and checked
against pinned r45 evidence. No counterexample source is discarded.

Each source retains its entire32-pixel input row, clip, transform geometry and
opacity. The source BitmapData is allocated once and reused for all25 draws.
Every draw reads back the full source/result on transparent and black destinations.
All48 sources use one common5×5 grid:

- multiplier changes `{−2,−1,0,1,2}/256`;
- offset changes `{−256,−1,0,1,256}/256`, i.e.−1,−1/256,0,+1/256,+1.

There are **1200 target pixels,38400 row pixels**. Every source readback matches
r45 exactly; all centered transforms match **1536/1536** native row pixels.
No new bracket sample reaches rational green clipping. Center and neighboring
alphas remain independently represented at all three sites.

## Native-only offset observation and independent confirmation

For every fixed source/multiplier, compare whole native rows without any candidate
math. At the negative integer offsets used by the brackets:

- offset−1/256 equals the integer-center draw: **7680/7680 RGBA**;
- offset+1/256 equals the integer-center+1 draw: **7680/7680 RGBA**.

Keeping the fractional offset in the old arithmetic makes19 bracket-alpha
intervals empty: no reciprocal coefficient can satisfy all those observations.
This points to an incorrect offset-consumption premise, not just reciprocal
precision. The contradiction remains recorded rather than widening intervals.

The separate `cxform-offset-fractions.as` control uses alphas49/51/135/204/255,
constant input RGB(117,128,240), width32 and enclosing nonidentity red/blue
transforms. Green multiplier1 and offsets
`{−513,−512,−511,−257,−256,−255,−1,0,1,255,256,257,511,512,513}/256`
independently cover both signs. It records `cxform.greenOffset*256` after draw.
The property retains the supplied fraction in all75 rows, but the draw result
matches its integer-toward-zero offset control in **2400/2400 RGBA pixels**.
Thus the property is not overwritten with an integer; these controls constrain
consumption by this long-row BitmapData.draw path. They do not prove a universal
rule for every Flash rendering/CXFORM API or scalar path.

## Uniform diagnostic rule and global rejection

Evaluate one common change: truncate the offset toward zero before the existing
arithmetic sequence. Apply it to every control, never by alpha, source byte or
observed output. Old controls all have integer offsets, so their inputs, bounds
and sequence predictions remain unchanged. Independent signed controls and all
bracket RGB channels are included; combined constraints now total **1224288**:
1101888 retained +115200 bracket +7200 signed-offset channels.

Including signed controls, the raw fractional-offset model has21 empty combined
alpha intervals in each space. The uniform integer-offset diagnostic removes
**all** empty intervals across the nine green space/order models and three
combined RGB models while retaining every old bound.

| Fixed normalization sequence | Bracket target exact, raw→integer offset /1200 | New RGB exact, raw→integer offset /122400 |
|---|---:|---:|
|divide|1051→1156|116989→120594|
|multiply rounded1/255|1050→1154|116980→120576|
|multiply estimated1/255|1016→1128|115979→119920|

All remaining differences are still hard failures, maximum channel delta1.
The best target result still has44 counterexamples. Alpha/opacity operation
orders remain indistinguishable on these controls. The unit combined interval
coverage for the seven old common constructions after the uniform offset rule is
**50,105,118,208,46,105,177 /255**; no space exceeds209/255. The three factorized
normalization constructions also fail globally. No coefficient is taken from a
feasible interval and no locally matching path is selected.

`analysis.json.gz` retains the disproved raw model, adjusted diagnostic,
contradictory native bound witnesses, signed controls and exact remaining
counterexamples. `cxform_control_analysis.py` centralizes the shared interval and
sequence comparison for these new probes; earlier analyzers/references are
unchanged.

## Reproduction and regressions

```sh
python3 tools/probes/build_flash_filter_probe.py --case cxform-transform-brackets \
  --output /tmp/r46-native --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py /tmp/r46-native \
  /tmp/r46-native/native.log --player-app "$FLASH_PLAYER" --allow-window-activation
# Build/capture cxform-offset-fractions similarly into a separate directory.
python3 -m tools.probes.analyze_cxform_brackets \
  --root evidence/importer-loud-fail/r46 \
  --output /tmp/r46-analysis.json.gz  # expected exit 1
python3 -m unittest tools.tests.test_cxform_brackets
python3 -m unittest discover -s tools/tests
```

Native sources/build/SWF hashes, complete lossless traces and player environment
are under `native/` and `offset/`; analysis/reference hashes are in
`provenance.json`. Four new tests enforce fixed source/grid/centered-row retention,
signed fractional property versus integer draw consumption, all inherited bounds
and raw/adjusted native witnesses, and rejection of still-failing common sequences.

Fresh checks are archived in `acceptance.json` and `checks/`: Python614 tests
(612 passed,2 skipped); caches26/26, fingerprint8/8, protected, integrity,
handoff and contracts pass. r36 composition4032/4032 and pinned Yulong4/4,
r37 nested124416/124416, leaf6/6 (69120), isolated Glow4/4, GPU sampler71824/71824
and CPU sampler regressions remain exact. Existing Python tests retain scalar3072,
three-alpha25920 and both held-out span8652 controls. Full roster replay and Web
export were not rerun for this diagnostic-only change.

## Remaining blocker and next experiment

The bounded offset-consumption rule is independently supported; the common
reciprocal/input-normalization sequence remains unresolved. A next discriminating
control can bracket the multiplier more finely than1/256, explicitly reading its
property while holding source bytes and now-integer offsets fixed. Retain both
center and neighboring alpha controls and compare globally; do not infer the
multiplier's storage/consumption precision from the offset result.

No new candidate advanced to the native filter-buffer or72576 GPU gate.
Historical results remain native-buffer43006/43200, nested GPU67774/72576 and
production components9/54. Full AS/clip-action ownership remains separately open.
Draft only; no production admission, merge, deployment or Worker changes.
