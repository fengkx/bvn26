# Rukia base move reference capture r01

Five fixed-input original Flash captures were replayed with the Godot harness. Original event streams are retained as deterministic gzip files; each case keeps its fixture, build/source hashes, tapes, instrumentation diff, capture summary, comparison, and native rows.

Four cases match all 602 states and 14 fields: rush, jump, summon, and defence. The first `砍技1` replay remains retained as a red before-fix result (555 differing states); its exact first divergence and source are documented in `source-diff.md`. A source-path/frame/operation/call-serial deduplication fix now makes the same input match all 602 states with zero differences. Before/after native rows and comparisons are preserved side by side.

The packet also includes post-fix r13/r14 full segment replay reports and native-only mirrored/held skill1 smoke summaries. Those native-only smokes do not claim original Flash parity. `SHA256SUMS.json` covers every packet file except itself.
