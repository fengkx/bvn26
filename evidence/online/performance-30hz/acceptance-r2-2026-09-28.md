# Checkpoint PBA candidate: independent acceptance review (2026-09-28)

## Verdict

The candidate preserves the complete serialized battle graph for all 331 captured frames, cross-version canonical whole-state comparison returns no difference after delayed input, and the native online-pair smoke passes its late-input correction and convergence cases. A visible-browser Web burst adds a small, local checkpoint-pack signal, but has zero corrections and does not measure real-time cadence; it does not pass the paired-Web 30 Hz gate.

## User-run P1/P2 context

The source logs remain in the user's Downloads folder and were not copied into this repository:

| Log | Bytes | SHA-256 | Build identity |
|---|---:|---|---|
| P1.json | 2,471,764 | `1af7abb446c735cfc634bf7bde2cde96374aff9535e214d264bbb6e0b0ac2fcf` | unknown; commit/PCK/buildID/resourceVersion absent |
| P2.json | 1,153,387 | `c384b2c9710f5c13aa4bfc9e406675703b8c6fde09af06dcc70eb341714b0a27` | unknown; commit/PCK/buildID/resourceVersion absent |

Both snapshots report 30 Hz, 现世, Naruto + Gaara helper versus Ichigo + Kon, and profile `chrome-exp-d2-p6`; `modeName` is unknown. Canonical initial-state JSON hashes match. Match-end wall timestamps differ by 5 ms, and 596 overlapping `(fightTick, slot)` consumed-input payloads match exactly. The peers can therefore be treated as the same observed match for the approximately 11-second paired summary window, but the missing build identity prevents linking the run to a specific candidate or proving both binaries identical.

| Metric | P1 | P2 |
|---|---:|---:|
| Final frontier / match-effective Hz | 2,152 / 19.19 | 2,145 / 19.16 |
| `simulation_step` mean | 23.88 ms | 45.68 ms |
| Checkpoint saves | 2,619 | 2,148 |
| Encode / pack / retain total | 30.229 s / 10.293 s / 0.850 s | 49.420 s / 15.193 s / 1.533 s |
| Encode / pack / retain per save | 11.54 / 3.93 / 0.325 ms | 23.01 / 7.07 / 0.714 ms |
| Corrections / replayed frames | 95 / 464 | 0 / 0 |
| Correction-receive timing | 12.776 s | 0 s |
| Input wait / clock wait | 36.750 s / 0 s | 0 s / 7.477 s |

Match totals start at each peer's `OnlinePerformance.start()` and are not aligned to the exact same instant, so do not sum peer totals. Checkpoint averages use each peer's actual checkpoint save count; P1's count includes extra replay saves. A one-to-one nearest pairing of summaries within 300 ms found 11 windows: weighted step means were 21.85 ms / 42.92 ms, while checkpoint delta per-save encode/pack/retain was 11.16/3.97/0.340 ms / 22.61/7.47/0.703 ms. The P2 encode/pack asymmetry persists in that shared window, rather than appearing only in its final sample.

`simulation_step` includes checkpoint work, and correction timing is also recorded under `input_receive`; these counters overlap and must not be added. Input wait is scheduler waiting, not RTT. The runtime reported no reliable RTT, and ICE host-host samples of 0–1 ms are connectivity/consent observations, not input end-to-end latency. No GPU time or continuous host CPU load was captured. These logs are diagnostic only and are not evidence of a candidate Web 30 Hz pass.

## Candidate correctness evidence

The baseline and candidate runtime files used for graph capture were frozen under `/private/tmp/bvn26-perf-opt-r2`. Godot was 4.7.2 stable. Baseline/candidate SHA-256 identities:

