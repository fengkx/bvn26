"""Conservative source-interval joins, never OS synchronization or lifetime proof."""
from collections import Counter
import importlib.util
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r14_shape',HERE.parent/'native-fight-r14/analyze.py')
r14=importlib.util.module_from_spec(spec);spec.loader.exec_module(r14)


def validate_keys(markers,keys):
    r14.validate_consumer(markers)
    before=list(map(unquote,markers[0]['data'].split(',')))
    owner=before[3]
    if before[0].rsplit('/',1)[0]!=owner:raise ValueError('Helper/body source-parent mismatch')
    result=markers[1]['data'].split(',')[-1]
    expected=9
    values=[]
    for row in keys:
        f=list(map(unquote,row['data'].split(',')))
        if len(f)!=10 or f[0]!=f'yihu-decision-{expected}' or f[2] not in ('true','false') or f[3]!=owner or f[4:7]!=['false','false','false']:
            raise ValueError('Unrelated/malformed/AI/paused key query within predicate')
        value=f[2]=='true';values.append(value)
        if expected==9 and not value or expected>9 and value:expected=99
        else:expected+=1
    if not values or expected not in (13,99):raise ValueError('Incomplete short-circuit query sequence')
    actual=values[0] and not any(values[1:]) and len(values)==4
    if result!=str(actual).lower():raise ValueError('Full predicate disagrees with actual short-circuit returns')
    if any(not (markers[0]['seq']<k['seq']<markers[1]['seq']) for k in keys):raise ValueError('Key outside predicate interval')
    return dict(predicate_result=result,source_interval_validated=True,helper=before[0],serial=int(before[1]),site=before[2],body=owner)


def join(rows):
    installs={};serials={};seen=set();active=None;intervals=[];orphans=[]
    def finish(extra=None):
        nonlocal active
        if extra:active['errors'].append(extra)
        try:
            result=validate_keys(active['markers'],active['keys'])
            if active['errors']:raise ValueError('; '.join(active['errors']))
            active['validation']=result
            active['key_join_status']='validated-source-interval'
        except (ValueError,IndexError) as exc:
            active['refusal']=str(exc)
            active['key_join_status']='not-joined'
        intervals.append(active);active=None
    for row in rows:
        kind=row['kind']
        if kind=='decision-installed':
            fields=list(map(unquote,row['data'].split(',')))
            if len(fields)==2 and fields[0]=='yihu-sprite16':installs.setdefault(fields[1],[]).append(row['seq'])
            if active:active['errors'].append('Decision reinstallation inside interval')
        if kind=='consumer-query-before':
            if active:finish('Interleaved consumer invocation')
            f=list(map(unquote,row['data'].split(',')))
            errors=[]
            if len(f)!=6 or not f[1].isdigit():
                orphans.append(dict(event=row,reason='Malformed query identity'));continue
            key=tuple(f[:3]);number=int(f[1])
            if len(installs.get(f[0],[]))!=1:errors.append('Missing/reused helper installation path')
            if key in seen or number!=serials.get(f[0],0)+1:errors.append('Repeated/gapped local serial')
            seen.add(key);serials[f[0]]=number
            active=dict(markers=[row],keys=[],errors=errors,installation_sequences=list(installs.get(f[0],[])))
            continue
        if kind.startswith('consumer-'):
            if active is None:orphans.append(dict(event=row,reason='Marker without active query'));continue
            active['markers'].append(row)
            if kind=='consumer-predicate-result' and row['data'].split(',')[-1]=='false':finish()
            elif kind=='consumer-goto-after':finish()
            continue
        if active:
            if kind=='fight-key-return':active['keys'].append(row)
            else:active['errors'].append('Interleaved event: '+kind)
    if active:finish('Truncated consumer interval')
    valid=[x for x in intervals if 'validation' in x]
    return dict(intervals=intervals,orphans=orphans,interval_count=len(intervals),validated_count=len(valid),refused_count=len(intervals)-len(valid),
                validated_predicates=dict(Counter(x['validation']['predicate_result'] for x in valid)),
                validated_sites=dict(Counter(x['validation']['site'] for x in valid)),
                certified_global_tick=False,os_input_join_proven=False,oracle_accepted=False,
                limitation='Unique observed source interval only; helper path/local serial are not certified lifetime/global tick, and OS command brackets are not input synchronization')
