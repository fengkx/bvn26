"""Record exact comparisons without promoting diagnostic captures to admission."""
import hashlib
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_mode_reference import compare, source_rows

OUT = Path(__file__).resolve().parent

def sha(path):
    raw = path.read_bytes()
    return hashlib.sha256(gzip.decompress(raw) if path.suffix == '.gz' else raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def collect():
    results = []
    for fixture in sorted((OUT / 'cases').glob('*.json')):
        case = json.loads(fixture.read_text())
        candidates = list(OUT.glob('original-*/' + case['id'] + '/events.jsonl*'))
        if len(candidates) != 1:
            raise ValueError(f'{case["id"]}: expected one original capture')
        source = candidates[0]
        native = OUT / 'native-final' / (case['id'] + '.json')
        comparison = compare(source, native)
        rows = source_rows(source)
        low, high = case['target_frames']
        target = any(r['slot'] == case['slot'] and low <= r['frame'] <= high for r in rows)
        observed = {}
        for slot in ('p1', 'p2'):
            actor = [r for r in rows if r['slot'] == slot]
            observed[slot] = {'hp_loss': actor[0]['hp'] - actor[-1]['hp'],
                              'max_hits': max(r['hits'] for r in actor), 'final': actor[-1]}
        results.append({'id': case['id'], 'comparison': comparison,
                        'target_seen': target, 'observed': observed,
                        'paths': {k: str(p.relative_to(ROOT)) for k,p in
                                  [('fixture',fixture),('source',source),('native',native)]},
                        'hashes': {'fixture':sha(fixture),'source':sha(source),'native':sha(native)}})
    write(OUT / 'comparisons.json', results)
    log = (OUT / 'logs/native-final.log').read_text()
    clean = 'MOVE_CASE_BATCH_OK 12' in log and 'SCRIPT ERROR' not in log and 'ERROR:' not in log
    flags = {key: False for key in ('production_admitted','native_parity_proven','oracle_accepted',
                                   'certified_global_tick','os_input_join_proven','native_initialization_complete')}
    report = {
        'status': 'blocked_in_progress_no_pr', 'base': '32ab99eecde34730fc2d6a5a7d26a403bd08faf5',
        'branch': 'port/weqal-base', 'worktree': str(ROOT), 'character': '小乌', 'source': 'weqal.swf',
        **flags,
        'native_flash': {'cases': len(results), 'matched':sum(r['comparison']['status']=='matched' for r in results),
                         'states':sum(r['comparison']['source_states'] for r in results), 'fields':14,
                         'complete':all(r['comparison']['complete'] for r in results),
                         'all_targets_seen':all(r['target_seen'] for r in results),
                         'clean_native_batch':clean, 'report':'comparisons.json',
                         'scope':'Diagnostic key injection, ticks 0-360, both actors; not full matrix/pixel/audio/OS-input proof'},
        'blockers': ['Source frame 1148 wankai and frame 1152 parent goto require reviewed BODY 808 form graph; variants are user-deferred. Strict frame-call and online manifest gates remain failed.',
                     'Source failure-label fallthrough into transformation prevents assuming the deferred path is unreachable based only on disabled J+K.'],
        'shared_runtime_changed':False,'shared_compiler_changed':False,
        'font': {'actual_regeneration':True,'font_number':199,'source_family':'Sarasa UI SC',
                 'build_log':'logs/font-build-r03.log','coverage_log':'logs/font-coverage-r03.log','coverage_passed':True},
        'source_tests': {'passed':9,'logs':['logs/source-tests.log','logs/hit-receive-source.log']},
        'rollback':{'passed':'WEQAL_ROLLBACK_SMOKE_OK' in (OUT/'logs/rollback.log').read_text(),
                    'scope':'Natural opening, ultimate snapshot replay, late guard input, round reset'},
        'saved_roster':{'cases':3,'report':'saved-roster-results.json','full_roster_executed':False},
        'visual':{'directory':'visual-final','scope':'Native selection/full footer and source frame 493; not Flash pixel parity',
                  'residual':'Renderer reports resource/RID leaks on process exit; not treated as clean lifecycle acceptance.'},
        'remaining':['Complete source-backed deferred-form design or separately authorized form implementation and parity',
                     'Passing online manifest and required complete saved-roster regressions',
                     'Full audiovisual/browser/AI and exhaustive move boundary acceptance'],
        'weekly_quota':{'current_remaining':None,'last_user_report':'approximately 10%','hard_block_observed':False},
        'flash_running':False,'pr_opened':False,'merged':False,'deployed':False,
    }
    write(OUT/'checks.json',report)
    print(json.dumps(report['native_flash']))

if __name__ == '__main__':
    collect()
