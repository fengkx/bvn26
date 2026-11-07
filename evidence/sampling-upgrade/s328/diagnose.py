"""Bound retained host facilities for ones entry; never manufacture a live clock."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'bf44f46e8b5ea19190566f9fa0c6cf570c9b6931'
GATES = {
    'observer': 'S328_ENTRY_INSTANCE_RESOLVER_UNPROVED',
    'independent-controls': 'S328_INDEPENDENT_CONTROLS_UNPROVED',
    'child-clock': 'S328_CHILD_CLOCK_UNPROVED',
    'fresh-capture': 'S328_FRESH_CAPTURE_BLOCKED',
}
FACILITIES = {
    'tools/probes/probe_owned_debugger.py#debugger_script': {
        'output': 'Selected thread frame-zero registers at attach, plus attach/detach status.',
        'missing_join': 'No ones target-entry breakpoint, outer instance layout or uninterrupted allocation lifetime in this script. A CPU register snapshot is not a frame-entry event.',
    },
    'tools/probes/monitor_owned_native.py#monitor_owned': {
        'output': 'PID ownership checks, run profile marker, ps state and a one-second sample request.',
        'missing_join': 'Process ownership is not outer clip identity. Statistical stack sampling does not enumerate all entries or count repeated targets. The ownership marker still reads the AIREF log.',
    },
    'tools/sampling_native.py#validate_capture': {
        'output': 'Case/configuration, sequential AIREF log, fighter state rows and completion checks.',
        'missing_join': 'Receipt validation consumes the supplied AS log; it does not independently observe the ones instance, target entry or observer-off execution.',
    },
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s328_locked_s319', HERE.parent / 's319/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facility_audit(sources):
    """Extract exact pinned functions; descriptions apply only to these adapters."""
    expected = json.loads((HERE / 'facility-function-sha256.json').read_text())
    if set(expected) != set(FACILITIES) or set(sources) != set(FACILITIES):
        raise ValueError('facility inventory changed')
    rows = []
    for key, limits in FACILITIES.items():
        path, function = key.split('#')
        source = sources[key]
        nodes = [n for n in ast.parse(source).body
                 if isinstance(n, ast.FunctionDef) and n.name == function]
        if len(nodes) != 1:
            raise ValueError('facility function missing or ambiguous: ' + key)
        node = nodes[0]
        body = ast.get_source_segment(source, node)
        if sha(body.encode()) != expected[key]:
            raise ValueError('facility function changed: ' + key)
        rows.append(dict(path=path, function=function, lines=[node.lineno, node.end_lineno],
                         function_sha256=sha(body.encode()), source=body, **limits,
                         invoked=False, independent_entry_resolver=None,
                         independent_instance_resolver=None, observer_off_on_qualified=None))
    return rows


def validate_prior(prior):
    if prior != json.loads((HERE.parent / 's319/diagnosis.json').read_text()):
        raise ValueError('locked s319 diagnosis changed')


def diagnose():
    for path, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError('locked input changed: ' + path)
    prior = load_prior().diagnose()
    validate_prior(prior)
    audit = facility_audit({key: (ROOT / key.split('#')[0]).read_text() for key in FACILITIES})
    return {
        'slice': 's328', 'base': BASE, 'scope': 'AFTER-s326 rank #2 only',
        'authority': 'evidence/sampling-upgrade/next-fix-priority-after-s326.md',
        'production_admitted': False, 'native_parity_proven': False, 'm0_02_status': 'pending',
        'locked_s319_reproduced': True,
        'historical_validation_only': prior['historical_validation_only'],
        'host_facility_source_audit': audit,
        'audit_boundary': 'Three existing host adapter functions, read only and not invoked. Not an exhaustive native facility search or a new native observation. Prior source/event findings are retained validation only.',
        'independent_observations_new': [],
        'qualification_matrix': prior['qualification_matrix'],
        'live_entry_resolver': None, 'live_instance_resolver': None,
        'observer_qualified': False, 'independent_controls_proved': False,
        'independent_child_clock_proved': False, 'fresh_capture_eligible': False,
        'new_builds': 0, 'new_player_launches': 0, 'new_attaches': 0,
        'new_captures': 0, 'new_images': 0, 'other_ranks_executed': [],
        're_ranked': False, 'product_obligations_closed': 0,
        'blocker': 'Independent outer-instance lifetime and all-ten-frame target-entry channel were not derived. Retained host adapters provide no qualified join from their outputs to those events. Repeated/changed/replacement/off-on controls remain unproved; fresh capture is blocked before launch.',
        'next_required_observation': 'Derive and bind a native target-entry site plus outer-instance lifetime resolver, including actionless frames2-10. Independently retain selection, actual entry and following root/callback order in one run/lifetime. Then qualify isolated repeated, changed, same-depth replacement and observer-off/on controls before fresh ones capture.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    failures = [code for flag, code in GATES.items()
                if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + result['blocker'])
        return 1
    print('S328_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
