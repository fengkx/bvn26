# r244 — Owned Jinye probe debugger feasibility

The successful fresh retry establishes that the pinned Rosetta Flash Player probe can be attached, x86 argument registers can be read, and the debugger can detach within a bounded deadline. The exact executable/movie PID was checked immediately before attachment. The captured RIP is an arbitrary interrupted instruction, **not** a verified matrix-function entry; these register values identify no source-fill operands or rendering branch.

The first 20-second workload / 15-second debugger deadline timed out without a debugger result receipt. Its original receipt incorrectly represented missing state as false. That original file is preserved under `debugger/`; `feasibility-corrected.json` records the state as unknown. The timeout is not evidence of permission denial, failed attachment or successful detachment. Native capture completed and its owned process was cleaned up.

Exactly one fresh retry used a 60-second workload, 45-second debugger deadline and 90-second capture deadline. It successfully attached, read registers, detached, completed all 447 native events and left no owned process. See `retry/debugger/feasibility.json`, `debugger-result.json` and `lldb.log`. No explicit breakpoint, expression evaluation or target memory write was requested. The tool does not claim to have verified LLDB's internal memory-write behavior.

Both workloads retain the actual source shape56/fill65/JPEG55 and r242 original direct matrices. Final imported raw tag hashes are checked independently. Their source readbacks total **7360/7360** exact; final images total **480000/480000** independently in raw and premultiplied RGBA against r242. These are instrumentation sanity checks, not replacement pixel references. The original r243 and r242 references are unchanged.

## Reproduction

Use the pinned FFDEC and Flash Player Debugger described in the reference environment. Serialize native execution; the owned-debugger probe controls capture launch and process cleanup.

```sh
python3 -m tools.probes.build_jinye_debugger_profile --output /tmp/r244/native --ffdec /path/to/ffdec-cli.jar --duration-ms 60000
python3 -m tools.probes.probe_owned_debugger --build /tmp/r244/native --output /tmp/r244/debugger --player-app '/path/to/Flash Player.app' --debugger-timeout 45 --allow-window-activation
python3 -m tools.probes.check_jinye_debugger_baseline --native /tmp/r244/native --output /tmp/r244/baseline.json
python3 -m unittest tools.tests.test_owned_debugger_probe
```

The debugger command's explicit activation flag and bounded timeout options must match the retained receipt. Final baseline verification requires the retained original build SWF: the checker validates its byte hash, final raw tags, fixture hash and harness hash before decoding. SWFs are intentionally not archived; the archive alone does not prove omitted movie bytes. A fresh reproduction must build a fresh run ID and capture it anew rather than substitute a fresh SWF into archived receipts. Tests: **6/6**; independent review retained in `review.json`.

## Next discriminator and acceptance

The next bounded experiment may test support for a hardware execution breakpoint at one byte-verified, profile-observed call site, then capture only its minimal matrix operands at a verified entry/caller context. Hardware support remains unproved. Do not silently substitute a software breakpoint, modify security settings/signatures, attach to unrelated processes, or treat arbitrary-stop registers as function inputs. Always detach and retain failure receipts. The observed caller must be tied to source matrices independently before claiming bitmap-fill setup semantics.

No sampler, renderer or gameplay change. No original image was rewritten. Candidate, GPU and production admission remain false; the unresolved source-bound Jinye sampling and separate AS ownership gates remain open.
