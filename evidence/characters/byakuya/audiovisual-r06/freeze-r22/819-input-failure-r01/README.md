# r22 819 capture failure: input gate

The capture driver launched the unique r22 SWF under the global flock and terminated its own Flash process after the run. The run reached `fight_tick=300` and emitted `done`, but never emitted `visual_freeze_end`.

The raw trace shows `input_next_display` with `summon=undefined` at fight ticks 10, 11, and 12, and P1 never reached source frame 819. This is an invalid input fixture/run, not a visual mismatch. The driver correctly failed closed with `done arrived before visual_freeze_end`. No screenshot is accepted.

The build metadata also records an old `fixture_url` from r21 while the embedded frame-10 patch points at the r22 case file. A new run must first fix and preflight this provenance/input wiring, then use a fresh run id. Existing accepted captures were not changed.
