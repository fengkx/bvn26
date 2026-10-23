# Checkpoint fixture exit cleanup

The initial run passed every behavioral assertion but leaked two `AudioStreamPlaybackMP3` instances and one `AudioStreamMP3` resource at immediate engine exit. The verbose trace identifies `generated/fighters/minren/40.mp3`, which this fixture deliberately starts twice to test sound publication deduplication.

Only `godot/tests/battle_checkpoint_smoke.gd` changed: after its final assertion, stop the active audio players, release their streams, and yield a process frame before fixture disposal. Runtime behavior and checkpoint assertions are unchanged. The final `clean.log` rerun prints `BATTLE_CHECKPOINT_SMOKE_OK` and exits without warnings, errors, leaked instances, or retained resources.

Final clean rerun command (earlier runs omitted `--log-file`):

```sh
Godot --headless --verbose --path godot --log-file /tmp/bvn-loud-fail/r12/godot/checkpoint-clean-engine.log --script res://tests/battle_checkpoint_smoke.gd
```

Original normal and verbose failure logs and the full final clean verbose rerun are retained alongside this file.

Correction: the retained `after-verbose.log` has startup `user://logs` permission errors, despite successful behavior and no audio leaks. `clean.log` is the final rerun with the explicit writable log path above; it contains the success marker and no ERROR/WARNING/leak diagnostics. Earlier logs remain unchanged.
