# r198 — changing only neighbor alpha changes a fixed target's matrix result

Keep target RGBA and the full authored matrix fixed. Independently vary three neighboring alphas, lane, group start and row widths4/8/16/17/33/223. All **2048 target source readbacks are exact**, and every source/output lane is retained. The256 groups each compare8 masks with identical target bytes.

**92/256 groups change target RGB when only neighbor alpha changes.** All92 use neighbors toggled0/255; none of the0/127 groups changes. For target(160,128,8,255), outputs include(58,148,231,255) and(58,149,231,255); the second target similarly changes by1. This independently rejects a pointwise RGBA-only rule.

The observations suggest adjacent-pair opacity handling within a whole-four-pixel prefix, with different treatment in the row remainder. That is a hypothesis, not an admitted partition or inferred hardware instruction. A naive paired-neighbor-only hypothesis misses144/2048 targets in remainder contexts. No lookup table or RGB-selected route is shipped, and no arithmetic construction is admitted.

[All target/neighborhood observations](summary.json), [complete native rows](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case matrix-neighbor-alpha --output /tmp/matrix-neighbor-alpha --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-neighbor-alpha /tmp/matrix-neighbor-alpha/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 180
python3 -m tools.probes.analyze_matrix_neighbor_alpha --native evidence/importer-loud-fail/r198/native --output /tmp/matrix-neighbor-alpha.json
python3 -m unittest tools.tests.test_matrix_neighbor_alpha
```

Next discriminator: independently move sourceRect and destination origins while retaining the same explicit target and neighbor bytes, sweep short processed widths1–9, and vary opaque neighbor RGB. Determine whether pairing is anchored to source storage, destination storage or the processed span, and whether neighbor color also matters. Keep original materialized buffers and old scalar/ramp controls as rejection gates before any common arithmetic model or GPU change.

`arithmetic_admitted=false`, `partition_admitted=false`, `production_admitted=false`. Main family10/12,2953 identity pixels differ,maxdelta1. Production54 historical9/54; AS ownership open. Draft only.
