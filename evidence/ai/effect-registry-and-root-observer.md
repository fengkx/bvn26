# Interleaved effect scripts and root observation

Status: r13 discrete-field segment passes; independent r14 still fails.
Full parity is not claimed. This supersedes the temporary effect phase in
[the preceding report](effect-random-and-repeat-contact.md).

## Native code probe

The [effect-order probe](../probes/schedule/effect-order/comparison.json) creates
an older callback, attaches an effect timeline, then creates a later callback.
The effect changes a flag on frames 2 and 4. FP32 executes the frame-4 resume
script between the later callback (which still reads paused) and the older
callback (which reads resumed). Frame scripts and enterFrame callbacks are
therefore not two globally separated batches for these instances.

```sh
python3 tools/probes/build_effect_attach_probe.py --probe effect_order --ffdec /tmp/bvn-ffdec-26.2.1/ffdec-cli.jar --output /tmp/bvn-effect-order-new
```

HitEffectRuntime now registers its per-frame execution in the existing shared
SourceCallbackRegistry at attachment, after the caller's existing instances.
New effects do not advance on their birth tick. Frame 1 remains deferred
until the attach caller completes; later frames retain their registration
relative to older and newer actor callbacks. Unloading and match shutdown
explicitly unregister the effect. The temporary universal early-effect phase
has been removed. No per-effect pause/resume phase table was introduced.

For r13 this removes the extra `beidax(true)` call on resume: hstm no longer
advances one tick early, landing no longer starts early, and all 35 frame-pair
differences disappear. The several-pixel displacement error disappears too.

## Root observer and capture termination

Seven remaining r13 state differences occurred on returning to stand. The
original root snapshot sees the new playhead but precedes the queued target
frame-1 script that resets action/hits/hstm. Native comparison had sampled
after that script. The original event ordering is retained in
`input-binary-r13/events.jsonl`; this is not inferred from animation playback.

Main exposes an optional read-only diagnostic observer after initial actor
frame batches and before deferred targets. Returning true ends that analysis
step at the observation point; production callers provide no observer and
always finish the frame. Combat replay only uses this cutoff when the final
root snapshot matches the unique original `done` event, whose source bootstrap
immediately calls `fscommand("quit")`. It does not discard an arbitrary tail
or edit the expected events.

The comparator is stronger now: frame pairs and state snapshots fail even
in boundary mode, and a completed segment must consume all expected source
boundaries, random records and clock records. Geometry remains reported
separately without tolerance or coordinate correction.

## Results

[r13 final report](effect-registry-validation/r13-root-final.json) matches all
1,166 post-checkpoint source boundaries, all 298 post-checkpoint random calls,
the complete clock tape, Ready, 897 frame-pair snapshots and 1,794 actor state
snapshots. There are no differing frame or discrete state records. The
[native log](effect-registry-validation/r13-root-final.log) completes without
script errors, including teardown.

This covers the original 600-fight-frame segment plus the partial post-load
intro prefix. It is not a boot-to-complete-match golden. P1 relative X still
differs by up to `3.0517578125e-5`; both actors retain initial single-precision
position offsets. Neither Y nor facing differs. Whole visual/audio behavior
and all source state fields are not covered by this report.

A fresh [r14 capture](input-binary-r14/summary.json) uses the same fixed player
inputs and configuration but an independent original random stream. Its
[native replay](effect-registry-validation/r14-first-difference.json) fails
at boundary 723: P2 expected frame 744/hstm=4, native frame 738/hstm=1. No random
or clock consumer failure precedes this difference. Native repeats the
received hit on Naruto's ranged attack.

The next source-backed investigation is projectile naming: Naruto's
`DefineSprite_260/frame_5/DoAction.as` writes `this._name="abcd"`, and the
placement callback at base frame 382 jumps to frame 5 on collision.
`getHitObj` then resolves the current named property, not the authored name
forever. Current projectile collision queries account for renamed targets,
but the fighter attack-contact path still queries authored hitbox names.
The rename's deferred frame-script timing must also be preserved; hiding the
old name immediately on goto could incorrectly suppress the initial hit.
This diagnosis is not yet an implemented or verified fix.

## Validation and remaining scope

[Five native tests](effect-registry-validation/checks.json) pass: effect/callback
interleaving, effect clock, Vs Com entry, KO flow and player lifecycle. The
interleaving regression checks both older and later observers around resume,
birth-tick exclusion and effect deregistration. Some test logs retain resource
exit warnings; certificate initialization warnings are environmental.

All prior tapes and failed reports remain intact. r14 is retained as a failing
case rather than selecting only the passing r13 stream. M5-03 remains pending:
projectile lifecycle, exact coordinate storage, further random paths, complete
match/round behavior, presentation and the Web browser matrix are still open.
