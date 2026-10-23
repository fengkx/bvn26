# Native body replacement runtime (r12)

Daitu now executes the real source frame 1307 `wankai()` and frame 1309 parent jump, retires the old body and callbacks, and installs the target sprite 1138 timeline, art, combat, controller and state on the next display phase. This is a complete two-profile production package, not a mocked helper transfer. Other form graphs remain blocked unless independently compiled and accepted.

## Native bound

`native-daitu/native.log` is Adobe Flash Player Debugger 32 output. The unmodified source `wankai()` sets the parent transformation flag, stores HP/energy, and replaces the body. The immediate observation reads undefined body HP/energy; the next reads 671/234. The next parent/body frames are **2/1292** because target `doWanKai()` jumps to its opening label (1291) before advancement. This differs from r07 forcing the parent goto directly with the transformation flag false: parent/body **2/2**. The runtime tests cover both paths; they do not incorrectly require body frame 2 after a real wankai.

The native root harness is not named p1, therefore its key values take the p2 branch (101–110). The Godot fixture explicitly uses p1 and checks the corresponding source p1 branch (91–100). This capture is not a full combat replay or image parity claim. Unchanged nested definitions and non-action tags are fingerprinted in build.json.

Reproduce the capture with `tools/probes/build_form_helper_probe.py --fighter daitu --observe-frames --ffdec <ffdec-cli.jar> --output <scratch>` then `tools/probes/capture_native_player.py <scratch> <log> --player-app <Flash Player.app> --allow-window-activation --timeout 40`. Never write instrumentation into game/ or scripts/.

## Runtime assertions

- `form-replacement-reference.log`: **4/4** real target-profile cases: wankai with useAI undefined/false/true, and direct parent goto. Checks HP/energy transfer versus undefined raw-goto HP, new state/retired sentinel and khit reset, source load values, wrapper visibility and scale_X initialization, old pending-frame retirement, source path references resolving the new body, old captured function calling the new body's method, root interval survival, and callback registration on the new placement phase.
- `form-replacement-checkpoint.log`: **1/1** full BattleCheckpoint test. Save base, replace, save target, restore base, repeat replacement, restore target, then deliver the restored captured root interval. Validates old and new immutable profile graphs remain distinct and live references survive actual rollback.
- `form-manifest-activation.log`: **1/1** Main match initialization consumes the shipped manifest without test-side form configuration; actual source wankai replaces the body and retains HP/energy and session key bindings.
- `form-helpers.log`: **7/7** source helper sets and **28/28** existing native helper observations.
- `undefined-increment.log`: **3/3** declared undefined increment assertions. Undefined becomes NaN and remains NaN on another increment, matching the separately captured Sasuke source behavior.

Run using `Godot --headless --path godot --script res://tests/form_replacement_reference.gd` and `res://tests/form_replacement_checkpoint.gd`, with production profile packages built by `tools/importer/build_form_profile.py`. No pixel tolerance or allowlist was added.

## Limits

Only Daitu has this end-to-end profile closure and native-bound execution check. Minren/Sasuke/Yihu and the newly exposed wankai branches still require their complete target graph and native acceptance; runtime support for slot-health callbacks alone does not authorize them. Parent gotoAndPlay remains a hard import error because the parent timeline clock is not implemented. This evidence does not resolve the outstanding placement/filter or full AS audit blockers.
