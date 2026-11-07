# s343 — AFTER-s335 rank #8: AImain allocation

Base: `485992a0` (origin/master, post-s342 squash #220).
Branch: `feat/s343-aimain-allocation`.
Authority: [unchanged AFTER-s335 rank #8](../next-fix-priority-after-s335.md).
Ranks 1–7 delivered as s336–s342 stay closed; rank 9 remains planning only.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero mechanism/product obligations closed. Evidence delivery is not lookup completion.

## Result

Neither separate byte-bound native lookup path was derived. The first prerequisite
remains unmet; live binding and actual clearing/replacement/free/reuse controls
were not executed. There are zero independent native observations.

The fresh [disk search](lookup-candidates.json) examines the locked s325 player
SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
It searches six source-route names in ASCII and UTF-16LE, with exact and lowercase
spellings kept separate. Lowercase is a search variant, not a semantic alias.
[Collector](collect_lookup_candidates.py) records every match and a bounded
48-byte preceding / 96-byte following context, mapped to its Mach-O section.

| Route/name | Fresh on-disk finding | What remains missing |
| --- | --- | --- |
| Parent/depth `_parent` | ASCII at file offset 18477025 in `__TEXT,__cstring` | Parent instance generation and field layout |
| Parent/depth `getDepth` | ASCII at 17286325, 17287618, 17287780 in `__TEXT,__const` | Executable entry and return-to-depth binding |
| Parent/depth `getInstanceAtDepth` | ASCII at 17286473 in `__TEXT,__const`, within a comma-separated method-name list | Instruction bytes, dispatch-to-implementation association, occupant layout/generation |
| Saved globals `s261Parent`, `s261Depth`, `s261Receiver` | No matches in these encodings/spellings | Independent saved-value location, representation and dereference path |

These are text bytes, not resolver code or live referents. The finite search cannot
exclude interned, encoded, runtime-created or indirect paths; absence of a global
name in the player does not imply the runtime global is absent. No guessed function
address or inferred pointer/layout follows from adjacency in a method-name list.
No instruction window was decoded and no code cross-reference was established.
The search stops at this unresolved name-to-executable association, without
claiming an exhaustive machine-code search or impossibility of a resolver.

[Diagnosis](diagnosis.json) fully reproduces locked s334 (recursively retaining
s325 and earlier AImain evidence). Its adapter inventory, symbol/import pins,
8,290 historical AIREF events and source routes are retained validation only,
not new proof. The disk-name search is new evidence of candidate text locations,
not new native identity, pool coverage or product progress.

## Separate prerequisites

The parent/depth path must independently bind parent generation + depth to the
current display-list occupant. The saved-reference path must independently locate
and decode the saved AS2 value to its referent. Both instruction addresses, bytes,
layouts, live bindings and result allocation generations remain null in diagnosis.
The saved path must not borrow the slot result. Disk module identity does not bind
a loaded module or owner generation.

Only after both paths are derived and qualified can an observer begin before
control allocation and stay uninterrupted through retained content clearing,
same-name/depth replacement, free and reuse, including internal pool checkout/
return and deferred-free ordering. Missing reuse is unproved, not success.
No imported allocator as pool coverage, pointer-only identity, 0→1 alias,
property deletion as clearing, token-loss inference or unloaded exemption.

## Reproduction and gates

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s343/diagnose.py --output /tmp/s343.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s343 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Diagnosis re-reads the installed locked binary and compares the candidate search
and bounded contexts (excluding measured duration), validates input pins and the
entire retained s334 report. It requires the recorded binary path and hash;
unavailable/changed inputs fail closed as `S343_EVIDENCE_INVALID`.

Base exit 0 means package consistency only. Each of `--require-slot-reference`,
`--require-content-clearing`, `--require-replacement`, and
`--require-allocation-identity` exits 1 with its distinct `S343_*_UNPROVED` code.
A local collection-timer bug was rejected by duration validation, corrected and
recollected; [development failure](development-failure.json) retains the initial
invalid exits separately from the final gates. It is not a native failure.
Tests reject substituted bytes, invented live binding, changed prior inputs and
all four proof claims. Search-fixture tests check byte matching, not native behavior.
See [gates](gates.json), [project checks](project-checks.json) and
[timing](session-timing.json) for actual exits and measured subprocess costs.

## Source-first and scope

1. Locked s334 chain retains Yijiao Sprite455 frame1 initCtrl unload, Sprite3
   frame1 stop and no frame2 DoAction. No new frame semantics are inferred.
2. Retained source placement is unchanged; no native lifetime was observed here.
3. No label-end return, timeline or scheduling change is introduced.
4. Tests protect evidence custody and unknowns, not guessed allocation behavior.
5. Historical same-input AS2 evidence is retained; no fresh original/Godot comparison.

Only s343 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
Authority, every prior s254–s342 tree, game/scripts, runtime, contracts and shared
sampler/threshold/validator remain unchanged. Zero builds, launches, attaches,
live memory reads or captures. No other rank execution or re-ranking.
[Scope](scope-audit.json), [manifest audit](manifest-audit.json),
[input pins](input-sha256.json) and [artifact hashes](artifact-sha256.json) retain
custody. Artifact index excludes itself and caches. Initial reading/design and
person-days are unknown; timing excludes subsequent commit/push/PR work.
Draft only: no ready marking, merge or deployment.

Validation: **126 tests pass**; base exit 0, four proof gates exit 1;
verify.py, check_handoff.py and whitespace checks pass.
