"""Bound retained observer applicability to the locked terminal root callback."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '78bf16cff0f568d65f3a12c131a4839176371f19'
GATES = {name: 'S323_' + name.upper().replace('-', '_') + '_UNPROVED'
         for name in ('independent-channel', 'logger-replacement',
                      'callback-completion', 'terminal-completeness')}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def excerpt(path, name):
    source = (ROOT / path).read_text()
    matches = [node for node in ast.parse(source).body
               if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise ValueError('ambiguous function: ' + name)
    node = matches[0]
    return {'path': path, 'file_sha256': sha(source.encode()),
            'start_line': node.lineno, 'end_line': node.end_lineno,
            'source': '\n'.join(source.splitlines()[node.lineno - 1:node.end_lineno])}


def audit_applicability(callback, callback_sha):
    if sha(callback.encode()) != callback_sha:
        raise ValueError('callback source changed')
    # Only the pure retained text transformer is evaluated; build() is never run.
    schedule = excerpt('tools/probes/build_ai_reference.py', 'instrument_schedule')
    quoted = excerpt('tools/probes/probe_reference_helpers.py', 'quoted')
    namespace = {'json': json}
    exec(compile(quoted['source'], quoted['path'], 'exec'), namespace)
    exec(compile(schedule['source'], schedule['path'], 'exec'), namespace)
    origin = 'main/frame_10/DoAction.as'
    transformed = namespace['instrument_schedule'](callback, origin)
    if transformed.count(callback) != 1:
        raise ValueError('schedule transformer changed archived callback')
    before, after = transformed.split(callback)
    if ',enter,' not in before or ',exit,' not in after:
        raise ValueError('schedule envelope changed')
    action = load(ROOT / 'tools/probes/doaction_observer.py', 's323_action')
    callsite = load(ROOT / 'tools/probes/callsite_observer.py', 's323_callsite')
    bundle = {'game_file': 'game/main.swf', 'swf_sha256': 'not-a-live-binding',
              'scripts': [{'path': 'frame_10/DoAction.as', 'source': callback}]}
    # The supplied source is an archived patch, not a claim about original bytes.
    record = action.inventory(bundle, include_clip=True)[0]
    if record['instrumented'] or action.instrument(callback, record) != callback:
        raise ValueError('main DoAction eligibility changed')
    if callsite.selected(record) or callsite.instrument(callback, record) != callback:
        raise ValueError('root callsite eligibility changed')
    builder = (ROOT / 'tools/probes/build_ai_reference.py').read_text().splitlines()
    start = next(i for i, line in enumerate(builder) if line.strip() == 'if body_boundaries and name in fighter_sources:')
    end = next(i for i in range(start + 1, len(builder)) if builder[i].strip() == 'if recovery_order_probe:')
    body_source = '\n'.join(builder[start:end])
    if not all(text in body_source for text in ('outer_callback', 'on_enterframe();',
                                               'body_callback_enter', 'body_callback_exit', '_root.aiEvent')):
        raise ValueError('BODY observer envelope changed')
    return {
        'method': 'Static eligibility and pure text transformation only; no compiled or executed observer.',
        'target': {'swf': 'game/main.swf', 'archive_member': 'patches/main/frame_10/DoAction.as',
                   'source_sha256': callback_sha, 'loaded_body': None},
        'schedule': {'implementation': schedule, 'quoted_dependency': quoted,
                     'prefix': before, 'suffix': after,
                     'original_callback_preserved': True,
                     'transformed_sha256': sha(transformed.encode()),
                     'interpretation': 'Markers surround the frame action that assigns onEnterFrame; neither is inside that assigned function. This is not callback entry/return instrumentation.',
                     'producer': '_root.aiEvent', 'applied_to_player': False},
        'doaction': {'inventory': excerpt('tools/probes/doaction_observer.py', 'inventory'),
                     'instrument': excerpt('tools/probes/doaction_observer.py', 'instrument'),
                     'target_kind': record['kind'], 'target_instrumented': record['instrumented'],
                     'output_unchanged': True,
                     'interpretation': 'Main SWF blocks are excluded; enabling a block entry would still not observe the assigned closure entry or dispatcher return.'},
        'callsite': {'selected': excerpt('tools/probes/callsite_observer.py', 'selected'),
                     'instrument': excerpt('tools/probes/callsite_observer.py', 'instrument'),
                     'target_selected': False, 'output_unchanged': True,
                     'interpretation': 'Reviewed fighter doAllAction handlers do not select this root property callback; call_after/end are inside their handler, not an outer dispatcher continuation.'},
        'body_callback': {'path': 'tools/probes/build_ai_reference.py',
                          'start_line': start + 1, 'end_line': end, 'source': body_source,
                          'interpretation': 'Fighter-only wrapper around on_enterframe(); exit marks continuation after that inner call, still within the enclosing clip callback. Slot and coordinates do not identify an owner generation or activation.'},
        'replacement_dependency': {
            'affected_candidates': ['schedule', 'body_callback', 'doaction', 'callsite'],
            'sink': '_root.aiEvent',
            'interpretation': 'Every candidate emits via the property replaced at the closing guard. No independent replacement-surviving sink is established; no new execution is inferred.',
            'independent_survival_witness': None},
    }


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    prior = load(HERE.parent / 's314/diagnose.py', 's323_prior').diagnose()
    if prior != json.loads((HERE.parent / 's314/diagnosis.json').read_text()):
        raise ValueError('locked s314 diagnosis mismatch')
    callback = json.loads((HERE.parent / 's304/diagnosis.json').read_text())['source_callback']
    applicability = audit_applicability(callback['source'], callback['sha256'])
    return {
        'base': BASE, 'scope': 'AFTER-s317 rank #6 only',
        'production_admitted': False, 'native_parity_proven': False, 'M0-02': 'pending',
        'product_obligations_closed': 0, 'locked_s314_reproduced': True,
        'retained_validation_not_new_progress': {'independent_pair_proved_and_closed': prior['independent_pair_proved_and_closed'],
                                                'runs': prior['runs'], 'channel_audit': prior['channel_audit']},
        'new_observer_applicability_audit': applicability,
        'independently_observed_live_invocations': [],
        'qualification_requirements': prior['qualification_requirements'],
        'independent_channel_proved': False, 'logger_replacement_survival_proved': False,
        'callback_completion_proved': False, 'terminal_completeness_proved': False,
        'terminal_inventory_executed': False,
        'blocker': 'Retained candidates either do not select the root closure or observe its assignment/inner call, and all use the replaced aiEvent property. No independent loaded-body/owner-generation/activation-to-dispatcher-return facility has been established.',
        'search_scope': 'Four retained source observer paths named in this report plus locked s314; not an exhaustive search for external facilities.',
        'next_discriminator': 'Resolve one live loaded closure, owner/defining-scope generation and activation independently; match its entry with its dispatcher continuation through logger replacement and qualify off/on effects. Return, unwind and termination must remain distinct; done and closing invocations must not share an inferred identity.',
        'gates': {name: {'proved': False, 'code': code} for name, code in GATES.items()},
        'new_builds': 0, 'new_player_launches': 0, 'new_process_attaches': 0,
        'new_memory_reads': 0, 'new_captures': 0, 'other_ranks_executed': False,
        'fixed_suffix_threshold': None, 'full_as_proven': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for name in GATES:
        parser.add_argument('--require-' + name, action='store_true')
    args = parser.parse_args()
    try:
        report = diagnose()
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    except (ValueError, KeyError, OSError, TypeError) as error:
        parser.exit(1, 'S323_EVIDENCE_INVALID: ' + str(error) + '\n')
    failed = [code for name, code in GATES.items()
              if getattr(args, 'require_' + name.replace('-', '_'))]
    if failed:
        parser.exit(1, '\n'.join(failed) + '\n')
    print('S323_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')


if __name__ == '__main__':
    main()
