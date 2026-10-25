# r201 — binary coefficients expose, but do not admit, input-center arithmetic

Use explicit opaque green byte ramps, red output from green, and binary-exact coefficients -2/-1/-0.5/0/0.25/0.5/1/2/4. The enclosing matrix remains nonidentity even for coefficient1. Neighbor alpha is independently0/255; negative coefficients use offset128. All18432 input pixels and all20 matrix properties are verified. All4608 G/B/A identity outputs remain exact.

With an opaque neighbor, ordinary nearest byte multiplication is exact2304/2304. With a transparent neighbor, coefficient2 gives red1 for source0 and coefficient4 gives red2; coefficient1 copies the full ramp exactly. These reject plain byte multiplication. Adding half an input byte before the multiply explains many changes, but fails255 coefficient1 cases (4353/4608 overall); it is **not admitted**. No epsilon or special identity branch is introduced.

Cross the half-input candidate with all r200 nonbinary ramps using shared fixed8–16 nearest-even coefficient precision. Best is fixed11,4602/4608; all six counterexamples are retained. Its opaque subset is exact2304/2304, but this is not an independent proof of coefficient consumption and does not authorize a precision rule or context selector. Neither the new binary controls nor original materialized native buffers are cleared by one common construction. All admission flags remain false.

[Full rows and rejection scores](summary.json.gz), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case matrix-binary-pairs --output /tmp/matrix-binary-pairs --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-binary-pairs /tmp/matrix-binary-pairs/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_matrix_binary_pairs --native evidence/importer-loud-fail/r201/native --prior evidence/importer-loud-fail/r200/native --output /tmp/matrix-binary-pairs.json
python3 -m unittest tools.tests.test_matrix_binary_pairs
```

Next discriminator: bracket coefficient1 and exact binary half-product boundaries with independently read-back coefficients at1/2048 and finer spacing, retaining full ramps and both alpha contexts. Compare copy-like behavior with adjacent consumed coefficients, and distinguish coefficient conversion from final byte rounding. Do not infer a bypass from coefficient1 alone or pick coefficients from observed output. A candidate must clear r200, r201, original materialized buffers and old scalar/ramp controls simultaneously before GPU advancement.

Main family10/12; identity2953 pixels,maxdelta1. Production54 historical9/54. No production changes; full AS ownership remains open; draft only.
