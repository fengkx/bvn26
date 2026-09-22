# Web input source chain diagnostic r01

Target export: `/private/tmp/bvn-qa-inputdiag5/index.js`.

The generated JavaScript contains this keyboard registration path:

```text
_godot_js_input_key_cb = function(pCallback, pCodePtr, pKeyPtr) {
  GodotInput.inputKeyCallback = GodotRuntime.get_func(pCallback);
  GodotInput.setInputKeyData = (pCode, pKey) => ...;
  GodotEventListeners.add(GodotConfig.canvas, "keydown",
    GodotInput.onKeyEvent.bind(null, true), false);
  GodotEventListeners.add(GodotConfig.canvas, "keyup",
    GodotInput.onKeyEvent.bind(null, false), false);
};
```

`GodotInput.onKeyEvent` reads modifiers, calls `setInputKeyData(pEvent.code,
pEvent.key)`, invokes `inputKeyCallback(pressed, repeat, modifiers)`, and calls
`preventDefault()`. The function contains no `isTrusted` check. The compiled
source therefore identifies the expected target as the canvas and does not
itself explain the missing Godot probe events.

On page24, a same-canvas capturing listener observed the synthetic events and
`document.activeElement` was `canvas`. The Godot `PROCESS_MODE_ALWAYS` probe
still emitted no `QA_PROBE_INPUT` entries and all sampled held states remained
false. This separates DOM dispatch from delivery into the registered Godot
callback, without claiming a runtime defect or modifying production code.
