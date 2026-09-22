# Continuous AI replay r03

This is an acceptance-only Ready-checkpoint replay for the clean source capture. The runner is `godot/tests/ai_continuous_checkpoint_reference.gd`; it loads the source identities (P1 一护, P2 白哉, 魂/魂), reuses the recorded intro poll/input/random/clock schedule, and observes source display tick 452 through fight tick 180.

The runner reached the complete post-Ready window: source and native Ready actor frames are 7/2, 181 frame observations and 362 actor state rows have no observed 14-field differences, and geometry/input/clock traces are retained. The fail-closed validator reports `validated` for this bounded replay: the runner local cursor is 85 with original-index offset 56, which maps to source cursor 141 at Ready. The recorded random slice is preserved by original indices 57..210 and matches source site/value order exactly; no random draw is synthesized.

This validates the selected Ready->180 source replay only. It is not full AI parity: boot/load/intro parity, other AI inputs, and all controller/child behavior combinations remain outside this run. No production runtime was changed. The prior `byakuya_ai_tape_probe` is not used.

The replay now emits 362 native helper rows and the validator compares each available source helper field per display tick: frame, x, y, facing/xscale, action, attacking and hits. Source-visible/pause/child-lifetime fields are not present in this capture; checkpoint identity and inactive/deferred lifecycle preconditions remain separately gated and full helper lifecycle parity is still pending.
