# Poll-before-step A/B

Both browser runs used the same `d0p2` paired fixture and 60-second active window. The complete DOM reports were retained in the root task's CUA variables; the browser download did not produce a disk JSON, so the figures below are transcribed summaries, not links to raw files.

| Run | Host / guest steps per active second | Host / guest 1s p5 Hz | Corrections, replays, hidden time, errors |
| --- | ---: | ---: | --- |
| Baseline, 3c89 | 29.0647 / 29.0481 | 27.5591 / 26.6535 | 0 / 0 / 0 / 0 |
| Poll candidate | 27.03 / 27.185 | 19.342 / 18.849 | 0 / 0 / 0 / 0 |

Baseline: 1,744 / 60,004 ms host steps and 1,743 / 60,004 ms guest steps. Candidate: 1,624 / 60,080 ms host steps and 1,632 / 60,033 ms guest steps. Both reported 444 exact inputs and 62 non-neutral inputs. Candidate later CPU samples rose from about 23 ms to 45–59 ms, with maxima 197.8 / 204.9 ms. The final waits did not improve (baseline input/clock 1,097 / 1,413 ms; candidate 1,295 / 1,321 ms).

The candidate did not show a measurable benefit. These runs do not prove the poll change caused the lower candidate rate: CPU load also rose substantially, and the harness does not measure packet-available-to-physics latency directly. The transient implementation and smoke test were removed; production sources are back at 3c89. Exported artifacts remain outside the repository at `/private/tmp/bvn-online-performance-60s/packs/`.
