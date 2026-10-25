# r86 — external PNG loading is not the constructor/leaf premultiplication path

A fresh native `MovieClipLoader` loads the exact retained RGBA PNG, then identity `BitmapData.draw` materializes it. The encoded image contains196608 pixels: every alpha/color byte pair in each varying RGB channel, with independent constant companion channels. PNG has no gamma/ICC metadata. Loaded size, scales and opacity are read back. Every original decoded PNG byte and every native alpha byte is exact: **196608/196608**.

| Global construction | Exact RGBA | Max channel delta |
|---|---:|---:|
| `c*(a+1)//256` (small Yulong leaf hypothesis) | 21839/196608 | 1 |
| nearest `c*a/255` (BitmapData constructor hypothesis) | 9806/196608 | 2 |
| floor `c*a/255` | 68472/196608 | 1 |
| Opaque identity, otherwise floor `c*a/256` | **196608/196608** | 0 |

The last construction is an **exploratory candidate**, not admitted. Full-opacity PNG bytes remain unchanged; partial-alpha bytes match integer product/256. It is one common arithmetic expression with the independently observable opaque boundary, not per-color/alpha coefficients. These observations currently combine PNG loading, display-object identity draw and black-background premultiplied readback. They do not locate which internal boundary consumes the bytes.

No old reference is rewritten: the102-texel Yulong leaf originated from an authored SWF bitmap/export pipeline and remains exact in its own gate. External PNG loading cannot be substituted for that path based on this experiment. Likewise BitmapData constructor/setPixel32 rules remain independently scoped.

## Reproduce

```sh
python3 tools/probes/build_png_decode_probe.py --output /tmp/bvn-r86/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r86/native /tmp/bvn-r86/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 45
python3 -m tools.probes.analyze_png_decode --native evidence/importer-loud-fail/r86/native --output /tmp/bvn-r86/recheck.json
python3 -m unittest tools.tests.test_png_decode
```

[Summary](summary.json), full per-coordinate rejected predictions in `analysis.json.gz`, original `native/game/probe.png`, [hashes](provenance.json), [acceptance](acceptance.json).

Next independently vary alpha across both axes in a new encoded PNG; compare direct display draw to black, transparent materialization followed by black, single-pixel clip draws and a second transparent BitmapData draw. Retain source/property readbacks. This separates downstream draw/readback rounding from the decoder hypothesis and challenges row-routing dependence before any GPU binding. Do not import a rule by whichever RGB happens to match.

`candidate_admitted=false`, `production_admitted=false`. No GPU/production change. Historical components9/54, general PNG/SWF-export relationship, fractional coverage/affine/implicit buffers and AS/clip-action ownership remain open. Full roster/Web and54 components not rerun. Draft only; no merge/deploy/Worker.

Validation note: the first full Python run was interrupted while unittest formatted a large tuple/list serialization mismatch in the diagnostic report. Failure rows now use canonical JSON-compatible lists; native capture and arithmetic are unchanged. The focused PNG tests pass; combined r86/r87 full regression results are recorded in acceptance.
