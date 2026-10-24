# r74 — actual bounded GPU filter path clears the pinned extent controls

The common six-significant-bit kernel consumption now runs in an isolated actual FilterGroup diagnostic. Authored source bounds, metadata, integer buffer extents and CXFORM arithmetic are unchanged. The blur shader decodes texture bytes, accumulates integer weights in units of1/64, then performs integer division; **no epsilon or channel tolerance** is used in this new blur path.

| GPU/native stage | r70 exact | r74 exact |
|---|---:|---:|
| Input | 115840/115840 | **115840/115840** |
| Filtered before CXFORM | 115596/115840 | **115840/115840** |
| Final | 115678/115840 | **115840/115840** |

All724 cases reuse unchanged native r62/r66/r68/r69 rows. The244 filtered and162 final differences disappear. Twelve batches assert actual buffer sizes, origins and pass counts; each blur pass reads back its consumed kernel and direction, checked independently against the Python construction. Glow composition retains the unchanged existing shader; blur passes use the new diagnostic integer shader. A preliminary run with consumed operands and the old floating shader also passed, but the archived final gate is the integer implementation, which does not rely on the old blur epsilon.

This gate covers integer-origin bounded single-pass Glow cases only. It does **not** prove multi-pass ordering, arbitrary clipped/affine placement or a global production binding. `production_admitted=false`; all new Godot code is under `godot/tests/`.

## Reproduce

```sh
python3 -m tools.probes.run_consumed_extent_gpu --godot /path/to/Godot \
  --output /tmp/bvn-r74/render
python3 tools/probes/run_filter_regressions.py --godot /path/to/Godot \
  --output /tmp/bvn-r74/regressions
python3 -m unittest tools.tests.test_consumed_extent_gpu
```

[Exact comparison](render/comparison.json), [lossless GPU rows and operands](render/rows.json.gz), [source/native hashes and commands](render/provenance.json), [acceptance](acceptance.json). All batch fixtures/logs are under `render/batches/`.

## Fresh independent regressions

Normal composition4032/4032; explicit nested composition124416/124416; complete Yulong diagnostic4/4; bound leaf6/6; isolated Glow4/4; GPU sampler71824/71824; CPU sampler suites pass. The stale-copy negative control remains a failure. [Commands and exits](regressions/exits.json), [complete fresh readbacks/logs archive](regressions/readbacks.tar.gz). These are unchanged diagnostic gates, not global production admission. No new Flash capture; pinned native sources are reused.

Next put the grouped-axis construction through actual multi-pass buffer nodes using the r73 native controls, then measure Glow/DropShadow multi-pass independently. The production alternating-axis mismatch exposed by r73 remains unfixed. Do not widen eligibility merely because the single-pass path is exact.

Components remain historical9/54; full AS/clip-action ownership and general coverage/affine/production eligibility remain open. Full roster/Web export and54 components were not rerun because production is unchanged. Draft only; no merge/deploy/Worker.
