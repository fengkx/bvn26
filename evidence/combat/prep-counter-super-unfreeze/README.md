# Preparation interruption anti-deadlock deviation

This change intentionally deviates from Flash, extending the Gin-class
`_clear_interrupted_super_preparation` fix. Flash still freezes in the retained
Orochimaru and Pain `prep-counter-super` recordings. Godot must recover and
continue the counter super, rather than match that freeze. This is not a port
parity correction or full character acceptance.

The baseline is `cdac5d96` (PR #36), whose runtime is the audited `2d3336bf`.
All original fixtures, Flash traces, source builds and historical native traces
remain unchanged in `evidence/characters/_audit-sample-2026-10-19/`.

## Cause and scope

At the tick-16 receiver callback, the fighter has reached the preparation
frame but its DoAction is still queued. `bs` is still zero, so the previous
helper returns. The queued preparation subsequently writes `bs = 1` even
though the receiver has already redirected the playhead into hurt. Ichigo's
later `bsw` sees that orphaned lock and cannot release the shared pause.

The helper now marks only the current queued invocation with a compiled
`bs = 1` write, when a real unguarded hit arrives outside an active super or
user pause. After that invocation executes, the same helper clears the lock.
The entry's execution serial distinguishes it from earlier queued scripts;
the marker lives in the existing checkpointed pending-frame dictionary.
The second call does not mark further entries. Energy and other source writes
still execute, and the existing active-super, user-pause and guard checks stay
in force. There are no fighter-specific runtime conditions, timers or frame
order changes.

## Source-first answers and SOP A–E

1. **Scripts, including empty frames.** The complete frame/placement review is
   [source-review.json](../../characters/_audit-sample-2026-10-19/source-review.json).
   `scripts/fighter/orochimaru.json`, `DefineSprite_541`: preparation 534–540
   has no DoAction at 534 or 536–539; 535 writes `动作 = 3; bs = 1; ql -= 100`;
   540 calls `bsd` and `showFace`. `scripts/fighter/pain.json`,
   `DefineSprite_573`: 600 and 602 have no DoAction, 601 writes `bs = 1`,
   subtracts 100 energy and sets action 3; 603 calls `bsd` and `showFace`.
   Their common frame-1 `beidax` returns immediately while root `zhanting` is
   true. `scripts/main.json`, `frame_8/DoAction.as`, `bsw` clears the caster's
   `bs` but stops it and returns if the opponent still has `bs == 1`.
2. **Placement lifetime.** Orochimaru's preparation retains the `bdmn`
   instance placed at frame 30 until removal at 539. Pain retains the
   receiver placed at 427 until removal at 602. Their receiver callbacks
   therefore run during preparation; these are not new instances that should
   wait a frame. Jiraiya `DefineSprite_342` removes `bdmn` at super entry 608
   (also at its other super entries): its preparation test remains a protected
   negative. No placement, MOVE, matrix or receiver geometry is changed.
3. **Exit.** A real `beida` hit redirects to the packet's hurt label before
   the queued preparation DoAction runs. Orochimaru's hurt scripts are
   1102 `play`, 1103 `onBeHit`, 1104 `beidax` placement, 1105 receiver placement,
   1108 `stop`, 1112 explicit standing goto. Pain uses 1181, 1182, 1183, 1184,
   1187 and 1191 respectively; intervening frames have no DoAction.
   No label-end standing rule is introduced. Ichigo's authored frame 463
   `bsw` is the release point, not a newly invented timeout.
4. **Invariants versus deviation.** Preserve the tick-16 interruption,
   100-energy preparation cost, tick-17 HP 960 and the active-super/guard/pause
   protections. The explicitly authorized new invariant is recovery from the
   orphaned lock, not fidelity to Flash's deadlock. The targeted smoke covers
   a queued preparation write as well as the previous direct-call conditions.
5. **Original same-input observation.** The two PR #36 Flash traces contain
   482 actor states each, with both actors paused for ticks 25–240 (216 each).
   Original terminal frames are 1108/1187 and Ichigo 463. These traces are
   preserved and hash-checked by the new runner; no new Flash capture is
   claimed. SOP A–D common receive chain, strength fields, presentation and
   placement evidence remain those of the audit; only orphan-lock cleanup
   changes. SOP E now explicitly expects Godot recovery for these two cases.

## Verification

Run after the normal Godot resource import:

```sh
python3 tools/test_prep_counter_super.py --godot /absolute/path/to/Godot \
  --output /tmp/prep-counter-super-check
```

The runner checks the unchanged 40 audit fixtures and Flash hashes, compares
all 14 fields exactly for the other 38 cases, and explicitly distinguishes
the two recovery deviations. Before tick 38 those two must still match every
field; the first divergence must be only pause release at tick 38. Recovery
also requires a real counter-super hit, no pause from ticks 100–240, standing
at tick 240, and changing idle frames late in the run. Four extra Godot-only
sequences exchange player slots or delay the counter input by one tick; they
are recovery coverage, not new Flash parity evidence.

[results.json](results.json) records 38 exact matches, two intentional deviations
and four additional recovery sequences (44 × 482 = 21,208 actor states).
Both original failing cases first release pause at tick 38, have their last
ordinary hit-pause observation at tick 57, and finish at HP 660 versus 1000
with both actors standing and unpaused. The one-tick-later cases last pause
at tick 59. All 13 Jiraiya cases remain exact.

[checks.json](checks.json) records eight passing Godot checks, including Gin,
Orochimaru, Jiraiya and Pain rollback checks, 313 passing Python tests with two
skips, and both 602-state shared-mode comparisons. The accepted 44-case replay
took 182.728 seconds; measured work through evidence packaging was 601 seconds.
Compressed native traces are in `traces/`; only the four added input fixtures
are copied into `cases/`. Run `python3 evidence/combat/prep-counter-super-unfreeze/recheck.py`
to verify the retained hashes and comparisons without starting an engine. Full
browser, audiovisual, AI and exhaustive cancellation acceptance remain pending.
No merge or Worker/Vercel deployment is part of this change.
