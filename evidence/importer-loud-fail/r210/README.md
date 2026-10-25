# r210 — original Orochimaru JPEG3 decoding is not exact

The native probe embeds the **unchanged original DefineBitsJPEG3 tag340**, exports it by linkage name and reads BitmapData.loadBitmap directly. No geometry, sampling, filter, opacity or display placement is involved. Both getPixel32 and compositing over black are retained for every original pixel; all70308 alpha bytes exactly match the source alpha stream.

Pillow12.3.0/libjpeg-turbo3.1.4.1 default decoding matches **37022/70308 RGBA pixels**, with33286 mismatches and maximum RGB delta19. Alpha is binary:30941 transparent,39367 opaque. Thus this independently measured input mismatch cannot be explained by filter math or fractional coverage. No decoder is admitted and no reference-rendered texture is substituted.

[Per-coordinate differences](summary.json.gz), [native readbacks](native/native.log.gz), [original tag and executable build provenance](native/build.json), [acceptance](acceptance.json). This is diagnostic only. Production count remains historical9/54; source-backed complete diagnostics remain36/54; production_admitted=false.

```sh
python3 -m tools.probes.build_original_jpeg_probe --output /tmp/orochimaru-jpeg --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/orochimaru-jpeg /tmp/orochimaru-jpeg/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_original_jpeg --native /tmp/orochimaru-jpeg --output /tmp/orochimaru-jpeg/summary.json
```

Next discriminator: independently compare libjpeg's documented whole-image integer/fast/float IDCT and fancy/simple chroma-upsample settings against these same bytes. Record JPEG component subsampling and decoder executable/version. Each setting is a single global construction, never a per-pixel route. Only exact source decoding can advance this component to sampling/filter diagnostics. Preserve old exact suites; AS ownership remains separate. Draft only; no merge/deploy/Worker.
