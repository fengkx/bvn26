# s355 — AFTER-s353 rank #2: Independent ones clock

Base: `a207da0a` (origin/master, post-squash #232 s354).
Branch: `feat/s355-ones-clock`. Authority: [unchanged rank #2](../next-fix-priority-after-s353.md).
Rank #1 delivery stays closed; ranks #3+ planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Honest-unproved: loaded ten-target entry and independent outer lifetime are absent.**

## Independent actual-caller route

s346's numeric 0x9f candidate did not bind the actual ones caller. This attempt
starts independently at the original `game/main.swf` Sprite1813 frame1 action,
corroborated by `scripts/main.json#DefineSprite_1813/frame_1/DoAction.as`.
[Extractor](extract_route.py) verifies the original hash, parses the tag hierarchy,
selects the unique action, retains its full 762 bytes, and checks the constant
pool, containing DefineFunction2 header and local branch targets. It does not
execute AVM or modify the movie. [Result](caller-route.json) records:

- Action payload begins at uncompressed SWF offset 7270480. The anonymous
  function assigned to `time` has body range [187,662) relative to the action.
- Ones operand window [629,662): pool19 `gs`, GetVariable, integer1, Add2,
  argument-count1, pool22 `个`, GetVariable, pool21 `gotoAndStop`, CallMethod,
  Pop. The call is action offset660, uncompressed offset7271140, opcode **0x52**.
  Pool20 `十` belongs to the preceding tens call and is not substituted for ones.
  No relative branch in this function enters the middle of the operand window.
- This is a static byte-bound caller, not proof of loaded receiver identity,
  successful name resolution, execution, or the selected target value.
- Re-read the receipt-pinned player's retained dispatcher/table/0x52 arm.
  Table `0x12cf44`, entry `0x12d07c`, resolves to `0x124c2b`. The retained
  arm's jump at `0x124cbd` leads to `0x1264db`. These old bytes are validation,
  not new s355 progress, and no Chad experiment is executed.
- New native prefix [0x1264db,0x1264ef), **20 bytes**:
  `mov rax,[r13+0xd50]; cmp byte [rax+0x951],0; mov rax,[rbp-0x60];
  je 0x126537`. Fallthrough is `0x1264ef`. Both successors remain unresolved.
  Discovery inspected 128 bytes; only this first-branch prefix is retained and
  analyzed. All addresses are module-relative, unslid disk coordinates.

The independent discriminator is the original caller's operand/function binding:
its immediate opcode is 0x52, so s346's 0x9f route cannot itself establish this
caller. This does **not** rule out eventual use of a common implementation.
The new prefix is a generic conditional route, not a gotoAndStop resolver or
frame-entry effect. The table association is conditional on dispatching these
bytes in this interpreter; no loaded run/module association was observed.
All ten target rows remain null for independent entry and ordering.

## Separate outer-lifetime assessment

The new route reads `[r13+0xd50]` then `[rax+0x951]`; no independently derived
object layout associates these with outer ones. A stack value, field address,
constant-pool name or numeric opcode is not an instance generation. Allocation,
removal, replacement and uninterrupted live generations are unbound. The old
Sprite1813 depth3 placement/removal inventory is retained context only, not new
lifetime progress. No independent lifetime channel was obtained; this bounded
attempt does not establish that such a channel is impossible.

Isolated repeated-target, changed-target, same-depth replacement and observer
off/on controls remain unexecuted/unqualified. Fresh capture stops before launch.
No helper/glyph identity, synthetic clock, empty action insertion, scene repair,
cross-run image or borrowed run is used. Zero live observations, builds, player
launches, attaches, memory reads, captures, images or product obligations closed.

## Retained proof and gates

[Diagnosis](diagnose.py) pins all s346 artifacts and replays its **complete**
locked diagnosis, recursively preserving the retained tooling and 26,828-event
historical stream. This is validation only. It separately records new disk facts
and missing live proof; old reports are not relabeled as progress.

| Gate | Expected exit |
| --- | --- |
| Base diagnose | 0, admission/parity false |
| --require-target-entry | 1 |
| --require-outer-lifetime | 1 |
| --require-independent-controls | 1 |
| --require-child-clock | 1 |
| --require-fresh-capture | 1 |
| All proof flags combined | 1 |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s355/diagnose.py --output /tmp/s355.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s355 -p 'test_*.py'
# Re-extract using the path in the pinned s303 receipt, or an identical binary:
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s355/extract_route.py --output /tmp/s355-route.json
# Optional: --binary /path/to/receipt-matching-player (full hash required).
python3 tools/verify.py
python3 tools/check_handoff.py
```

[run_checks.py](run_checks.py) runs each gate, complete predecessor regression
commands, local mutation tests and disk re-extraction with exact JSON equality.
All new implementation paths are repo-relative or resolved from a pinned receipt;
no disassembler executable is needed for rechecking. The external player is a
receipt-matching input, not a bundled dependency. New tests reject wrong original
or player bytes, swapped ones/tens operands, changed function bounds, forged
loaded association, mutated complete prior replay and promoted admission.
[Gate results](gates.json), [project results](project-checks.json),
[input pins](input-sha256.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [artifact hashes](artifact-sha256.json)
and [measured timing](session-timing.json) retain custody. Timing excludes initial
reading and later Git/PR work; person-days unknown.

## Source-first and scope

1. Sprite1810 frame1 is `stop();`; frames2–10 have no DoAction, as retained in
   s292/s346. Empty frames are not treated as neutral or independently observed.
2. Outer Sprite1813 depth3 is separate from inner depth1 glyph MOVE and helper
   generations. Their inventory cannot establish native outer lifetime.
3. Original timer calls `gotoAndStop(gs+1)`; no synthetic advance/reset is added.
4. Tests lock original bytes, provenance and honest unknowns, not scheduling guesses.
5. No fresh original/Godot same-input comparison; parity remains unproved.

Only s355 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s354 evidence, all authority tables, game/, scripts/, runtime, contracts,
shared sampler/threshold/validator stay unchanged. No other rank executes.
No contract/Godot checks apply to this evidence-only cut. Next work needs loaded
actual-caller-to-method/frame-entry association for ten targets and a separate
outer-generation channel before controls, then qualified same-capture evidence.
Delivery closes this evidence cut only; it does not close the mechanism or M0-02.

Validation: **127 unique tests pass** (nine final local mutation tests also
rerun after refinement). Base exit0; five proof flags and combined exit1.
Re-extraction equals the full record; verify, handoff and diff checks exit0.
