# Sakura frame 727 finite SOUNDINFO loop

The retained source is `game/fighter/Sakura.swf` (SHA-256
`7d5d060ea9949f54535f801abd3ebdb23de5e7fc7cd5644186f7d805a47ba544`), timeline
sprite 630. The corresponding compiled event is `godot/generated/fighters/sakura/timeline.json`,
frame 727, sound 49. Its source fields are `in_point=1100`, `out_point=5400`,
`loop_count=20`; `sync_stop=false`, `sync_no_multiple=false`, and there is no envelope.
The DefineSound asset is `Sakura_assets/sounds/49.mp3`, SHA-256
`369de2228ca3bf2d5f1da9b046b106a1f4e994dd9a0e7f69eb4846995b720826`.

## SOURCE_FIRST

1. Frame 727 contains a StartSound tag and no source DoAction or ClipAction required to start it.
2. Frame 726 has the prior depth-27 display object; frame 727 does not change that placement; frame 728 replaces depth 27. The sound event is independent of that replacement.
3. The source display timeline advances from 727 to 728 without a goto/stop at this location.
4. The tag is one event with one finite LoopCount value; no SyncStop, SyncNoMultiple, or envelope fields are authored. Adobe's Flash CS6 teaching notes define Repeat as the number of times the file plays; the SWF v19 specification places the count in SOUNDINFO.LoopCount. This supports treating 20 as 20 total plays of the clipped region. The SWF specification defines InPoint as samples skipped at the beginning and OutPoint as the position of the last sample to play.
5. Native run `sakura-sound-loop-r02` naturally reached frame 725@fight38, 726@39, 727@40, 728@41. The independent tag marker was sequence 3272 at display tick 494/fight tick 39, immediately before the subsequent state row for frame 727. The runner verified the actual loaded fighter path and hash. This confirms tag arrival on the original path, not audible output or loop completion.

## Playback-position feasibility check

Run `sakura-sound-loop-r03` added a temporary observer after the frame-727 tag. It created
`new Sound(this)` and read only `position` and `duration` every 25 ms for at most 2600 ms.
Across 103 observations both fields were `undefined`, so an AS2 Sound object attached to this
movie clip does not expose this timeline StartSound instance. No sound was started/stopped and no
`onSoundComplete` callback was installed. The added timer changed wall-clock callback phase and
the later random/state trace; r03 is not a behavior baseline. Its log is retained to show the
observer's limit. No hardware audio capture was available.

## Baked result

The current converter applies the repository's established exclusive-end convention and crops
source samples `[1100,5400)` (4300 frames at 44.1 kHz), repeating that envelope-free region 20
times. The generated stereo WAV has 86,000 sample frames and duration 1.9501133787 s. The original
MP3 remains unchanged. This exclusive-end interpretation is inherited from the segment pipeline;
it was not measured in the Flash capture. The SWF v19 wording calls OutPoint the position of the
"last sample to play", which may imply including sample 5400. Neither the tag-arrival marker nor
the Godot stream-start probe resolves that boundary. If that wording is inclusive, the source
region would be 4,301 samples and the repeated WAV 86,020 frames. Keep this boundary question open
until a source-backed native observation or stronger format evidence settles it; do not treat the
86,000-frame result as native duration proof. Looped sounds with envelopes remain rejected until
their playback-wide envelope semantics are evidenced. A missing loop-count field means the
ordinary single play; an explicitly present non-positive count fails closed rather than guessing.

## Godot stream-start verification

The same source frame was replayed through `godot/tests/source_audiovisual_probe.gd` with
`res://generated/fighters/sakura` and frame `[727]`. The retained trace is
[`sakura-frame727-player-trace.json`](godot/sakura-frame727-player-trace.json). Godot reported
source/runtime sound ID `[49]`,
one newly playing stream, and exact resource-path equality:
`res://generated/fighters/sakura/sound_segments/49-637083dcdf7f140f.wav`. The probe verifies
resource selection and player start, not 1.95-second completion or Flash-vs-Godot audible
equivalence. The WAV SHA-256 is
`8d8d5cfd8725ed7d0ccd5feeb52237a8332570c9c50c8f41774b9c85d97321f6`; the untouched MP3 SHA-256
remains `369de2228ca3bf2d5f1da9b046b106a1f4e994dd9a0e7f69eb4846995b720826`.

The related non-loop in/out/envelope regression uses Rifagu frame 253, sound 150. Its source event
has `in_point=4400`, `out_point=36864` and one envelope record. The same probe passed with one
newly playing segment stream; see
[`rifagu-frame253-player-trace.json`](godot/rifagu-frame253-player-trace.json).

Three generated sound-segment manifests currently contain 37 Sakura, 34 Rukia and 41 Yulong
root-timeline events. The source MP3s are retained; segment WAVs and manifests are generated
outputs. Yulong's nested sprite 185/frame 8 sound 164 remains a separate nested-timeline path and
is handled by its nested timeline/runtime change, not flattened into the root frame manifest.

References:

- [Adobe Flash Professional CS6 Classroom in a Book, Instructor Notes, Lesson 8](https://ptgmedia.pearsoncmg.com/imprint_downloads/peachpit/peachpit/academic/FlashCS6CIB_instructor_notes.pdf)
- [SWF File Format Specification v19, StartSound/SOUNDINFO](https://open-flash.github.io/mirrors/swf-spec-19.pdf)
- [Adobe Flash Professional CS6 Help, sound Repeat and Sound.position/duration](https://helpx.adobe.com/archive/en/flash/cs6/flash_reference.pdf)
