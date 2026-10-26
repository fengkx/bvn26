# Shipped cache refresh and XG_rush, r05 (2026-10-23)

Draft PR #48 remains blocked, but cached fighter acceptance advances from 0/26
to **21/26** without relaxing guards. Twenty-one production ai.json files now
contain their audited frame calls. XG_rush is materialized from the locked main
SWF, including its nine bitmaps, source sound and explicit unload event.
No production GDScript or shader changed. No new character/form was ported.

## Cache and import acceptance

`tools/importer/refresh_frame_calls.py` recompiles each context, verifies source
identity, substitutes only frame_calls, and runs the existing cache/asset guard
before writing. `--write-successful` explicitly permits partial progress; the
command still exits 1 when any context fails. cache-refresh.json records each
result. Other context fields retain their earlier independent owners: Kakashi,
Renji and Rifagu have deferred controller_scope_fields/limits differences;
Yulong has a deferred sensing difference. Those were not mixed into this change.

frame-call-audit.json confirms 21 compilable contexts and 21 valid caches. The
five remaining errors are unchanged and exact source is in goto-blockers.json:

| Source | Sprite/frame | Missing native operation |
|---|---|---|
| Rukia | 533/141 | `gotoAndPlay(130)` into the middle of label 127..144 |
| Daitu | 458/1309 | `_parent.gotoAndStop(2)` form replacement/load |
| Naruto/minren | 764/1382 | `_parent.gotoAndStop(2)` form replacement/load |
| Sasuke | 603/1232 | `_parent.gotoAndStop(2)` form replacement/load |
| Ichigo/yihu | 638/1055 | `_parent.gotoAndStop(2)` form replacement/load |

Current frame events route goto through a label-only consumer; substituting
Rukia's label start 127 for absolute frame 130 would be wrong. The four parent
jumps replace the base-body instance and execute another form's load, for which
there is no parent/form-switch frame-event consumer. These paths remain hard
errors pending real implementations, not exceptions based on disabled controls.
Byakuya 631/985's reviewed hash/form scope is unchanged. No allowlist was added.

All **89** current generated timelines (including new XG_rush) pass cached
placement and nested-control validation. placement-acceptance.json maps all
34 locked-source placement errors to current generated closures: none occurs
inside a retained slice. They remain errors outside those slices, not proven
harmless. The list is unchanged: blend 7 Kenshin (1), blend 13 minrenx (1),
qilabi (30), main (1), and main 1504/frame 1 DropShadow (1). This is a refreshed
closure check against r04's 62-SWF scan, not a new raw XML scan or full AS audit.

Build/fingerprint acceptance still exits 1 at Yihu 638/1055. Existing compatibility
outputs were not regenerated around the gate and are now stale with respect to
the changed content. They must be regenerated normally after all blockers clear.
Shipped fighter/assist/stage import acceptance is therefore **not green**.

## XG_rush source-first and native evidence

1. Original main export XG_rush is sprite 22, 18 frames. Its sole DoAction is
   `this.unloadMovie()` at frame 17; frame 1 includes sound 5. The complete
   placement/frame sequence is retained in generated/effects/XG_rush/timeline.json.
   The main frame-8 shunbuxg wrapper calls addChildXG(player,"XG_rush",0,0), pinned
   by the r04 source evidence and each compiled wrapper hash.
2. The probe attaches a fresh instance at 128,128. Original definition tags,
   internal PlaceObject/MOVE tags, bitmaps, sound and DoAction are unmodified.
   definitions-verification.json confirms all 10,099,521 definition bytes are
   identical before and after root probe-script import. export-report.json pins
   the original main SWF, JPEXS output files and source asset hashes.
3. There is no guessed label-end exit: generated effect.json retains the explicit
   frame-17 unload. Existing HitEffectRuntime consumes it; no new scheduler was
   invented. This is an isolated attachment, not a full combat input capture.
4. A GPU regression checks **21/21 entered source frames** against captured native
   rows. Flash's root enterFrame observer sees the entered frame before child
   frame actions. Godot records effect_frame before deferred node destruction,
   including the entered unload frame 17. This measures visited source frames,
   not full callback ordering or an assertion about when a node reference dies.
