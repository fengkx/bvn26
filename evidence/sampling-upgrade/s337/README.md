# s337 — AFTER-s335 rank #2: Independent ones clock

Base: `8e873eaffaac7cf80c0a3f90a32ef1a6c032ab2f` (s336 #214 squash).
Branch: `feat/s337-ones-clock`. Authority: [AFTER-s335 rank #2](../next-fix-priority-after-s335.md).
Only rank #2 executes. Rank #1 delivery stays closed; ranks 3+ remain planning.
The authority's “ranks 2+ planning” describes s336 and is not rewritten here.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Honest-unproved: neither required independent channel was derived.**

## Attempt and result

[extract_native.py](extract_native.py) reads the disk player only, verifies the
complete receipt-pinned SHA-256 and Mach-O metadata, and searches for the exact
NUL-delimited ASCII `gotoAndStop` name. This is a bounded attempt to locate an
anchor for a native target-entry derivation, not another host adapter inventory.
For any match it would map the file coordinate to an unslid address and enumerate
that eight-byte little-endian address pattern; even such patterns would require
independent instruction/relocation and registration analysis before use.

[Actual result](native-search.json): **zero exact name matches** in the
24,120,048-byte binary, SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
Consequently no address-pattern search was reached, no candidate function bytes
were extracted, and no byte-bound executable entry site was obtained. Other name
encodings, computed references and instruction-led derivations are outside this
attempt. The result does not prove an entry channel impossible or absent.

There is also **no independent outer-instance lifetime channel**: no object
layout, loaded instance binding or uninterrupted lifetime observation was derived.
The failed name route supplies none of those relations. No separate live lifetime
experiment was run and no claim of exhaustive lifetime search is made. A native
method name, even if found, would not establish outer identity. This cut closes
zero mechanism obligations and adds zero independent runtime observations.

[diagnose.py](diagnose.py) pins every s328 artifact and reproduces its complete
locked diagnosis, recursively revalidating the retained 26,828 historical events.
The three adapter assessments, frame1 reports, glyph mapping and encoded helper
generations are **retained validation only**, not new progress or native identity.
No prior proof is rewritten. The only new measured fact is the negative bounded
disk search; neither it nor a green base diagnosis proves a clock.

## Qualification boundary

All ten rows retain null independent entry, isolated repeated-target,
changed-target, same-depth replacement and observer-off/on qualifications,
including frame1. Each of the four controls is explicitly unexecuted and
unqualified in [diagnosis.json](diagnosis.json). Fresh capture stops before launch.

The next required evidence is a byte-bound target-entry dispatch covering frames
1–10 plus independently resolved outer ones lifetimes. Both must bind to the
actual loaded module and same run, with uninterrupted generations through
replacement. Observe selection, actual entry and following root/callback order;
then qualify isolated repeated/changed targets, replacement and observer-off/on
with the independent channel surviving both modes. Only then capture fresh ones.
This describes missing evidence, not newly measured scheduling behavior.

## Gates and reproduction

| Mode | Expected exit | Code |
| --- | --- | --- |
| Base diagnosis | 0 | S337_DIAGNOSIS_OK |
| --require-target-entry | 1 | S337_BYTE_BOUND_TARGET_ENTRY_UNPROVED |
| --require-outer-lifetime | 1 | S337_INDEPENDENT_OUTER_LIFETIME_UNPROVED |
| --require-independent-controls | 1 | S337_INDEPENDENT_CONTROLS_UNPROVED |
| --require-child-clock | 1 | S337_CHILD_CLOCK_UNPROVED |
| --require-fresh-capture | 1 | S337_FRESH_CAPTURE_BLOCKED |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s337/diagnose.py --output /tmp/s337.json
# Run each proof flag above separately; each must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s337 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
# Optional read-only extraction; no player launch or process attachment:
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s337/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output /tmp/s337-native-search.json
```

[Gates](gates.json) and [project checks](project-checks.json) record actual commands,
exits and subprocess durations, including disk re-extraction equality. Offline
base diagnosis uses the sealed search record and does not require an installed
player. Tests reject binary substitution, result/provenance mutation, altered
full prior replay and fabricated proof. Byte-search fixtures test search syntax,
not a synthetic clock or positive native control. Retained s328/s319/s310/s301/
s292/s282 and shared ones/countdown/sampling tests rerun unchanged. No contract or
Godot check applies: neither interface nor runtime changed.

## Source-first and scope

1. Locked Sprite1810 frame1 contains `stop();`; frames2–10 have no actions,
   as retained by s328 and the s292 byte audit. No empty actions are inserted.
2. Outer Sprite1813 depth3 lifetime is distinct from inner glyph depth1 MOVE.
   Neither path/depth nor helper generation is used as native allocation identity.
3. Timer selection uses `gotoAndStop`; no synthetic playback or label-end reset.
4. Tests protect provenance and honest unknowns, not an assumed Flash schedule.
5. No fresh original/Godot same-input comparison; native parity remains false.

Only s337 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s336 trees, authority tables, game/, scripts/, runtime, contracts,
shared sampler/threshold/validator remain byte-identical. No re-ranking, other
rank execution, glyph-as-entry, synthetic clock, empty-actions-as-neutral,
scene repair, cross-run images, build, launch, attach, memory read or capture.
No ready marking, merge or deployment.

[Input pins](input-sha256.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [artifact hashes](artifact-sha256.json)
retain custody. Artifact index excludes itself and caches. [Timing](session-timing.json)
measures implementation/check wall time, excluding initial reading/design and
later commit/push/PR; person-days remain unknown. Package completion is not
mechanism proof or product acceptance.

Validation: **110 tests pass**. Base diagnosis exits 0; all five proof flags
exit 1. Disk re-extraction is byte-identical; verify, handoff and whitespace
checks exit 0. These results do not qualify any independent clock channel.
