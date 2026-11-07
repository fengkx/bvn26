# s328 — AFTER-s326 rank #2: Independent ones entry clock

Base: `bf44f46e8b5ea19190566f9fa0c6cf570c9b6931` (s327 #205 squash).
Branch: `feat/s328-ones-entry-clock`.
Authority: [unchanged AFTER-s326 table, rank #2](../next-fix-priority-after-s326.md).
Only rank #2 is executed; rank #1 delivery stays closed and ranks 3+ remain planning.
The table's “ranks 2+ planning” describes s327; the table is not rewritten here.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Evidence-only, honest-unproved: no independent entry/instance clock was derived.**

## Result

[diagnose.py](diagnose.py) pins every s319 artifact and reproduces the complete
locked s319 diagnosis, recursively validating its historical 26,828 events.
Glyph mapping, four historical frame1 joins, replacement helper events and the
three reporters' shared dependencies are retained validation, not new progress.

The attempted derivation checks the applicability of three retained host adapter
functions. [Diagnosis](diagnosis.json) records exact function source, line spans,
hashes and the missing association for each candidate. These functions were read,
not invoked; this is a bounded source assessment, not a live facility experiment.

| Candidate | Available output | Missing association for rank #2 |
| --- | --- | --- |
| `probe_owned_debugger.debugger_script` | Selected thread/frame-zero registers, attach/detach status | No ones entry site, native outer-instance layout or continuous lifetime resolver in this script. A register snapshot cannot identify entry into frames1–10. |
| `monitor_owned_native.monitor_owned` | PID checks, AIREF profile marker, process state and a one-second stack sample request | PID ownership does not identify an outer clip; statistical stacks cannot enumerate repeated entries. The ownership marker still depends on the AS log. |
| `sampling_native.validate_capture` | Case/configuration and AIREF sequence/state/completion validation | Host custody of AS reports is not an independent entry channel, including while the observer is off. |

The retained adapters cannot be used as-is to qualify the required clock. Their
source does not establish that deriving another native channel is impossible.
No native dispatcher address or object layout was guessed; no attach, sample,
player launch, build, memory read, control execution, fresh capture or image was
performed. This package adds reproducible feasibility reporting and guards; it
adds **zero independent native observations and closes zero mechanism obligations**.

All ten frame rows retain null independent entry, isolated repeated-target,
changed-target, same-depth replacement and observer-off/on order qualifications.
Even frame1 is unqualified. Both live resolvers remain null. No old report is
promoted by the new packaging. Fresh capture is blocked before launch.

## Required next observation

Derive a byte-bound native target-entry site and independently resolved outer
ones instance lifetime, including the nine actionless frames. Bind those to the
actual loaded module and same run without substituting an AS helper generation,
glyph, path/depth or CPU sample for identity. Observe target selection, actual
entry and following root/callback boundary independently in that run/lifetime.
Then qualify isolated repeated-target, changed-target, same-depth replacement
and observer-off/on controls, keeping the independent channel in both modes.
Only after qualification may a fresh ones-only capture run. Future facility
work is not performed or pre-approved as a successful result here.

## Gates and reproduction

| Requirement | Expected exit | Code |
| --- | --- | --- |
| Base diagnosis | 0 | `S328_DIAGNOSIS_OK` |
| `--require-observer` | 1 | `S328_ENTRY_INSTANCE_RESOLVER_UNPROVED` |
| `--require-independent-controls` | 1 | `S328_INDEPENDENT_CONTROLS_UNPROVED` |
| `--require-child-clock` | 1 | `S328_CHILD_CLOCK_UNPROVED` |
| `--require-fresh-capture` | 1 | `S328_FRESH_CAPTURE_BLOCKED` |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s328/diagnose.py --output /tmp/s328.json
# Run each proof flag separately; all four must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s328 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) and [project checks](project-checks.json) retain actual commands,
exits, timings and log names. Checks include s319/s310/s301/s292/s282 plus retained
digit lifetime, callback visual state, countdown phase and sampling tests.
Mutation tests reject changed register selection, sample request, log sequence
validation, missing facilities, altered prior diagnoses and proof promotion.
They test provenance and honest unknowns, not an assumed Flash schedule.
No contracts or runtime changed; contract/Godot checks are not applicable.

## Source-first and scope

1. Locked Sprite1810 frame1 is `stop();`; frames2–10 have no actions.
   s319 and its retained s292 byte audit remain the source evidence.
2. Sprite1813 outer depth3 lifecycle is separate from glyph depth1 MOVE/character
   changes. Neither helper generations nor process identity prove outer lifetime.
3. Timer selection uses `gotoAndStop`; no synthetic playback, entry count or
   label-end reset is introduced.
4. Tests protect exact retained inputs and unproved gates, not inferred timing.
5. No fresh original/Godot same-input comparison exists; native parity stays false.

Allowed changes are new s328 files and minimal STATUS/SAMPLING_UPGRADE/tasks/
manifest tracking. Authority and all s254–s327 evidence remain unchanged, as do
game/, scripts/, runtime, contracts and shared sampler/threshold/validator.
No re-ranking or other-rank execution. No glyph-as-entry, helper generation as
native identity, synthetic clock, empty actions as neutral, scene repair,
cross-run images, ready marking, merge or deployment.

[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json),
[input pins](input-sha256.json) and [artifact hashes](artifact-sha256.json) retain
custody. Artifact index excludes itself and Python caches. [Timing](session-timing.json)
measures implementation/check wall time; initial reading/design and person-days
are unknown, and later commit/push/PR time is excluded.

Validation result: **103 tests pass** (8 s328, 49 retained slice tests, 46 shared
tool tests). Base diagnosis exits 0; all four proof flags exit 1. Integrity and
handoff exit 0. The first attempt used system Python 3.9 without Pillow and
failed before diagnosis; [failure log](initial-environment-failure.txt) is retained.
Successful checks use the existing Python 3.11.15 with Pillow 12.3.0; full executable
paths are in the command records. No dependencies were changed.
