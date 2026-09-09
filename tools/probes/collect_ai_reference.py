"""Validate and retain a completed instrumented original-game capture."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def decode_number(value: str) -> float:
    if not value.startswith('f:'):
        return float(value)
    _, sign, exponent, high, low = value.split(':')
    sign, exponent, high, low = map(int, (sign, exponent, high, low))
    if sign not in (-1, 1) or not -1074 <= exponent <= 1023 or not 0 <= low < 2 ** 26:
        raise ValueError('Invalid binary source number')
    if high == 0:
        if low != 0 or exponent != 0:
            raise ValueError('Invalid binary zero')
    elif not 2 ** 26 <= high < 2 ** 27:
        raise ValueError('Invalid binary significand')
    return sign * math.ldexp(high * 2 ** 26 + low, exponent - 52)


def verify_key_reads(events: list[dict], build: dict) -> dict:
    if build.get('input_injection') != 'body_kis_alias_with_per_read_trace':
        return {'status': 'unverified_legacy_global_Key_isDown_override'}
    bindings = [event for event in events if event['kind'] == 'input_bindings']
    if len(bindings) != 1:
        raise ValueError('Input alias capture requires unique key bindings')
    codes = dict(pair.split('=') for pair in bindings[0]['value'].split(','))
    if not codes or any(not code.isdecimal() for code in codes.values()):
        raise ValueError('Input key bindings are not numeric')
    held = set()
    reads = 0
    pressed = Counter()
    for event in events:
        if event['kind'] == 'input_next_display':
            states = dict(pair.split('=') for pair in event['value'].split(','))
            if set(states) != set(codes) or any(value not in ('true', 'false', 'undefined') for value in states.values()):
                raise ValueError('Input intent does not match recorded bindings')
            held = {codes[key] for key, value in states.items() if value == 'true'}
        elif event['kind'] == 'key_read':
            receiver, code, value = event['value'].split(',')
            if value not in ('true', 'false') or (value == 'true') != (code in held):
                raise ValueError('Source key read does not match the current input intent')
            reads += 1
            if value == 'true':
                pressed[receiver + ':' + code] += 1
    if reads == 0:
        raise ValueError('Input alias capture has no source key reads')
    return {'status': 'source_key_reads_match_recorded_intent', 'bindings': codes,
            'reads': reads, 'pressed_reads': dict(pressed)}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',required=True,type=Path)
    parser.add_argument('--capture',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--retain-post-done-frames', action='store_true',
                        help='Preserve asynchronous quit tail separately; compare only through the first done')
    args=parser.parse_args()
    build=json.loads((args.build/'build.json').read_text())
    prefix='AIREF|'+build['run_id']+'|'
    # Flash's own localized warnings may use a legacy encoding. AIREF trace
    # records are retained separately; replacement is forbidden within them.
    events=[]
    for line in args.capture.read_bytes().splitlines():
        if not line.startswith(prefix.encode()):continue
        columns=line.decode('utf-8').split('|',7)
        events.append({'run_id':columns[1],'sequence':int(columns[2]),'time_ms':int(columns[3]),
                       'display_tick':int(columns[4]),'fight_tick':int(columns[5]),
                       'kind':columns[6],'value':columns[7]})
    if not events or [e['sequence'] for e in events]!=list(range(1,len(events)+1)):
        raise ValueError('Capture is missing events or mixes repeated runs')
    completed=[i for i,e in enumerate(events) if e['kind']=='done']
    if not completed or (len(completed)!=1 and not args.retain_post_done_frames) or events[completed[0]]['fight_tick']!=build['frames_after_ready']:
        raise ValueError('Capture did not complete the requested fight interval')
    if sum(e['kind']=='ready' for e in events)!=1 or any(e['kind']=='timeout' for e in events):
        raise ValueError('Capture has no unique ready event or timed out')
    if any(b['time_ms']<a['time_ms'] for a,b in zip(events,events[1:])):
        raise ValueError('Non-monotonic event clock')
    boundary=completed[0]
    trailing=events[boundary+1:]
    if args.retain_post_done_frames:
        terminal = events[boundary]
        previous_tick = terminal['display_tick']
        for event in trailing:
            delta = event['display_tick'] - terminal['display_tick']
            if delta < 0 or event['display_tick'] < previous_tick or event['fight_tick'] != terminal['fight_tick'] + delta:
                raise ValueError('Post-done tail has inconsistent display/fight ticks')
            previous_tick = event['display_tick']
        done_ticks = [events[index]['display_tick'] for index in completed]
        if len(done_ticks) != len(set(done_ticks)):
            raise ValueError('Duplicate completion within one display tick')
    if not args.retain_post_done_frames and any(e['display_tick']!=events[boundary]['display_tick'] or
           e['fight_tick']!=events[boundary]['fight_tick'] for e in trailing):
        raise ValueError('Display continued after the requested terminal snapshot')
    events=events[:boundary+1]
    input_delivery = verify_key_reads(events, build)
    args.output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(args.build/'build.json',args.output/'build.json')
    shutil.copyfile(args.build/'instrumentation.diff',args.output/'instrumentation.diff')
    with (args.output/'events.jsonl').open('w') as stream:
        for e in events:stream.write(json.dumps(e,ensure_ascii=False,separators=(',',':'))+'\n')
    if trailing:
        with (args.output/'post-done-events.jsonl').open('w') as stream:
            for e in trailing:stream.write(json.dumps(e,ensure_ascii=False,separators=(',',':'))+'\n')
    counts=Counter(e['kind'] for e in events)
    samples=[e for e in events if e['kind']=='sample']
    ready=next(e for e in events if e['kind']=='ready')
    init=[e for e in events if e['kind']=='initCtrl']
    rng=[]
    for e in events:
        if e['kind']!='random':continue
        first,value=e['value'].rsplit(',',1)
        index,site=first.split(',',1)
        rng.append({'index':int(index),'site':site,'value':decode_number(value),'sequence':e['sequence'],'time_ms':e['time_ms']})
    if [r['index'] for r in rng]!=list(range(1,len(rng)+1)):
        raise ValueError('Random draw index is not contiguous')
    (args.output/'random-tape.json').write_text(json.dumps(rng,ensure_ascii=False,indent=2)+'\n')
    clock = []
    for event in events:
        if event['kind'] != 'clock':
            continue
        index, site, value = event['value'].split(',')
        clock.append({'index': int(index), 'site': site, 'value': int(value),
                      'sequence': event['sequence'], 'time_ms': event['time_ms']})
    if [record['index'] for record in clock] != list(range(1, len(clock) + 1)):
        raise ValueError('Clock read index is not contiguous')
    if any(record['value'] < 0 for record in clock) or any(a['value'] > b['value'] for a, b in zip(clock, clock[1:])):
        raise ValueError('Clock values are negative or backwards')
    (args.output/'clock-tape.json').write_text(json.dumps(clock, ensure_ascii=False, indent=2)+'\n')
    report={'status':'original_capture_completed_not_port_parity','run_id':build['run_id'],
            'input_delivery': input_delivery,
            'events':len(events),'post_done_events':len(trailing),'counts':dict(counts),'frames_after_ready':events[-1]['fight_tick'],
            'termination_policy':'first_done_with_retained_async_tail' if args.retain_post_done_frames else 'unique_done_same_frame_tail',
            'ready':ready,'init_events':init,'first_sample':samples[0],
            'samples_before_ready':sum(e['sequence']<ready['sequence'] for e in samples),
            'sample_intervals_ms':dict(Counter(str(b['time_ms']-a['time_ms']) for a,b in zip(samples,samples[1:]))),
            'last_states':[e for e in events if e['kind']=='state'][-2:],
            'raw_capture_sha256':sha(args.capture),
            'retained_sha256':{p.name:sha(p) for p in args.output.iterdir()},
            'limits':['Trace instrumentation adds execution overhead.',
                      'Math.random capture covers selected bundles; random(n) is not intercepted.',
                      'Full per-read sensing is not logged; body DoAction boundaries require the body_boundaries build option.',
                      'No Godot fight replay has been compared with this capture.']}
    (args.output/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','events','counts','samples_before_ready','sample_intervals_ms')}))


if __name__=='__main__':main()
