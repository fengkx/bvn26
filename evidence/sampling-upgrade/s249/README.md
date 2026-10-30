# s249 — Ranked #1: default display completion window

Baseline `69319713`, branch `feat/s249-gap-fix-priority`. The
[priority list](../next-fix-priority.md) was written before this implementation.
One shared mechanism only: ordinary standalone `--sampling-display` now uses
s248's proven terminal-period closure, independent of fighter selection.
`production_admitted=false`; `native_parity_proven=false`.

## Change and limits

The builder arms the existing observer at done, retains callbacks belonging to
that terminal root period, then closes before the next root increment. It uses
the existing instrumenter and historical `aiYulongDisplayComplete` private name
for compatibility with the retained s248 control. Metadata explicitly records
`display_completion_window`; the historical Yulong case-restricted opt-in still
works. Mixed sampling modes keep their previous behavior. The native validator,
original SWFs, source tapes, rejected captures, and full gates are unchanged.
No gameplay/Godot changes. No automatic receipt repair or suffix trimming.

Evidence supports four display receipt prerequisites (s219/s226/s233/s240),
not four green dimension gates. This cut freshly checks **Yijiao only**, using
the unchanged s231/s233 attack tape. s248 supplies the prior Yulong proof;
Sasuke and Ichigo have not been recaptured here.

## Observed gates

| Fresh run | Native receipt | Display structure | Full display/source gate |
| --- | --- | --- | --- |
| Normal exit, 8,408 events | 0 | 0: 61 samples / 1,533 nodes | 1: 169 obligations |
| Declared held exit, 8,577 events | 0 | 0: 61 samples / 1,533 nodes | 1: 169 obligations |

Normal exit stops at done without exercising the guard. The held-exit control
moves only the probe quit request to the next root callback (after closure),
as in s248. Its done is event 8542, followed by **34 retained terminal-period
callbacks**, then `capture_window_closed` at event 8577. No tick61 or second done.
This is an explicit control, not a claim about ordinary shutdown latency.
The wrapper's source hash and second-stage diff are bound in build metadata.
Top-level artifacts are the held run; `normal-exit/` retains the normal run.
`gates.json` records exact display commands and exits; reports retain every
source obligation. `observations.json` records event/sample counts.

Focused tests include the untouched s233 rejection, missing final display end,
and an injected later-root event. These continue to reject. Tests also verify
that the new non-Yulong capture did not use the Yulong opt-in and retained
terminal callbacks. 163 focused tests pass (exit 0); verify, handoff and contracts each exit 0.
See `tests.log` and `project-checks.json`. The initial test run used the wrong
case key (`case_id` instead of `id`); its failure log is retained, then corrected.

## Reproduction

Use the same case at `../s231/yijiao__attack__neutral__ground__near.json`.
Build a fresh normal run with:

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s249-build --run-id s249-yijiao-display --frames 60 \
  --move-case evidence/sampling-upgrade/s231/yijiao__attack__neutral__ground__near.json \
  --p1-character 一角 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-display
PYTHONPATH=. python3 evidence/sampling-upgrade/s249/build_held_display.py \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s249-held-build --run-id s249-yijiao-display-held
```

For each build, `capture_native_player.capture(build, trace, 180,
lock_timeout=45)` uses `/tmp/bvn-native-flash-capture.lock`, then
`sampling_native.seal(case, build, trace, capture_native_player.BINARY, receipt)`.
Player: `/Volumes/Flash Player/Flash Player.app`. Both captures acquired and
released the shared lock; no lock was removed. Use fresh paths/IDs for retries.
For retained receipt revalidation restore build tar contents to the exact
`/tmp/bvn-s249[-held]-build` path and raw gzip to
`/tmp/bvn-s249[-held]-capture/native.log`; restore receipts alongside them.
Source XML hashes/paths remain those in s233: restore common XML from s30's
source archive and Yijiao XML from s233's `yijiao-source-export.tar.gz` as needed.
Run commands in `gates.json` at this revision. No new XML export is claimed.

## Residuals

The 169 source/hierarchy obligations, masks/camera ownership, all non-display
completion failures and strict RGBA/AS failures remain. No s241–s244 reopening.
The Yulong-specific residual evidence queue remains delivered, while the shared
fix queue begins here. M0-02 remains pending; this is not native/Godot parity.
