# Resumed original sampling

The user explicitly allowed popup windows and requested continued sampling.
The active batch writes `/tmp/bvn-move-resumed-oracles-r2/results.json` (313 remaining fixtures), using the unchanged windowed original probe and fixed inputs. This directory retains a checkpoint, not the completed batch. Its comparisons use the earlier native baseline; recompare the full corpus against `/tmp/bvn-move-resumed-native-precision` after that native batch completes. Preserve earlier source recordings and red traces.

The repaired Ichigo transformation-start call now matches observations 0 through 100 inclusive (202 actor states). The full trace still differs from observation 101 at form replacement. `tools/test_transform_start_reference.py` checks only that explicit prefix and reports the separate full-move status. This does not implement transformation completion.

A first sandboxed launch failed process inspection before opening Flash. The resumed batch uses authorized execution; a new batch preflight prevents repeating a missing-player/process-inspection error for every case. No original recording from the failed launch is accepted.

The first guarded aerial-ranged recording exposed a trace-export precision loss: default Godot JSON emitted 303.333333333333 for a stored 303.3333333333333. The move recorder now enables full precision. The same 602-state recording matches exactly after re-export; no comparator tolerance or combat rule changed. Earlier rounded native traces remain retained.

The post-batch archiver is running as part of this sampling job. It waits for all 313 original attempts and the complete 356-case full-precision native batch, then writes a new `resumed-full` evidence directory and its unaccepted coverage ledger. It refuses to finalize an incomplete native matrix and stops if source sampling ceases to produce results. Current logs are `/tmp/bvn-move-resumed-r2.log` and `/tmp/bvn-finalize-resumed-moves.log`.
