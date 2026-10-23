# Player visual fixture exit cleanup

The original run passed behavior but leaked 8 objects/4 resources at exit. A verbose reproduction passed behavior and leaked 6 objects/3 resources (audio-thread timing changes the count): MP3 streams and playbacks for the intro Ready sound and Yihu sounds 140/568. Full logs are retained.

Only `godot/tests/player_visual_smoke.gd` changed. After all behavior assertions, explicitly stop its active intro/fighter audio players, release their streams, and yield a process frame before menu transition and disposal. Runtime files and assertions are unchanged.

The final `clean.log` verbose rerun exits successfully, prints `PLAYER_VISUAL_SMOKE_OK`, and contains no WARNING, ERROR, leaked instances, or retained resources.

```sh
Godot --headless --verbose --path godot --log-file /tmp/bvn-loud-fail/r12/godot/player-visual-clean-engine.log --script res://tests/player_visual_smoke.gd
```

Correction: the retained `after-verbose.log` has startup `user://logs` permission errors, despite successful behavior and no audio leaks. `clean.log` is the final rerun with the explicit writable log path above; it contains the success marker and no ERROR/WARNING/leak diagnostics. Earlier logs remain unchanged.
