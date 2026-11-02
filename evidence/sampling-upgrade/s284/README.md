# s284 — Independent s228 DoAction completion pair (evidence-only, unproved)

Base master `d58aee18fb5c94de66e556851c6f15f21f329f63` / #161.
Branch `feat/s284-s228-completion`; exclusive [AFTER-s281 rank 3](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
No product obligation is closed. Other ranks and solved s259/s269 cuts are not executed.

## Result

Two fresh, separate native runs use the unchanged s228 Ichigo zero-stage tape,
standalone DoAction, catalog key 一护2. Both full saved streams pass the unchanged
native capture validator and DoAction entry collector; original receipts are
retained without resealing. This establishes a bounded observed completion
window, **not a fully proved independent pair or full-AS/native parity**.

| Observation | Normal quit | Held quit |
| --- | --- | --- |
| Saved events | 5,752 | 5,733 |
| Requested samples, ticks0–60 | 61 | 61 |
| DoAction entries (including startup) | 432 | 429 |
| After done | No events | 34 key reads, then closure |
| Host-log equality checked independently | Unproved | Exact equality |
| Native capture / DoAction entry validation | exit0 / exit0 | exit0 / exit0 |
| Full-AS coverage gate | exit1 | exit1 |

Held closure retains tick60 and the done display value before the next root
increment. No tick61, extra sample or second done is admitted. The terminal
34 key reads match the historical selected period; this is a run-specific
observation, not a universal callback-count threshold. Normal requests quit
at done and has no suffix: report quit truncation separately, never treat
absence as terminal completeness. Neither run proves exact shutdown timing.

Both runs match all 122 actor records, 122 records of each helper category,
and 61 input records at ticks0–60 against s228. Key reads through tick59 match;
normal omits the 34 terminal reads. Random values differ in both runs. Full-run
random callsite order matches historically for normal but differs for held;
startup clocks and action-entry totals differ. Full random rows and terminal
callback order remain in [diagnosis.json](diagnosis.json); no random replay,
startup equivalence or native parity is inferred from the state matches.

**Missing proof:** launching held cleared the account-wide Flash log before
normal's independent host-log equality check was saved. Normal's complete
capture-tool output and original receipt remain, but they do not establish
that additional check. Held's saved trace exactly equals its host run lines.
The pair requirement therefore remains false and `--require-completion-proof`
exits1. This evidence is not repaired by rerunning, trimming or resealing.
There are two player launches only; the first normal command failed at sandbox
`ps` preflight before launch, then succeeded with tool escalation.

Full-AS rejects independently for each run: **547 unvisited blocks, 656
uninstrumented scripts; statement/call ownership unproven**. The full coverage
reports retain those obligations under each run directory. Historical s228's
complete 5,630-event stream still rejects events beyond completion boundary.

## Source-preserving opt-in qualification

[build_probe.py](build_probe.py) has one fixed case/configuration and explicit
invocation; `--hold-quit` only selects the independent held control. No shared
builder, sampler, threshold, validator or runtime changes. The s269 source
pattern is reused without executing its case or adopting its receipts.

[qualify.py](qualify.py) verifies original source hashes, complete inventory,
all output hashes, unchanged four fighter/helper SWF bytes, and the complete
ordinary instrumentation diff against s228 after **only** run-ID and build-path
substitution. Erasing the explicit flag/guard/arm/quit relocation from the
candidate root must reproduce the archived root source exactly. It checks the
precise delta, not just matching token counts. Both builds passed before launch.
This is source/inventory/binary qualification, not a general AVM equivalence
or observer-perturbation proof. The ordinary sampler's existing limitations
remain; runtime resource consumption identity is not newly proved.

Done arms the flag. The next root callback closes observation before changing
clocks, inputs or samples, disables observation, and returns. Normal keeps quit
at done; held moves that request to the closure. Full scripts, instrumentation
diffs, build metadata and SWFs are archived separately. The qualification is
recomputed from those archives during diagnosis, without launching a player.

Source-first boundary: the root observer and terminal per-callback order are
bound to archived source; no authored frame action, PlaceObject/MOVE lifetime,
goto/stop/label exit or gameplay invariant changes. Tests assert source-derived
closure placement, same-input observations and strict rejection, never guessed
frames. The unchanged tape ran natively in both modes; these probe observations
do not authorize any Godot mechanism change or completion status.

## Reproduce and checks

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s284/diagnose.py --output /tmp/s284.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s284/diagnose.py --output /tmp/s284-required.json --require-completion-proof # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s284/diagnose.py --output /tmp/s284-old.json --strict-historical # exit1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s284 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gate commands/results](gates.json) retain focused tests, unchanged native
receipt validation at the original temporary paths, both full-AS gates and
negative requirements. Portable diagnosis validates archived sources/builds,
raw streams and original receipt bindings; it does not relocate or reseal a
receipt. Live receipt validation requires the original temporary artifacts.
[Project checks](project-checks.json) cover integrity and handoff; no runtime or
contract change requires a Godot or contract run. [Timing](session-timing.json)
distinguishes measured checks from unmeasured wall-clock build/capture costs.

A future separately authorized pair should save host-log equality immediately
after **each** run, before launching the next. It must retain the same source
qualification, full logs, independent negative gates and quit-truncation
accounting. No default rollout, mixed modes, receipt repair, production-ready
claim, merge or deployment is authorized by this result.

Validation: 10 new focused tests and 54 retained tests pass. Diagnose, both
original receipt validations, integrity and handoff exit0. Completion proof,
historical native rejection and both full-AS gates retain expected exit1.
