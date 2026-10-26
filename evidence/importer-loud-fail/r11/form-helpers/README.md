# BODY-owned transfer and root interval checkpoint

This is an executable helper consumer, **not the complete replacement transaction**.
Production form frame calls remain rejected; no cache or gameplay data was updated.

## Implemented

`compile_ai_body.py --form-helpers` compiles the actual initial BODY functions
wankai, doWanKai, initCtrl and randAI, plus the existing initial feixue/loseHp.
The seven fixtures cover daitu458, minren764, Sasuke603, yihu638, Byakuya631,
rifagu638 and rukia533. The similarly named AI controller predicate wankai is a
separate function/scope and is not substituted for the BODY helper. Metadata
records original script and SWF hashes; the builder is reproducible. Unknown
statements, key targets, timer forms, methods or helper parameters fail with the
SWF and initialization script path.

`SourceFormContext` owns wrapper transfer HP/energy and binds current body keys.
The same object must survive replacement; its transfer dictionary does not belong
to the retiring body's AiSourceState. `AiBodyContext` requires an explicitly
connected form context; absence asserts. Native consumers for parent/controller
operations are still required through its dispatcher. They are recorded, not
implemented as gameplay, in the helper fixture. The dispatcher must report old
receiver liveness for parent nextFrame. This prerequisite prevents publishing
these generated helper programs as if they completed a usable form profile.

`SourceRootIntervals` owns feiint/feiint2/airanset handles independently of body
driver lifetime. Assignment registers a distinct captured function and overwrites
only the source field; it does not cancel the old interval. clearInterval cancels
only the referenced ID and leaves its numeric handle field in place. Missing or
cancelled handles are no-ops. Handle snapshots are validated before the queue is
mutated and preserve cancelled handle values. The production root match owner is
**not yet wired**. AiCpuDriver.stop remains match teardown, not replacement.

The source helper test exercises undefined/false/true useAI, ordered initCtrl
boundary effects, HP/energy restoration, both timer overwrite and explicit clear,
source-addressed five-value randAI delivery, independent root handles and strict
rollback. Diagnostics preserve the source `initCtrl: true/false` text. Generated
helpers preserve both player and CPU branches even when other BODY functions are
compiled in CPU-only mode.

## New native finding: nextFrame retires the calling function

Seven original fighter movies were captured in Flash Debugger32/Rosetta. Only the
root observer is patched; original nested definitions and non-DoAction root tags
are byte-identical. The observer invokes the actual BODY wankai with HP671, energy
234, wudi=true, root_y17, useAI undefined and paused movement.

All seven show, immediately after the call:

- parent 万解=true and transfer HP671/energy234;
- root_y stays17: wankai's trailing `_root._y = 0` **does not execute**;
- mc.hp and mc.ql are already undefined, before replacement initialization;
- next observation restores HP671/energy234 and assigns the ten p2 keys101..110;
- no feiint was registered in this invulnerable branch.

A parent nextFrame that removes the executing body therefore cannot be lowered
to an ordinary synchronous method that resumes the old function afterward.
Generated wankai checks the consumer's receiver-liveness result and returns when
the old receiver retires. This is not a claim about Godot node identity. The
fixture dispatcher explicitly reports retirement; it does not actually replace
the visual/combat/controller profile.

Native minren and yihu additionally change root_y17 to12 by the next observation;
the other five keep17. This target continuation remains recorded and unresolved.
The helper comparison deliberately compares only transfer/keys/interval absence
and the pre-initialization wrapper prefix. It does not fabricate the native
undefined body fields or claim target-frame root-coordinate parity.

## Source-first scope

1. Helpers are exact initial BODY functions in the seven metadata source paths;
   every statement is compiled, including trace and the trailing root_y write.
2. Parent nextFrame leaves root frame1 and selects the actual next parent placement;
   the observer preserves all placement/load tags. Existing r07 captures document
   target frame2 loads and fresh khit/reset behavior for the first four sources.
3. wankai exits through parent nextFrame. doWanKai first calls initCtrl; if the
   wrapper flag is true it restores HP/energy, binds keys, gotoAndStop("开场"), play().
4. Continuation retirement and transfer/key values come from the native captures,
   not guessed behavior. Timer ownership tests lock the explicit source operations.
5. These are isolated original fighter-movie helper captures, not a complete
   original main.swf transformation combat replay. Full replacement remains blocked.

## Validation

`godot.log`: **7/7 helper sets,28/28 native helper observation groups**, no script
errors. Native logs contain35 raw observations (including seven done markers).
This count excludes full replacement, controller effect execution, callback phase
ordering and source timer cadence. Separate Python tests compare generated fixture
bytes/metadata to the source compiler and reject modified unsupported statements.

Controller field normalization now respects identifier boundaries and string
literals. Sasuke's `_parent.khitn` is no longer corrupted into `value("khit")n`;
unsupported khitn remains a hard error. Controller compilation adds exact SWF and
callback path around expression failures (including nested controller functions).
No missing field was defaulted or accepted to make staging pass.

## Reproduce

```sh
python3 tools/probes/build_form_helper_fixture.py --output godot/tests/fixtures/form_helpers
python3 tools/probes/build_form_helper_probe.py --fighter daitu --ffdec "$FFDEC" --output "$OUT/daitu"
python3 tools/probes/capture_native_player.py "$OUT/daitu" "$OUT/daitu/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
# Repeat native probes sequentially for minren/sasuke/yihu/byakuya/rifagu/rukia.
"$GODOT" --headless --path godot --script res://tests/form_helpers_smoke.gd
python3 -m unittest tools.tests.test_form_helpers tools.tests.test_form_callbacks tools.tests.test_controller_aliases
```

## Remaining integration requirements

Atomic target profile/assets swap, load/frame-script/enterFrame queue phases,
old callback retirement/new registration, complete path-reference resolution,
main root timer ownership, concrete updateGJL/controller initialization effects,
and minren/Sasuke later feixue reassignment are still missing. The helper layer
must not be used to remove the existing frame compiler errors at these sites.
