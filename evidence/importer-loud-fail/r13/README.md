# Importer loud-fail r13 — four additional production form graphs

Draft PR #48 remains blocked. Cache acceptance improves **20/26 → 24/26** without weakening guards. Sasuke, Byakuya, rifagu and rukia now use complete source-bound replacement packages alongside Daitu. Minren and Yihu remain hard errors; the online manifest / preview build must still fail.

## Landed

- Four complete asset/combat/controller/BODY graphs, reviewed against original Flash observations. Main enables the authored transformation input only after manifest preflight. Five admitted graphs pass natural opening → attack+jump → transformation → initialized target, with defined/transferred HP and energy. Source-selected opponent slot `pn` is initialized from the compiled frame1 contract.
- Sasuke's two slots retain captured health callbacks, root selection, wrapper transfer, replacement gap, live path references and independent interval IDs. Root callback objects have stable script identity; root values/interval owners participate in complete rollback. The compiler retains `_parent.万解=true` after interval registration instead of silently dropping it.
- Root interval delivery now passes through the immutable RollbackBattle journal and Main. The authority retains repeating IDs/deadlines and rollback state. **Existing online timing is a documented stability deviation:** online_match supplies simulation-frame milliseconds, and authority samples deliver at most once per interval. These tests do not prove native wall-clock scheduling fidelity. See [exact clock source and tests](root-interval-authority/README.md).
- `prepare_form_graph.py` recompiles and validates the complete dependency graph before publishing its activation, restores installed bytes on ordinary publication failure, and rejects missing shared target effects. It does not claim cross-directory crash atomicity; build hashes reject interrupted graphs.
- Byakuya's source mask882 now accepts one used rectangular contour despite an unused fill-table entry. Multiple used contours remain errors. Rifagu/Yihu special-cost aliases follow proven empty source frames to the actual energy deduction. Controller `*=` uses the existing numeric field consumer. See [target imports](target-import/README.md), [native cost](special-cost/README.md), and [Yihu diagnostic](yihu-graph/README.md).
- No new allowlist. Byakuya631/985 retains its exact historical hashes/form scope; a regression compiles the admitted graph with the exception disabled and asserts the real parent-conditional consumer. The old disabled-transformation evidence is explicitly historical.

Read [source-first boundaries](forms/source-first.md), [native/runtime form evidence](forms/README.md), and [native helper observations](form-helpers/README.md). These are bounded lifecycle/state comparisons, not full transformed combat or pixel parity.

## Remaining merge blockers

1. **Minren:** base764/frame1379 wrapper transfer stays rejected without a complete graph. Parent2/body1293/frame1157 reaches parent3/body1821; the latter wrapper frame3/depth1 Glow7×10/passes3 still lacks a consumer. Do not activate only parent2.
2. **Yihu:** base638/frame1052 wankai stays rejected. Both candidate replacement edges reach native body872/1004 and pass complete rollback, but nested sprite1027/frame1 `_root._y -= 5` (frame3 restores5) is unconsumed. Native rootY12 versus runtime17 is an explicit failing assertion, exit1. All candidate profiles remain outside production. Source hashes and repro are in [Yihu evidence](yihu-graph/README.md).
3. Fresh scan of **62 locked SWFs** retains **34 placement hard errors**, with exact source/frame/construct in [inventory](locked-swfs.json). Shipped closure checks are **93/94**; Yulong root frame1/depth1 zero Blur still lacks wrapper-filter handling. The four new targets pass all placement/control/blend checks. No unsupported field is waived.
4. Strict color results remain **3/5**, filter-order **2/4**, maximum premultiplied RGBA error1, with no tolerance. [Fresh comparisons](pixels/) retain every difference. Real component images9/54 and clocks4242/4242 are prior evidence, not rerun this turn; XG_rush pixels and complete AS/clip-action ownership remain open.
5. Online manifest generation still fails at the unadmitted Yihu graph; runtime/content fingerprint generation is blocked. Fingerprint unit tests passing does not certify a build.

## Acceptance

Final counts and command evidence: [acceptance-summary.json](acceptance-summary.json). Runtime was frozen after the real-input `pn` fix; roster and Godot acceptance were restarted. Old test assumptions that all transformations remain disabled were updated to test only unadmitted graphs; admitted graphs have separate real-input assertions. A stale Python negative fixture now validates the admitted package then removes the source form call and verifies rejection.

```sh
python3 tools/test_importer_roster.py --godot "$GODOT" --output "$OUT/roster"
python3 -m unittest discover -s tools/tests
python3 tools/importer/audit_frame_calls.py --output "$OUT/frame-calls.json"
python3 tools/importer/audit_shipped_placements.py --output "$OUT/placements.json"
python3 tools/importer/audit_importer.py --ffdec "$FFDEC" --output "$OUT/locked-swfs-full.json"
python3 tools/build_online_manifest.py --check
python3 tools/test_online_manifest.py
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/validate_contracts.py
```

The full raw scanner output is scratch; the committed inventory retains all62 sources, hashes, counts, wrapper obligations and every failure. Original game/ and scripts/ bytes are unchanged. Reviewed covered-file hash changes are in reviewed-hashes.json. No merge, deployment or new character port. Workers: form_runtime (critical runtime/native), placements (targets/guards/root authority), pixels (source cost/controller/Yihu native diagnostic); only the lead commits/pushes.
