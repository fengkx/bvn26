# Explicit helper source-initialization observation preparation

Base 37cac8dce9700ad900285fa3075d9a32ae4447ce. Offline only: two independent
SWF builds, no player launch/capture/debugger connection. All five flags remain
false; M0-02 pending. This does not repair historical r12/r13 or supply any native
initialization, lifetime, dispatcher-return, global-clock or visual proof.

## Source-bound scope

Locked scripts/main.json, DefineSprite_1900/frame_1/DoAction.as has loadfz(pr),
which resolves the selected fzurl and calls the existing MovieClipLoader once.
The same script already installs LO.onLoadComplete(target), which increments
loadStep and invokes the next loadSteps entry. It has **no onLoadInit callback**.
Locked scripts/fighter/fz/{woailuo,kon}.json frame_1/DoAction.as initializes inited,
attacking, coordinates and hit fields, executes stop(), then initializes gjl.
The new marker is appended after the final unchanged assignment, not after stop
alone. It witnesses reaching the source frame's normal end, not native dispatch
return or a new callback that we pretend existed.

New opt-in --helper-init-observer requires both --p1-helper woailuo and
--p2-helper kon (Chinese catalog IDs also accepted). Unknown or implicit pairs
fail before output creation. Original source strings at exactly three sites are
SHA256-pinned; changed/missing/duplicate anchors or incomplete installation fail.
Without this opt-in, prior builder behavior/schema is unchanged.

New event schema is stored in build.json.helper_init_observer:

| Event | Fields | Meaning |
| --- | --- | --- |
| helper_init_request | slot, selection, resolved_url, target | Immediately before original helper loadClip, which is still called once |
| helper_init_load_complete | slot, target, loaded_url | Entry to the existing onLoadComplete callback, only when its target equals the current p1fz/p2fz object |
| helper_init_frame_tail | slot, source_asset, target, loaded_url, frame, inited, attacking | End of the pinned helper's existing frame1 script; slot determined by current object equality |

No extra listener, onLoadInit handler, synthetic identity, stored target reference,
generation stamp, injected frame transition or key/random replacement is added
by this facility. The inherited diagnostic builder still auto-starts and injects
input: it is **not** certified clean or behavior-preserving. Additional Trace
work can affect timing; noninterference remains unproved. The full validator now
also refuses the new helper_init_observer intervention flag. Old helper_load
remains a request marker and is never interpreted as completion by this analyzer.

## Fail-closed interpretation

The offline analyzer requires the exact audited config, a single run ID,
contiguous event sequence and one Ready. For each slot it requires exactly one
request -> load-complete callback -> source-frame tail **before Ready**, exact
selection/asset/target/URL agreement, and actual frame1/inited=true/attacking=false.
Missing callbacks/tails, duplicate pre-Ready observations or reloads, wrong order,
foreign run, gaps, wrong asset/slot/URL and undefined state refuse. If real Flash
ordering or URL canonicalization differs, it refuses; no normalization or inferred
event fills the gap. Later events remain outside this initial-Ready claim.

A passing future chain may report source_frame_initialization_observed=true;
native_initialization_complete and all admission flags remain false. Object
comparison is at each observed instant, not a cross-event lifetime/generation
proof. No native completion has been observed in this offline slice. Both a
fresh receipt-matched capture and preservation review are still required before
using this facility on a player; no live follows automatically.

## Executed checks

- 20 Python unit tests pass (new observer/config/negative tests plus existing
  helper resolution and replay/log tests). Synthetic complete chains are labeled
  synthetic, never mixed into historical or real evidence.
- Five existing Ready-report regressions pass.
- FFDec independent build succeeds; compiler SHA256
  090ab695053ad94cba6408574c7d7eea20ec60b6ae789ee6056a23f45106762f.
  The compiler came from the retained r23 tool path. No Godot code changed and
  no Godot/player execution was necessary.
- Baseline explicit-helper build vs observer: after normalizing only temporary
  fixture directory literals for source comparison, exactly three changed source
  sites. Binary audit: main has two changed DoAction tags (loader plus fixture URL
  bootstrap), each helper one DoAction, both fighter SWFs identical. All tag paths
  preserved. Original-to-copy full probe audit also retains inherited changes:
  main12 tags (DoAction/DoInitAction), minren8 (DoAction/PlaceObject), yihu14
  (DoAction/PlaceObject), each helper1 DoAction. No claim that the whole probe is
  only three DoActions. See incremental-audit and tag-audit receipts.
- Original source hashes checked by builder; game/ and scripts/ unchanged.
- Historical r13 analyzer without new config exits1. Even supplying the audited
  config to its old events refuses missing initialization rather than backfilling.
- Full r12/r13 validation stays unknown/source_build_provenance_not_clean;
  all checks/provenance equal retained acceptance reports. Helpers and r12 strict
  decimal mismatch are unchanged. historical-checks.json pins the replay bytes.
- verify.py, check_handoff.py, git diff --check pass. Quota UNKNOWN.

## Reproduce offline

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tools.tests.test_helper_init_observer tools.tests.test_helper_source_resolution tools.tests.test_ai_continuous_replay tools.tests.test_godot_result
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/replay-ready-report -p 'test_*.py'
python3.11 tools/probes/build_ai_reference.py --ffdec /private/tmp/bvn-m0-observer-tools/ffdec/ffdec.jar --output /tmp/bvn-helper-init-offline-20261112 --run-id helper-init-offline-20261112 --frames 600 --p1-helper woailuo --p2-helper kon --helper-init-observer
python3.11 tools/probes/helper_init_observer.py --events evidence/ai/input-binary-r13/events.jsonl --build evidence/ai/input-binary-r13/build.json --output /tmp/bvn-helper-init-r13-refusal.json
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
git diff --check
```

Use a fresh output directory for rebuilding; the builder refuses existing paths.
The baseline command is identical except --helper-init-observer is absent and
output is /tmp/bvn-helper-init-baseline-20261112. Compare nested tag payloads with
retained native-fight-r03/build_observer.py tags(); no SWFs are committed here.
The analyzer CLI exits0 only for its narrow observed chain, otherwise1; neither
outcome admits the oracle. Full acceptance remains a separate refusing gate.
