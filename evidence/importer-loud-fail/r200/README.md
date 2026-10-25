# r200 — single-coefficient ramps reject ordinary byte multiplication

Capture all256 input bytes for each of the nine authored RGB coefficients, with an opaque target and independently opaque/transparent adjacent pixel. The processed row is4 pixels; negative coefficients use offset128 to retain unclamped evidence. All20 matrix properties and all source/output pixels are retained. **18432/18432 explicit source pixels** verify; target G/B/A identity channels remain exact in **4608/4608** cases.

The tested shared constructions use stored float32 or fixed8/9/10/16 coefficient precision (truncate/floor/even), followed by floor/nearest or explicit float32 multiply/add. Every construction rejects. Best red-channel scores are **2285/2304** with opaque neighbor and **1803/2304** with transparent neighbor (both fixed16/even/nearest). These are rejection scores, not admitted quantization or an explanation of the context switch. Full counterexamples are retained in [summary](summary.json.gz); no output-dependent route is selected.

[Native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case matrix-coefficient-pairs --output /tmp/matrix-coefficient-pairs --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-coefficient-pairs /tmp/matrix-coefficient-pairs/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_matrix_coefficient_pairs --native evidence/importer-loud-fail/r200/native --output /tmp/matrix-coefficient-pairs.json
python3 -m unittest tools.tests.test_matrix_coefficient_pairs
```

Next discriminator: independently constrain input-byte conversion under the same pair-alpha geometry. Use binary-exact single-channel multipliers (including identity and half/double) plus fixed integer offsets, keeping enclosing matrix nonidentity and original source readbacks. Compare operation sequences globally against these nine nonbinary coefficient ramps and original materialized buffers; do not infer ColorMatrix operand rules from CXFORM, fit coefficients to intervals, or assume separate materializations commute.

Arithmetic/GPU/production admission stays false for this path. Main family10/12, identity2953 differing pixels,maxdelta1; production54 historical9/54. Prior exact controls remain unchanged; full AS ownership open. No production change, merge, deployment or Worker operation.
