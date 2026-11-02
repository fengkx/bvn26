# s293 — AFTER-s290 rank #3: independent s228 completion pair

Base: origin/master `5bdc9f619ca18c217110e8829149d82c060a3706` (#170).
Branch: `feat/s293-s228-completion`. Exclusive authority:
[AFTER-s290 rank #3](../next-fix-priority-after-s290.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

**Evidence-only: the bounded independent pair is proved. Terminal callback
completeness and full-AS remain honestly unproved.** The new pair has distinct
`s293-normal-20261102-r01` / `s293-held-20261102-r01` identities. The locked
[s284 diagnosis](../s284/README.md) is reproduced exactly and remains unproved;
none of its captures or receipts is repaired, relocated or resealed.

## Observations and limits

| Observation | Normal quit | Held quit |
| --- | --- | --- |
| Complete saved events | 5,849 | 5,549 |
| Requested samples, ticks0–60 | 61 | 61 |
| DoAction entries, including startup | 441 | 412 |
| After done | No events | 34 key reads, then closure |
| Independently archived host log vs saved stream | Exact equality | Exact equality |
| Strict native / DoAction entry validation | exit0 / exit0 | exit0 / exit0 |
| Full-AS coverage | exit1 | exit1 |

Both runs match s228's 122 actor records, 122 records of each helper category
and 61 input records at ticks0–60. Key reads through tick59 match. Normal omits
34 terminal reads; the empty suffix is retained as quit truncation, not proof
that callbacks completed. Held closes at the done tick/display before another
root increment, with no tick61 or additional sample. The 34 reads are an observed
count for this run, not a new threshold or scheduling rule.

Random values differ in both runs. Full-run random callsite order matches s228
for normal and differs for held. Startup clocks and action-entry counts also
differ. Full random rows and the terminal suffix remain in
[diagnosis.json](diagnosis.json); no cross-run random tape is substituted.
Both full-AS gates retain 547 unvisited blocks, 656 uninstrumented scripts and
unproved statement/call ownership. Shutdown timing and terminal callback
completeness are not proved by host equality or bounded state agreement.

## Capture custody and qualification

[capture_pair.py](capture_pair.py) invokes the unchanged s284 builder and
qualification with new build paths and run IDs. All source/inventory/output
hashes, four fighter/helper binaries and the complete ordinary instrumentation
diff are checked; erasing only the declared flag/guard/arm/quit relocation must
reproduce s228's archived root observer exactly. Both builds qualified **before**
launch. This is the locked source-preservation qualification, not a general
AVM equivalence or observer non-perturbation proof.

The native capture implementation is unchanged. The driver acquires its existing
account-wide advisory lock, calls its unchanged `_capture_locked` implementation,
and keeps that lock through host archival, equality checking and original receipt
creation/validation. This extends custody through the independent check without
changing the shared sampler or validator. The lock serializes cooperative captures;
it cannot stop unrelated external programs from writing the account-wide log.

Each complete host file is saved as `normal/host-log.txt.gz` or
`held/host-log.txt.gz`. Equality selects **all** lines bearing that run ID in
host order, with line endings normalized, without sorting, deduplication or suffix
trimming. Non-run bytes remain in the full host archive and its hash. Each host file also
retains 118 diagnostic/non-event lines, including native undeclared-variable
warnings; these locale-encoded bytes are preserved without UTF-8 conversion.
Capture validation does not assert that those warnings are absent. The native
stream, original receipt, environment, full build archive and qualification are
saved separately. [execution.json](execution.json) records measured build/capture
costs and UTC archive/check/launch ordering. Normal's host check at
07:29:14.934925 UTC preceded held's launch at 07:29:20.955973 UTC; held's host
check was at 07:29:49.233615 UTC. There were exactly two builds and two launches.

[diagnose.py](diagnose.py) checks pinned inputs and capture hashes, reproduces
s284's locked result, reuses its unchanged portable source/receipt/stream checks,
and independently derives host equality from both archived byte streams. It also
checks separate run identities and archive/check ordering. It never consults the
current mutable host log and never launches the player. Original-path live receipt
validation is additionally recorded in [gates.json](gates.json); offline diagnosis
does not reseal receipts or claim to revalidate an absent player installation.

## Source-first and scope

1. The complete root observer and its precise delta are in each archived
   `patches/main/frame_10/DoAction.as` and `instrumentation.diff`; qualification
   checks guard-before-clock/input/sample and done-before-arm placement.
2. No authored PlaceObject/MOVE lifetime is changed; fighter/helper binaries and
   ordinary instrumentation are unchanged after run-ID/build-path substitution.
3. Normal retains quit at done; held moves quit to the next root closure guard.
   No gameplay goto/stop/label end or timeline fallthrough is synthesized.
4. Tests protect source erasure, strict stream boundaries and host custody; no
   guessed frame, callback count or startup/random equivalence is asserted.
5. The unchanged s228 input tape ran in the original native player twice. This
   evidence is not an original/Godot parity comparison or runtime authorization.

Only s293 and proportionate tracking/manifest updates change. Ranks1–2 and4–9
are not executed. s254–s292, game/scripts, runtime, contracts and shared
sampler/threshold/validator remain unchanged. No default rollout, solved
s259/s269 replay as new work, trimming, full-AS claim, merge or deployment.
Zero product obligations are closed; the broader M0-02 task remains pending.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s293/diagnose.py --output /tmp/s293.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s293/diagnose.py --output /tmp/s293-pair.json --require-completion-proof
PYTHONPATH=. python3 evidence/sampling-upgrade/s293/diagnose.py --output /tmp/s293-terminal.json --require-terminal-completeness # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s293/diagnose.py --output /tmp/s293-full.json --require-full-as normal # exit1; held also exit1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s293 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s284 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

The capture driver is deliberately single-use for these paths/identities: replay
analysis from archives; a future authorized capture needs fresh identities and
paths. It requires explicit `--allow-window-activation` and the external JPEXS
jar recorded in execution.json. No fresh launch is needed for diagnosis/tests.

[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[session timing](session-timing.json) retain validation evidence and measured
costs. Initial reading/design and person-days are unmeasured. No runtime or
contract change requires a Godot or contract check.

Validation: **81 tests pass** (17 new, 10 retained s284, 54 retained tools).
Diagnosis, independent pair proof, both original receipts, integrity and handoff
exit0. Terminal completeness and both full-AS gates exit1 as required.
