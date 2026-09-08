# Combo board presentation — 2026-09-08

Implemented from the locked `game/main.swf`, not a replacement font.

## Source gate

- `scripts/main.json`, `DefineSprite_1833`: frame 1 stops, frame 11 reads the victim's hits and calls `sz.changeNum`, frame 50 returns to frame 1. Other frames have no DoAction. Label 连击 starts at 10.
- SWF sprite 1833: `sz` (1828) is placed at 10, then MOVE preserves it through 49; HITS (1830) and RUSH (1832) are placed at 11. Frame 50 removes the display list. The exported 50-frame timeline preserves matrices, depth, color transforms and terminal flashing.
- Root frame 56 places p1hits at (5, 37.4), p2hits at (455, 37.4), with no mirroring. p1hits reads victim pn=2; p2hits reads pn=1. Runtime board keys denote the attacking player's side.
- Sprite 1828 `changeNum` selects hundreds/tens/units via digit+1, hides leading places and clamps negative input to zero. Digit sprite 1827 stops on frame 1. The original bitmap assets are 1816 (digits), 1829 (HITS), 1831 (RUSH).
- The supplied original screenshot confirms the 2 HITS/RUSH composition. A controlled same-input original playback trace has not been captured; full timing equivalence remains pending, and M2-04 remains pending.

## Build and validation

```sh
python3 tools/importer/build_combo_presentation.py --workspace /tmp/main-pinned --output godot/generated/main/combo
godot --headless --path godot -s res://tests/combo_hud_smoke.gd
godot --path godot -s res://tests/combo_hud_smoke.gd -- --capture
```

The dedicated smoke passed; real OpenGL rendering was captured at `/tmp/combo-hud.png` and visually inspected against the supplied original: the source graphics, digit spacing and board positions are present. Tests cover both sides, frame 10/11 entry, leading places, three-digit selection, and frame 50 removal. Existing 40 Python tests, input integrity, handoff and contract checks passed. No locked input was changed.

Combat smoke also emitted `COMBAT_SMOKE_OK` with exit code 0; shutdown reported two ObjectDB instances and one resource still in use. This is recorded separately from the clean dedicated HUD smoke.
