# Original Vs Com menu entry

Scope: the current fixed P1 Naruto / P2 Ichigo / AI=5 Vs Com slice. Additional
character ports are explicitly deferred by the user. Character/assist selection
remains bypassed; confirming Vs Com enters the existing original map selector.

## Source and implementation

- `scripts/main.json::frame_10/DoAction.as` enters MENU.
- Sprite 666 has 72 authored frames and stops on frame 72. The wheel (620) is
  newly placed on frame 63; its controller's enterFrame begins the next tick.
- Sprite 620's load and enterFrame scripts are compiled by
  `tools/importer/build_title_menu.py` into native GDScript. Initial selection,
  eight-item order, 5-pixel scrolling, wrap copies, independent W/S/J checks and
  the an/anj locks come directly from those scripts.
- Sprite 597 stops on frame 1. J calls play; frame 15 sets modo=2,
  p1cpu=false, p2cpu=true and requests character selection. Releasing J is not
  required. The existing authorized fixed-selection bypass follows this route
  into map selection. Source button target frame is retained in menu.json.
- Imported presentation uses the original button frames, 72 background frames,
  clip rectangle, placement matrices, color additions and root footer. JPEXS
  rasterization happens only at build time on a separate SWF copy; production
  uses Godot textures, native controller logic and the original key sounds.
- Sprite 672's hint timer is 30 ms, separate from the 30 Hz wheel update.
  Root version/footer placement and the hint position are retained from XML.

The Java export helper removes only the dynamic wheel and initially invisible
update panel from the temporary background copy. The source SWF, its original
image bytes and scripts remain unchanged. The Python importer checks the SWF,
XML export report and sound hashes before emitting runtime assets.

## Original execution evidence

`original.log`, `instrumentation.diff` and `probe.json` retain an isolated native
Flash Player probe. It presses S for controller tick 1 and holds J from tick 12.
The original selects Vs Com, moves its Y from 51 to 1 over ticks 1–11, starts the
button on tick 12 and executes its frame-15 exit on tick 26. The exit reports
mode 2, P1 human and P2 CPU. The probe exits before character selection.

The current source test checks the same 26-tick sequence and also checks held-S
repeat and simultaneous W/S. The integration test drives configured key events
through Main (including remapped Q/E), waits for the real confirmation animation,
then verifies map selection and the fixed CPU match. It does not call the menu
confirmation handler directly to substitute for the input path.

`checks.json` records four passing native tests with success markers, exit 0 and
no SCRIPT ERROR. The existing menu smoke's training section was stale after the
previous source settlement migration: it now checks the unchanged 8 HP before
the receiver DoAction, then -7 after the 15-damage settlement, rather than
expecting immediate clamped HP. No combat runtime change was made for that test.

## Rebuild

```sh
python3 tools/importer/build_title_menu.py --workspace /tmp/bvn-title-menu \
  --ffdec /tmp/bvn-ffdec-26.2.1/ffdec-cli.jar --xml /tmp/bvn-main-ko/main.xml
```

The importer needs Pillow, Java and the checked JPEXS export workspace. The font
subset builder needs fontTools and takes a Sarasa UI SC source TTC and its OFL
license explicitly; `font.json` retains the source hash and upstream license URL.
Both fonts and all generated PNGs are regular Godot export resources.

## Limits

This is not acceptance of every menu destination. Normal campaign, About,
external links and Exit actions have not been implemented by this task. Existing
versus/training/key-settings routes remain available; the settings shortcut is
not a reconstruction of the original settings submenu.

The SWF references system SimSun without embedding any glyphs. A renamed OFL
Sarasa subset prevents missing Chinese Web glyphs; it is not pixel-identical
SimSun. The baked background plays its 72 authored frames, then holds its last
raster; independently looping nested background effects after that stop are not
fully reproduced. The root footer hint and button behavior remain live.

Web export and the in-app browser entry are separate from the full Firefox/Safari
matrix, exact pixel/audio parity and complete Vs Com gameplay acceptance.
Headless audio checks may emit the existing dummy-playback exit resource warning;
success markers are not a leak-free or audio-quality claim.
