# Kon assistance source audit (2026-09-08)

## Source-first gate

1. All root scripts in `scripts/fighter/fz/kon.json`: frame 1 initializes and
   parks/stops; 2 play + fzccXg; 12 sets action=1; 15 bsd(pn,"XG_fzbs",true);
   30 bsw(pn) (no true argument); 67 action=0; 72/75/78/81/85/89 subtract 20
   from opponent ql; 102 fzccXg. Other root frames have no DoAction. Sprite 18
   defines legacy beida/fangyu functions, but has no call or enterFrame hook.
2. Root `atm1` is newly placed at 37, MOVE changes at 39 through 63, removed at
   65. There is no clip load hook aiming it at the opponent. Gaara's frame 44
   load script belongs only to its PlaceObject2_48_2 and must be compiled as such.
3. Frame 102 has no goto or stop: show its exit effect, then naturally wrap to
   frame 1, which parks/stops. fzccXg only creates XG_fzcc; it does not hide.
4. Invariants: source 30 Hz/102 frames, one continuous atm1 placement at 37–64,
   10 damage/300ms hitstun; six unconditional -20 MP events; both facing
   directions retain timeline geometry; scene P2 summon uses Kon and its portrait.
   Source `main.json frame_8` bsd's true branch marks helper.bs, attempts to stop the owner
   and opponent, and puts XG_fzbs on the helper. bsw's omitted fz argument must
   not be silently changed to true. Root frame 1 resets helper.bs to zero. `doZhaoHuan()` sets the owner bs=1,
   so stopMc must leave the owner playing; bsw at 30 clears owner.bs. This
   missing summon field is compiled as set_bs and tested through return to idle.
5. The existing original screenshot covers Gaara only. No fixed-input original
   Kon trace has been captured in this change; full behavior alignment remains
   pending. Source compilation and native smoke are implementation evidence.

Original sources are untouched. `data/slices/kon-helper.timeline.json` derives
from locked `game/fighter/fz/kon.swf`; all imagery and sounds use JPEXS 26.2.1.
XG_fzcc and XG_fzbs are main.swf ExportAssets 379 and 393.

## Executed validation

- Godot 4.7.2 `kon_helper_smoke.gd` passed headless and macOS rendering. Full
  scene path includes P2 summon spending 100 MP, helper super-start while owner
  bs=1 keeps playing, six MP drains exactly once, natural wrap and bs reset,
  owner returning to idle and accepting another attack, and both facing directions.
- Rendered frame saved to `/tmp/bvn-kon-helper.png` shows Kon in front of Ichigo
  and the matching right MP portrait. Effect clips were advanced with the scene.
- Existing `combat_smoke.gd` and `helper_presentation_smoke.gd` passed.
- Python discovery: 40 tests passed. Source tests also lock the absent Kon aim
  hook, original bsd/bsw fz argument difference, and doZhaoHuan's bs assignment.
- `verify.py`, `check_handoff.py`, and JSON contracts passed. Web export rebuilt
  `dist/web/`. Source game/scripts hashes are unchanged.
- Known remaining limitation: existing audio playback warns about unhandled
  SOUNDINFO out_point (Kon sound 44 and helper effects). No sound endpoint or
  fixed-input original-player trace alignment is claimed. Headless dummy audio
  reports playback resources at exit as described in docs/VALIDATION.md.
