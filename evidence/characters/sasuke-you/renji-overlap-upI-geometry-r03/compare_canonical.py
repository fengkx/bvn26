import gzip
import json
from pathlib import Path

ROOT = Path(__file__).parent

def read(path, compressed=False):
    stream = gzip.open(path, 'rt') if compressed else open(path)
    with stream:
        return [json.loads(line) for line in stream]

canonical = read(ROOT.parent / 'renji-overlap-upI-r01' / 'source-events.jsonl.gz', True)
probe = read(ROOT / 'events.jsonl')
result = {'canonical': {}, 'probe': {}, 'same_by_fight_tick': {}}
for kind in ('state', 'helper_state'):
    base = [(e['fight_tick'], e['value']) for e in canonical if e['kind'] == kind and e['fight_tick'] >= 0]
    observed = [(e['fight_tick'], e['value']) for e in probe if e['kind'] == kind and e['fight_tick'] >= 0]
    result['canonical'][kind] = len(base)
    result['probe'][kind] = len(observed)
    result['same_by_fight_tick'][kind] = base == observed
    if not result['same_by_fight_tick'][kind]:
        raise SystemExit(json.dumps(result, ensure_ascii=False))
result['startup_rows'] = {
    kind: {
        'canonical': sum(e['kind'] == kind and e['fight_tick'] < 0 for e in canonical),
        'probe': sum(e['kind'] == kind and e['fight_tick'] < 0 for e in probe),
    }
    for kind in ('state', 'helper_state')
}
result['geometry_rows'] = [
    {k: e[k] for k in ('sequence', 'display_tick', 'fight_tick', 'value')}
    for e in probe if e['kind'] == 'you_geometry'
]
print(json.dumps(result, ensure_ascii=False, indent=2))
