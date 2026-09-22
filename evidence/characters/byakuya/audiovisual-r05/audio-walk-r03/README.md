# Byakuya action-walk audio trace

`audio-walk.json` is an actual GUI Godot main-scene replay of `byakuya-455-bishaAir-energy_exact.json` with explicit 魂/魂 helpers and the fixture input tape. It records 300 fight ticks, root `last_sound_ids`, nested sound callbacks, source frame, action, and energy. Observed root sounds include source frame 38 at fight tick 7 (id 44), frame 456 at tick 21 (id 326), frame 486 at tick 51 (id 110), frame 497 at tick 62 (id 390), and frame 112 at tick 128 (id 52).

The source side is the same fixture's 602-state Flash trace plus the generated timeline's StartSound tags. This closes the Godot action-walk emission timing observation for this fixture; Flash device playback, native StartSound callback timing, and stop/restart waveform semantics remain outside this artifact's claim.
