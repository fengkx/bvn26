# Round 3 checkpoint profile

This note records the 2026-09-24 user-log diagnosis and a short native profile
of the checkpoint encoder. The supplied browser log was not copied into the
repository. Its SHA-256 is
`76034d2d5abc70c095f3c0046f7a17ce4b6cf55f00557866c7a89371e8492960`.

## User-log diagnosis

The log contains 15 performance windows at d0/p2. Across 247,222 ms, the
frontier advanced 4,331 ticks (17.52 Hz). Physics callbacks numbered 7,414,
near 30 Hz; hidden and recovery time were both zero. Input wait totalled
73,230 ms over 1,906 waits. There were 219 corrections and 389 replayed
frames; correction receive work totalled 18.49 s with a 164 ms maximum.
Measured simulation steps averaged 28.63 ms and peaked at 74.3 ms.

The 4,723 checkpoint saves recorded 70.509 s in encode, 20.489 s in pack, and
1.966 s in retain, or 19.68 ms per save combined. The save and step samples
have different denominators, and saves include replay work; these totals are
not a direct per-step CPU breakdown. Input wait is a coordinator-window
measurement, not RTT or one-way network latency, and must not be added to CPU
time. Browser build identifiers were empty, so this log cannot be tied to an
exact source build or commit.

## Native profile

Godot 4.7.2 ran the existing user-log profile with the same 90-frame warmup
and 330 measured frames in serial order. Each source had one sample and zero
late-input rollbacks, so the values screen candidates but do not establish an
A/B gain.

| Source | Receive + step mean | p95 | p99 | Encode / save | Pack / save | Retain / save |
|---|---:|---:|---:|---:|---:|---:|
| Frozen `3c89d814` | 20.057 ms | 25.106 ms | 26.948 ms | 8.074 ms | 2.041 ms | 0.209 ms |
| Untyped-dictionary prototype and descriptor flags | 20.901 ms | 25.847 ms | 29.528 ms | 8.316 ms | 2.253 ms | 0.210 ms |
| Above plus per-save constant/ref wrappers | 19.896 ms | 24.733 ms | 27.771 ms | 8.219 ms | 2.017 ms | 0.195 ms |

The samples got faster in run order, while encode time did not improve over the
frozen source. These results do not show a stable checkpoint gain, so the
candidate code was discarded and `battle_checkpoint.gd` restored to SHA-256
`fa7d03d2719b2ca61738aaa30f7e5d0b17da583342ef3a3e4e878ce7b9fbcbac`.

A final temporary primitive-dispatch candidate also showed no gain: against
the frozen source, its single receive-plus-step mean was 21.264 vs 20.625 ms
and encode was 9.117 vs 8.251 ms per save. It was discarded without changing
the runtime; these single samples are screening evidence only.

## Encoder micro-profile and parity

A temporary counter-only instrumented run covered 331 saves. It counted
144,577 container hash calls and 141,930 container records. Summing the sizes
of each identity bucket gives at most 5,191,043 possible identity checks
(15,683 per save); this is an upper bound because the encoder stops scanning
when `is_same` finds the existing container. The largest observed bucket had
131 entries. Dictionary prototype lookup built 88,823 signatures and hit the
cached type 88,822 times; Array type-key lookup ran 53,124 times and hit its
cache 53,098 times. Opaque value encoding ran 53,408 times.

In this 330-tick fixture, retained state plateaued by tick 60: `_states`,
`_snapshots`, and `_snapshot_graphs` stayed at 32; `_constants` stayed at
1,440; and `_immutable_fields` stayed at 38. This short sample does not prove
constant memory use over a complete match.

The wrapper-cache experiment first confirmed that shared and freshly created
equal `constant`/`ref` wrappers serialize to identical `var_to_bytes` bytes.
The full baseline and wrapper-candidate 331-frame graph traces then compared
byte-for-byte: both were 158,996,470 bytes with SHA-256
`b0227f7af37d10b220bcddcbdc0a73429f31b76c0d1d125c5b81f154897db17b`. Graph
parity passed, but the performance screen showed no stable gain. No checkpoint
optimization or 30 Hz acceptance claim follows from this experiment.
