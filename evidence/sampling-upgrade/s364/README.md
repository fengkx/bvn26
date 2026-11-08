# s364 — Independent ones clock

Base: `c092443fb61dd07954f363ca4f331398312ca269` (s363 #241 squash).
Branch: `feat/s364-ones-clock`. Authority: [AFTER-s362 rank #2](../next-fix-priority-after-s362.md).
Only rank #2 executes. Rank #1 delivery stays closed; ranks #3+ remain planning.
The table's “ranks 2+ planning” records the s363 cut, not a prohibition on this
explicitly authorized next cut. The authority is unchanged; no re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Honest-unproved: loaded ten-target entry and independent outer lifetime absent.**

## Independent route and observed disk facts

The attempt seeks an executable method association through a packed-name
container, independently of the numeric opcode route. s337 only searched for an
entire NUL-delimited `gotoAndStop`; s355 bound the original static caller and
numeric continuation. Neither is repeated as new progress here. The new
[extractor](extract_native.py) checks the full receipt-matching player hash and
Mach-O metadata, then reads raw occurrences and selects an entire comma-delimited
member of a printable NUL-bounded container. No loaded method identity is inferred.

[Native record](native-route.json) independently records:

- Two ASCII substring occurrences at file offsets **17286385** and **17452759**.
  No UTF-16LE/BE occurrences. The second has preceding byte `0x0b`; the retained
  context is not interpreted as an ABC schema, registration or method definition.
- Exactly one qualifying printable comma container at file range
  **[17286200,17286528)**: **328 bytes**, in `__TEXT,__const`, unslid address
  **4312253496**. It has 27 comma members: `gotoAndStop` is zero-based member17,
  `removeMovieClip` member19. Prefix digits on other names remain literal bytes;
  they are not interpreted as versions or semantics.
- Zero candidates for that **container-start address** using seven-byte
  REX.W RIP-relative LEA encodings in `__TEXT,__text`, and zero exact eight-byte
  little-endian occurrences across the disk file. Section metadata defines bounds;
  no guessed function or opcode identity is used. The LEA search is an encoding
  filter, not a disassembly or exhaustive reference analysis. Interior, relative
  data-table, computed and enclosing-blob references remain outside this search.

This adds a concrete packed-text anchor missed by the older exact-NUL-name
boundary, but the route **stops before executable registration**. The text may
belong to embedded data; it is not established as a native registration table.
The absence of these two reference forms is not global absence or impossibility.
No actual ones call is associated with loaded method resolution or any frame entry.
No additional code path is expanded. The initial exploratory search and final
section-bounded extraction agree; only disk bytes and metadata were inspected.

The binary path defaults to the pinned s303 receipt, SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
An optional `--binary` path must match that entire hash and metadata. No absolute
machine-specific executable path is embedded in the new tools. Rechecking uses
Python standard-library parsing, not an installed disassembler.

## Separate lifetime and qualification boundary

The adjacent removal name supplies no typed receiver, allocation/removal hook,
replacement event or uninterrupted outer generation. This route did not derive an
independent outer-instance lifetime channel. No separate live lifetime experiment
was executed; neither pointer stability nor text adjacency fills that gap.

All ten rows retain null independent entry and order, including frame1. Four
controls—isolated repeated target, changed target, same-depth replacement and
observer off/on—remain explicitly unexecuted and unqualified. Fresh capture stops
before launch. There is no opcode-as-identity, helper/glyph-as-outer-lifetime,
synthetic clock, empty-action neutrality, scene repair or cross-run image.

[Diagnosis](diagnose.py) pins every s355 artifact and replays its **complete locked
report**, embedding it unchanged and recursively retaining tooling and historical
streams. This is retention validation only. New disk observations are separate
from live witnesses, all of which remain null. Zero mechanisms/product obligations
closed; zero builds, launches, attaches, memory reads, captures or images.

## Gates and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s364/diagnose.py --output /tmp/s364.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s364 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s364/extract_native.py --output /tmp/s364-native.json
python3 tools/verify.py
python3 tools/check_handoff.py
```

Portable diagnosis uses the sealed record and requires no installed player.
Optional extraction reads the receipt-pinned binary; supply an identical binary
with `--binary` on another platform. Write reruns to temporary outputs, not over
historical evidence. [run_checks.py](run_checks.py) is the package-production runner.

Base diagnosis exits **0** for custody/static consistency, with both admission
flags false. Each proof flag and the combined invocation exit **1**:

- `--require-target-entry`
- `--require-outer-lifetime`
- `--require-independent-controls`
- `--require-child-clock`
- `--require-fresh-capture`

Codes are `S364_<FLAG>_UNPROVED`. Invalid evidence is separately exit2 with
`S364_EVIDENCE_INVALID`; it is never accepted as an honest proof-gate failure.
No proof-import override is supplied. Tests reject every rehashed container-byte
mutation, provenance/bounds changes, fabricated live binding, binary substitution
and complete prior-report drift. Search fixtures exercise byte matching only,
not a synthetic clock or positive runtime proof. Full predecessor tests rerun
unchanged; [gates](gates.json) and [project checks](project-checks.json) record
commands, expected/actual exits and measured subprocess durations.

## Source-first, scope and next boundary

1. Retained source binds original Sprite1813 timer's actual static ones call;
   Sprite1810 frame1 is `stop();`, frames2–10 have no actions. No new action semantics.
2. Outer Sprite1813 depth3 differs from inner depth1 glyph MOVE and helper lifetimes;
   no independent outer generation was obtained from this disk-name route.
3. Original timer uses `gotoAndStop(gs+1)`; no synthetic advance or reset.
4. Tests protect raw bytes, custody and unknowns, not invented scheduling.
5. No new original/Godot same-input comparison; parity remains unproved.

Only s364 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s363 trees, priority tables, game/, scripts/, runtime, contracts and shared
sampler/threshold/validator remain unchanged. No contract/Godot check applies to
this evidence-only cut. No deployment, ready marking or merge.

[Input pins](input-sha256.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json), [artifact index](artifact-sha256.json) and
[timing](session-timing.json) retain custody. Timing covers initial independent
packed-name discovery, implementation, packaging and gates; excludes preceding
reading/design and subsequent commit/push/PR work. Person-days remain unknown.

Next evidence must derive executable method/frame-entry and independent outer
lifetime channels, then associate actual loaded caller, receiver generations and
all ten entries in one run. Only after both prerequisites may isolated controls
and fresh capture qualify. Delivery closes this bounded evidence attempt only;
it does not close Independent ones clock, M0-02 or product acceptance.

Validation: **135 unique tests pass** (the inherited nine-test local rerun also
passes: 144 executions in the recorded runner). Base exit0; five individual and
combined proof gates exit1. Disk re-extraction matches the entire record;
verify.py, check_handoff.py and whitespace checks exit0. Scope audit confirms
zero protected-path differences.
