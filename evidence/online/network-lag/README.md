# Cross-machine online lag evidence

Field logs and simulator results for the
[lag diagnosis](../../../docs/online-multiplayer/NETWORK_LAG_PLAN.md) and the
[implementation plan](../../../docs/online-multiplayer/NETWORK_LAG_IMPLEMENTATION.md).
Logs are copied byte-for-byte from the in-game "export log" download; only the
file names change. Before adding a log, check that it contains no TURN
credentials, IP addresses, ICE candidates or room/invitation tokens.

## Retained logs

| File | Exported as | SHA-256 | Peer | Notes |
|---|---|---|---|---|
| [p1-net-2026-09-29.json](p1-net-2026-09-29.json) | `P1 net.json` | `bf45ff68ca8c3555111461c8be600fd4cca97b370af7ad82c6cf91e35498d18d` | P1, clock authority; Chrome 153 | M0 baseline. Build identity empty. |
| [p2-net-2026-09-29.json](p2-net-2026-09-29.json) | `P2 net.json` | `4417e022c24926d80ab163e90539b6f03551fca5c80080bcffd6daebfa091ade` | P2, guest; Chrome 152 | M0 baseline. Build identity empty. |

Both logs record the same match from each side over TURN relays on
https://bvn26.vercel.app/: 白哉 + 松本 against 小李 + 我爱罗 on 温泉, profile
`chrome-exp-d2-p6`. The scan before copying found only Chrome version strings
matching an IPv4 pattern, and no credential, candidate or token fields.

## Implementation evidence and current gates

| Package | Evidence | Local state | Acceptance still pending |
|---|---|---|---|
| LAG-01 | [lag01-local.md](lag01-local.md) | Final full Web export passed; PCK sidecar matches; local IAB diagnostics log reports `build.status=match` with matching build, commit and PCK identity. | Deployed-page diagnostics log and two-machine field acceptance. |
| LAG-02/03 | [lag02-03-local.md](lag02-03-local.md) | Diagnostics counters, replay tagging and console gating pass local Godot/analyzer checks. Analyzer suite: 11 total, 8 passed and 3 skipped. | Paired field metrics and duplicate-console check under corrections. |
| LAG-04 | [lag04-local.md](lag04-local.md) | Six 10-second scenarios have recorded correctness/hash checks; pair smoke and simulator self-test passed. Slow-host reached 30 Hz with zero corrections, unlike the field pattern; cost calibration remains provisional. | Reproduce the diagnosed behavior with calibrated costs and matching state fingerprints. |
| LAG-11 | [lag11-local.md](lag11-local.md) | Packet-drain batching; local ordering/full-state checks and native A/B measurements. | Same-build paired Web/TURN run and 30 Hz acceptance. |
| LAG-10/20 | [lag10-20-local.md](lag10-20-local.md) | Opt-in sparse saves and pacing; full-state checks, native confirmed-input measurements and six-scenario model comparison. | Real paired browser performance; pacing remains off after no model rate benefit. |
| LAG-10 stride / LAG-12 | [lag12-stride-local.md](lag12-stride-local.md) | Optional predicted stride two measured against fixed full-state references; field-path micro-optimization rejected after remeasurement. | Paired Web/TURN run; no super-freeze resolution. |

No two-machine acceptance run or deployed-page verification has passed. The
local browser diagnostics log only verifies this local artifact identity.
LAG-10/20 are local experiments; LAG-30/22/40 remain open. `plan/tasks.json` and its NET acceptance checkboxes are unchanged.

Replay presentation and online combo suppression are enabled by default;
[local evidence](replay-display-local.md) records state, visual and diagnostic
equality plus native timings. Total-time gains are inconclusive; Web acceptance
remains pending.
