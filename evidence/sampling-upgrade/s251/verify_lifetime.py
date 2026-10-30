"""Recompute the bounded load-stamp proof; this is not the full geometry gate."""
import gzip
import json
from pathlib import Path
from urllib.parse import unquote

from tools.probes.deidara_atm1_observer import LOAD_SOURCE
from tools.sampling_atm1_provenance import ATM1, HELPER, STAMP_SITE, FIELDS
from tools.sampling_geometry import collect

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STAMP_FIELDS = ('stamp_id', 'stamp_source', 'stamp_birth')


def prove(lines, metadata):
    observations = []
    for line in lines:
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed event')
        if parts[6] == 'atm1_provenance':
            values = parts[7].split(',')
            if len(values) != len(FIELDS):
                raise ValueError('incomplete observation')
            row = dict(zip(FIELDS, map(unquote, values)))
            row.update(sequence=int(parts[2]), display=int(parts[4]), tick=int(parts[5]))
            observations.append(row)
    expected = [('root_sample', 'undefined')] * 2 + [
        ('stamp_before', HELPER), ('stamp_after', HELPER),
        ('load_before', ATM1), ('stamp_before', ATM1),
        ('stamp_after', ATM1), ('load_after', ATM1)] + [('root_sample', ATM1)] * 3
    if [(r['phase'], r['path']) for r in observations] != expected:
        raise ValueError('missing/duplicate/reordered lifecycle observation')
    if any(a['sequence'] >= b['sequence'] for a, b in zip(observations, observations[1:])):
        raise ValueError('reordered observation sequence')
    roots = [r for r in observations if r['phase'] == 'root_sample']
    if [r['tick'] for r in roots] != list(range(56, 61)):
        raise ValueError('missing root boundary')
    for r in observations:
        site = 'root-before-geometry' if r['phase'] == 'root_sample' else STAMP_SITE if r['path'] == HELPER else LOAD_SOURCE
        if r['site'] != site:
            raise ValueError('wrong source site')
    before, stamp_before, stamp_after, after = observations[4:8]
    for r in (before, stamp_before):
        if any(r[f] != 'undefined' for f in STAMP_FIELDS):
            raise ValueError('child already stamped before load stamp')
    for r in observations[4:8]:
        if (r['tick'], r['frame'], r['helper_frame'], r['depth'], r['present']) != (57, '1', '44', '-16382', 'true') or r['display'] != before['display']:
            raise ValueError('load boundary identity changed')
    identity = tuple(after[f] for f in STAMP_FIELDS)
    if (not identity[0].isdigit() or identity[1] != LOAD_SOURCE
            or identity[2] != str(before['display'])
            or identity[0] == observations[3]['stamp_id']):
        raise ValueError('invalid child stamp identity/source/birth')
    for r in [stamp_after, *roots[2:]]:
        if tuple(r[f] for f in STAMP_FIELDS) != identity:
            raise ValueError('stamp not retained')
    if [(r['frame'], r['helper_frame'], r['depth']) for r in roots[2:]] != [('1', '44', '-16382'), ('2', '45', '-16382'), ('3', '46', '-16382')]:
        raise ValueError('wrong sampled lifetime')
    if any(observations[2][f] != observations[3][f] for f in STAMP_FIELDS):
        raise ValueError('parent stamp changed')
    sources = set()
    for path in metadata['sources_sha256']:
        if path.startswith('scripts/'):
            bundle = json.loads((ROOT / path).read_text())
            sources.update(bundle['game_file'] + '#' + s['path'] for s in bundle['scripts'])
    geometry = collect(lines, metadata['run_id'], 60, sources)
    boxes = [(s['tick'], b) for s in geometry['samples'] for b in s['boxes'] if b['path'] == ATM1]
    if [tick for tick, _ in boxes] != [58, 59, 60]:
        raise ValueError('missing/extra child geometry')
    for tick, box in boxes:
        if (box['instance_id'], box['source'], str(box['birth_display'])) != identity or box['frame'] != tick - 57 or box['depth'] != -16382 or box['role'] != 'helper_attack':
            raise ValueError('geometry not bound to load lifetime')
    missing = [{'tick': s['tick'], 'slot': slot} for s in geometry['samples'] for slot in ('p1', 'p2')
               if not any(b['role'] == 'hurt' and f'.game.{slot}.' in b['path'] for b in s['boxes'])]
    return {'observations': observations, 'helper_boxes': boxes,
            'stamp_binding_complete': True, 'geometry_structurally_complete': True,
            'geometry_samples': len(geometry['samples']),
            'geometry_boxes': sum(len(s['boxes']) for s in geometry['samples']),
            'full_geometry_missing_receivers': missing,
            'production_admitted': False, 'native_parity_proven': False}


def main():
    lines = gzip.open(HERE / 'native-capture.log.gz', 'rt').read().splitlines()
    metadata = json.loads((HERE / 'native-build.json').read_text())
    report = prove(lines, metadata)
    def states(rows):
        parts = [r.split('|', 7) for r in rows]
        return [(int(p[5]), p[7]) for p in parts if p[6] == 'state' and int(p[5]) >= 0]
    report['retained_state_checks'] = {}
    for name in ('s64', 's246'):
        old = gzip.open(HERE.parent / name / 'native-capture.log.gz', 'rt').read().splitlines()
        parts = [r.split('|', 7) for r in old]
        missing = [{'tick': tick, 'slot': slot} for tick in range(61) for slot in ('p1', 'p2')
                   if not any(p[6] == 'geometry_box' and int(p[5]) == tick
                              and p[7].startswith('hurt,') and f'.game.{slot}.' in p[7].split(',')[1]
                              for p in parts)]
        report['retained_state_checks'][name] = {'states': len(states(old)), 'exact_tick_payload_match': states(old) == states(lines),
                                               'raw_missing_receivers': missing}
    (HERE / 'lifetime-proof.json').write_text(json.dumps(report, indent=2) + '\n')
    print('LOAD_STAMP_LIFETIME_OK; full geometry obligations retained:', report['full_geometry_missing_receivers'])


if __name__ == '__main__':
    main()
