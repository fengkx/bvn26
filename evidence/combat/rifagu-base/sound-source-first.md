# Sound segment source gate

The base Sprite 638 contains 40 root StartSound events, including two in
the deferred transformation sequence. All source sounds are materialized;
the reachable nested sprites contain no StartSound tags.

- Complete commands and SOUNDINFO are retained in the base timeline. Examples:
  frame 122, sound 50, outPoint 5286; frame 252, sound 149, inPoint 2000;
  frame 253, sound 150, inPoint 4400/outPoint 36864, left/right envelope
  15999/16307. Twelve root events have an explicit start or end position.
- These are frame commands, not enterFrame callbacks. Re-rendering one
  unchanged source frame must not restart its event sound. Audio is owned
  by the corresponding timeline instance; frame progression alone does not
  destroy an active event sound.
- Start/end positions use the retained SOUNDINFO 44.1 kHz sample units.
  Playback ends at its specified sample or the sound's natural end, whichever
  comes first. PCM segments avoid stopping audio on coarse simulation ticks.
- Left/right envelope levels are kept independently, on the 0..32768 scale.
  A nonconstant envelope or loop/stop command is rejected by this importer;
  unsupported behavior must not silently become a whole-sound playback.
- Fresh original cases exercise the actual action frames and keys (see the
  retained base references). This establishes trigger paths, not waveform
  identity. PCM range tests and runtime stream-length checks verify the
  compiled segments. Native Flash/Godot waveform/device latency equivalence
  remains a separate acceptance item.

`XG_bs` sound 444 has inPoint 5100/outPoint 51340; `XG_cbs` sound 426
has outPoint 51892. The same segment compiler handles these shared effects.
Each effect owns exactly one scheduled StartSound playback. Its visual
TimelinePreview must not replay that sound independently; both previously
started the same tag. The runtime regression checks zero players before
the deferred initial frame and one afterward, with the authored duration.

The browser summon path additionally exercises `XG_fzcc` sound 97 (outPoint
17950) and `XG_fzbs` sound 382 (outPoint 25000; left/right 19484/20960).
Their retained frame StartSound tags use the same static-segment rule. These
are event sounds on placed effect timelines, not repeating enterFrame calls;
segment materialization does not change placement, removal or label exits.
Original summon fixtures establish the input path; browser warnings exposed
the missing segment manifests. Waveform comparison remains unaccepted.

Original SWF bytes remain locked. The importer verifies the timeline's SWF
hash, exports WAV through pinned JPEXS, records its hash, resamples with the
recorded ffmpeg version, and retains per-segment source and output hashes.

Static zero-position envelopes on XG_fyq/XG_mffy (sound 197, levels
18008/18893) and XG_mfdjx/XG_qdjx (sound 219, levels 25978/27454) use
the same materialization rule. XG_mfdj has a single point at pos44=100;
its leading interval has not been established by a waveform oracle, so it
remains explicitly outside the accepted segment subset.
