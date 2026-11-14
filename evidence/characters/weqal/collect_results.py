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
        native = OUT / 'native-base-form-r02' / (case['id'] + '.json')
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
    log = (OUT / 'native-base-form-r02/run.log').read_text()
    clean = 'MOVE_CASE_BATCH_OK 12' in log and 'SCRIPT ERROR' not in log and 'ERROR:' not in log
    flags = {key: False for key in ('production_admitted','native_parity_proven','oracle_accepted',
                                   'certified_global_tick','os_input_join_proven','native_initialization_complete')}
    report = {
        'status': 'targeted_sop_candidate_pending_final_checks', 'base': '32ab99eecde34730fc2d6a5a7d26a403bd08faf5',
        'branch': 'port/weqal-base', 'worktree': str(ROOT), 'character': '小乌', 'source': 'weqal.swf',
        **flags,
        'native_flash': {'cases': len(results), 'matched':sum(r['comparison']['status']=='matched' for r in results),
                         'states':sum(r['comparison']['source_states'] for r in results), 'fields':14,
                         'complete':all(r['comparison']['complete'] for r in results),
                         'all_targets_seen':all(r['target_seen'] for r in results),
                         'clean_native_batch':clean, 'report':'comparisons.json',
                         'scope':'Diagnostic key injection, ticks 0-360, both actors; not full matrix/pixel/audio/OS-input proof'},
        'blockers': [],
        'shared_runtime_changed':False,'shared_compiler_changed':False,
        'font': {'actual_regeneration':True,'font_number':199,'source_family':'Sarasa UI SC',
                 'build_log':'logs/font-build-r03.log','coverage_log':'logs/font-coverage-r03.log','coverage_passed':True},
        'source_tests': {'passed':9,'logs':['logs/source-tests.log','logs/hit-receive-source.log']},
        'rollback':{'passed':'WEQAL_ROLLBACK_SMOKE_OK' in (OUT/'logs/rollback.log').read_text(),
                    'scope':'Natural opening, ultimate snapshot replay, late guard input, round reset'},
        'saved_roster':{'report':'regressions-form-r02/flash-replay/report.json','full_roster_executed':False},
        'visual':{'directory':'visual-final','scope':'Native selection/full footer and source frame 493; not Flash pixel parity',
                  'residual':'Renderer reports resource/RID leaks on process exit; not treated as clean lifecycle acceptance.'},
        'remaining':['Full audiovisual/browser/AI and exhaustive move boundary acceptance'],
        'weekly_quota':{'current_remaining':None,'last_user_report':'approximately 8% at continuation start; live exact remainder unavailable','hard_block_observed':False},
        'flash_running':False,'pr_opened':False,'merged':False,'deployed':False,
    }
    forms = json.loads((OUT / 'form-comparisons.json').read_text())
    report['form_native_flash'] = {
        'cases': len(forms), 'matched': sum(row['comparison']['status'] == 'matched' for row in forms),
        'states': sum(row['comparison']['source_states'] for row in forms),
        'complete': all(row['comparison']['complete'] for row in forms),
        'all_targets_seen': all(row['target_seen'] for row in forms),
        'report': 'form-comparisons.json',
        'scope': 'Diagnostic transformation, target combo/supers/mirror warp; recorded source interval delivery; explicit target-form energy refills.'}
    report['source_tests']['passed'] = 11
    report['source_tests']['logs'].append('source-form-tests-r01.log')
    report['replacement_graph'] = {'nodes': 2, 'sprites': [387, 808], 'audit': 'form-graph.json',
        'strict_guard_passed': True, 'lifecycle_log': 'weqal_replacement_checkpoint-r02.log',
        'input_log': 'weqal_input_activation-r02.log', 'failure_fallthrough_tested': True,
        'explicit_parent_goto_tested': True}
    regressions = OUT / report['saved_roster']['report']
    if regressions.exists():
        rows = json.loads(regressions.read_text())['results']
        report['saved_roster'].update(cases=len(rows),
            states=sum(row['comparison']['source_states'] for row in rows if row['comparison']),
            full_roster_executed=len(rows) == 288,
            all_matched=all(row['execution']['executed'] and row['comparison']['status'] == 'matched' for row in rows))
    report['rollback'] = {
        'passed': 'WEQAL_ROLLBACK_SMOKE_OK' in (OUT / 'weqal_rollback_smoke-r02.log').read_text(),
        'scope': 'Natural opening, ultimate snapshot replay, late guard input, round reset',
        'log': 'weqal_rollback_smoke-r02.log'}
    report['replacement_graph']['timer_round_log'] = 'form-lifecycle.log'
    report['form_native_flash']['clean_native_batches'] = all(
        'ERROR:' not in (OUT / path).read_text() and 'SCRIPT ERROR' not in (OUT / path).read_text()
        for path in ['native-forms-r01/run-r02.log', 'native-forms-r03/run.log'])
    report['web'] = json.loads((OUT / 'web/browser-check.json').read_text())
    report['online_manifest'] = {
        'passed': 'ONLINE_MANIFEST_OK' in (OUT / 'online-manifest-check-r03.log').read_text(),
        'log': 'online-manifest-check-r03.log'}
    report['visual']['form_directory'] = 'visual-form'
    write(OUT/'checks.json',report)
    print(json.dumps(report['native_flash']))

if __name__ == '__main__':
    collect()
