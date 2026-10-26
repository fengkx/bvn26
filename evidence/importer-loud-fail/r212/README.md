# r212 — grayscale IDCT exact; independent color conversion and chroma gaps

Six global decoder configurations are compared against16 independently encoded32×32 native bitmap readbacks (16384 original pixels). Source RGB/gray construction, encoded JPEG hashes, quality/subsampling and encoder version are pinned; every native pixel is retained.

Accurate integer IDCT clears all four grayscale controls: **4096/4096 exact**. Fast IDCT and floating IDCT have counterexamples, including grayscale, so they cannot replace it globally. All four constant-color controls fail every configuration by1 channel even without subsampling: native[72,128,210] vs default[72,127,210]. Thus color conversion itself remains a separate gap. Unsubsampled ramps differ by up to2;4:2:0 boundaries/ramps differ by up to81 with accurate IDCT depending on upsampling. Neither standard fancy nor simple upsampling is admitted.

[All counts](counts.log), [complete coordinate counterexamples](summary.json.gz), [input provenance](native/build.json), [native bytes](native/native.log.gz), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_jpeg_controls --output /tmp/jpeg-controls --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jpeg-controls /tmp/jpeg-controls/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jpeg_controls --native /tmp/jpeg-controls --djpeg /path/to/djpeg --output /tmp/jpeg-control-analysis
```

Next discriminator: obtain decoded Y/Cb/Cr plane bytes independently with accurate integer IDCT, bypassing libjpeg color conversion. For unsubsampled controls, compare globally fixed documented YCbCr operation sequences (including separately truncated channel contributions) against explicit native RGB. Keep subsampling out of that first comparison, then separately recover chroma placement from the boundary control. No coefficient fitting or output-selected sequence. Original JPEG3 and every old control remain rejection gates. Production remains false; component diagnostics36/54, historical production9/54; AS ownership open. Draft only.
