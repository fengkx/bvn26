# s248 — Yulong display/camera completion boundary

User-selected s240 follow-up only, from master
`5c328c615e518280299ca63c85c03a65c4102879` on
`feat/s248-yulong-display-completion`. Same
`yulong__attack__neutral__ground__near` tape; no new cell, no replay of the other
six character dimensions. `production_admitted=false`; `native_parity_proven=false`.

## Retained failure diagnosis

Both untouched s240 raw captures still fail the original native validator with
`events beyond completion boundary`; neither receives a retroactive receipt.
`retained-failure-analysis.json` binds their archives by hash and records:

| s240 capture | First done (seq / display / tick) | First later root boundary | Additional done ticks |
| --- | --- | --- | --- |
| Main r02, 8,314 events | 8110 / 514 / 60 | 8147 / 515 / 61 | 61, 62 |
| First rejected attempt, 8,201 events | 8096 / 512 / 60 | 8133 / 513 / 61 | 61 |

Both first done markers follow a complete tick-60 `display_end`. The generated
bootstrap requests `fscommand("quit")` but leaves its root observer active;
the raw traces show additional root observations while player shutdown is
pending. This is capture-window re-entry, not missing final display data.
The existing validator correctly rejects it. No old suffix, sample, source
obligation or receipt hash is edited.

## Opt-in window and actual execution evidence

`--yulong-display-completion` accepts only the exact s240 case and enables
only display sampling (other sampling/residual flags are rejected). At `done`
it arms an analysis-only terminal flag. It **does not mute events at done**:
callbacks belonging to that terminal root period remain observable. On the
next root callback, before counters, inputs or samples advance, it emits
`capture_window_closed`, disables the probe root callback/emitter, and returns.
Default capture behavior and gameplay files are unchanged. The closure marker
uses the last admitted root counters and explicitly names its phase as
`before-next-root-increment`; it is not another tick-60 game sample.

Two normal-exit fresh captures produced valid receipts but quit before executing
the new guard. They are retained in `first-capture/` (r02, 7,943 events) and
`second-capture/` (r03, 8,096 events), each with 61 complete samples, 1,509 nodes,
and a full display gate exit 1. These successes alone do not prove the guard ran.

The final **controlled exit-delay run** (r05, top-level evidence) moves only the
probe's terminal quit request to the next root callback, after window closure.
It forces the pending-exit condition without changing the tape or observations
through tick 60. `build_yulong_display_hold.py` records this second-stage diff,
updated output hashes and its own source hash in build metadata before capture.
This is a declared harness control, not a claim that the original player always
has this delay.

- **7,981 events**, exactly one done: sequence **7944**, display **497**, tick **60**.
- **36 subsequent terminal-period events retained**, including key reads and
  existing callback markers.
- Last event **7981** is `capture_window_closed`; no tick 61 or second done appears.
- Native receipt **exit 0**; unchanged display structure collector **exit 0**:
  **61/61 samples, 1,509 nodes**.
- Full display/source gate **exit 1**: **166 obligations**, comprising **122
  missing source frames** and **44 unresolved runtime symbols**. Full lists remain
  in `source-gaps.json` and `display.json.gz`; dynamic masks/full camera ownership
  remain incomplete.

The normal and held-exit captures match all 122 actor-state payloads in the
planned 0–60 tick window. This bounded native/native comparison does not prove
Godot parity, timing equivalence, or full source ownership.

## Verification

`gates.json` records commands and exits, including revalidation of all three
new receipts. `negative-proof.json` removes a final-tick begin/camera/node/end
record: native sequence and display structure checks reject. Restoration brings
back 61 samples while the full gate still rejects all 166 obligations.
Tests also retain rejection of a duplicate done and any tick-61 suffix; the
original completion rule was not relaxed.

**159 focused sampling/probe/import tests pass**. New tests prove the bootstrap
addition leaves original statements intact, the controlled variant moves only
the terminal quit request, source/tape ambiguity rejects, the retained old trace
still fails, and the actual delayed run exercises closure after terminal callbacks.
Integrity, handoff and contracts checks are retained. No production runtime change.

## Reproduction and restoration

Use fresh paths/run IDs for new captures. The two normal attempts used:

```sh
python3 tools/probes/build_ai_reference.py \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s248-build-r02 --run-id s248-yulong-display-close-r02-20261029 \
  --frames 60 \
  --move-case evidence/sampling-upgrade/s240/yulong__attack__neutral__ground__near.json \
  --p1-character 石田 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 \
  --yulong-display-completion
# r03 uses its own build path and run ID.
python3 -m tools.probes.build_yulong_display_hold \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s248-build-r05 --run-id s248-yulong-display-held-r05-20261029
```

Each capture calls `capture_native_player.capture(build, trace, 180,
lock_timeout=45)` with authorized window activation, then `sampling_native.seal`.
The shared `/tmp/bvn-native-flash-capture.lock` is acquired/released by the
capture context; it was not deleted. Environments and measured capture times are
retained per attempt. r01 was an unrun development build; r04 failed during build
before any player launch. No new capture was rejected or trimmed.

Restore each build archive inside its original `/tmp/bvn-s248-build-rNN`, raw
trace to `/tmp/bvn-s248-capture-rNN/native.log`, and receipt to that capture
directory's `receipt.json` (NN=02,03,05). Top-level artifacts belong to r05.
Keep the original s240 case and this commit's source tools at receipt-recorded
paths. Do not rewrite hashes. Receipts retain static-loader limitations
(`runtime_fighter=null`), not independent runtime identity attestation.

`source-exports.json` reuses the five hash-verified source XMLs: extract
`s30/source-exports.tar.gz` and `s240/yulong-source-export.tar.gz` under
`/tmp/bvn-s248-source/`. No new source export or obligation exemption is introduced.

```sh
python3 -m tools.sampling_display \
  --case evidence/sampling-upgrade/s240/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s248-capture-r05/receipt.json \
  --exports evidence/sampling-upgrade/s248/source-exports.json \
  --output /tmp/s248-display.json
# Exit 1: 166 unresolved source/hierarchy obligations, not completion-boundary rejection.
python3 -m unittest tools.tests.test_yulong_display_completion
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

## Yulong residual queue status

The requested Yulong-specific follow-up queue now has evidence for both items:
s247 diagnoses s239's owner-context failure; s248 diagnoses the old s240
completion failure and provides a validated opt-in capture plus an exercised
closure control. This closes the **completion-boundary evidence gap for this
case**, not the general default harness or all Yulong acceptance gates.

The existing s241–s244 RGBA/AS/clip/call failures remain recorded and were not
reopened. s247 receiver ownership, display source binding, masks, full camera,
Godot parity and M0-02 remain unaccepted. No merge or deployment.
