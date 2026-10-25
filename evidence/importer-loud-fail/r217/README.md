# r217 — original coefficient-preserving widths isolate the final partial row group

Original JPEG3 baseline readbacks remain **70308/70308 unchanged**. Six opaque JPEG2 controls preserve every original byte except the two-byte declared SOF width, retaining the same MCU count. Original39367 opaque pixels exactly match the same-width JPEG2 control; hidden RGB is now independently observable.

| Width | Candidate exact pixels | Native overlap versus width192 |
|---|---:|---:|
|184|69552/69552|69552/69552|
|185|69895/69930|69895/69930|
|186|70231/70308|70231/70308|
|187|70575/70686|70575/70686|
|188|70937/71064|70937/71064|
|192|72576/72576|baseline|

Every residual is in x184..width−1, maximum delta1. All have Y0 in this source; r216 independently showed that Y0 alone does not cause a difference. The geometry evidence isolates a partial-row group; it does not establish SIMD implementation or justify an output-selected path.

[Complete coordinate/native-overlap comparisons](summary.json.gz), [unchanged entropy/header provenance](native/build.json), [native readbacks](native/native.log.gz), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_jpeg_edge_widths --output /tmp/jpeg-widths --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jpeg-widths /tmp/jpeg-widths/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jpeg_edge_widths --native /tmp/jpeg-widths --dump /tmp/jpeg-planes --output /tmp/jpeg-width-analysis
```

Next discriminator: independently encoded constant YCbCr controls at widths7/8/9,15/16/17,23/24/25, varying Y/chroma and subsampling. Compare whole-row fixed group-size hypotheses and contribution-floor versus nearest-total arithmetic. A route must derive from geometry alone and retain all original/old controls; never choose from observed RGB. Production remains false, original four residuals not cleared, AS ownership open. Draft only.
