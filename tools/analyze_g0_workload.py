"""Summarize paired G0 raw samples, without certifying a G0 pass."""
import argparse
import json
import math
from pathlib import Path


def stats(values):
    values = sorted(values)
    if not values: return {"n": 0, "status": "UNKNOWN"}
    return {"n": len(values), **{f"p{q}": values[max(0, math.ceil(len(values)*q/100)-1)] for q in (50, 95, 99)}, "max": values[-1]}


def union_duration(spans):
    total, end = 0, None
    for start, stop in sorted(spans):
        if stop < start: raise ValueError('Reversed timing span')
        total += max(0, stop - max(start, end if end is not None else start))
        end = max(stop, end if end is not None else stop)
    return total


def display_union(row):
    spans = row['display_spans_us'] + [
        span for tick in row['ticks'] for span in tick['display_spans_us']]
    return union_duration(spans + [[row['submit_start_us'], row['submit_us']]])


def analyze(report):
    samples = report['samples']
    ticks = [tick for row in samples for tick in row['ticks']]
    if [tick['tick'] for tick in ticks] != list(range(1, 901)):
        raise ValueError('Missing, duplicated or reordered workload ticks')
    if not any(x['advance_total_us'] > 0 for x in ticks):
        raise ValueError('Instrumentation absent: all advancement timings are zero')
    for row in samples:
        for tick in row['ticks']:
            is_latest = tick['tick'] == row['latest_tick']
            expected_latency = row['submit_us'] - tick['input_sample_us'] if is_latest else None
            if tick['input_to_submit_us'] != expected_latency:
                raise ValueError('Latency credits a superseded or unrelated state')
            if tick['display_status'] != ('submitted' if is_latest else 'superseded_before_submit'):
                raise ValueError('Invalid submit membership')
    for tick in ticks:
        if tick['advance_total_us'] != tick['materialize_in_advance_us'] + tick['simulation_excluding_materialize_us']:
            raise ValueError('Broken per-sample exclusive partition')
        if tick['simulation_excluding_materialize_us'] < 0: raise ValueError('Negative exclusive time')
    segments = {}
    for segment in ('warmup', 'normal', 'heavy_candidate', 'observed_heavy_effect'):
        selected = [x for x in ticks if (x['super_active'] or x['helper_visible'] or '必杀' in x['action_after'])] if segment == 'observed_heavy_effect' else [x for x in ticks if x['segment'] == segment]
        segments[segment] = {field: stats([x[field] for x in selected if x.get(field) is not None])
                             for field in ('advance_total_us', 'materialize_in_advance_us', 'simulation_excluding_materialize_us', 'input_to_submit_us')}
        selected_ids = {x['tick'] for x in selected}
        submits = [row for row in samples if row['latest_tick'] in selected_ids]
        segments[segment]['render_cpu_ms'] = stats([row['render_cpu_ms'] for row in submits])
        segments[segment]['materialize_display_submit_wall_union_us'] = stats([display_union(row) for row in submits])
        segments[segment]['observed_super_ticks'] = sum(x['super_active'] for x in selected)
        segments[segment]['helper_visible_ticks'] = sum(x['helper_visible'] for x in selected)
        segments[segment]['superseded_ticks'] = sum(x['display_status'] != 'submitted' for x in selected)
    # Renderer counters may refer to a previous frame on some backends. Preserve
    # them as separate distributions; never add them to unrelated tick percentiles.
    return {'g0_passed': False, 'validity': 'not-a-pass', 'segments': segments,
            'render_cpu_ms': stats([x['render_cpu_ms'] for x in samples]),
            'materialize_display_submit_wall_union_us': stats([display_union(row) for row in samples]),
            'submit_interval_wall_us': stats([x['submit_interval_wall_us'] for x in samples]),
            'display_draw_exclusive_us': stats([x['display_script_exclusive_us'].get('draw', 0) for x in samples]),
            'raf_interval_ms': stats([x['interval_ms'] for x in report.get('raf_frames', [])]),
            'long_stalls_over_100ms': sum(x['interval_ms'] > 100 for x in report.get('raf_frames', [])),
            'gpu_time_ms': 'UNKNOWN', 'invalidations': report.get('invalidations', ['browser_not_measured']),
            'joint_materialize_render_cpu': 'UNKNOWN: backend renderer counter alignment not certified; do not add independent p95s'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(json.loads(args.report.read_text())), indent=2))
