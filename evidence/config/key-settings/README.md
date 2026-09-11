# Key settings accessibility correction (2026-09-11)

The reported P1 configuration binds both `w` and `d` to Flash code 68.
The editor previously used remapped menu inputs with up-before-right priority,
so D could never select P2. The default font also lacks the arrow glyphs used
by source `showKeyName`.

The editor now accepts fixed physical arrows, Enter and Escape, with priority
over conflicting bindings. This is an editor accessibility adaptation, not a
claim that Flash implemented keyboard row navigation. Existing mapped controls
and mouse selection remain available. Arrow key labels use ASCII words only in
this view; source codes and `showKeyName` remain unchanged.

Source boundary: `scripts/main.json` buttons 754–757 select P2 direction slots
on release; Sprite 835 frame 1 stops, frame 5 sets the capture hint, and the new
frame-5 PlaceObject2_833_1 keyDown handler writes the selected root key then
returns to frame 1. Button 740 returns to Config, which owns persistence.
No source timeline lifecycle or battle behavior changes here. Native Flash
same-input comparison and complete visual parity remain unverified.

Validation: `godot/tests/key_settings_smoke.gd` injects physical input with the
reported duplicate D binding, selects P2, releases Enter before capture, binds
P2 Up to R, preserves P1, and returns to P1. Result: KEY_SETTINGS_SMOKE_OK.

Entry and reset now leave every row unselected, as requested. Confirm without
a selection does not start capture. First directional input selects the first
row (Right selects P2); clicking still selects and edits the clicked row.
The focused smoke covers initial and reset markers and ignored entry confirm.