| File | Baseline | Candidate |
|---|---|---|
| `battle_checkpoint.gd` | `fa7d03d2719b2ca61738aaa30f7e5d0b17da583342ef3a3e4e878ce7b9fbcbac` | `192c42ae80014bdbf0b3f576303ea63cdbc9765817735975f23875f031eaa076` |
| `simulation_state.gd` | `dfc0b2c83eaf33418b7516746ee6934df1ef8a3d89e89c566ba4417a86b6bbc4` | `8d8ee664371b5612b57e625545595d1e6ce12f52f1364fc10c32b66f95122522` |

I independently parsed `baseline-graphs.txt` and `candidate-graphs.txt`: both have rows 0–330, each declared raw byte length matches its decoded hex data, and every frame's full raw graph bytes are identical. Combined frame/length/raw-byte stream SHA-256 is `9950e9ec80f7c3b966a4c8aedaa5a249a2175387bffcf8f6703fc26eaa09ace6`; both original text captures are 158,996,470 bytes with SHA-256 `8f9424453b59a449897297da7c772c2fdf8e08110cee82131c54c70649f266ae`. This comparison uses full graph bytes; no build-marker normalization is applied to the graph.

The first comparison attempt was invalid because the profile helper wrote the representation marker to `result.owners.battle.owners.build`, adding a different owner field. The corrected harness changes only `result.owners.battle.build`, after decoding the entire graph into records. It leaves all other fields in the canonical state intact, then compares with `State.first_difference`. Both runs performed 10 corrections and 65 replays; each delayed final state matched its on-time reference, and the candidate had no cross-source difference. Both canonical-state SHA-256 values are `c5ae5a388f63db1d0a85a52673e3324c310e1a040691ce07cc6310e9967a842a`. The comparison logs are `/private/tmp/bvn26-perf-opt-r2/baseline-canonical-check.log` (SHA-256 `f0d9d529b4a8828775eead514830c1660d4917dff263cf53c22f55690a2130b0`) and `/private/tmp/bvn26-perf-opt-r2/candidate-canonical-check.log` (SHA-256 `660c74c1ce311fc2e409664cf8b1377dbd9ca62bd3a010d460a57f77aef65b7b`); the baseline canonical state bytes are in `/private/tmp/bvn26-perf-opt-r2/baseline-canonical-state.bin` (SHA-256 equal to the canonical-state hash above). Both log files include the known macOS CA lookup warning; neither contains a script or assertion failure.

I independently ran the native paired coordinator test:

```bash
/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot --headless --path godot \
  --script res://tests/online_match_pair_smoke.gd \
  --log-file /private/tmp/bvn26-perf-opt-r2/acceptance-online-match-pair.log
```

It exited 0 and reported matching initial hashes, a withheld/released late P2 input with rollback, equal state through frame 331, pause/resume barriers, recovery convergence, and the new-epoch case. This is an in-process fake transport test; it does not exercise WebRTC, two browsers, the renderer, or wall-clock cadence. Godot also reported 7 leaked ObjectDB instances and 3 resources still in use at shutdown; the test exited successfully, but the warning should remain visible in the acceptance record.

Implementation-reported native ABBA screening showed step mean 34.70→32.48 ms (-6.4%), step p95 62.90→62.05 ms, pack 4.86→3.24 ms (-33%), encode 13.96→13.61 ms (-2.5%), and correction p95 463→280 ms with 10 corrections per arm. The p95 change is small and the sample is short; this is not a stable-tail result or a Web 30 Hz pass.

## Visible-browser Web burst (diagnostic, not a cadence pass)

The browser was visible in Chrome 153 at DPR 2 on the same machine, running Godot 4.7.2 stable. Each page warmed up for 90 frames, then measured 330 frames with fixture `user-log-r01`: the same 222 recorded input ticks (28–249) from the 9/23 user trace, with synthetic neutral padding at ticks 1–27 and 250–330. The harness added no attacks, assists, or supers. Every run had 331 checkpoint saves, zero rollbacks, and zero replayed frames; `cadenceMeasured` is false. This is a checkpoint/step burst, not a real-time online match.

