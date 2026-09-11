# Web player shell — 2026-09-11

User-requested browser UI, independent of Flash gameplay semantics. No fighter,
input mapping, source timeline or combat runtime changes.

- Default windowed layout preserves a 3:2 canvas and browser-accessible toolbar.
- Fullscreen is requested only by the button. The game fills the screen at 3:2 (letterboxing only as needed).
  Controls and exit instructions float above the game and fade after 4.5 seconds;
  moving the pointer to the top edge reveals them. No page header consumes space.
  No keyboard shortcuts or key interception are installed. Escape remains a
  browser/game-owned key, so the UI recommends the exit button.
- Export downloads JSON locally: engine stdout/stderr, console errors, uncaught
  errors/rejections, lifecycle/fullscreen events and browser/canvas metadata.
  Recent 2,000 entries are retained, each capped at 8,192 characters; dropped
  entry count is included. Refresh starts a new session. No automatic upload,
  storage/cookie export or URL query/hash collection.
- The shell is a custom Godot export template, so regular builds include it.

Validation: Godot 4.7.2 release Web export succeeded. Chromium headless boot and
the following focused scenario passed against the actual exported game:

    node tools/test_chromium_web_boot.mjs http://127.0.0.1:9237 http://127.0.0.1:8067/ /tmp/bvn-shell.png 'M0_BOOT_OK ' shell

The scenario checks default windowed bounds, toolbar context-menu availability,
fullscreen entry/exit and exit instructions, the downloaded Blob's engine/error
messages and metadata, ring-buffer eviction, and restored canvas focus. Screenshot
inspection confirmed the toolbar, 3:2 title screen and feedback fit a 756×469
viewport. Temporary build/test logs and screenshots remain outside source.

tools/verify.py, tools/check_handoff.py and git diff --check passed.
The sandbox denied writing Godot's global editor settings; export itself completed.
Firefox/Safari, browser-controlled Escape behavior and full gameplay browser
acceptance remain unverified. This is not a full AT-13 or gameplay parity claim.

Follow-up: red/black game styling replaces the generic blue toolbar. Chromium
checks verify maximal fullscreen bounds, preserved aspect ratio, floating toolbar,
auto-hide and top-edge reveal. Windowed and fullscreen screenshots were inspected.
