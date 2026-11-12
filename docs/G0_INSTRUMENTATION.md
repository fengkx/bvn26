# G0 timing and offline browser workload

**G0 is NOT passed.** This is instrumentation preparation, not the optional
host-authority MVP. No admission/parity/oracle/tick/input/initialization proof flag
is changed. Weak-machine execution and a decision on the display budget remain
outstanding. No Flash, FDB, debugger or live reference capture is needed or allowed
by this workflow.

## Scope and source-first boundary

The builder copies `godot/` to a new external directory, then wraps existing void
methods in that copy. It never edits gameplay, frame scripts, placements, exits,
input rules, damage, timers, or the production renderer. Therefore the source-first
five-question mechanism gate has no new mechanism to approve. No native parity is
claimed. Early returns stay inside the original method, so the outer timing scope
always closes. Nested and recursive materialization uses exclusive time.

The diagnostic scene uses the existing render surface (including its sample-grid
resolve and dynamic viewports), one offline battle adapter, and no rollback
session, network state channel, host selection, guest presenter or Worker changes.
The adapter supplies the already-existing explicit source clock and event path;
its checkpoint object is configured but not saved per tick.

## Reproduce a fixed build

Use Godot **4.7.2 stable** and the matching single-thread Web release template.
Choose a new directory under the OS temporary directory, **not `/tmp`**, outside
the repository. Outputs/logs/caches are not source files. Export only into
`dist/web/`; do not deploy this diagnostic pack as the production game.

```sh
python3 tools/build_g0_workload.py --stage "$TMPDIR/bvn-g0-project"
python3 tools/bind_web_export_template.py \
  --preset "$TMPDIR/bvn-g0-project/export_presets.cfg" --template "$WEB_TEMPLATE"
"$GODOT_BIN" --headless --path "$TMPDIR/bvn-g0-project" --editor --import --quit
"$GODOT_BIN" --headless --path "$TMPDIR/bvn-g0-project" \
  --script res://g0/timing_smoke.gd
mkdir -p dist/web
"$GODOT_BIN" --headless --path "$TMPDIR/bvn-g0-project" \
  --export-release Web "$PWD/dist/web/index.html"
python3 tools/package_g0_workload.py --stage "$TMPDIR/bvn-g0-project" --web dist/web
python3 -m http.server 8077 --bind 127.0.0.1 --directory dist/web
```

Open the page locally, click Start, leave it visible, then Save raw report. Preserve
that pack and its artifact hashes for later weak-machine comparisons. Identity
records source HEAD, dirty state, hashes of staged source/content/settings/tape,
wrapper inventory, and final HTML/JS/PCK/WASM hashes. Do not compare reports from
different packs as a same-build machine comparison. Record machine model, OS,
power mode, browser full version, other load, and thermal conditions alongside it.

Fixed configuration: 600×400 logical/backing canvas, DPR 1 (other DPR refused),
HIGH quality, production sample grid, Compatibility, single-thread Web, 30 Hz,
seed 727, Naruto/Ichigo, Gaara/Matsumoto helpers, Karakura stage, PvP mode with
neutral scripted P2, HP 1000, time setting 60, AI setting 5 with both CPUs off,
volume 100% unmuted, synthetic initial energy 300 for each actor (one-time fixture precondition). No persisted gameplay settings or physical keyboard input
controls the battle. This is a single local player workload with an idle opponent,
not AI or a pair simulation.

The explicit source-clock envelope uses `tick * 33` ms, intro polling every 15 ticks,
and intro skip on ticks 30–89, matching the existing offline fixture convention.
It is a synthetic schedule, not a captured native timer trace or parity proof.

The frozen 900-tick synthetic tape includes movement, melee, ranged, summon and
special inputs. Ticks 1–164 are opening/warmup; 165–299 normal combat; 300–900
heavy-effect **candidates**. No health or energy is replenished during measurement; the declared initial energy permits a super without changing any move rule.
Raw action changes, energy, super-pause and helper attack activity accompany each tick.
A candidate label alone never proves heavy-effect coverage. If required effects
are absent, the weak-machine run is incomplete; fix/version the tape before
freezing a comparison, never relabel idle samples as heavy effects.

