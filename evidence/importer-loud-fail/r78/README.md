# r78 — crossed shadow parameters expose two remaining arithmetic boundaries

1620 fresh native explicit DropShadow cases cross multi-pass blur with signed fractional offsets, non-unit filter alpha and fractional/saturating strength. The source and separate Blur buffers remain exact, while final composition rejects the current common operation sequence.

| Gate | Exact RGBA samples |
|---|---:|
| Source inputs | **207360/207360** |
| Independent Blur controls | **207360/207360** |
| Composition using observed alpha property | **190396/207360** |
| Negative control using requested alpha | 181008/207360 |
| Old phase / sweep / tie impulses | **48/48 +520/520 +48/48** |

The16964 observed-property composition failures have maximum channel delta3. No GPU/production arithmetic changed; **bounded_cpu_passed=false, production_admitted=false**. The requested-value negative control is not a competing admitted model.

## Independent observations

- Filter alpha properties do not retain the requested0.5/0.75: native getters report0.498039215686275 and0.749019607843137, corresponding to127/255 and191/255. The analysis validates the serialized getter values, uses their exact byte fractions and retains the requested values separately. It does not select coefficients from RGB.
- At unit filter alpha/strength, four offset groups remain4608/4608 exact each. Only the direct negative-distance half-phase `angle0, distance−0.501953125` rejects: **4492/4608**,116 failures. Older616 impulse controls still pass, so replacing their phase rule would be premature.
- Non-unit gain/alpha also rejects at zero distance. Therefore offset timing alone cannot explain all failures. Source readbacks and independent blurred pixels are already exact; neither source raster nor CXFORM compensation is appropriate.

Controls use kernels3.99609375/7.99609375/8.25; source alphas25/135; constant/impulse/ramp inputs; quality1/3; offsets(0,0),(45,0.375),(45,−0.375),(0,−0.501953125),(135,1.25); filter alpha0.5/0.75/1 and strength0.75/1/2.5. Actual blur/quality/alpha/strength/angle/distance properties are recorded. Central row/column sampling counts the shared center twice. The separate Blur operation is not claimed to read a hidden native shadow buffer.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case shadow-crossed-parameters \
  --output /tmp/bvn-r78/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r78/native /tmp/bvn-r78/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_shadow_crossed_parameters \
  --native evidence/importer-loud-fail/r78/native --output /tmp/bvn-r78/analysis.json
python3 -m unittest tools.tests.test_shadow_crossed_parameters
```

[Readable partitions and deltas](summary.json), [all exact comparisons/counterexamples](analysis.json.gz), [native readbacks](native/native.log), [hashes](provenance.json), [checks](acceptance.json). Analysis exits after writing its rejected result; it is not a production admission gate.

Next discriminate direct negative distance versus positive distance with reversed angle, and explicit applyFilter versus a filtered bitmap display object, using no blur/unit gain and the same input bytes. Separately isolate zero-offset gain/alpha with unblurred byte ramps and retained original/source-hidden outputs before testing fixed quantization/operation sequences. Keep the old phase references unchanged; do not splice a locally matching phase or gain formula.

No new GPU render. Prior r74/r75/r77 graphical controls remain pinned regressions. Components remain historical9/54; full AS/clip-action ownership and general production rendering eligibility remain open. Full roster/Web and54 components were not rerun. Draft only; no merge/deploy/Worker.
