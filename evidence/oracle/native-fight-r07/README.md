# r07: correct the fighter asset binding; retain initial-state refusal

Offline only; zero Flash launches, inputs or captures. Official remaining UNKNOWN;
not claiming above floor. Work was limited to receipt/source diagnosis, a targeted
asset/site correction, one offline compile and tests. M0-02 stays pending;
production_admitted=false, native_parity_proven=false, oracle_accepted=false.

## Diagnosis supported by receipts and locked source

r06's raw flashlog says `loadman : p1,一护`; its tagged game-state rows consistently
select `一护`. The pinned registry in `scripts/main.json`, `frame_6/DoAction.as`,
registers **一护 → yihu.swf**, while **一护2 → ichigo.swf** is a distinct clone.
The loader in `DefineSprite_1900/frame_1/DoAction.as` obtains the selected registry
entry and calls `loadClip(fighterDir + entry.url, game[pr])`. `frame_7` sets
fighterDir to `fighter/`. r05/r06 modified **ichigo.swf**, not **yihu.swf**.

The retained temporary movie copy still matches the receipt hashes for main,
ichigo and yihu; yihu's captured hash equals its locked original hash. Thus the
observer was installed in the wrong asset for the source-selected character.
This is a concrete configuration/source-routing defect, not an inference that AI
ran, the player chose a transformed form, or physical J was ignored. The raw
loadman line is account-wide, corroborated by tagged selection; neither substitutes
for loaded-byte/method attestation. r06 did not record a loaded URL/decision install
marker, so actual loaded definition identity at J remains unproved.

Correct base-form source: `scripts/fighter/yihu.json`, root frame1 places body638
with load-time `kis = Key.isDown`. Body638 frame1 places helper16 at depth31;
`DefineSprite_638/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`
calls `doAllAction()` if `gameRunning()`. Helper16's frame1 defines the 39 lexical
queries. This source chain justifies changing the observer target to yihu/Sprite16.
Placement/lifetime tags are not changed. It does not prove every query executes.

The ten incomplete timer boundaries are exactly local timer ordinals1–5,
entry and exit; their undefined actor field is **HP (field index5)**. The locked
`frame_8/DoAction.as`, `var chushi = function()` contains the assignment
`_root.game.p1.mc.hp = _root.game.p2.mc.hp = _root.maxhp;` after position/facing setup.
The source body load initializes several fields but does not establish HP there.
These facts explain why a loading snapshot cannot be assumed to be a fully
initialized fight state. They do **not** prove when chushi executed relative to
these timer callbacks: r06 has no initialization-boundary event. Do not discard
ordinals1–5, fill undefined HP, or treat the first complete snapshot as tick zero.

`diagnosis.json` retains source paths/lines, exact statements, input-J receipt,
screenshot/session/raw-log hashes, copy comparisons and all ten failing boundaries.
`diagnose.py` regenerates this bounded cross-check; missing temp copies become null,
not invented loaded-byte proof. Tests preserve the failures and routing distinction.

## Engineered offline

The isolated builder layers on immutable r03, correcting r05's external asset to
`game/fighter/yihu.swf`, `DefineSprite_16/frame_1/DoAction.as`. It retains every
original expression except explicit lexical forwarding through owner.kis(code),
called once with the original receiver and argument; short-circuit order survives.
An appended `decision-installed` event includes `yihu-sprite16` and this._target.
That future event can distinguish definition execution from mere compilation.
No global API replacement, forced timeline or runtime changes were introduced.

One temporary offline build succeeded. Final changed payloads versus originals:
main's four existing r05 DoActions, plus yihu `root/19:39/sprite16/1:12`.
All other headers/tag topology/payloads and73 other assets remain unchanged;
ichigo is now unchanged. `build.json` pins all sources/outputs/compiler and the
new facility. Both instrumentation layers and compiler logs are retained compressed.
The timer observer is deliberately unchanged; its rejection remains valid.

```sh
python3.11 evidence/oracle/native-fight-r07/build_observer.py \
  --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-m002-r07-recheck \
  --run-id m002-r07-offline-recheck
python3.11 -m unittest discover -s evidence/oracle/native-fight-r07 -v
python3.11 evidence/oracle/native-fight-r07/diagnose.py
python3.11 evidence/oracle/native-fight-r07/analyze.py
python3.11 evidence/oracle/native-fight-r07/analyze.py --require-oracle
```

Both r07 gate commands intentionally return1: no r07 live proof exists. They are
an explicit no-live refusal, not a new permissive parser or replacement acceptance
validator. The unchanged r05 analyzer on immutable r06 also returns1 in both modes
with `Incomplete actor state at clock boundary`. `checks.json` retains actual exits.

## Minimum discriminating next capture (NOT authorized or executed here)

Before one freshly authorized foreground run, prepare and audit source-local
markers around the existing loader request (selected key, resolved URL, target)
and actual onLoadInit callback, and immediately before/after the existing chushi
HP assignment (both actors, positions, source frames, readiness and pause flags).
Keep original calls/assignments exactly once and retain all early states.
This marker extension is a plan, not implemented or claimed compiled in this cut.
Use the corrected Sprite16 install marker and key forwards to test whether the
loaded helper and positive native returns belong to the selected P1 instance.

Then, under a new run tag and fresh user foreground authorization, use the exact
movie-PID AX/CG/System Events path, rechecking main **and yihu** copy hashes;
prior r06's main/ichigo build guard must not be reused unchanged. Preserve the
physical input receipt, complete log from boot and all marker/actor boundaries.
Stop on focus loss; no additional run without authorization. Require selected URL,
load callback, helper install, owner and actual key-return evidence to agree.
If installation is observed but returns remain absent, investigate active callback
reachability/AI/pause from observations; do not switch forms or broaden queries by
name guessing. Initial-state admission must prove initialization completion and
phase ordering while retaining the loading prefix, not trim it to make gates pass.

Still unproved: loaded definition identity, positive corrected queries and downstream
consumption ticks, exact initial boundary/global clock, complete random tape,
exclusive complete state trace, deterministic repeat and SOURCE_FIRST same-input
original/instrumented noninterference. No product/acceptance obligation is closed.
