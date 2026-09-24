# TURN buffer virtual scheduling comparison

This small deterministic model compares the existing 30 Hz rollback session with three agreed delay/prediction profiles under injected 50, 100, and 150 ms RTT and a fixed short-jitter sequence. It uses the production `RollbackSession`, a lightweight state adapter, reliable ordered per-direction queues, sample-once local input, and the production host/guest scheduling constraint: the host advances at most one frame per virtual physics tick and emits an authoritative clock only after advancing; the guest waits for that frame clock before stepping.

Each case samples 60 virtual seconds, then has a separate convergence window of at most 120 ticks. The reported rates cover only the 60-second measurement window. The `MaxSampledPredictionBacklog` fields are maxima of the six 10-second samples, not continuous peaks. All nine cases drained their queues and reached a valid, equal common-confirmed state within the convergence window.

| Injected RTT | Profile | P1/P2 virtual frames per second | P1 input-wait ticks / P2 clock-wait ticks | P1 corrections / replayed frames | Sampled backlog P1/P2 |
|---:|:---:|---:|---:|---:|---:|
| 50 ms | d0p2 | 30.00 / 29.98 | 0 / 1 | 105 / 210 | 2 / 0 |
| 50 ms | d1p4 | 30.00 / 29.98 | 0 / 1 | 105 / 105 | 1 / 0 |
| 50 ms | d2p6 | 30.00 / 29.98 | 0 / 1 | 0 / 0 | 0 / 0 |
| 100 ms | d0p2 | 18.00 / 18.00 | 720 / 720 | 104 / 208 | 2 / 0 |
| 100 ms | d1p4 | 30.00 / 29.97 | 0 / 2 | 105 / 315 | 3 / 0 |
| 100 ms | d2p6 | 30.00 / 29.97 | 0 / 2 | 105 / 210 | 2 / 0 |
| 150 ms | d0p2 | 12.87 / 12.87 | 1028 / 1028 | 69 / 135 | 2 / 0 |
| 150 ms | d1p4 | 25.72 / 25.68 | 257 / 259 | 96 / 377 | 4 / 0 |
| 150 ms | d2p6 | 30.00 / 29.95 | 0 / 3 | 105 / 410 | 4 / 0 |

In this scheduling model, `d2p6` continued advancing at roughly 30 virtual frames per second through the 150 ms case, while `d0p2` and `d1p4` accumulated more input or guest-clock waits as RTT rose. This is a scheduling upper bound, not measured FPS or a promise of real-world throughput. After the run, only output field names were clarified to identify the ten-second sampled maximum; simulation logic and numerical results did not change. The model omits CPU/rendering cost, browser/WebRTC behavior, selected ICE route, and TURN relay; the supplied same-machine log had no RTT or selected-pair data, so it does not establish that the traffic used TURN. Corrections and replay work remain nonzero in higher-RTT cases.

The d2p6 choice adds about 66.7 ms of nominal local input delay at 30 Hz. Production monotonic frame-clock sampling was not changed. The structured case data, timing windows, convergence checks, run command, and script hash are in [`turn-buffer-model.json`](turn-buffer-model.json).
