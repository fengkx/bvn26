# QA HUD Web export r01

This is a temporary QA export with only Byakuya/Lee fighters and Kon/Gaara helpers enabled in the copied project. Production roster and source inputs are unchanged.

- Served from `http://127.0.0.1:8781/`
- PCK SHA256: `a00625c6ba15796e02c35bae37be2799b9b492984b789224baac30239b33a9b0`
- DevTools page: 29, isolated context `bvn-hud-r01`
- Verified title -> Vs Human -> fighter selection -> helper selection with canvas keyboard events.
- This is QA evidence, not production release or full parity evidence.

## Fresh page29 run

The visible flow reached the real map selection and battle canvas after selecting Vs Human, the two temporary fighters, both helpers, and the `现世` map. The battle canvas showed both HUD bars and the countdown. Console records `COMBAT_EVENT` for both `白哉` fighters at intro frame 958. Two WebGL warnings (`bindBuffer: element array buffers can not be bound to a different target`, `bufferSubData: no buffer`) remain in the browser console; no JavaScript parse error or Godot SCRIPT ERROR occurred.

## Input/pause method

For this WebGL run the reproducible path was `canvas.focus()` followed by a canvas `KeyboardEvent` keydown carrying `key`, `code`, `keyCode`, `which`, `location`, `bubbles`, and `cancelable`; hold for about 260 ms, then dispatch a separate keyup and wait at least 300 ms. `s/KeyS/83` selected Vs Human; `j/KeyJ/74` confirmed P1; `1/Numpad1/97/location=3` confirmed P2. Enter opened the pause panel and a second Enter resumed it. The page reached battle and logged the two frame-958 Byakuya intro events. Screenshot saving through DevTools was rejected by its configured path policy, so the screenshots remain inline tool evidence.

## Action-input diagnostic

Fresh canvas events were recorded without an internal action call: D keydown/up at 894046.7/894572.2 ms, J at 959799.7/960325.8 ms, K at 1036326.3/1036553.5 ms. No subsequent `COMBAT_EVENT` was emitted for these attempts, so the current artifact proves DOM dispatch and the earlier menu path, but does not prove fighter action delivery. The camera/scene changes were not treated as movement evidence.

## QA input probe r01

`input-probe-r01/qa_input_probe.gd` is an autoload used only in the temporary QA copy. It runs with `PROCESS_MODE_ALWAYS`, logs key events and per-physics `Input.is_physical_key_pressed` state plus session/fighter input fields. Headless validation produced `QA_INPUT_PROBE_READY` and no parse error; this probe was not added to production.

## Old page29 boundary

Page29 had no QA input probe. Its earlier no-action observations occurred after a long-running page session with countdown/round transitions; console retained only boot, intro, and WebGL warning records. It is retained as a separate observation and is not silently reclassified as a production input failure.
