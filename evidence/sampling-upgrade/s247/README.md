# s247 — Yulong attack k1atm.mian source-list provenance

User-selected [s239 residual](../s239/README.md), based on master
`45e93c67de6878ca7ac361af630100f3e53b34c3` (merged s246 / PR #124).
Branch `feat/s247-yulong-k1atm-provenance`. Only the unchanged
`yulong__attack__neutral__ground__near` s239 tape. Native menu name is 石田.
No s240 completion-boundary work, other cells, gameplay/Godot changes or reruns
of the Chad/Deidara residuals. `production_admitted=false`;
`native_parity_proven=false`.

## Result: the missing operand is target, not a list or stamp

One native capture contains **5,079 events**, 61 geometry begin/end pairs,
245 bound box records and three retained `missing-source-list` errors at ticks
16–18. Receipt revalidation exits **0**. The diagnostic source-list gate and
the unchanged full geometry gate both exit **1**. No complete geometry report
is admitted; no suffix or failing tick is removed.

Nine new observations distinguish the original predicate's four operands:

| Boundary | Sequence / tick | Observation |
| --- | --- | --- |
| Root before geometry | 3509 / 15 | Selected nested path absent |
| Sprite 2 initializer, after existing stamp | 3534 / 15 | Nested path present; stamp ID 71, source Sprite2/frame1, birth display 448 |
| Root / exact source-list check | 3544 / 3548 at 16; 3566 / 3570 at 17; 3586 / 3590 at 18 | Same receiver/stamp; lists defined with lengths 96, 5, 10; direct parent pn undefined; target undefined |
| Root before geometry | 3607 / 19 | Selected nested path absent |

At initialization and every live sample:

- `_fsArray`, `_fzfsArray`, and `stgks` are all present. Their actual contents
  are retained in `provenance.json`, not replaced with empty arrays.
- `__aiGeoId`, `__aiGeoSource`, and `__aiGeoBirth` are present and stable.
- Direct parent is `_level0.game.p1.mc.k1atm`; its `pn` is `undefined`.
- The original target expression `_root.game["p" + mc._parent.pn]` yields
  `undefined`. This is the **only true failure predicate** at ticks 16–18.
- Grandparent is `_level0.game.p1.mc`, with `pn=2`. This is an observed context
  field, not authorization to replace the original target with an ancestor lookup.
- Both `getHitObj` and `getStgHitObj` are functions, so the existing structural
  geometry walker includes this nested instance as a receiver. Function presence
  alone does not prove source gameplay invokes it as a normal body hurt receiver.

The diagnostic localizes an owner-context/receiver-classification gap rather
than missing list initialization or missing stamp provenance. It does not fix
classification, change target resolution, suppress the error, or claim native
geometry parity. Source-driven receiver ownership remains a follow-up.

## Source chain and scope of instrumentation

`source-binding.json` retains locked source hashes, selected script bodies and
placement facts from the hash-verified existing XML archive:

1. Yulong Sprite 345, frame 188 places new Sprite 104 at depth 28 named `k1atm`.
2. Sprite 104, frame 1 places new Sprite 2 at depth 2 named `mian`, with no clip
   actions on that placement. Sprite 2's frame-1 script declares the two functions
   and initializes all three lists; the existing observer appends its stamp there.
3. Sprite 104's frame-1 script is `stop()` and does not initialize `pn`. The
   projectile's authored outer enterFrame handler refers to its own `_parent.pn`
   (the fighter body), while the geometry walker's nested receiver expression
   refers to `mian._parent.pn` (the projectile). These are different contexts.
4. Static Sprite 104 frame 5 removes depth 2 and renames itself `abcd`. The
   tick-19 path-absence sample is not independently an exact removal/rename
   boundary or a proof of the projectile's entire lifetime.

The s240 archive is reused **only as existing static XML input**; no display
capture or completion-boundary gate is executed or altered.

The opt-in `--yulong-k1atm` flag accepts only the exact s239 case and enables
existing geometry capture. It adds read-only snapshots immediately before root
geometry at ticks 15–19, immediately after the original target computation for
this exact path, and after this exact hash-checked Sprite2 source block and its
existing stamp. It logs the already computed target at the failing check,
without substituting an ancestor, calling gameplay functions, or changing the
four-way predicate. Original `sampling_geometry.as` and its collector are unchanged.

## Validation and limits

`gates.json` records actual commands/exits and timings. `provenance.json` marks
`observation_complete=true` and `source_list_checks_complete=false`, identifying
`target == undefined` for each failing tick. `capture-summary.json` retains the
three original-category geometry errors. `negative-proof.json` removes each of
the three marker kinds: native sequence validation and provenance validation
both reject; restoring the raw stream restores only the valid receipt, not a
passing source-list gate.

**150 focused sampling/probe/import tests pass**, including exact-source/tape
rejection, unchanged original initializer/predicate checks, and missing/wrong-source/
wrong-list-length actual-evidence negatives. Integrity, handoff and contract checks
are retained. All 122 fight actor-state payloads match the retained s239 native
capture; this is not a Godot comparison or proof of timing equivalence.
Pre-fight counts and display offsets differ and remain untrimmed. M0-02 stays pending.

## Reproduction and restoration

Use a fresh build path and run ID for each new capture. The actual capture used:

```sh
python3 tools/probes/build_ai_reference.py \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s247-build-r01 --run-id s247-yulong-k1atm-r01-20261029 \
  --frames 60 \
  --move-case evidence/sampling-upgrade/s239/yulong__attack__neutral__ground__near.json \
  --p1-character 石田 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 \
  --yulong-k1atm
```

`capture_native_player.capture(build, trace, 180, lock_timeout=45)` used the
shared `/tmp/bvn-native-flash-capture.lock` with authorized window activation,
then `sampling_native.seal` wrote the receipt. The lock was released on return.
Capture took 30.756 seconds; one attempt, no rejected capture retries. Environment
and player path are recorded. The existing static-loader receipt still has no
independent runtime fighter attestation (`runtime_fighter=null`).

Restore `native-build.tar.gz` inside `/tmp/bvn-s247-build-r01`, decompress the raw
trace to `/tmp/bvn-s247-capture-r01/native.log`, and restore the receipt to
`/tmp/bvn-s247-capture-r01/receipt.json`. Keep the original s239 case and this
commit's probes at their receipt-recorded paths; never rewrite hashes.

```sh
python3 -m tools.sampling_k1atm_provenance \
  --case evidence/sampling-upgrade/s239/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s247-capture-r01/receipt.json --output /tmp/s247-provenance.json
# Exit 1: original target lookup remains undefined; complete diagnosis retained.
python3 -m tools.sampling_geometry \
  --case evidence/sampling-upgrade/s239/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s247-capture-r01/receipt.json --output /tmp/s247-geometry.json
# Exit 1: missing-source-list; no full geometry report admitted.
python3 -m unittest tools.tests.test_yulong_k1atm_observer
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Residuals: source-driven receiver eligibility/owner context, exact intra-frame
lifetime, full native/Godot geometry and AS ownership remain unproven. No automatic
ancestor walk, fabricated list, stamp repair, or receiver exemption is introduced.
Original tapes, rejected traces and strict gates remain intact. No merge/deploy.
