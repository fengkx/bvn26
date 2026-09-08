# Original map-selection implementation

The mode menu now skips fighter/assist selection and enters the map selector.
The fighter/assist slice stays Naruto/Ichigo and Gaara/Kon. Map names are instance
names, including 火影瀑布 and 宇智波村, rather than the alternate catalog display names.

## Source-first gate

1. `scripts/main.json`, `DefineSprite_1505/frame_1/DoAction.as` contains the entire
   selector controller: `init(2)`, `updateXY(1,1,0)`, sparse grid construction,
   independent left/right/up/down/OK/cancel branches, five-frame repeat and the
   500 ms timeout. This is a one-frame sprite. `DefineSprite_1504/frame_1/DoAction.as`
   assigns `txt.text = _name` and `bg.gotoAndStop(_name)` to each thumbnail.
2. Main root frame 46 places `xure` (1506); its 地图 label starts at frame 35 with
   a new `xrmc` (1505). Source matrices and display lists are compiled into
   `godot/generated/main/map_selection/presentation.json`. The new controller
   starts with P1 enabled, P2 disabled and an undefined counter (initialized to 10).
   Input starts on the following frame. Frames 35–50 preserve the source wipe.
3. `DefineSprite_1506/frame_50/DoAction.as` stops the parent timeline. The one-frame
   controller continues receiving enterFrame. OK disables P1 immediately, then
   calls onOK after 500 ms; a nonempty curStage enters 游戏场景. K enters MENU.
4. Tests lock the native grid, default, wrap/scan order, independent simultaneous
   branches, repeat counter, confirmation lock, cancellation cleanup, and map
   spawn markers. FloorY=-25 and mapSizeX=1000 come from root frame_7 defaults,
   not the selected map's elevated spawn marker.
5. Native Flash Debug Player 32.0.0.465 ran the isolated source probe. Navigation:
   现世 → left 木叶村 → up 宇智波村 → right 尸魂界通道 → down 现世. The injected
   six-frame Down hold moves at ticks 1 and 6; confirmation at tick 12 disables
   input, and frame 56 is reached after 503 ms. See navigation.log, input.log and
   capture.json. Only the input reader is replaced; the controller logic is original.

## Rebuild and tests

```sh
python3 tools/importer/build_stage_catalog.py --workspace /tmp/main-pinned
uv run tools/importer/build_map_selection.py --workspace /tmp/main-pinned \
  --temporary /tmp/map-selection-build --ffdec-jar /tmp/ffdec-26.2.1/ffdec-cli.jar
python3 tools/probes/build_map_selection_probe.py \
  --ffdec /tmp/ffdec-26.2.1/ffdec-cli.jar --output /tmp/map-oracle-rebuild
python3 -m unittest tools.tests.test_map_selection tools.tests.test_stage_catalog
godot --headless --path godot -s res://tests/map_selection_smoke.gd
```

The menu compiler has a pinned Pillow script dependency. The modified XML/SWF
and raster workspace remain temporary; production uses PNG/JSON/MP3 only.
JPEXS rasterizes masks and gradients. Glyphs are exported at 2x; the source
white text is composed above its black shadow to avoid JPEXS's reversed shadow
composition. Flash device-font substitution and filter rasterization have not
passed pixel-level acceptance; no claim of exact cross-renderer pixels is made.

Map smoke tests enter all ten maps, check P1/P2 origins, floor, music fallback,
return/re-entry, timer cancellation and mode preservation. Combat smoke and the
existing Python suite also passed. Dummy-audio shutdown can report retained
playback instances, as documented in docs/VALIDATION.md.

This completes the selector's source-derived implementation and focused native
input comparison, not all M6 menu/content acceptance. Full-map animation/collision
parity and the three-browser matrix remain pending. Approximate effort for this
selector pass: 0.08 person-days, including reference capture and integration.

Web verification: the in-app browser loaded the release, displayed all ten maps and changed the highlighted map. Automated very short key pulses were not reliably sampled by the polling loop; the user verified with a real keyboard that selection and entering combat work. This is one browser smoke check, not the full browser matrix.
