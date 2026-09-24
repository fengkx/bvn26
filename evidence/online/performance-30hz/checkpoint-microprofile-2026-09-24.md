# Checkpoint encoder micro-profile — 2026-09-24

This is a focused native follow-up to the [round 3 checkpoint diagnosis](round3-checkpoint-profiling.md). It uses the previously retained partial Hitsugaya/Sasuke tape (tape SHA-256 baea2b6b29caa8e45e2431bf724b592ef5546df232d3c0caf4ff0eee0d8eaa64). The tape metadata identifies its source as a 2026-09-23 runtime log with SHA-256 76034d2d5abc70c095f3c0046f7a17ce4b6cf55f00557866c7a89371e8492960; it was already present in commit 3c89d814. It is not a replay of the newly supplied 2026-09-24 log (SHA-256 f46af7c575b5c268a50845919a280d95deecc74c93787f21e3b3b10d9f4525d4). This headless profile uses 330 ticks and 90 warm-up ticks; the new browser log remains a separate slowdown signal and is not reproduced by two live peers here.

## Setup and scope

Godot 4.7.2-stable ran the existing rollback_performance_profile.gd in /private/tmp/bvn26-perf-round3-microprofile/baseline-godot. The original checkpoint source SHA-256 was fa7d03d2719b2ca61738aaa30f7e5d0b17da583342ef3a3e4e878ce7b9fbcbac; the unmodified profile script was 460bf74a149f9917466ebcb9c46bf3a71275c99f1e457607b689ebca9087a1b5. Both files were restored after the runs. Temporary instrumented versions and raw logs remain under /private/tmp only. Their hashes and the raw measurements are in the [machine-readable record](checkpoint-microprofile-2026-09-24.json).

The command for both instrumented passes was:

    /private/tmp/bvn-toolchain-2026-09-12/Godot.app/Contents/MacOS/Godot \
      --headless \
      --path /private/tmp/bvn26-perf-round3-microprofile/baseline-godot \
      --script res://tests/rollback_performance_profile.gd \
      -- --scenario=user-log-r01

An earlier uninstrumented run of the same fixture is retained as the control. Each run measured 330 ticks after 90 warm-up ticks. The rollback profile had no late inputs, so it recorded zero rollbacks and zero replayed frames.

## Results

All direct totals below cover 331 checkpoint saves. The additional save is part of the existing fixture lifecycle.

| Run / block | Calls or comparisons | Timed total | Per save |
|---|---:|---:|---:|
| Uninstrumented encode | — | 2,672,652 µs | 8.074 ms |
| Uninstrumented pack | — | 675,528 µs | 2.041 ms |
| Uninstrumented retain | — | 69,195 µs | 0.209 ms |
| Container hash(value) | 144,182 calls | 45,626 µs | 0.138 ms |
| Identity bucket lookup and scans | 144,182 blocks; 5,174,111 actual comparisons; maximum 122 in one block | 578,884 µs | 1.749 ms |
| Full _empty_prototype_key call | 141,542 calls | 150,138 µs | 0.454 ms |
| Non-recursive var_to_bytes plus hex encoding | 53,247 calls | 25,000 µs | 0.076 ms |

The second pass sampled property operations to limit timer overhead. Its profile recorded 8.579 ms encode per save.

| Sampled block | Total calls | Timed samples | Sampled total | Heuristic estimate per save |
|---|---:|---:|---:|---:|
| Script field value.get(field) | 402,141 | 12,567, every 32nd call | 4,938 µs | 0.477 ms |
| Node2D/Sprite2D native property getter | 53,130 | 3,321, every 16th call | 1,349 µs | 0.065 ms |
| Immutable-field cache branch | 42,570 | 2,661, every 16th call | 2,966 µs | 0.143 ms |
| get_signal_connection_list | 18,480 | 1,155, every 16th call | 1,022 µs | 0.049 ms |
| _register_placements | 990 | all calls | 615 µs | 0.002 ms |

The immutable-field path performed zero constant refreshes in the measured interval. It therefore measured cache checks and record writes, not repeated _constant(contents) serialization. Signal timing covers the connection-list query only; callback encoding follows outside that timer. Property getter estimates extrapolate fixed-stride samples and are approximate.

The identity bucket scan is the largest directly timed block at about 1.7 ms per save. Its actual comparison count is close to the previous counter-only upper bound. Reducing it safely requires preserving is_same alias behavior for distinct equal-content arrays and dictionaries, plus WeakRef lifetime semantics. No safe identity index was established in this profile. Hash computation itself was about 0.12–0.14 ms per save; prototype lookup was about 0.42–0.45 ms; scalar value encoding was about 0.07 ms. The measured property, signal, immutable-cache, and placement blocks are also individually small.

These stage measurements are **not additive**. Hashing, identity scanning, prototype lookup, and scalar encoding were timed in one instrumented pass; property operations were timed in another. Sampled estimates are not self-time totals for recursive _encode. _empty_prototype_key measures the full helper call and can include its own constant work on a cache miss; that value is not added to a separate constant timer. The second pass times each selected getter without its following recursive _encode.

Instrumentation overhead is not isolated. The uninstrumented, first instrumented, and second instrumented runs had receive-plus-step means of 20.06 ms, 21.95 ms, and 19.39 ms, respectively. This spread changes direction between runs, so it does not support a numeric overhead correction. Sample counters and checks execute on each relevant operation, and sub-microsecond getter measurements are close to timer overhead.

## Validation boundary

The harness completed with exit code 0 and its final State.first_difference check found no difference between one battle_only final save_state result and one rollback_no_late_input final result after 330 measured ticks. This is a final-state comparison only, not a per-frame serialized graph trace. It had no late-input correction or replay and says nothing about browser/Web performance.

No checkpoint optimization was accepted or applied to runtime code. This profile does not pass the browser 30 Hz gate or establish a speedup. The temporary baseline files were restored to their original hashes after capture.
