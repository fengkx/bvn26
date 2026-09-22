import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'evidence' / 'characters' / 'lee'
CASES = BASE / 'move-cases'
GODOT = BASE / 'godot'
OUT = BASE / 'coverage-r01.json'

cases = {}
for path in sorted(CASES.glob('*.json')):
    data = json.loads(path.read_text())
    cases[data['id']] = data

comparisons = {}
for path in GODOT.glob('**/compare*.json'):
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        continue
    dirname = path.parent.name
    case_id = dirname.rsplit('-r', 1)[0] if '-r' in dirname else dirname
    aliases = {
        'lee-normal': 'lee-157-nornalhit-neutral',
        'lee-574-bisha-energy_below': 'lee-574-bisha-energy_below',
        'lee-574-bisha-guard': 'lee-574-bisha-neutral',
        'lee-795-bishaSuper-energy_above': 'lee-795-bishaSuper-neutral',
        'lee-795-bishaSuper-energy_exact': 'lee-795-bishaSuper-neutral',
        'lee-795-bishaSuper-energy_below': 'lee-795-bishaSuper-neutral',
        'lee-66-jump2-neutral': 'lee-66-jump-neutral',
        'lee-1050-defence2-neutral': 'lee-1050-defence-neutral',
    }
    case_id = aliases.get(case_id, case_id)
    status = data.get('status')
    if status in {'matched', 'different'}:
        comparisons.setdefault(case_id, []).append({
            'status': status,
            'path': str(path.relative_to(ROOT)),
            'source_states': data.get('source_states'),
            'native_states': data.get('native_states'),
        })

labels = {}
for case_id, case in cases.items():
    if case.get('scenario') != 'neutral':
        continue
    label = case['label']
    entry = labels.setdefault(label, {
        'label': label,
        'source_timeline': False,
        'fixture_cases': [],
        'comparisons': [],
    })
    entry['source_timeline'] = entry['source_timeline'] or bool(case.get('has_source_timeline'))
    entry['fixture_cases'].append(case_id)
    candidates = comparisons.get(case_id, [])
    if candidates:
        # Keep the highest revision for a case family; old failed probes must not taint acceptance.
        def revision(item):
            import re
            m = re.search(r'-r(\d+)', item['path'])
            return int(m.group(1)) if m else 0
        newest = max(revision(item) for item in candidates)
        candidates = [item for item in candidates if revision(item) == newest]
    entry['comparisons'].extend(candidates)

for entry in labels.values():
    unique = {}
    for cmp in entry['comparisons']:
        unique[cmp['path']] = cmp
    entry['comparisons'] = list(unique.values())
    statuses = {cmp['status'] for cmp in entry['comparisons']}
    if not entry['source_timeline']:
        entry['classification'] = 'unreachable_source_timeline'
    elif 'different' in statuses:
        entry['classification'] = 'diverged'
    elif 'matched' in statuses:
        entry['classification'] = 'matched'
    else:
        entry['classification'] = 'uncompared'

ordered = sorted(labels.values(), key=lambda item: item['label'])
summary = {
    'format': 'lee-coverage-v1',
    'fixture_count': len(cases),
    'neutral_label_count': len(ordered),
    'reachable_label_count': sum(e['classification'] != 'unreachable_source_timeline' for e in ordered),
    'matched_label_count': sum(e['classification'] == 'matched' for e in ordered),
    'diverged_label_count': sum(e['classification'] == 'diverged' for e in ordered),
    'uncompared_label_count': sum(e['classification'] == 'uncompared' for e in ordered),
    'unreachable_label_count': sum(e['classification'] == 'unreachable_source_timeline' for e in ordered),
    'labels': ordered,
}
OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in summary if k.endswith('_count')}, ensure_ascii=False))
for entry in ordered:
    print(entry['classification'], entry['label'], entry['fixture_cases'][0], len(entry['comparisons']))