## Measurement meaning

- `advance_total_us`: the entire `_advance_fight` invocation, including early exits.
- `materialize_in_advance_us`: exclusive materialization work under that invocation;
  nested materializations are counted once.
- `simulation_excluding_materialize_us`: subtraction **within that same sample**.
  It is the remaining CPU wall duration, including other presentation work inside
  `_advance_fight`, not a claim that every remaining instruction is simulation.
- `exclusive_us`: disjoint instrumented categories. Script `_draw` scopes and
  materialization outside advancement remain separately observable.
- `render_setup_cpu_ms` and `viewport_cpu`: engine CPU counters for root, source,
  and all discovered nested viewports. `render_cpu_ms` sums those counters as
  documented by RenderingServer; zeros may mean unavailable on a backend.
  Counter frame alignment is not certified. Do not sum these with script draw
  time (possible overlap), or with another tick's percentile. Deferred deletion,
  audio and uninstrumented engine work are not presented as a complete guest cost.
- `display_spans_us`: raw materialize/draw intervals. The analyzer unions these
  with the same submission's pre/post-draw interval, producing
  `materialize_display_submit_wall_union_us`. Overlap/nesting is counted once,
  including all catch-up ticks belonging to that submission. This is a measured
  joint **wall** budget (including stalls), not complete CPU utilization or GPU
  time; it does not rely on delayed renderer counters.
- `submit_interval_wall_us`: pre-draw to post-draw **wall interval**, which may
  include driver waits. It is not GPU completion or time-to-photons.
- `raf_frames`: browser callback intervals, with >100 ms stalls marked; these are
  not proof of distinct physical frames. Long Tasks are recorded when supported,
  otherwise `UNKNOWN`. Draw calls, objects and video-memory counters are retained.
- GPU time is `UNKNOWN`: no reliable disjoint-safe GPU timer is joined to frames.
- Each input sample is assigned its consumed tick. At post-draw only the newest
  tick receives `input_to_submit_us`; earlier catch-up ticks are explicitly
  `superseded_before_submit`. Thus an unseen intermediate state is not credited
  with a display latency. The clock is Godot monotonic microseconds throughout.
  This is the **sampled-input** offline baseline, excluding OS event-to-sampling
  delay. State change is not causal action proof; no response, hit and visible
  action latency must not be inferred from consumption or submission.

The analyzer reports p50/p95/p99, maxima and sample counts separately by segment.
It rejects absent/all-zero advancement timing and validates the per-tick exclusive partition and never adds/subtracts independent
percentiles. Joint renderer/materialization CPU remains UNKNOWN until backend
counter alignment is qualified; raw tick-to-submit membership is retained for
that work. Visibility/resize invalidations invalidate a controlled comparison.
Instrumentation itself adds overhead; retain this same build on both machines.

```sh
python3 tools/analyze_g0_workload.py /path/to/g0-not-a-pass.json
python3 tools/tests/test_g0_workload.py
```

For a development-only browser dry run, launch a dedicated headless Chromium with
an isolated profile and debugging port (never attach to a user's normal profile):

```sh
node tools/test_g0_browser.mjs http://127.0.0.1:9333 \
  http://127.0.0.1:8077 "$TMPDIR/g0-not-a-pass.json"
```

The runner fails on browser exceptions/console errors or a missing report and
labels the artifact `headless Chromium on development machine; not-a-pass`.
A headless Godot timer smoke test cannot validate browser pacing or rendering.

Rendering counter definitions follow the
[Godot RenderingServer reference](https://docs.godotengine.org/en/stable/classes/class_renderingserver.html#class-renderingserver-method-viewport-get-measured-render-time-cpu).
They do not turn CPU submission into GPU completion evidence.

Development validation is recorded in the [dry-run evidence](../evidence/performance/g0-instrumentation/README.md).
