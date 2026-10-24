# r21 — exact pixel inventory and fail-closed semantic audit

**Not merge-ready. No runtime change or newly cleared pixel group this turn.** The current renderer was measured against pinned native captures, and two audit reporting holes were fixed. The 34 placement errors remain cleared; complete AS ownership and exact component images remain distinct unresolved gates.

## What changed

- `audit_importer.py` now exits1 for incomplete semantic coverage and failed visual-cache checks. Previously it unconditionally reported `incomplete_semantic_audit` in JSON but could exit0, and its exit condition ignored visual checks. A green placement scan was therefore liable to be mistaken for full semantic acceptance.
- All6,324 DoAction blocks remain in owner review, including2,073 blocks containing recognized visual controls. Finding `stop()`/goto does not prove that other statements in that block have consumers. Existing runtime/control compilers are not changed.
- A source-hashed inventory lists all8,853 locked scripts, event handler locations,2,407 clip-action intervals/2,485 event records, and252 syntactic importer skip sites. These are **unverified coverage obligations**, not8,853 newly discovered missing runtime implementations. Existing selected-function compilation/cache checks do not certify entire scripts. Likewise, a `continue` is not inherently a bug. No row was allowlisted or falsely assigned a consumer.
- The new component inventory reports source SWF/hash, owner sprite, placement frame/depth, child clip, wrapper/child observation frames, per-channel changed-pixel counts, maximum deltas and example worst pixels. It rejects missing images and changed locked sources. RGB comparison is over the original harness's opaque background; it is not an alpha-channel measurement.

## Remaining exact pixels

See [per-source table](pixel-inventory.md), [all54 images with exact locations](component-pixels.json), and adjacent native/runtime PNGs under components/. Native captures are reused from r03, source hashes rechecked; no new Flash launch or environment change this turn.

- Components: **9/54 images exact**, **4,242/4,242 clocks match**. The45 failing images include Jinye, Jiraiya, Lanran, main/XG_mfdjx, Orochimaru, Yijiao and Yulong. Maximum channel deltas are substantially larger than1 in these real components (up to177); do not attribute them all to scalar filter rounding.
- Color groups: **3/5 exact**. Matrix100% has64 changed channels; chain100% has128; maximum delta1.
- Filter/CXFORM order: **2/4 exact**. Glow100% and50% each have one changed channel, maximum delta1.
- Scalar ColorMatrix: **20/24 exact**; comparison contains the exact input row/component, expected and observed RGBA.
- XG_rush: **21/21 entered source frames match**;234/5,103 RGB channels differ, maximum135. Use r05/rush-native/native.log, not the historical after-frame timer experiment under rush-native-final, which intentionally is not the valid frame oracle.

Every strict comparator exits1 on its remaining differences. No reference output or tolerance was changed. Next rendering experiment: compare unfiltered input rasters at the same fractional transforms before tuning filter math, then isolate the Matrix byte arithmetic using the existing scalar/ramp probes. Full action/text/image fidelity is not implied by passing primitive blend or shadow tests.

## AS / clip-action remaining scope

[audit-summary.json](audit-summary.json) records62 locked SWFs, zero placement failures,26/26 cache acceptance and98/98 current visual closures. The **full audit exits1**. The complete review lists are:

- source-script-review.json: every locked decompiled path, source hash and event-handler lines requiring a complete ownership proof.
- frame-action-review.json:6,324 bytecode action blocks, including recognized controls that previously disappeared from this inventory.
- clip-action-review.json: exact SWF/sprite/frame interval/depth/event/code-hash scopes. Metadata preservation is not event-body execution proof.
- importer-skip-review.json:252 compiler skip/empty-return sites requiring contextual review.

This is not a claim that each listed script should be compiled by the BODY compiler, or that every unported SWF belongs in the current shipped closure. Remaining work is to map complete statement/event scopes to actual consumers, reject uncovered reachable semantics at import, and retain separate full-source blockers for unsupported content. No such mapping was fabricated to make this audit green. The Byakuya scoped exception is unchanged.

## Reproduction

Run from the repo root with the same Godot4.7.2 Compatibility/Pillow setup as r20 and a fresh `$OUT`. Reuse source-pinned native captures without launching Flash:

```sh
mkdir -p "$OUT"
cp -R evidence/importer-loud-fail/r03/components/components "$OUT/components"
# Decompress each components/*/native.log.gz to native.log (keep the gzip file).
BVN_REVIEW_DIR="$OUT" BVN_GODOT="$GODOT" python3 evidence/characters/pain/visual-parity/review/probes/render_components.py
python3 tools/probes/compare_filter_components.py --output "$OUT"
python3 tools/probes/inventory_component_pixels.py --directory "$OUT" --output "$OUT/component-pixels.json"
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/audit.json"
```

The final three commands intentionally exit1 until their respective exact/semantic gates are complete. Existing color/rush reproduction commands are in tools/probes/flash_filters/README.md and r05/README.md. Tests cover incomplete/failed audit scopes, recognized controls remaining visible, channel-separated image differences, missing native images and source hash mismatches.

## Acceptance boundary

See acceptance-summary.json and logs. Runtime, generated production assets and locked game/scripts are unchanged. Whole-roster and the full production GPU suite are therefore not rerun; r20's227/227 and7/7+22/22 remain historical evidence, not new runs. This turn reruns current component/color/order/rush/arithmetic measurements, Python, fresh62-SWF/cache audit, protected/integrity/handoff/contracts, online fingerprint and full local Web build. Build acceptance of the current shipped subset and failed full semantic audit are intentionally reported separately. No merge, deployment, Worker change or new port.

Final results: Python500 passed+2 skipped; PROTECTED_FUNCTION_OK, reviewed integrity hashes, handoff/contracts, fingerprint8/8 and full local build_web exit0 (including post-export manifest/metadata) pass. Full semantic audit and strict pixel parity remain FAIL as listed above. No runtime changes; no new full-roster/full-GPU-suite claim.
