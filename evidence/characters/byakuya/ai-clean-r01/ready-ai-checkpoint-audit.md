# Ready checkpoint AI audit

This audit deliberately starts at the original Ready boundary. It does not claim boot, load, or intro parity. The complete structured checkpoint is in [ready-ai-checkpoint-audit.json](ready-ai-checkpoint-audit.json).

The original checkpoint is `ready` sequence 2663, display tick 452, fight tick 0. It records both actors' source frame, raw source x/y/facing/HP/energy tokens, action, sw/touch/touchFloor/hits/paused/hstm/hurtSkling, the last AI sample before Ready, source random cursor, and the first source predicate events after Ready. The last pre-Ready AI sample is sequence 2593; the source random cursor at Ready is 141 (including the unrelated main consumer).

The original first post-Ready Byakuya predicate sequence begins at fight tick 0 with `rush=true` and `dash=false`, followed by `dash=false` each tick until the later source decisions. These are retained verbatim with sequence/display/fight ticks in the JSON so controller decisions can be compared without pretending the complete scene was restored.

The existing Godot artifact `/tmp/ai-clean-polls4.json` is retained only as diagnostic context. It contains full observed actor fields at its logical tick 0, but is marked invalid for checkpoint parity because the probe calls `battle_intro.begin` a second time after production `_enter_current_fight`, and it does not restore the source child/controller queue, source frame callbacks, and exact Ready checkpoint state. No runtime acceptance or source-frame shift is derived from it.

Acceptance scope is therefore currently **controller/checkpoint preparation only**, not AI parity. A valid next replay must restore the JSON checkpoint fields and the recorded random/clock cursor before consuming the same post-Ready input tape; otherwise the result must remain unaccepted.
