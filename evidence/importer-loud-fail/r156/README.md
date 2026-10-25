# r156 — explicit removal/Stop ownership in bounded component graphs

The previous static/animated rectangle diagnostic correctly rejected RemoveObject2. A separate bounded extractor now records removal as an empty display slot and clears inherited placement state. It decodes AVM1 Stop opcode07 followed by End00 into an explicit frame control. Unknown actions/fields still reject with source locations; no hash exception or silent removal skip.

Original main297 has17 frames/eight leaves, removes depth1 and stops at frame17. Original Yijiao298 has50 frames/six leaves, removes depth1 at13 and remains empty through50 before looping. Compiled natural playback matches **404/404 original native clocks** across three main cases and one Yijiao case. Full wrapper XML, placement records and fill tables remain in compressed fixtures. Negative tests reject Play opcode06 and unowned removal depth2.

All source bitmaps are retained with encoding and sampling metadata. Main uses fill67 (clipped unsmoothed); Yijiao uses fill65 (clipped smoothed). The prior smoothed renderer must not consume main's fill as though it were65. **No new sampler is admitted** by this inventory.

[Main graph](main-summary.json), [Yijiao graph](yijiao-summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_rect_control_graph --fixture evidence/importer-loud-fail/r156/main-fixture.json.gz --output /tmp/main-controls.json
python3 -m tools.probes.analyze_rect_control_graph --fixture evidence/importer-loud-fail/r156/yijiao-fixture.json.gz --output /tmp/yijiao-controls.json
python3 -m unittest tools.tests.test_rect_control_graph
```

Next discriminator: capture original authored/clear/cache boundaries of the two ColorMatrix graphs with complete20-coefficient property readbacks and original clock/restoration checks. Preserve empty frames. Only after isolating input differences should nearest sampling or matrix arithmetic be changed. Full AS/clip-action ownership remains incomplete; these are bounded diagnostic consumers, not a production AS engine.

`diagnostic_clock_exact=true`, `full_as_ownership_proved=false`, `production_admitted=false`. Production unchanged; Draft only; no merge/deploy/Worker.
