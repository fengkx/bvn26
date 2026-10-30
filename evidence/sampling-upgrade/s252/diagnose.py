"""Recompute the bounded call-boundary diagnosis; never infer a VM return."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile
import tempfile
import xml.etree.ElementTree as ET

from tools.probes.chad_lifecycle_observer import CALLEE, CALLEE_SHA256, HANDLER
from tools.sampling_callsite import collect_calls
from tools.sampling_chad_lifecycle import collect_lifecycle
from tools.sampling_doaction import check_inventory, collect
from tools.sampling_k1atm_provenance import collect_provenance
from tools.sampling_native import sha, validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read_capture(slice_id):
    base = HERE.parent / slice_id
    metadata = json.loads((base / 'native-build.json').read_text())
    raw = gzip.decompress((base / 'native-capture.log.gz').read_bytes())
    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(metadata['move_case'], metadata, trace)
    return metadata, raw.decode().splitlines()


def fight_states(lines):
    return [(int(p[5]), p[7]) for line in lines
            if (p := line.split('|', 7))[6] == 'state' and int(p[5]) >= 0]


def diagnose():
    results = []
    states = []
    for slice_id in ('s76', 's245', 's252'):
        metadata, lines = read_capture(slice_id)
        records = check_inventory(metadata)
        actions = collect(lines, metadata['run_id'], 60, records)
        calls = collect_calls(lines, metadata['callsite_specification'], retain_incomplete=True)
        missing = calls['incomplete_invocations']
        assert len(missing) == 1 and missing[0]['observer_tick'] == 10
        assert [p['phase'] for p in missing[0]['phases']] == ['predicate_before', 'true', 'call_before']
        lifecycle = collect_lifecycle(lines) if slice_id != 's76' else None
        if lifecycle:
            assert lifecycle['missing_boundaries'] == ['goto_after', 'callee_exit', 'caller_after']
            before, entry, goto, root = lifecycle['observations']
            assert missing[0]['instance'] == before['saved_path']
            assert missing[0]['phases'][-1]['sequence'] < before['sequence'] < entry['sequence'] < goto['sequence'] < root['sequence']
            assert all(row['same_occupant'] == 'true' for row in (before, entry, goto))
            assert root['same_occupant'] == 'false' and root['occupant'] == 'undefined'
            assert root['parent_frame'] == '183' and root['saved_parent'] == 'undefined'
        start = missing[0]['entry_sequence']
        end = lifecycle['observations'][-1]['sequence'] if lifecycle else start + 30
        results.append({'slice': slice_id, 'raw_sha256': sha(HERE.parent / slice_id / 'native-capture.log.gz'),
                        'event_count': len(lines), 'root_samples': len(actions['samples']),
                        'true_count': calls['true_count'], 'false_count': calls['false_count'],
                        'incomplete_invocations': missing, 'lifecycle': lifecycle,
                        'unvisited': len(actions['unvisited']), 'uninstrumented': len(actions['uninstrumented']),
                        'boundary_window': lines[start - 1:end], 'raw_validation_exit': 0})
        states.append(fight_states(lines))
    assert len(states[0]) == 122 and states[0] == states[1] == states[2]

    manifest = json.loads((ROOT / 'manifest.json').read_text())
    bundle_path = ROOT / 'scripts/fighter/chad.json'
    assert sha(bundle_path) == manifest['file_sha256']['scripts/fighter/chad.json']
    bundle = json.loads(bundle_path.read_text())
    sources = {s['path']: s['source'] for s in bundle['scripts']}
    assert hashlib.sha256(sources[CALLEE].replace('\r\n', '\n').encode()).hexdigest() == CALLEE_SHA256
    body = re.search(r'function doAllAction\(special\).*?^}', sources[CALLEE], re.M | re.S)[0]
    assert not re.search(r'\breturn\b', body)
    boundaries = json.loads((HERE.parent / 's245/source-boundaries.json').read_text())
    assert sha(ROOT / boundaries['source_swf']) == boundaries['source_sha256']
    with tarfile.open(ROOT / boundaries['xml_archive']) as archive:
        xml = archive.extractfile('fighter-chad.xml').read()
    assert hashlib.sha256(xml).hexdigest() == boundaries['xml_sha256']
    sprite = next(n for n in ET.fromstring(xml).iter('item')
                  if n.get('type') == 'DefineSpriteTag' and n.get('spriteId') == '607')
    frame = 1
    facts = []
    for index, tag in enumerate(sprite.find('subTags')):
        if ((frame == 1 and tag.get('depth') == '31')
                or (frame == 13 and tag.get('type') == 'RemoveObject2Tag' and tag.get('depth') == '31')
                or (frame == 183 and tag.get('type') == 'FrameLabelTag')):
            facts.append({'frame': frame, 'tag_index': index, 'attributes': dict(tag.attrib)})
        if tag.get('type') == 'ShowFrameTag':
            frame += 1
    assert facts == boundaries['timeline_facts']
    pcode = {}
    for source in (CALLEE, HANDLER):
        path = HERE / 'pcode' / (source.removesuffix('.as') + '.pcode.gz')
        pcode[source] = gzip.decompress(path.read_bytes()).decode().replace('\r\n', '\n')
    # This proves emitted sites, not that the player executes them after removal.
    sequence = ('Push "砍1"\nPush 1\nPush register2\nPush "gotoAndPlay"\nCallMethod\nPop\n'
                'Push register1\nPush "goto_after"\nPush 2\nPush register3\nPush "bvnChadObserve"\nCallMethod')
    assert sequence in pcode[CALLEE]
    assert 'Push "doAllAction"\nCallFunction\nPop\nPush "this"\nGetVariable\nPush "caller_after"' in pcode[HANDLER]
    _, yulong_lines = read_capture('s247')
    yulong = collect_provenance(yulong_lines)
    assert yulong['source_list_failures'] == [
        {'tick': tick, 'failed_predicates': ['target == undefined']} for tick in (16, 17, 18)]
    return {'production_admitted': False, 'native_parity_proven': False,
            'exit_model_fix_proved': False, 'new_native_capture': True,
            'fight_states_equal': True, 'fight_state_count': 122, 'captures': results,
            'source': {'bundle_sha256': sha(bundle_path), 'handler_path': HANDLER,
                       'handler': sources[HANDLER], 'callee_path': CALLEE, 'callee': body,
                       'timeline': boundaries},
            'compiled_sites_present': True, 'compiled_sites_execute_after_removal_proved': False,
            'separate_s247_context_failures': yulong['source_list_failures']}


if __name__ == '__main__':
    payload = (json.dumps(diagnose(), indent=2, ensure_ascii=False) + '\n').encode()
    (HERE / 'diagnosis.json.gz').write_bytes(gzip.compress(payload, mtime=0))
