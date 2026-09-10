# Quality rendering and timeout HUD correction — 2026-09-10

## Source-first gates

1. Config root frame 16, Sprite 836, frame 1 quality child 698 at depth 6:
   unchanged load/keyDown/enterFrame callbacks are retained in
   `godot/generated/main/config/config.json`. HIGH and MEDIUM write `_quality`;
   LOW writes ordinary `quality` and leaves raster quality unchanged. There are
   no additional quality frame callbacks. Original option traces have 161 states.
   Timeout Sprite 1848 frame 67 increments the winner counter and calls
   `gotoAndStop` / `bzxg.play` on `_root.p1win` or `_root.p2win`.
2. The actual win clip is Sprite 1785: frame 1 stops with no children, frame 2
   places shape 1784 at depth 1 (X 432 twips), frame 3 retains it and places the
   same shape at depth 2 (X 0). Neither placement has a name. There is no `bzxg`.
   The actual HUD lives under `_root.xuetiao`, Sprite 1815/1814 and p1xt/p2xt.
   Config re-entry replaces its option clips; persistence still uses `qualiy`.
3. Config stops at frame 1 and saves/returns through its existing compiled
   callbacks. Win markers remain stopped unless explicitly addressed. Normal KO
   Sprite 1858 frame 94 calls `updateWins`, defined in Sprite 1814 frame 1; timeout
   frame 67 calls missing aliases instead. Timeout continuation is unchanged.
4. Test original option values, missing targets and stopped marker frames. Do
   not invent flashing or redirect undefined aliases to a real clip. The native
   graphical test separately verifies that the rendering adapter changes edge
   coverage and forwards keys/mouse once; it is not a Flash pixel oracle.
5. `native.log.gz`, `build.json.gz`, and `instrumentation.diff.gz` retain original
   run timeout-badges-r02. It finishes successfully with 3353 total events;
   `badges.json` contains 693 observations (231 callback ticks). Both root aliases
   and both bzxg targets are undefined throughout; actual p1xt/p2xt win frames
   remain 1 even after the winner counter becomes 2. Locked inputs are unchanged.
   Existing original Config 161-state tape is reused unchanged.

## Rendering implementation and acceptance boundary

`RenderSurface` hosts the same game scene in a supersampled SubViewport, keeping
its logical canvas size and simulation unchanged. It resolves every sample in
an integer grid per output pixel, rather than changing bitmap filtering. A
GameSession signal updates the raster only when actual `_quality` changes,
including loading storage. The original LOW assignment bug remains intact.

The quality grid is 4x4 for HIGH, 2x2 for MEDIUM and 1x1 for actual LOW, per the
[Adobe runtime reference](https://airsdk.dev/reference/actionscript/3.0/flash/display/StageQuality.html).
[Godot Compatibility lacks 2D MSAA](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html),
so setting the MSAA enum would not implement this in Web.

This is a working multisample-density adapter, not a replacement Flash rasterizer.
Prerendered asset edges cannot regain their original vector geometry, and Flash's
coverage rounding, smoothing and bitmap cache decisions remain separate parity
limits. HIGH renders 16 samples per output pixel; full high-DPI performance and
cross-browser budgets remain unaccepted. Native settings layout is retained as
requested. No deployment is implied by a successful local Web build.

## Validation

- Original option replay: 161 states matched unchanged.
- Original timeout winner/draw replay: 230 + 221 states matched; additional
  stopped-badge assertions pass. Explicit updateWins still advances the badge.
- Native graphical quality fixture: LOW has no partial-coverage levels, MEDIUM
  has 3 and HIGH has 15. Keys reach Config once; mouse clicks work at both grids.
- Config flow/storage, player controller/visual, Vs Com KO resume and 100 Python
  tests pass. Some existing headless cleanup warnings remain.
- Web and final packaging results are recorded in validation.json.

Reproduce with Godot 4.7.2: `--path godot res://tests/quality_visual.tscn` for the
native graphical check. For Web, copy the project into a temporary workspace,
set its main_scene to this fixture, and export Web there; both bundled Web
release/debug templates reject command-line scene overrides. Production remains
`render_surface.tscn`. Do not leave test HTML or exports in source control.

Initial Web rendering exposed an attachment-size limit at high DPI. Window
ViewportTexture.get_size() also included the stretch twice; allocation now uses
the actual canvas-to-pixel transform and excludes letterboxing. The surface
now queries the actual WebGL texture/renderbuffer/viewport limits and bounds the
presentation resolution using the maximum quality grid. Every quality therefore
uses the same output resolution, with only sampling density changing. The
hardware-limited case can render below the full device pixel resolution; it does
not silently select a different quality. This is a port rendering constraint,
not an original gameplay rule.
