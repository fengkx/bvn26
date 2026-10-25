# r141 — animated Lanran native cache boundaries preserve original clocks

Lanran640/frame732/depth32→sprite13 is a nine-frame animation, so the existing static boundary builder correctly rejects it. Its guard remains unchanged. A separate animated harness retains the original observation ticks0/4/8/11 and the original parent-frame change at tick10. It records authored/clear/cache images in the same frame, restores filters/cache state, and asserts the child frame did not advance during mutation.

All **24/24 original clock records** through tick11 match. All four authored images reproduce the original pinned full54 images **960000/960000 pixels**. Measured cache equals clear **960000/960000**; unchanged Blur0×10 quality1 applied to measured cache reproduces authored **960000/960000**. This isolates source-input reconstruction without treating an animation as a static clip.

[Summary](summary.json) retains clocks, before/after properties, matrices and restored frames; native capture and all boundary PNGs remain under `native/` and `images/`. [Provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_animated_component_boundaries --cases evidence/importer-loud-fail/r21/components/lanran/cases.json --case lanran-640-732-32 --output /tmp/lanran-boundaries --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/lanran-boundaries/components/lanran /tmp/lanran-boundaries/components/lanran/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_animated_component_boundaries --native evidence/importer-loud-fail/r141/native --output /tmp/lanran-boundary-analysis
python3 -m unittest tools.tests.test_animated_component_boundaries
```

Next discriminator: source-extract all nine frames and original replacement placement fields, retain active/inactive fill slots and matrices, then select source leaves using independently verified native frame clocks. Unknown action/display fields must reject. Compare raw source reconstruction before adjusting filter arithmetic.

`source_derived_input_verified=false`, `production_admitted=false`. Eight source-backed original live diagnostic images remain exact; historical production54 remains9/54, not rerun. Full AS/clip-action ownership and general affine/coverage remain open. Draft only; no merge/deploy/Worker.
