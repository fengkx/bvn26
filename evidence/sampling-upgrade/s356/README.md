# s356 — AFTER-s353 rank #3: Yulong erasure

Base: `566bf4f2` (origin/master, post-squash #233 s355).
Branch: `feat/s356-yulong-erasure`. Authority: [unchanged rank #3](../next-fix-priority-after-s353.md).
Only rank #3 executes; ranks 1–2 deliveries stay closed, ranks 4+ planning only.
The table's historical planning wording remains unchanged. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result: independent association still unproved

No original/candidate loaded definition, same-input activation pair or defining
scope was independently associated. Initialization-to-overwrite/return erasure
remains unmeasured. Zero independent runtime observations and zero mechanism or
product obligations closed. Null measurements do not mean zero effects.

The independent route asks whether the **existing SWF debugger metadata** can
provide a source-breakpoint entry, instead of extending s347's numeric dispatch
branch or repeating the function-header/CFG/adapter inventory. This is a bounded
failed prerequisite attempt, not loaded-definition proof.

[probe_debug_route.py](probe_debug_route.py) reads the original Yulong movie and
the unique `game/fighter/yulong.swf` member directly from the retained s275 tar
archive, without extracting or changing files. Both are checked against the
pinned s275 build receipt. The parser validates full SWF length, complete tag
boundaries, nested timelines and End tags; it records existing EnableDebugger
(58), DebugID (63), and EnableDebugger2 (64) tags with uncompressed offsets.
It neither interprets actions nor inserts debug tags or helper code.

[Independent disk result](debug-route.json):

| Artifact | SHA-256 | File bytes | Validated timelines | Tags 58 / 63 / 64 |
| --- | --- | --- | --- | --- |
| Original | `fcf2246b602b4e498caf2b3c9ac6625ae492e45b6249effb22e9b7d669713199` | 625728 | 18 | 0 / 0 / 0 |
| Archived candidate | `6552776258058bc3e9362fb9056b33db7da09a8f82db9f2c9883dfd2fe99fd57` | 628218 | 18 | 0 / 0 / 0 |

These are fresh disk observations, not runtime identity. Archive availability
and matching hashes do not establish which definition was loaded, whether it
executed, its invocation, or a defining scope. No existing debug-tag entry was
found for this route; no source-breakpoint-to-definition channel was obtained.
Tag absence does **not** establish that native debugging or an independent native
resolver is impossible. No native debugger protocol session was attempted.
This narrow negative does not prove erasure, harmlessness, or equivalence.

The [binding attempt](binding-attempt.json) keeps both runs, loaded bodies,
activations, scopes, same-input tape association and uninterrupted lifetime null.
All six paired boundary rows remain null: initialization, enumeration, member
access, coercion, overwrite, and no-overwrite null return. An overwrite witness
would not prove the separate return path. No observer was installed; no off/on
controls were executed. Zero new builds, launches, attaches, memory reads or
captures. No stack address is treated as scope; no early helper, extra hitTest,
ancestor pn, enlarged boxes or inferred harmlessness is used.

Next work must derive an independent loaded-definition/activation/scope channel
for one original/candidate pair, preserving lifetime through those six boundaries,
before measuring erasure and then qualifying observer effects. Rebuilding with
debug tags would change the artifact and is not an accepted shortcut here.

## Retained evidence and gates

[diagnose.py](diagnose.py) pins all s347 artifacts and reproduces its **complete**
locked diagnosis, recursively retaining prior Yulong tooling. This is validation
only; neither historical traces nor s347's static route are new s356 progress.
It also re-extracts the entire independent disk record and rejects fabricated
binding/boundary data. There is no proof override or trace-import path.

| Gate | Actual exit |
| --- | --- |
| Base diagnose | 0, admission and parity false |
| `--require-activation-pair` | 1 |
| `--require-activation-scope` | 1 |
| `--require-activation-erasure` | 1 |
| `--require-observer` | 1 |
| All four proof flags | 1 |

Codes are `S356_<UPPERCASE_FLAG_WITH_UNDERSCORES>_UNPROVED`.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s356/diagnose.py --output /tmp/s356.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s356 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s356/probe_debug_route.py --output /tmp/s356-route.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s356/run_checks.py
python3 tools/verify.py
python3 tools/check_handoff.py
```

All new input/tool paths are repo-relative. No external player or disassembler is
needed for this recheck. [run_checks.py](run_checks.py) records gates, complete
predecessor regression commands, local mutation/parser tests, exact whole-record
re-extraction, verify, handoff and whitespace checks. Synthetic parser fixtures
are not behavior proof. [Gates](gates.json), [project checks](project-checks.json),
[input pins](input-sha256.json), [route pins](route-sha256.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json),
[artifact hashes](artifact-sha256.json) and [timing](session-timing.json) retain
custody. Timing measures implementation/check wall time; initial reading/design
and later Git/PR work are excluded, person-days unknown.

## Source-first and scope

1. Complete Sprite2 functions/operands remain locked in s294/s302/s309/s318.
2. Sprite345 frame188 depth28 k1atm and nested mian placement do not identify
   a native activation or defining scope. No placement is altered.
3. Sprite104 stop/goto/removal and explicit returns remain retained context;
   label end or absent observations are not return.
4. Tests enforce provenance, parsing bounds and honest unknowns, not gameplay
   assumptions. Header/CFG/tag inventories are not mechanism proof.
5. No fresh original/Godot same-input comparison; native parity stays unproved.

Only s356 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s355 trees, all priority tables, game/, scripts/, runtime, contracts and
shared sampler/threshold/validator remain unchanged. No other rank executes.
Godot and contract checks do not apply to this evidence-only cut. Delivery is a
Draft PR only, no ready marking, merge, deployment or product closure.

Validation: **141 tests pass**. Base exit0; four proof gates and combined
exit1. Full disk re-extraction matches; verify, handoff and whitespace checks
exit0. Protected diffs are zero.
