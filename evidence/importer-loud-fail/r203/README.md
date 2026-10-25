# r203 — independent output offsets split coefficient plateaus

Retain27 independently read-back coefficient brackets, ten explicit source bytes, both pair-alpha contexts and nine fixed quarter-byte offsets from−1 to1. All19440 source pixels verify; all4860 G/B/A target identity outputs are exact. The540 zero-offset cases exactly retain r202's source, properties and full output rows.

**56 coefficient-pair equivalences** seen at zero offset split when offsets vary. A zero-offset plateau alone therefore cannot establish identical consumed coefficients. All earlier shared arithmetic candidates reject; best4580/4860 target reds. [Full cases and equivalences](summary.json.gz), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case matrix-offset-brackets --output /tmp/matrix-offset-brackets --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-offset-brackets /tmp/matrix-offset-brackets/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 120
python3 -m tools.probes.analyze_matrix_offset_brackets --native evidence/importer-loud-fail/r203/native --prior evidence/importer-loud-fail/r202/native --output /tmp/matrix-offset-brackets.json
python3 -m unittest tools.tests.test_matrix_offset_brackets
```

Next discriminator: independently inspect and pin the installed player's matrix-conversion and byte-arithmetic instructions before another fitted arithmetic experiment. Static locations0x100016830 (coefficient/offset preparation),0x100017c5c (packed coefficients),0x100017d70 (paired input/term products),0x100018030 (remainder) and0x1001f3d9a (integer reciprocal table initialization) supply a testable construction. Record exact constants/bytes and distinguish static evidence from verified runtime invocation. Reject that construction against all r200–r203 controls, original materialized RGBA boundaries and retained geometry controls before any GPU admission.

All admission flags remain false in this evidence round. Main family10/12; identity2953 pixels,maxdelta1. Production54 historical9/54; full AS ownership open. No production runtime or source-reference changes.
