"""Derive rejection witnesses directly from locked raw visual records, not summaries."""
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOCKED = HERE.parent / 's262'


def derive(raw, run_id, scene, source):
    """Negative evidence only: equal digits never grant complete scene admission."""
    shapes = {}
    for change in source['symbols']['1810']['changes']:
        tag = ET.fromstring(change['tag'])
        if tag.attrib.get('type') == 'PlaceObject2Tag':
            shapes[change['frame']] = int(tag.attrib['characterId'])
    if set(shapes) != set(range(1, 11)):
        raise ValueError('incomplete source glyph mapping')
    rows = {}
    for row in scene['rows']:
        key = (row['tick'], row['native_display'], row['replayed_firings'])
        if key in rows:
            raise ValueError('duplicate scene boundary')
        rows[key] = row
    pending = None
    witnesses = []
    seen = set()
    for line_number, line in enumerate(raw.decode().splitlines(), 1):
        if not line.startswith('AIREF|'):
            continue
        parts = line.split('|', 7)
        if len(parts) != 8:
            raise ValueError('malformed event')
        _, run, sequence, _, display, tick, kind, value = parts
        if run != run_id:
            raise ValueError('cross-run record')
        if not kind.startswith('s262_'):
            continue
        boundary = (int(tick), int(display))
        if kind == 's262_begin':
            if pending is not None:
                raise ValueError('overlapping boundary')
            pending = dict(boundary=boundary, firing=int(value), digits={}, begin_line=line_number)
        elif kind == 's262_visual':
            if pending is None or pending['boundary'] != boundary:
                raise ValueError('unbound visual record')
            fields = value.split(',')
            if len(fields) != 14:
                raise ValueError('incomplete visual record')
            role = fields[0]
            if role in ('timer/十', 'timer/个'):
                if role in pending['digits']:
                    raise ValueError('duplicate digit')
                frame = int(fields[3])
                if frame not in shapes:
                    raise ValueError('unknown source frame')
                pending['digits'][role] = dict(frame=frame, path=fields[1], depth=int(fields[2]),
                                               sequence=int(sequence), raw_line=line_number)
        elif kind == 's262_end':
            if pending is None or pending['boundary'] != boundary or pending['firing'] != int(value):
                raise ValueError('mismatched end')
            key = (*boundary, int(value))
            if key not in rows or key in seen or len(pending['digits']) != 2:
                raise ValueError('missing or duplicate boundary join')
            seen.add(key)
            row = rows[key]
            differences = []
            for role, field in (('timer/十', 'tens'), ('timer/个', 'ones')):
                digit = pending['digits'][role]
                other = row['godot'][field]
                if type(other) is not int or other not in shapes:
                    raise ValueError('unknown scene source frame')
                if digit['frame'] != other:
                    differences.append(dict(role=role, **digit, scene_frame=other,
                        native_source_shape=shapes[digit['frame']], scene_source_shape=shapes[other]))
            # A single contradictory source frame suffices; no floating-point or pixel policy.
            witnesses.append(dict(run_id=run_id, tick=key[0], display=key[1], firing=key[2],
                begin_line=pending['begin_line'], end_line=line_number,
                digit_conflict=bool(differences), witness=differences[0] if differences else None))
            pending = None
    if pending is not None or seen != set(rows) or len(seen) != 61:
        raise ValueError('incomplete boundary coverage')
    return dict(route='raw digit/source-shape contradiction; negative-only',
                raw_sha256=hashlib.sha256(raw).hexdigest(), rows=witnesses,
                boundaries_with_digit_conflict=sum(r['digit_conflict'] for r in witnesses),
                complete_admission_inferred=False, new_runtime_observations=0,
                exact_rgba_edge_residual=None, exact_rgba_interior_residual=None)


def collect():
    raw = gzip.decompress((LOCKED / 'native-capture.log.gz').read_bytes())
    receipt = json.loads((LOCKED / 'native-receipt.json').read_text())
    if hashlib.sha256(raw).hexdigest() != receipt['files'][receipt['trace']]:
        raise ValueError('receipt raw hash mismatch')
    build = json.loads((LOCKED / 'native-build.json').read_text())
    return derive(raw, build['run_id'], json.loads((LOCKED / 'paired-scene.json').read_text()),
                  json.loads((LOCKED / 'source-contract.json').read_text()))


if __name__ == '__main__':
    print(json.dumps(collect(), indent=2, ensure_ascii=False))
