# r08: source-local loader and HP initialization markers

Offline only: no Flash launch, foreground capture or inputs. Initial base is
r07 `9cfd26859a2ef181cf8d94c8631ab89c88d1007d` (#250), with master still
`2a3ab5eff97ad6472dfa31201482c33e4310b5e0` at the pre-publication check.
This change depends on #250; it does not modify that PR or historical r01–r07.
Official remaining UNKNOWN; not claiming above floor.

production_admitted=false, native_parity_proven=false, oracle_accepted=false.
M0-02 remains pending. Compile success is not live observation or noninterference.

## Exact source boundaries

All source names below refer to locked `scripts/main.json` unless specified.

| Boundary | Source | Retained observation |
|---|---|---|
| `loader-request` | `DefineSprite_1900/frame_1/DoAction.as`, `loadman(pr)`, immediately before existing loadClip | slot pr, selected key, resolved fighterDir+url, target._target |
| `load-complete-entry` / `load-complete-exit` | Same DoAction, **existing LO.onLoadComplete(target)** | target._target and loadStep before/after original increment and next loadSteps call |
| `chushi-hp-before` / `chushi-hp-after` | `frame_8/DoAction.as`, `var chushi = function()`, immediately bracketing existing chained HP assignment | maxhp, pause flags, both actors' coordinates/facing/body frame/HP/ql/action/beida/kcplayed |
| `decision-installed`, 39 lexical native-alias forwards | Retained r07 `scripts/fighter/yihu.json`, `DefineSprite_16/frame_1/DoAction.as` | yihu-sprite16 target marker; owner.kis called once, actual result returned unchanged |

**Required onLoadInit observation is not implemented:** none exists in the locked
exported source. A case-insensitive search across all62 script bundles found zero
onLoadInit occurrences; `callback-search.json` pins its scope and hashes. The
actual loader registers onLoadProgress, onLoadError and onLoadComplete. We observe
onLoadComplete by its real name; it does not prove onLoadInit or initialization
completion. Adding a new listener/callback would violate the requested existing-
callback boundary and is not done. A negative test explicitly rejects claiming
onLoadInit from this source. The earlier r07 plan's onLoadInit assumption is
corrected here, without rewriting that historical README.

The load request itself is left byte-for-byte as source text: called once with
original receiver/arguments and original handling of its result. We do not wrap
or manufacture that native result. Additional field reads are observations and
still require a same-input noninterference check. The callback exit marker means
normal return from the existing body; if its next-step call fails, silence is not
an exit. No catch/finally or new flow is inserted. HP is assigned exactly once;
all before/after snapshots preserve undefined values without filtering/filling.
Actor snapshots immediately follow their boundary marker in the common sequence;
the existing camera phase/ordinal is not relabeled as a global tick.

SOURCE_FIRST: every patch uses unique source anchors; missing/duplicate anchors
fail closed. Original calls, assignments, conditional control flow, placements,
MOVE/removal tags and timeline structure remain intact. Restoring only inserted
markers reconstructs the exact inherited loader and original frame8 text in tests.
Loaded identity, marker ordering and original/instrumented equivalence remain
unproved. No runtime mechanism or task completion is claimed.

## Build and tag audit

`build_observer.py` invokes the unchanged r07 builder into a fresh temporary path,
then imports only two patched main scripts. r07's yihu copy and 39 forwards are
retained without recompilation at the marker stage. `r07-build.json` pins the
inherited layer; build.json's inherited facility_sha256 names belong to r07,
while marker_builder_sha256 pins this r08 builder. The three compressed diffs
cover r03, r07 extension, and this marker layer. Compiler logs are retained.

Final original→copy differences:

- main: `root/547:12`, **`root/637:12`** (root frame8),
  `root/2012:39/sprite1813/1:12`, `root/2106:39/sprite1900/1:12`,
  `root/2198:39/sprite1991/1:12`.
- yihu: `root/19:39/sprite16/1:12`.
- Six DoAction payloads total. Every other tag/header/topology and73 other assets
  remain unchanged. Marker stage changes only root637 and loader sprite1900.

```sh
python3.11 evidence/oracle/native-fight-r08/build_observer.py \
  --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-m002-r08-recheck \
  --run-id m002-r08-offline-recheck
python3.11 -m unittest discover -s evidence/oracle/native-fight-r08 -v
python3.11 evidence/oracle/native-fight-r08/analyze.py
python3.11 evidence/oracle/native-fight-r08/analyze.py --require-oracle
```

The jar hash is receipt-pinned, output must be temporary and new, and original
hashes are verified. Both analysis commands exit1: no live capture, no onLoadInit
proof. This is an explicit refusal CLI, not a new permissive live acceptance
parser. Shared and historical gates are unchanged; r06 still refuses on incomplete
actor state. `checks.json` records actual tests and project-gate exits.

## What the next freshly authorized live must prove

Use a new tag and the exact movie-PID AX/CG/System Events path, with source/copy
hash checks for main and yihu, capture lock, foreground guards and owned cleanup.
No such run is authorized or executed by this offline package.

Preserve from boot: loader request selected key/URL/target; actual load-complete
callback target and sequence; yihu-sprite16 install target; chushi before/after
snapshots; every early timer boundary; physical input receipts and fight query
results. Verify target continuity and ordering from actual events. A load-complete
event or install marker alone cannot certify native initialization completion;
this missing obligation requires independently justified evidence or separately
approved instrumentation, not renaming a marker.

Prove whether HP is undefined before the original assignment, becomes assigned
there, and how that boundary orders relative to timer callbacks. Keep all earlier
undefined records and keep the existing rejection. A future acceptance design
must distinguish loading from initialized fight state with evidence, not select
the first convenient complete row. Positive fight queries still need downstream
consumption and tick binding. No local timer/camera ordinal is a global tick.

Still unproved: actual loaded identity, onLoadInit boundary, positive query and
consumption tick, exact initial-state/global clock, full random tape, exclusive
complete state trace, deterministic repeat and observer noninterference.
