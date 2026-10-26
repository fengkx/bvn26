# r216 — low-luma special treatment rejected by independent constants

448 independently encoded16×16 constant YCbCr controls vary Y0/1/2/3/16/127/254/255, Cb129..135, Cr131..134 and4:4:4/4:2:0. Every decoded component byte is checked against the independently authored constant. Native reads every RGB pixel. The unchanged r213/r215 construction clears **114688/114688 pixels**.

The four original JPEG3 residual colors are included. A low-Y correction would regress these controls; none is added. The original image remains70304/70308, four max-delta1 failures. No production decoder admission.

[Input provenance](native/build.json), [native RGB](native/native.log.gz), [decoded constants, plane hashes and comparisons](summary.json.gz), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_jpeg_low_luma --output /tmp/jpeg-low --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jpeg-low /tmp/jpeg-low/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jpeg_low_luma --native /tmp/jpeg-low --dump /tmp/jpeg-planes --output /tmp/jpeg-low-analysis
```

Next discriminator: keep original JPEG coefficient/entropy bytes fixed and vary only declared SOF widths within the same final MCU count (184/185/186/187/188/192), using explicit opaque JPEG2 controls to expose formerly hidden RGB. Retain the unchanged original JPEG3 as a separate baseline. Compare overlapping edge coordinates and independently decoded planes; distinguish partial-edge reconstruction from image-wide conversion. No reference replacement or edge-coordinate patch. Productionfalse; diagnostics36/54, production historical9/54; AS open. Draft only.