5. Captured with Adobe Flash Player Debugger 32.0.0.465/Rosetta, through the existing
   capture_native_player.py. Raw logs, actual probe source, build hash and capture
   environment live in rush-native/. Rendering uses Godot 4.7.2 Compatibility.
   The refreshed 21 caches are also exercised by the final whole-roster replay.

Native/Godot RGB samples are compared directly over opaque black, with no
representation conversion or tolerance: **5,103 channels, 234 different,
maximum error 135**. The clock assertion passes, but rush-comparison.json exits
1. This asset is no longer silently absent; its pixels are not certified exact.

An after-frame timer experiment under rush-native-final/ is retained but is NOT
the reference: timer scheduling skipped an early observation phase (tick 1 saw
frame 3), so it cannot establish deterministic per-frame correspondence. The
initial after-deletion Godot measurement also omitted entered frame 17; both
reports are preserved. The final entered-frame measurement documents its narrower
contract explicitly rather than claiming identical callback/destruction timing.

A diagnostic-only `linear` mode in the GPU probe tests bitmap interpolation;
it does not change production rendering. The source uses fill_style_type 65
(0x41), distinct from non-smoothed 0x43 in the
[Adobe SWF specification](https://open-flash.github.io/mirrors/swf-spec-19.pdf).
Current production fill rendering forces nearest sampling. Diagnostic linear
sampling still fails (252 channels differ, maximum 100); no approximate sampling
change or new tolerance was landed. Interpolation, transform sampling and edge
coverage require further native work.

## Final acceptance

- Whole roster after Godot asset import: **227/227**, **130,334 states** match the
  unchanged native baselines; roster-report.json / roster.log. The premature
  first run had 3 resource-loader failures before import finished (224 passes);
  pre-import-failures.json preserves them. It is not used as final acceptance.
- Python: **382 run, 380 passed, 2 skipped**, python-final.log.
- Existing GPU regressions: **7/7** asserted subsets; Blur **242/242 / 37,280 alpha
  samples**, blend **38/38**. New rush entered-frame regression: **21/21**.
- Godot player/controller/retained clocks/clip placement smoke: **4/4**.
- Canonical colors remain 3/5 exact; Matrix100 and Glow→Matrix differ by 64/128
  channels, maximum 1. Order remains 2/4 exact; each Glow group has one differing
  channel, maximum 1. Both full strict comparisons remain red.
- Previous 21 real filter/cache components were not recaptured; r03 remains
  9/54 pixel-exact images and 4,242/4,242 clocks. XG_rush is additional evidence.
- PROTECTED_FUNCTION_OK, original 1,086 bytes/SHA; integrity after reviewed
  hashes, handoff and contracts: logs in this directory.
- Cache **21/26**, placement/nested **89/89**, overall build/fingerprint **FAIL**.

No new stability deviation, source-file edit, merge or deployment. Still open:
five goto consumers, full AS/clip-action ownership, all-source placement issues,
remaining context-field review, exact filter/bitmap/component pixels, and final
whole-build acceptance after future changes.

## Reproduce

Use a fresh scratch directory and local FFDEC/GODOT/FLASH_APP paths:

```sh
python3 tools/importer/export_swf_xml.py --ffdec-jar "$FFDEC" \
  --output-dir "$OUT/main-export" game/main.swf
python3 tools/importer/build_ai_effect_assets.py --workspace "$OUT/main-export" \
  --clip XG_rush --output godot/generated/effects/XG_rush
python3 tools/importer/refresh_frame_calls.py --write-successful --report "$OUT/cache-refresh.json"
# Expected exit 1 while five goto consumers are absent; successful contexts are written.
"$GODOT" --headless --editor --path godot --import --quit
python3 tools/probes/build_rush_probe.py --ffdec "$FFDEC" --output "$OUT/rush"
python3 tools/probes/capture_native_player.py "$OUT/rush" "$OUT/rush/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 40
"$GODOT" --path godot --rendering-method gl_compatibility \
  --script res://tests/rush_effect_reference.gd -- "$OUT/rush-godot.json"
python3 tools/probes/compare_rush_probe.py --native-log "$OUT/rush/native.log" \
  --godot-rows "$OUT/rush-godot.json" --output "$OUT/rush-comparison.json"
# Strict pixel comparison currently exits 1.
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 tools/build_online_manifest.py --check
```

[Existing filter reproduction commands](../../../tools/probes/flash_filters/README.md)
remain applicable. No generated SWF/player/tool cache is committed.
