# s314 — AFTER-s308 rank #6: terminal observer qualification

Base: current origin/master `dfdbdcd5d1de59b27194b21e6fc138ef91bc37ae`
(post-s313 squash). Branch: `feat/s314-terminal-callback`.
Authority: [AFTER-s308 rank 6](../next-fix-priority-after-s308.md);
[s304 README](../s304/README.md) and diagnosis are locked prior.
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

## Exact cut and result

Qualify independent loaded-body/owner-generation/activation entry-to-dispatcher-return
observation for the one root `onEnterFrame` installed by the archived
`patches/main/frame_10/DoAction.as`. This is an instrumentation callback, not
an asserted authored gameplay callback. Complete terminal dispatch inventory is
explicitly deferred. No ranks 1–5 or 7–9 experiments are executed.

[diagnose.py](diagnose.py) replays s304 exactly, including its locked s293 result,
without recapturing the solved independent normal/held pair. The new audit
extracts the actual `aiEvent` serializer from the held archive's frame-1 action,
retains its member SHA-256 and line bounds, and relates its eight fields to the
selected callback's nine source boundary sites and four post-marker operations.
[diagnosis.json](diagnosis.json) retains the complete normal/held terminal suffix,
the channel audit and five explicit qualification requirements.

What is proved by this static/replay audit:

- The archived serializer emits `AIREF`, run ID, event sequence, timer, display,
  fight counter, kind and value. It has no dedicated loaded-body, owner-generation,
  activation-entry or dispatcher-return fields. The selected markers do not add them.
- The closing guard emits its marker, replaces the callback, disables `aiEvent`,
  requests quit, then contains an explicit return. Source ordering does not prove
  execution of those later operations. Ordinary/timeout fallthrough is also not
  a dispatcher-return observation.
- The guard precedes display increment. Done and closure markers have the same
  archived clock values despite occupying different source invocation paths.
  Tick/display therefore cannot serve as the missing activation identifier.
- Host custody preserves the same producer's rows; independent custody is already
  closed, but it does not create an independent callback observer.

What remains unproved: loaded body resolution, root owner lifetime/defining scope
and closure generation, unique activation entry, the same activation returning to
its dispatcher, and observer-off/on preservation through logger replacement.
All five `qualified_witness` values remain null. Neither source SHA nor a root
receiver string identifies the executing closure. Property replacement does not
return an active invocation. Quit, unwind and normal return must remain distinct.

The search is bounded to the locked prior and its archive/logs; this is not a
claim that no external facility exists. No qualified independent facility is
established in those inputs. A new capture cannot supply that missing qualification
by itself, so none is attempted. Future qualification must keep the done-producing
and closing invocations distinct and match each relevant return to its own entry.
Even success for this callback would not prove all terminal callbacks complete.

## Gates and reproduction

| Command mode | Expected exit | Meaning |
| --- | --- | --- |
| Base diagnosis | 0 | Reproducible bounded audit; both admission flags false |
| `--require-observer-qualification` | 1 | Independent observer not qualified |
| `--require-callback-completion` | 1 | Same-activation dispatcher return absent |
| `--require-terminal-completeness` | 1 | Full inventory deferred and unproved |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s314/diagnose.py --output /tmp/s314.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s314/diagnose.py --output /tmp/s314.json --require-observer-qualification
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s314/diagnose.py --output /tmp/s314.json --require-callback-completion
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s314/diagnose.py --output /tmp/s314.json --require-terminal-completeness
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s314 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Project checks](project-checks.json) and [gates](gates.json) retain commands,
exit codes and measured durations; tests include s314, retained s304/s293/s284
and existing sampling/terminal tests. Negative mutations protect the serializer,
source ordering, input custody and false gates, not guessed runtime behavior.
[Input hashes](input-sha256.json) pin the prior and authority; s304 recursively
checks its own locked inputs. [Artifact hashes](artifact-sha256.json) cover all
s314 top-level files except the hash index itself.
[Scope audit](scope-audit.json) and [manifest audit](manifest-audit.json) record
the exact allowed diff and reviewed tracking hash updates.
[Timing](session-timing.json) records the implementation interval and subprocess
costs; initial reading/design and person-days are unknown.

## Source-first and exclusions

1. s304 retains the complete callback; this cut additionally binds its logger
   implementation and boundary lines. No gameplay mechanism is changed.
2. No PlaceObject/MOVE or instance lifetime changes; property replacement does
   not prove removal or active invocation completion.
3. No label end/goto/stop is synthesized; source exits are conditional facts,
   not observed native returns.
4. Assertions protect archived source/data invariants and missing observations.
5. Existing unchanged input/captures are replayed; no new original/Godot comparison.

Only s314 plus proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest changes.
Empty diff on s254–s313 and every other evidence directory; no game/, scripts/,
runtime, contracts, shared sampler, threshold or validator changes. Zero new
builds, launches, attaches, memory reads or captures. No solved-pair recapture,
fixed read-count threshold, silence-as-return, trimming, random tape replacement,
receipt resealing, full-AS claim, merge or deployment.