All three reports identify pair `checkpoint-pba-r2-20260928`, tape SHA-256 `baea2b6b29caa8e45e2431bf724b592ef5546df232d3c0caf4ff0eee0d8eaa64`, and `main.gd` SHA-256 `a44d5d47826efa6b4a62023dd20a006a7b0b4c4737445d18ff615186a2387f8c`. The baseline checkpoint SHA-256 is `fa7d03d2719b2ca61738aaa30f7e5d0b17da583342ef3a3e4e878ce7b9fbcbac`; candidate is `192c42ae80014bdbf0b3f576303ea63cdbc9765817735975f23875f031eaa076`. I checked each JSON's completion flag and its source/fixture fields; the candidate and `main.gd` hashes also match the current workspace files.

| Run | Source revision | `receive + step` mean / p50 / p95 / p99 / max (ms) | `battle_only` mean / p95 (ms) | Encode / pack / retain total (ms) |
|---|---|---:|---:|---:|
| A1 baseline | Baseline overlay; root transcribed the visible DOM, original JSON not retained | 24.078 / 24.300 / 32.800 / 37.600 / 48.600 | 11.282 / 18.700 | 3,197.0 / 1,005.4 / 87.3 |
| B1 candidate | `battle_checkpoint.gd` `192c42ae…aa076` | 20.690 / 21.100 / 26.600 / 29.700 / 38.600 | 9.505 / 15.000 | 2,959.8 / 707.9 / 81.8 |
| B2 candidate | `battle_checkpoint.gd` `192c42ae…aa076` | 20.202 / 20.500 / 25.900 / 30.700 / 44.900 | 9.000 / 14.200 | 2,897.6 / 663.0 / 80.6 |
| A2 baseline | `battle_checkpoint.gd` `fa7d03d2…fbcbac` | 21.162 / 21.500 / 27.200 / 28.800 / 29.900 | 8.910 / 13.900 | 2,901.7 / 846.1 / 80.2 |

The most comparable warm pair, B2 then A2, shows candidate `receive + step` mean 20.202 ms versus 21.162 ms (-4.5%); p50 and p95 are about 4.7% lower. Pack time was 2.003 ms/save versus 2.556 ms/save (-21.6%), while encode was effectively flat (8.754 versus 8.767 ms/save). The `battle_only` means were close (9.000 versus 8.910 ms), supporting a narrow pack-path signal. Candidate p99 was 6.6% higher and its maximum was 44.9 versus 29.9 ms, so the tail did not improve consistently.

The complete A1→B1→B2→A2 means are descriptive only: baseline moved from 24.078 ms in A1 to 21.162 ms in A2, a 12.1% within-baseline shift; candidate moved 2.4% between B1 and B2. That drift, sequential page loads, and the missing A1 raw capture leave browser order and load as confounders. Do not attribute the full four-run average difference to the change. B1, B2, and A2 source JSONs are in `/private/tmp/bvn26-perf-opt-r2/web-burst-candidate.json`, `web-burst-candidate-b2.json`, and `web-burst-baseline-a2.json` (SHA-256 `030e3ca9d3c8810b7a2ae61386a0ca325ef222c5f6bac0e22e4bb599a73c564e`, `506f5cad32691c4eabec951ae1229915414dd85a6ab44321444eb5b69ed5d9b3`, and `b021f78728c3672d2d4292ec959b5333ff04a53d8aa36efe382005d133b3bb41`, respectively). A1's numbers above are explicitly a DOM transcription, not a retained raw report.

## Remaining gate

- Keep full per-frame raw graph comparison as representation-parity evidence; do not replace it with final HP, a digest token, or a build-marker rewrite. The full semantic comparison above is separate and decodes the full graph before normalizing only the local representation marker.
- Any real-time performance claim still needs same-build, same-configuration paired Web measurements with cadence and delayed corrections. The visible burst used zero-late-input fixture playback, and the original P1/P2 logs have unknown build identity; neither the burst nor native fake-transport smoke is the online 30 Hz gate.
