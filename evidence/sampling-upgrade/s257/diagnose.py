"""Recompute the bounded discriminator without promoting absence to VM return."""
import argparse
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
from tools.sampling_native import sha, validate_capture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def observations(lines):
    result = []
    for line in lines:
        p = line.split('|', 7)
        if len(p) != 8:
            raise ValueError('malformed raw event')
        if p[6] != 's257_witness':
            continue
        fields = p[7].split(',')
        if len(fields) != 6:
            raise ValueError('malformed witness')
        result.append(dict(zip(('type', 'token', 'before', 'control', 'post', 'observer_entry'), fields),
                           sequence=int(p[2]), tick=int(p[5]), display=int(p[4])))
    if [r['tick'] for r in result] != [10, 11, 12]:
        raise ValueError('missing/duplicate/out-of-order witness')
    if any(result[0][key] != 'undefined' for key in
           ('type', 'token', 'before', 'control', 'post', 'observer_entry')):
        raise ValueError('witness existed before selected call')
    for row in result[1:]:
        if (row['type'], row['token'], row['before'], row['control']) != (
                'object', 's257-chad-normal-goto', '1', '1'):
            raise ValueError('missing plain-object identity or positive pre-call control')
        if row['post'] not in ('0', '1') or row['observer_entry'] not in ('0', '1'):
            raise ValueError('invalid continuation observation')
    return result


def compiled_sites(callee, hooks):
    # Register-only writes precede any post-goto target lookup or observer guard.
    sequence = ('Push "砍1"\nPush 1\nPush register2\nPush "gotoAndPlay"\nCallMethod\nPop\n'
                'Push register5\nPush "post"\nPush 1\nSetMember\n'
                'Push register5\nPush register1\nPush "goto_after"\nPush 3\n'
                'Push register6\nPush undefined\nCallMethod')
    entry = ('4, "s257Witness" {\nPush register4\nPush "observerEntry"\nPush 1\nSetMember\n')
    control = ('Push register5\nPush register1\nPush "s257_control"\nPush 3\n'
               'Push register6\nPush undefined\nCallMethod')
    if sequence not in callee or entry not in hooks or control not in callee:
        raise ValueError('missing compiled independent witness/control/entry')
    if 'InitObject\nStoreRegister 5\nPop' not in callee:
        raise ValueError('witness is not a saved plain object')
    return {'post_goto': sequence, 'observer_entry': entry, 'positive_control': control,
            'executed_pc_trace': False}


def read_capture(slice_id):
    base = HERE.parent / slice_id
    metadata = json.loads((base / 'native-build.json').read_text())
    raw = gzip.decompress((base / 'native-capture.log.gz').read_bytes())
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / 'native.log'
        trace.write_bytes(raw)
        validate_capture(metadata['move_case'], metadata, trace)
    return metadata, raw.decode().splitlines()


def states(lines):
    return [(int(p[5]), p[7]) for line in lines
            if (p := line.split('|', 7))[6] == 'state' and int(p[5]) >= 0]


def diagnose():
    metadata, lines = read_capture('s257')
    previous, old_lines = read_capture('s252')
    if metadata['move_case'] != previous['move_case']:
        raise ValueError('changed tape')
    rows = observations(lines)
    lifecycle = collect_lifecycle(lines)
    calls = collect_calls(lines, metadata['callsite_specification'], retain_incomplete=True)
    actions = collect(lines, metadata['run_id'], 60, check_inventory(metadata))
    missing = calls['incomplete_invocations']
    assert len(missing) == 1 and missing[0]['observer_tick'] == 10
    assert missing[0]['instance'] == lifecycle['observations'][0]['saved_path']
    assert rows[0]['sequence'] < missing[0]['entry_sequence'] < lifecycle['observations'][2]['sequence'] < rows[1]['sequence']
    assert lifecycle['missing_boundaries'] == ['goto_after', 'callee_exit', 'caller_after']
    assert states(lines) == states(old_lines) and len(states(lines)) == 122

    provenance = json.loads((HERE / 'pcode-provenance.json').read_text())
    for path, expected in provenance['exports_sha256'].items():
        assert sha(HERE / path) == expected
    with tarfile.open(HERE / 'native-build.tar.gz') as archive:
        for path, expected in metadata['outputs_sha256'].items():
            assert hashlib.sha256(archive.extractfile(path).read()).hexdigest() == expected
        assert hashlib.sha256(archive.extractfile('instrumentation.diff').read()).hexdigest() == metadata['instrumentation_sha256']
        assert json.loads(archive.extractfile('build.json').read()) == metadata
    for path, expected in provenance['inputs_sha256'].items():
        assert metadata['outputs_sha256'][path] == expected
    for path, expected in metadata['sources_sha256'].items():
        assert sha(ROOT / path) == expected
    callee = gzip.decompress((HERE / 'pcode/chad' / (CALLEE.removesuffix('.as') + '.pcode.gz')).read_bytes()).decode().replace('\r\n', '\n')
    hooks = gzip.decompress((HERE / 'pcode/main/frame_1/DoAction.pcode.gz').read_bytes()).decode().replace('\r\n', '\n')
    sites = compiled_sites(callee, hooks)
    bundle = json.loads((ROOT / 'scripts/fighter/chad.json').read_text())
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
    frame, facts = 1, []
    for index, tag in enumerate(sprite.find('subTags')):
        if ((frame == 1 and tag.get('depth') == '31')
                or (frame == 13 and tag.get('type') == 'RemoveObject2Tag' and tag.get('depth') == '31')
                or (frame == 183 and tag.get('type') == 'FrameLabelTag')):
            facts.append({'frame': frame, 'tag_index': index, 'attributes': dict(tag.attrib)})
        if tag.get('type') == 'ShowFrameTag':
            frame += 1
    assert facts == boundaries['timeline_facts']
    return {'production_admitted': False, 'native_parity_proven': False,
            'exit_model_fix_proved': False, 'positive_post_goto_witness': any(r['post'] == '1' for r in rows[1:]),
            'events': len(lines), 'root_samples': len(actions['samples']), 'observations': rows,
            'actor_comparison': {'rows': 122, 'exact_tick_payload_equal_s252': True},
            'lifecycle': lifecycle, 'incomplete_invocations': missing,
            'call_counts': {'true': calls['true_count'], 'false': calls['false_count']},
            'full_as': {'unvisited': len(actions['unvisited']), 'uninstrumented': len(actions['uninstrumented'])},
            'boundary_window': lines[rows[0]['sequence'] - 1:rows[2]['sequence']],
            'compiled_sites': sites, 'source': {'handler_path': HANDLER, 'handler': sources[HANDLER],
                'callee_path': CALLEE, 'callee': body, 'timeline': boundaries},
            'next_discriminator': 'Executed-PC or VM stack observation across this exact goto CallMethod/Pop and following register5 SetMember, paired with a positive same-context continuation control. Do not infer return or abort from absent writes.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'diagnosis.json')
    args = parser.parse_args()
    args.output.write_text(json.dumps(diagnose(), indent=2, ensure_ascii=False) + '\n')
    print('S257_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
