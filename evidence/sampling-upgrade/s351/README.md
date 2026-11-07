# s351 — AFTER-s344 rank #7: AImain allocation

Base: `ac8cc1deab469f4e902f930922fa9701841fe227` (s350 #228 squash).
Branch: `feat/s351-aimain-allocation`.
Authority: [unchanged AFTER-s344 rank #7](../next-fix-priority-after-s344.md).
Ranks 1–6 delivered; ranks 8+ planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result

**Neither the name-to-executable association nor the independent saved-reference
native dereference path is proved.** Live generations and clearing, replacement,
free, reuse and internal pool controls remain unexecuted. Zero mechanism/product
obligations closed; zero independent native runtime observations.

The new [reference attempt](reference-attempt.json) takes the five exact unslid
addresses already locked by s343 as inputs. It checks every byte alignment in the
receipt-matching player for each little-endian 64-bit absolute address and reads
the Mach-O section relocation descriptors. It does not repeat name inventory.
The [extractor](resolve_references.py) is Python standard-library only, takes any
local `--binary` path, and rejects bytes not matching player SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.

| Retained text address | New absolute-address occurrences |
| --- | --- |
| `0x10107c4b5` getDepth | 0 |
| `0x10107c549` getInstanceAtDepth | 0 |
| `0x10107c9c2` getDepth | 0 |
| `0x10107ca64` getDepth | 0 |
| `0x10119efe1` _parent | 0 |

All 31 section relocation counts are zero; raw load-command and section-header
bytes are retained. This is a new finite static reference-resolution attempt,
not an executable resolver. Dynamic-loader info is recorded but its rebase/bind
streams are **not decoded**. RIP-relative instructions, relative tables and
references to enclosing string-list bases are outside this attempted route.
Consequently zero exact absolute occurrences and zero section relocations do not
prove absence of executable references, dynamic fixups or a possible resolver.
No adjacent word is treated as a function pointer; no instruction entry is invented.

The saved path is separately blocked at locating and decoding the saved AS2 value.
The retained source route `_global.s261Receiver -> saved` is a source-level read,
not a native dereference. Its location, representation, instruction bytes and
result allocation generation remain null in [diagnosis](diagnosis.json). There
is no independently grounded native target for that path; this slice does not
search its name again or substitute the parent/depth slot result. This is an
explicit unfulfilled prerequisite, not new progress from the old source route.

Both paths must be derived independently before binding loaded-module, parent,
saved-value and result generations, followed by uninterrupted observation from
before control allocation through content clearing, replacement, free and reuse.
Internal pool checkout/return and deferred-free ordering remain required. No
allocator import as pool coverage, pointer-only identity, 0→1 alias, deletion as
clearing or token-loss inference. Missing measurements are not observed negatives.

## Retention and reproduction

[Input pins](input-sha256.json) lock s343, its direct dependencies and authority.
The complete s343 diagnosis is preserved in the new report. Portable diagnosis
replays the complete s334 chain and checks it against s343's retained result;
it does **not** rerun s343's host-specific name collector or call that inventory
new proof. The local regression suite separately runs retained s343 tests against
the installed receipt-pinned binary. [Route pins](route-sha256.json) bind the new
extractor and raw report; portable consistency validation does not claim a fresh
binary re-extraction. For an independent disk recheck, supply a matching player:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s351/diagnose.py --output /tmp/s351.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s351 -p 'test_*.py'
python3 evidence/sampling-upgrade/s351/resolve_references.py --binary /path/to/receipt-matching-player --check
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base exit 0 proves package consistency only. Each `--require-name-executable`,
`--require-saved-reference`, `--require-slot-reference`, `--require-content-clearing`,
`--require-replacement` and `--require-allocation-identity` exits 1 with a distinct
`S351_*_UNPROVED` code. Combined proof flags also exit 1. There is no proof override.
Tests reject modified custody, substituted player/route bytes and invented native
bindings; unaligned-address fixtures test extraction mechanics, not Flash semantics.
See [gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json),
[artifact hashes](artifact-sha256.json) and [timing](session-timing.json).

## Source-first and scope

1. s343/s334 retain Yijiao Sprite455 frame1 initCtrl unload, Sprite3 frame1 stop
   and no frame2 DoAction; no new frame semantics are inferred.
2. Original placement evidence is unchanged; no live placement or lifetime observed.
3. No timeline, label exit or scheduling changes.
4. Tests protect evidence custody and unknowns, not guessed allocation behavior.
5. Historical same-input AS2 evidence remains retained only; no fresh original or
   Godot comparison, launch, attach, capture, build or memory read.

Only s351 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s350 trees, authority tables, game/scripts, runtime, contracts and shared
tools remain byte-identical. Draft PR only; no ready marking, merge or deployment.
Measured packaging and subprocess times exclude initial reading/preliminary probe
and later Git/PR work; person-days remain unknown.

Validation: **133 tests pass**; base exit 0, six individual proof gates and
combined proof gate exit 1; disk recheck, verify.py, check_handoff.py and whitespace
checks exit 0. These are evidence checks, not native parity.
