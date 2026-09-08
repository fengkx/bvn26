# Battle pause menu

2026-09-08. Implemented for the current Godot slice; original-player same-input
trace and browser acceptance remain unverified. Move List detail is now implemented.

## Source-first gate

1. `scripts/main.json::DefineSprite_1991/frame_1/DoAction.as`: `onKeyUp`,
   Enter 13 opens with `_kn=2`; arrows 38/40 wrap over three rows; Enter
   dispatches MENU / menu.play / resumeGame2. `_menuEnabled` rejects intro/KO.
   `DefineSprite_2010/frame_1/DoAction.as` stops the panel. Frames 2–9 have
   no frame script; frame 10 stops the Move List. Godot advances one source frame per 30 Hz tick and stops at frame 10.
2. `game/main.swf` root `game_menu`: new PlaceObject2, character 2010, depth
   157, position (88,159.85). Its first frame places the panel, text, and
   selector `skk` (2001). Selector positions are compiled from `_knys`.
   Opening changes visibility and gotoAndStop(1), not a new instance.
3. Title uses root gotoAndStop("MENU"), destroying battle clips; Cancel hides
   the panel and resumes. Godot reloads the main scene on Title so transient
   fighter/helper/effect/input state cannot carry into a new match.
4. Tests assert source key-release behavior, initial Cancel, wrap, conditional
   stopMc (hited clips keep playing), resume, Title and clean re-entry.
5. The supplied screenshot is the visual reference. No original-player input
   replay was recorded in this change; strict timing parity remains unverified.

`frame_8/DoAction.as` defines pauseGame2/resumeGame2 and conditional stopMc/playMc.
The implementation retains running effect clips and the existing battle update
path, using root_zhanting and game_paused rather than pausing the whole SceneTree.
Existing intro and full KO presentation are not implemented by this slice.

## Art build

```
python3 tools/importer/build_pause_menu.py --xml /tmp/main-pinned/main.xml --ffdec-jar /tmp/ffdec-26.2.1/ffdec-cli.jar --workspace /tmp/bvn-pause-menu --output godot/generated/main/pause_menu
```

The XML is used read-only for placement coordinates and button bounds.
`SpriteBounds.java` reads the locked SWF with JPEXS, reports the rasterizer's
bounds, and writes a temporary copy trimmed to panel frame 1 without skk.
Original image bytes and fonts are preserved, avoiding the former JPEG3 XML
round-trip alpha problem. Frames 2–10 are exported directly from the locked SWF.
Output contains only PNGs and presentation data; no SWF runtime dependency.

The original page is common to all fighters (EditText 2006), with A/B/C and
up/down input combinations. It retains the source default-key wording even
when keys are remapped. `Button2009` mouse release returns to panel frame 1 and
keeps battle paused. Its Enter keyPress also returns to frame 1; the controller's
following keyUp dispatches the selected row (normally Cancel, resuming battle).
The latter sequence is source-derived and still needs native-player replay.

## Validation

- `tests/pause_menu_smoke.gd`: PAUSE_MENU_SMOKE_OK, headless and macOS graphical.
- Graphical capture: `/tmp/bvn-pause-menu.png`; original panel art and placement
  visually checked, including the middle row selected as in the supplied image.
- `tests/menu_smoke.gd`: MENU_SMOKE_OK.
- `tests/combat_smoke.gd`: COMBAT_SMOKE_OK; existing headless audio resource
  warnings remain at shutdown.
- `tools/verify.py` and `tools/check_handoff.py`: passed.

No original same-input frame trace or browser smoke run is claimed.

## Move List follow-up validation

- `tests/move_list_smoke.gd`: MOVE_LIST_SMOKE_OK in headless and macOS graphical
  runs; covers frames 1→10, terminal stop, paused state, repeated opens, mouse
  press/release and Enter press/release ordering.
- `/tmp/bvn-move-list.png`: graphical capture checked against original JPEXS
  frame 10, including text, translucent panel, position and Return button.
- Pause-menu regression: PAUSE_MENU_SMOKE_OK; 41 Python tests pass;
  COMBAT_SMOKE_OK. Combat shutdown still reports 10 ObjectDB instances and
  4 resources; no clean engine log or browser test is claimed.
- Web release rebuilt successfully; editor-settings writes are blocked by the
  sandbox after savepack, but exporter exits 0.
- Current fighter SOP audit: [report](combat/current-moves-sop.md) and
  [machine inventory](combat/current-moves-audit.json). Acceptance remains open.
