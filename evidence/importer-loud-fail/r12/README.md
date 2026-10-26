# r12: first complete production body-replacement graph

Draft PR #48 remains **not merge-ready**. Daitu's real parent/body replacement is
now wired and admitted through source-checked production assets, improving cache
acceptance from **19/26 to 20/26**. The other six form entries remain hard errors.
No allowlist, pixel tolerance, new character port, merge or deployment was added.
Locked `game/` and `scripts/` inputs are unchanged.

## What executes now

The source 458/1307 `wankai()` retires the old body, frame queue and callback
registrations immediately. On the next display phase the runtime installs sprite
1138's visual/combat/controller/state/audio package, executes source load and
initialization, restores HP/energy, binds keys and registers new callbacks.
Source path references resolve the replacement; captured functions and root-owned
interval IDs retain their distinct ownership. This also works through actual
BattleCheckpoint restoration, including restoring the old profile and replacing
it again.

The native distinction matters: real wankai sets the wrapper flag and reaches
parent/body **2/1292** through target `doWanKai()` and the opening label. A direct
parent goto with the flag false reaches **2/2**. Neither path is approximated by
Godot object identity. See [native and runtime evidence](forms/README.md): four
end-to-end cases, one full rollback case and one Main activation case pass.

The manifest pins the complete base and target packages. Source audit recompiles
AI, BODY, controllers and predicates and resolves every outgoing form edge.
Build validation rejects changed assets, dropped calls, altered loads and missing
targets against the reviewed contract; form assets participate in the runtime
fingerprint. See [build guard](form-build-guard/README.md). The profile builder
also reuses the existing player hurt-hook compiler: Daitu base/target retain
three/four placement callbacks rather than silently omitting them.

## Source-first checks

1. Frame scripts: retained Daitu 458/1307, 458/1309 and 1138/1, with exact source
   and load hashes in the manifest and reviewed frame-call catalog.
2. Placement: parent frame 2 replaces depth-1 `mc` with sprite 1138; load values
   precede new frame initialization, and new enterFrame eligibility starts on the
   following tick. The original nested definitions are unchanged in the probe.
3. Exit: wankai's nextFrame terminates the old function before its trailing root-Y
   assignment. The pending old 1309 action is retired. Target doWanKai controls
   the opening goto; label ends are not guessed as return-to-idle.
4. Invariants: old sentinel disappears, khit resets, wrapper HP/energy transfer,
   current-path field/method resolution, callback ownership and independent root
   interval identity are asserted against the r07–r12 native observations.
5. Comparison: fresh original-player sampling and production Godot/rollback/Main
   tests are linked above. This is bounded lifecycle/state parity, not a full new
   form combat replay or image-parity claim.

## Newly detected or retained blockers

- **Minren:** parent2/body1293 requires parent3/body1821 at 1293/1157. The latter
  root frame3/depth1 Glow (7x10, passes3) has no wrapper-filter consumer and fails
  extraction. Parent2 alone is not a complete graph.
- **Yihu:** parent2/body1180 wankai at 1036 requires parent3/body1672. Its source
  必杀 label537 has no unique compiled energy cost; controller390/depth34 uses
  unimplemented `_parent._parent._xscale *= -1`. Both remain hard errors.
- **Sasuke:** a complete parent2 candidate package now compiles, but complete
  native/Godot/rollback acceptance and persistent p1bs/p2bs ownership are still
  missing. No production manifest enables it.
- **Byakuya631/1110, rifagu638/1233, rukia533/1164:** wankai graphs remain
  unadmitted. The prior Byakuya631/985 exception retains its exact hashes and
  base-form scope; no new exception was introduced.
- **Yulong root frame1/depth1:** zero-size Blur on the body wrapper is now rejected
  rather than dropped. Zero radius does not prove harmless cache quantization.
- The original **34** locked-source placement errors remain. The fresh 62-SWF
  inventory additionally pins wrapper obligations and rejects legacy/unknown
  placement tags. With the Daitu target included, shipped closure checks are
  **89/90**, failing Yulong. See [placements](placements/README.md) and the final
  [closure report](placements.json).
- Exact color/order results remain **3/5** and **2/4**, with maximum error1.
  Full component/XG_rush image parity and the complete AS/clip-action audit remain
  open. The 2,048-sample arithmetic ramp is diagnostic, not a parity fix.

The missing-field investigation also prevented incorrect defaults: original
Sasuke khitn++ produces NaN; original Yihu's missing nn satisfies its Less2/Not
`>=` branch. Candidate compilation now preserves those semantics, with actual
original callback tests. See [native fields](missing-fields/README.md) and
[three candidate packages / recursive blockers](target-profiles/README.md).

## Acceptance and reproduction

Final counts and logs are recorded in [acceptance-summary.json](acceptance-summary.json).
Build/fingerprint remains FAIL because the other six form graphs are unsupported;
the strict color/order comparisons also remain FAIL. Passing unit/render checks
do not override those blockers.

```sh
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 -m unittest discover -s tools/tests
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/build_online_manifest.py --check
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
```

Rebuild replacement assets with `stage_parent_forms.py` and
`build_form_profile.py`; the latter compiles complete candidate packages without
automatically activating them. Native probe reproduction is in each linked
evidence directory. Three parallel workers were used: `form_runtime` (runtime
and native replacement), `placements` (placement/build/root ownership), and
`pixels` (pixel diagnostics, missing scalar semantics and target packages).
Only the lead performed Git commits and pushes.
