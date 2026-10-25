# r199 — processed-span origins and opaque neighbor RGB are independent controls

Apply the same authored ColorMatrix to explicit64-pixel source rows, processing widths1–9. Independently move sourceRect and destination starts0/1/3, retain each target byte, and compare same-color/green/black opaque neighbors versus transparent neighbors. All **110592 source pixels** are verified;1728 target observations and every output pixel are retained. Pixels outside the processed destination remain clear.

**192/192 origin groups are invariant** across all9 source/destination start combinations. **432/432 opaque-neighbor color groups are invariant** across three neighbor RGB choices. This rejects absolute storage-origin anchoring and neighbor-RGB dependence within these controls; neighbor alpha and processed width remain the distinguishing inputs. It does not prove arbitrary clipping, negative origins, larger spans or a hardware instruction.

[All observations and groups](summary.json), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case matrix-span-origins --output /tmp/matrix-span-origins --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-span-origins /tmp/matrix-span-origins/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 180
python3 -m tools.probes.analyze_matrix_span_origins --native evidence/importer-loud-fail/r199/native --output /tmp/matrix-span-origins.json
python3 -m unittest tools.tests.test_matrix_span_origins
```

Next discriminator: hold this independently controlled geometry fixed and capture single-channel byte ramps for each authored matrix coefficient, with the target opaque and its paired neighbor independently opaque/transparent. Retain full coefficient properties and input rows. Derive common arithmetic constructions from those controls, then reject against old scalar/ramp and original materialized buffers. Do not infer coefficient consumption from CXFORM's separate rules or combine per-channel outputs as though materialization commuted with the full transform.

All admission flags false. Main family10/12; identity2953 pixels,maxdelta1. Production54 historical9/54. Full AS ownership open. Full r197 Python944 pass+2skip retained; no production changes. Draft only.
