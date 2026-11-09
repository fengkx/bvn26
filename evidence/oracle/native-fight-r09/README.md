# r09: discriminating live r08 capture

One authorized run, **85.9118 seconds**, movie PID **47665**, tag
**m002-r09-live-20261109-a71f**, from master cdda0875 (#250/#251).
No second run. No human-only prompt, TCC error or focus-loss failure was observed.
The initial pre-activation frontmost PID was87154; all17 subsequent sampled probes
show47665. Focus checks are at operation boundaries, not continuous monitoring.
Owned cleanup left no movie PID. Original assets and all75 copy hashes, including
main and yihu, passed before/after checks. Screenshots show 一护/Naruto active fight.

production_admitted=false, native_parity_proven=false, oracle_accepted=false;
M0-02 remains pending. Official remaining UNKNOWN, not claiming above floor.

## Actual observations, not full acceptance

7,760 fresh-tag contiguous events:

| Kind | Count |
|---|---:|
| fight-key-return | 2,787 |
| positive fight-key-return | **2** (both yihu-decision-9) |
| loader-request | 2 |
| load-complete entry / exit | 4 / 4 |
| decision-installed | 12 |
| chushi-hp before / after | 1 / 1 |
| camera game-state entry / exit | 758 / 758 |
| actor-state | 3,132 |
| timer entry / exit | 24 / 24 |
| intro key-return | 250 |
| random-return | 1 |
| boot / ready marker | 1 / 1 |

`yihu-decision-9` is the `_parent.斩` query in `nornalhit`, line135 of
`scripts/fighter/yihu.json:DefineSprite_16/frame_1/DoAction.as`. The two true returns
are seq6718/getTimer78882/camera ordinal684 and seq6779/getTimer79180/ordinal693;
code74, owner `/game/p1/mc`, useAI=false and both pause flags=false. These are actual
native-alias return observations. The physical fight-J receipt records a0.5s hold
on owned PID47665. No certified synchronization maps OS input time to game tick;
positive query observation is not downstream consumption or global tick proof.

## Source-local event order

- Seq2: request p1/一护 → `fighter/yihu.swf`, target `/game/p1`.
- Seq3: existing onLoadComplete entry for `/game/p1`, loadStep0.
- Seq4: callback body requests p2/鸣人 → `fighter/minren.swf`, target `/game/p2`.
- Seq5: P1 onLoadComplete normal exit, loadStep1.
- Seq6: yihu-sprite16 decision-installed at `/game/p1/mc/instance2411`.
- P2 callback seq13/14; assist callbacks seq21/22 and29/31. These are
  onLoadComplete, **not onLoadInit**. No existing onLoadInit was added or claimed.
- Timer ordinals1–6, both entry/exit, contain undefined HP (12 boundaries).
  The last such pair is seq1130/1133, before HP assignment markers.
- Seq1142: chushi-hp-before, both actor HP undefined. Seq1145: chushi-hp-after,
  both actor HP equal maxhp's exact retained encoding `f:1:9:131072000:0` (=1000).
  Both markers have getTimer62119/camera ordinal182 and paused=true. This proves
  the source assignment transition within this tagged run, not initial fight tick.
- Further helper installations are retained, including seq6728 at getTimer78894,
  between the two positive returns. Twelve installation events have distinct
  instance paths. Key events log the owner body, not the helper instance; an exact
  helper-generation join at J remains unproved and is not inferred from proximity.

The actual sequence supports r07's asset correction and shows why early HP samples
were incomplete: this run's six timer callbacks precede the observed assignment.
It does not retroactively establish unlogged ordering in r06 or make its failure
acceptable. All early undefined rows remain in this run as well.

## Gates and reproducible checks

Both local `analyze.py` and `--require-oracle` return **1**. Provenance checks require
build/session equality, a fresh tag and contiguous exact raw selection, no foreign
observer tag, append-only interval, physical input PID returns, owned cleanup and
retained copy/tag hashes. Descriptive counts are written before invoking the
**unchanged r05 validate_rows** structural gate on the entire prefix. It refuses
`Incomplete actor state at clock boundary`. Nothing is trimmed, filled or relaxed.
The CLI remains exit1 even if a future prefix passes structure: full oracle
obligations are not implemented by this reporter. `analysis-gates.json` records
both exits and `observations.json` retains exact marker/HP/positive-query events.

```sh
python3.11 evidence/oracle/native-fight-r09/analyze.py
python3.11 evidence/oracle/native-fight-r09/analyze.py --require-oracle
python3.11 -m unittest discover -s evidence/oracle/native-fight-r09 -v
```

The analyzer's byte audit needs the receipt-pinned temporary movie copy. Missing
copies fail closed; no machine-specific path is silently replaced. All raw logs,
input ops, AX/CG snapshots, nine screenshots and session/cleanup receipts are in
run-01. Account-wide flashlog attribution text is retained unchanged; unique-tag
selection is separate and is not OS-level per-write PID attestation.

The unmodified r08 builder compiled a fresh independent copy. Six original→copy
DoAction changes (five main, one yihu) match the prepared audit. All other payloads,
headers/topology and73 other assets are unchanged. Build and three diff layers,
compiler logs and inherited r07 metadata are retained. The local capture driver
only changes r06's build guard to r08/main+yihu; tape is unchanged from r06.
No global API hijack, forced frames, locked source edits or new game flow.

Still missing: certified input consumption/global clock and exact initial-state
boundary, onLoadInit proof, exact helper-generation attribution, complete random
tape/provenance, exclusive complete contract trace, deterministic repeat and
SOURCE_FIRST same-input observer noninterference. No M0-02 closure is claimed.
