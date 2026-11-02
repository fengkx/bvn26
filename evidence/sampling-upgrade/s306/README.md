# s306 — AFTER-s299 rank #7: Loader consumed bytes

Base: origin/master `caaec62ce3e60bf87418bc727490419e963851d8` (s305 #183).
Branch: `feat/s306-loader-attestation`.
Exclusive authority: [AFTER-s299 rank #7](../next-fix-priority-after-s299.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; zero product obligations closed; M0-02 pending.

The executed P1 returned-byte/consumer/immutable-request/target join remains
unproved. Normal qualification is missing, so no wrong-resource control ran.

## New bounded result

[Native bytes](native-bytes.json) retain a **432-byte static wrapper** at unslid
`0x1004b3440–0x1004b35f0` and its six-byte `CFReadStreamRead` import stub.
[Extraction](extract.py) checks the full receipt-matching executable SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`, retains Mach-O
header/load commands and derives file offsets from the file-backed text segment.
The executable itself is not copied into the repository.

[LLDB transcript](read-wrapper.txt) (trailing whitespace normalized;
[raw transcript](read-wrapper-raw.json) retained losslessly) disassembles the complete containing function
from the executable on disk. [Diagnosis](diagnose.py) checks contiguous instruction
bytes through the entire range, verifies source-bound operand bytes and derives
signed relative call/branch targets. These are static instruction facts:

| Location | Derived fact | Still missing |
| --- | --- | --- |
| `0x1004b3451/54/58` | Entry length/buffer/object saved in r12d, rbp-0x30, rbx | Actual argument values and native object type |
| `0x1004b3541/45/49` | Stream comes from rbx+0x18; saved buffer/length restored to rsi/rdx | P1 membership, immutable request generation and consumption |
| `0x1004b354d` | Direct call resolves to locked stub `0x100fb5baa` | Whether this call executes for P1 at all |
| `0x1004b3552/55/57` | Candidate return site tests rax; negative goes to `0x1004b3592`, positive to `0x1004b35e6`, zero falls through | Returned count, bytes, complete ranges and actual path |
| `0x1004b35e6/59` | Positive path copies eax to r14d then branches to `0x1004b3592` | Loader consumer and callback target association |

The wrapper checks stream availability/status and has indirect calls elsewhere
in its body. We do not infer a class layout or request identity from rbx, its
`+0x18` field, or a reusable stream pointer. The function name emitted by LLDB is
an address label, not a resolved Loader class. Other read/buffering/mapped paths
and indirect callers remain unresolved. Finding this candidate is **not** a
claim that CFReadStreamRead is the P1 resource path.

Exploration scanned direct-call byte candidates for the four already locked
read stubs and inspected candidate functions on disk; these were rank #7 static
analysis only. The delivered result is limited to the complete wrapper above,
not an exhaustive call graph or read-site inventory. No new metadata name queries,
player launches, attaches, builds or captures occurred. Exploration costs before
retained extraction/validation are unknown; no unrecorded cost is estimated.

## Locked evidence and source boundary

The complete [s297 diagnosis](../s297/README.md) is executed and compared to its
locked report, recursively reproducing the 5,503 historical events, receipt/archive
provenance, original/archived loader order and four static stubs. [Input pins](input-sha256.json)
include s297 files, authority, new extraction and facility transcripts. No old
receipt, archive, tape, baseline or diagnosis is edited or resealed.

The original and archived `scripts/main.json` script
`DefineSprite_1900/frame_1/DoAction.as` shares one MovieClipLoader across P1,
P2, P1 assist, P2 assist and sound. Its callback ignores its `target` parameter:

```actionscript
LO.onLoadComplete = function(target)
{
   loadStep++;
   loadSteps[loadStep]();
};
```

There is no onLoadInit listener. This is authored source order, not an observed
callback schedule. A later mutable current-request field can already name the
next request; a wrapper object pointer cannot repair that ambiguity.

All eight live observation fields in [diagnosis.json](diagnosis.json) remain
null. Source-first execution qualification is incomplete: no new frame/script,
PlaceObject/MOVE or exit mechanism is implemented, no new original same-input
run exists, and tests assert only retained source/native bytes and rejection
boundaries. They do not invent Flash behavior or a successful synthetic join.

The next required discriminator is an independently resolved **actual P1** native
consumer and immutable request generation. Then retain executed API returns,
complete returned/consumed ranges (or actual mapped ranges and consumption),
and the request-bound callback target **before** inline loadStep advance.
Qualify observer effects and same-request init/use/unload/replacement separately.
Only after normal qualifies may a separate actual Yihu-for-Yijiao control run
with expected Yijiao identity unchanged, retaining supplied/returned/consumed
bytes and errors. A breakpoint hit, static file hash, server delivery or archive
substitution is insufficient. This fixed-evidence analyzer cannot admit a fresh
capture by changing flags; new execution needs independent analysis.

## Gates and verification

| Requirement | Exit | Code |
| --- | --- | --- |
| Fixed evidence diagnosis | 0 | `S306_DIAGNOSIS_OK` |
| Normal consumed-byte association | 1 | `S306_LOADER_ASSOCIATION_UNPROVED` |
| Target before inline advance | 1 | `S306_PRE_ADVANCE_TARGET_UNPROVED` |
| Separate wrong-resource control | 1 | `S306_WRONG_RESOURCE_BLOCKED` |

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s306/diagnose.py --output /tmp/s306.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s306/diagnose.py --output /tmp/s306.json --require-loader-attestation # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s306/diagnose.py --output /tmp/s306.json --require-pre-advance-target # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s306/diagnose.py --output /tmp/s306.json --require-wrong-resource-control # expected exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s306 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s297 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s287 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_loader_read_target_diagnosis tools.tests.test_loader_attestation_diagnosis tools.tests.test_capture_runtime_fighter tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

On a host with the matching executable, regenerate the retained extraction:

```sh
python3 evidence/sampling-upgrade/s306/extract.py --binary '/Volumes/Flash Player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output /tmp/s306-native-bytes.json
cmp /tmp/s306-native-bytes.json evidence/sampling-upgrade/s306/native-bytes.json
```

[Gates](gates.json), [checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) record
actual outcomes. Extraction hashes establish file provenance, never live bytes.
Initial exploration/design and person-days remain unknown. No Godot or contract
check is required because neither runtime nor contracts changed.

Only s306 and proportionate tracking/manifest updates change. Ranks 1–6 and 8–9
are not executed; s254–s305, game/scripts, runtime, contracts, shared sampler,
thresholds and validators remain unchanged. No static hash as live bytes, mutable
request proxy, helper stamp, global counter, receipt resealing or rollout.
No production admission, merge or deployment; M0-02 remains pending.

Validation: **73 tests pass** (11 focused, 9 retained s297, 4 retained s287,
49 retained loader/capture tests). Integrity, handoff and diff checks pass;
all three proof gates retain exit 1.
