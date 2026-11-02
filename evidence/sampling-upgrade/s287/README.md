# s287 — Loader read-return/consumer/request association (unproved)

Base: master `2e92fccd` / #164. Branch: `feat/s287-loader-attestation`.
Exclusive authority: [AFTER-s281 rank 6](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only; zero product obligations closed.

**No live read-return/consumer/request association was proved.** The normal
P1 prerequisite remains missing, so the separately qualified wrong-resource
control was not executed. Both requirement commands exit 1.

## What this slice establishes

[diagnose.py](diagnose.py) replays unchanged s277 → s268 analysis of only
s259-normal P1: all 5,503 historical events, receipt/archive provenance and
original loader source checks remain intact. Hashes identify retained inputs,
not bytes consumed by a running player. No receipt is resealed.

Five fresh static facility queries against the receipt-matching executable are
retained in [facility.json](facility.json), with commands, complete transcripts,
exit codes, SHA-256 and measured subprocess durations:

- Name lookup of the four read candidates and name-based `read` disassembly
  exit 1. Loader/request/completion name lookup also exits 1.
- `otool -Iv` succeeds. Address-based LLDB disassembly succeeds for four
  six-byte x86_64 RIP-relative indirect jumps. Diagnosis checks their computed
  destination slots against the same indirect-symbol table.

| Import | Unslid stub | Unslid pointer slot |
| --- | --- | --- |
| CFReadStreamRead | 0x100fb5baa | 0x1014b2660 |
| fread | 0x100fb65be | 0x1014b33d0 |
| mmap | 0x100fb6720 | 0x1014b35a8 |
| read | 0x100fb6882 | 0x1014b3780 |

These are **on-disk addresses**, not executed call sites, live pointers or a
qualified read facility. A name query failing does not imply the import is
absent; the address query demonstrates that distinction. None identifies the
API actually used for P1, its returned buffer, buffering/mapping coverage,
native consuming loader, request object or callback target. The query failure
also does not establish that native debugging or reverse engineering is
impossible. No player launch, attach, binary patch, security change, SWF build
or new capture was performed. The s277 DTrace failures are historical context,
not newly repeated observations.

## Exact association still required

The original and archived `scripts/main.json` source at
`DefineSprite_1900/frame_1/DoAction.as` uses one MovieClipLoader. P1 load is
followed by P2, P1 assist, P2 assist and sound. Its `onLoadComplete(target)`
executes `loadStep++` and the next step inline, ignores `target`, and installs
no `onLoadInit` listener. Source order is not a measured callback schedule.

The next bounded experiment must resolve the executed P1 read-return chain,
retain all returned byte ranges (or actual mapped ranges and consumption),
and bind their native consumer to an immutable request identity. Observe
that request's target **before** the authored completion advances loadStep;
observe init/use and unload/replacement separately with the same association.
A later read of a mutable current-request proxy can already name P2. A shared
loader pointer, global counter, helper stamp or path equality cannot repair
this. Original callback bodies/order and input/random tapes must be preserved;
observer perturbation remains to be qualified.

Only after normal association is independently qualified, run an isolated
actual Yihu-for-Yijiao resource control with the expected Yijiao identity
unchanged. Observe actual supplied/returned/consumed bytes and the same
request/target boundary, including errors. Static archive substitution or
server delivery alone cannot supply that control. Neither this document nor
the fixed-evidence diagnosis accepts a new capture or changes admission rules.

## Scope and verification

Only new `s287/` evidence and the four requested tracking files change.
Ranks 1–5/7–9, s254–s286, game/scripts, runtime, contracts, shared samplers,
thresholds, validators and baseline tapes remain untouched. No mechanism is
implemented; source-first runtime qualification remains incomplete. No broad
loader rollout, merge, deployment or production-readiness claim.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s287/diagnose.py --output /tmp/s287.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s287/diagnose.py --output /tmp/s287-required.json --require-loader-attestation # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s287/diagnose.py --output /tmp/s287-wrong.json --require-wrong-resource-control # expected exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s287 -p 'test_*.py'
python3 -m unittest tools.tests.test_loader_read_target_diagnosis tools.tests.test_loader_attestation_diagnosis tools.tests.test_capture_runtime_fighter tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

All 53 focused tests pass (4 new boundary tests and 49 retained tests).
Diagnosis, integrity, handoff and diff checks pass; both negative requirements
retain exit 1.

[Gates](gates.json) and [project checks](project-checks.json) retain actual
results/timings. [Scope audit](scope-audit.json) and
[manifest audit](manifest-audit.json) distinguish permitted tracking changes
from locked inputs. [Session timing](session-timing.json) records elapsed wall
time; future native qualification/capture costs and person-days are unknown.
No Godot or contract test is required because neither implementation nor
contracts changed.
