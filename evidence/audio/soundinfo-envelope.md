# SOUNDINFO envelope bake evidence

## Scope

This record covers `tools/importer/build_sound_segments.py` and its focused
tests. It does not claim an original Flash-player trace. The original-player
window was assigned to the Renji worker while this repair was made.

## Source semantics

- The retained project contracts in `docs/DATA_CONTRACTS.md` and
  `docs/HIT_RECEIVE_SOP.md` record `pos44`, `in_point`, and `out_point` in the
  44.1 kHz sample domain, independent of the DefineSound encoding rate.
- The SWF 19 specification's Sound Envelope section defines each envelope
  point as a 44 kHz sample position plus left/right levels in the range
  0..32768: [SWF File Format Specification 19](https://open-flash.github.io/mirrors/swf-spec-19.pdf).
- The interpolation and endpoint behavior are implemented from the retained
  source-compatible player reference in Ruffle: its `EnvelopeSignal` starts
  at the first point's level, linearly interpolates between points, and emits
  the final level after the last point. This is an implementation reference,
  not an original Flash observation: [Ruffle mixer.rs](https://github.com/ruffle-rs/ruffle/blob/master/core/src/backend/audio/mixer.rs#L1000-L1058).

The importer follows those semantics per channel. `build()` decodes with
`ffmpeg -ar 44100` before `segment()`, so `pos44` indexes the decoded array
directly. `in_point` and `out_point` remain the authored source range; the
existing importer convention treats `out_point` as the exclusive end sample.

## Regression evidence

`tools/tests/test_sound_segments.py` has eight passing tests. The real Renji
timeline event is frame 21, sound 38, with envelope points
`0:16532/15646 -> 33366:0/0`; the test reads that generated timeline and
checks both channels and the fade endpoint. A second test applies a nonzero
`in_point` to that same source envelope to cover the dynamic-envelope plus
crop path. The real Rifagu frame 253, sound 150 event covers authored
`in_point=4400` and `out_point=36864` with its source envelope.

The full Renji reconstruction was run in a temporary directory:

```text
rm -rf /tmp/bvn-renji-segments /tmp/bvn-renji-wavs
mkdir -p /tmp/bvn-renji-segments /tmp/bvn-renji-wavs
cp godot/generated/fighters/renji/timeline.json /tmp/bvn-renji-segments/timeline.json
java -Djava.awt.headless=true -jar /private/tmp/bvn-ffdec-26.2.1/ffdec-cli.jar \
  -format sound:wav -export sound /tmp/bvn-renji-wavs game/fighter/Renji.swf
python3 -c 'from pathlib import Path; from tools.importer.build_sound_segments import build; \
result=build(Path("/tmp/bvn-renji-segments"),Path("/tmp/bvn-renji-wavs"),Path("/opt/homebrew/bin/ffmpeg")); \
print(result["frames"]["21"][0])'
```

Result: 34 frames, frame 21 sound 38 range `0..36864`, segment SHA-256
`fb6428b8943be50db60d2951bb67d304b59ef0ce08b97c0460ed856804ddac4e`.
The tool inputs used FFDec SHA-256
`23c1e70ff2b08388e35de10afd97a2875386cbfdc2ef99c8176d40b4f8a3ada9` and
FFmpeg 8.0.1 (binary SHA-256
`67b7321240d27e0a04ec9fe802c9d4d3cf6c79d2fdd88e446ca98bcddc92f8c5`).

Checks:

```text
python3 -m unittest tools.tests.test_sound_segments  # 8 tests, OK
python3 tools/verify.py                              # passed
python3 tools/check_handoff.py                       # passed
```
