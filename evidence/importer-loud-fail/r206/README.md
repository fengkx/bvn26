# r206 — old scalar and ramp controls clear with explicit input readbacks

The unchanged r204 packed construction matches **24/24 scalar and2048/2048 ramp RGBA samples**, maxdelta0. Fresh native probes retain every original r11/r12 filtered-output event exactly; only unfiltered input readbacks and full matrix properties are added. Original vector geometry, filter API, opacity and output sampling remain unchanged. No reference is rewritten.

The old64px vector samples are interior paired pixels; the old2px vector uses the independently established rounded+expanded3px cache and scalar remainder. Actual premultiplied input bytes are retained, rather than guessed from80% opacity. The same construction already clears554400 RGBA boundary/control pixels in r204 and55296 all-alpha pixels in r205.

This clears the bounded CPU prerequisites for a **diagnostic GPU implementation**. It does not authorize production binding, arbitrary alpha-changing matrices or general overflow behavior. Main live GPU family remains10/12 until actually rerendered. Production54 historical9/54; production admission false.

[Full inputs/outputs](summary.json.gz), [scalar native](scalar/native.log.gz), [ramp native](ramp/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case color-arithmetic-input --output /tmp/matrix-legacy-scalar --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/build_flash_filter_probe.py --case color-arithmetic-ramp-input --output /tmp/matrix-legacy-ramp --ffdec /path/to/ffdec-cli.jar
# Capture each sequentially with capture_native_player.py and the pinned native player.
python3 -m tools.probes.analyze_matrix_legacy_inputs --scalar evidence/importer-loud-fail/r206/scalar --ramp evidence/importer-loud-fail/r206/ramp --output /tmp/matrix-legacy.json
python3 -m unittest tools.tests.test_matrix_legacy_inputs tools.tests.test_matrix_packed_candidate tools.tests.test_matrix_all_alpha_pairs
```

Next discriminator: port the bounded packed arithmetic into an isolated diagnostic shader at the actual FilterGroup matrix boundary. Require all explicit native rows and original buffers exact on GPU before rerendering the12-state main family; keep original texture decode, coverage, cache allocation, post-CXFORM and composition. Do not globally replace the production matrix shader from this CPU pass. Full AS ownership remains a separate blocker. Draft only.
