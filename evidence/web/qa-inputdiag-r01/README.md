# QA input probe r01

Temporary export only; production roster and mappings are unchanged.

- URL: `http://127.0.0.1:8782/`
- PCK SHA256: `520d6a38276918ac98166ea0ffb7d35f6957a67c03696c973ac5135f74bf6672`
- Availability in copied QA project: fighters 白哉/小李; helpers 魂/我爱罗.
- The full source selection grid remains packaged; this QA overlay changes only temporary availability.
- Probe fields: `_input` keycode/physical_keycode/pressed/echo; every physics tick physical D/J/KP1; `root_label`, `modo`, `paused`; and `session.fighter_input("p1"/"p2")` during battle.
- QA-only `PROCESS_MODE_ALWAYS`; no production runtime change.

## page30 observed chain

The isolated probe page reached `modo=3`, `root_label=游戏场景`. During a J hold it recorded `QA_INPUT_EVENT keycode=74 physical=74 pressed=true`, then per-physics states with `physical_j=true` and `p1.attack=true`. The same run emitted real `COMBAT_EVENT hit_settlement` rows at frame 874 with health 1000→970→940→890 and hits 1→3. During D it recorded `physical_d=true` and `p1.right=true`. This closes the DOM → Godot Input → GameSession fighter_input path for the probe package; page29's earlier no-action observation lacked this probe and is superseded as an input diagnostic.
