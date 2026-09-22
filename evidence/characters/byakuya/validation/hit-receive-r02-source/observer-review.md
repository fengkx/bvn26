# Source hit/receive observer: Byak 690 guard

This is an instrumented original-player capture, not a Godot parity claim. The canonical fixture is `evidence/characters/byakuya/boundary-r03/byakuya-690-bishaSuper-guard/fixture.json` (Byak P1 / Ichigo P2, Kon helpers, mode 3, both QL 300, P1 down+special, P2 down guard). The unique run is `hit-receive-byak-690-guard-r01`.

At display tick 496 / fight tick 45, source event sequence 3739 recorded `source_hit_test` true for P1 `cbsatm`, parent frame 736, with MATRIX b=-3.5914154052734375 and c=10.374526977539062. Its `_root.game` bounds were [36.65, -221.8, 456.8, 15.05]. The receiver instance is P2 `mc.bdmn` itself; receiver bounds were [321.7, -78.3, 352.25, -26.0]. Sequence 3740 at the same tick recorded the actual receiver packet (`pw=450`, `zl=15`, `htype=击飞`) and source guard branch `break`.

The `target_bdmn_*` columns in the raw event schema are auxiliary data from `player.bdmn` where `player` is the attacker; they are `undefined` in this contact. They are not the defender measurement. Use the `receiver_*` fields for the defender body. The raw values are preserved unchanged in `events.jsonl`.

The native contact sidecar is `/tmp/byakuya-action-audit-native-r01/byakuya-690-bishaSuper-guard.json.contacts.json`. Its attack game bounds are x=36.599998474121094, y=-221.8000030517578, width=420.1499938964844, height=236.85000610351562; defender body bounds are x=321.6499938964844, y=-78.30000305175781, width=30.600000381469727, height=52.29999923706055. Compared to source, native/source edge deltas are approximately 0.05 px on the attack left/right and defender left edge; the other listed edges agree to displayed precision. Do not describe this as exact geometric equality or infer a production defect from the 0.05 px delta without checking the respective bounds-to-twips quantization.

The user has accepted this 0.05 px difference as negligible. It is retained above as measured evidence, but is not a blocker or a reason to change shared geometry. Only a demonstrated behavioral consequence, such as a hit/miss difference, would reopen this question.

Raw capture SHA-256: `a852e453705184f692d7f17f59903616062fda39f4ab6a370122b928ccdc6ed5`. Build JSON SHA-256: `4d16ae513705835efd2c5bbb1632a7f19a74e064c5ee6a9074ad274e73e0c2c2`. Instrumentation diff SHA-256: `71fc1253dc41536ffbd338daf203faec7b3be5adab20e2a4130730c22abc1030`.

The instrumentation leaves the original `hitTest` evaluated exactly once and observes the original receiver packet branch. It adds execution overhead. This evidence covers this fixture/contact only; it is not full combat, all-angle, or all-character parity.
