"""Fail closed on the unfulfilled AFTER-s335 rank-6 measurement prerequisite."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATES = ('independent-channel', 'logger-replacement', 'callback-completion',
         'off-on', 'terminal-completeness')
BOUNDARIES = ('activation-entry', 'done-producing-invocation', 'closing-invocation',
              'callback-replacement', 'logger-replacement', 'quit-request',
              'dispatcher-continuation')


def verify_pins(path):
    for name, digest in json.loads(path.read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Locked input changed: ' + name)


def load_prior():
    spec = importlib.util.spec_from_file_location('locked_s332', HERE.parent / 's332/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay():
    result = load_prior().diagnose()
    if result != json.loads((HERE.parent / 's332/diagnosis.json').read_text()):
        raise ValueError('Complete locked s332 replay changed')
    return result


def expected_attempt():
    # A missing witness is not an observed negative or a proof-import interface.
    return dict(
        slice='s341', scope='AFTER-s335 rank #6 only',
        status='blocked-before-live-binding',
        target='archived patches/main/frame_10/DoAction.as root onEnterFrame',
        loaded_closure_body=None, owner_generation=None, defining_scope_generation=None,
        closure_generation=None, activation_entry=None, independent_channel=None,
        uninterrupted_lifetime=None, logger_replacement=None,
        matched_dispatcher_continuation=None, outcome=None, replacement_survival=None,
        observer_off=None, observer_on=None, off_on_preservation=None,
        boundaries=[dict(boundary=b, event=None, closure_generation=None,
                         owner_generation=None, activation=None, outcome=None)
                    for b in BOUNDARIES],
        off_on_controls_executed=False, terminal_inventory_executed=False,
        independent_observations=[],
        reason='Locked s332 has an aiEvent-independent host sink but no loaded '
               'closure/body, owner-generation or activation resolver through replacement '
               'and dispatcher continuation. No replacement-surviving live binding '
               'was obtained in s341. Off/on qualification must precede inventory.')


def audit_attempt(record):
    if record != expected_attempt():
        raise ValueError('Unobserved callback binding record changed; new proof requires independent review')


def diagnose():
    verify_pins(HERE / 'input-sha256.json')
    retained = replay()
    attempt = json.loads((HERE / 'binding-attempt.json').read_text())
    audit_attempt(attempt)
    return dict(
        slice='s341', scope='AFTER-s335 rank #6 only',
        production_admitted=False, native_parity_proven=False, m0_02_status='pending',
        locked_s332_reproduced=True, replay_is_new_progress=False,
        repeated_adapter_inventory_is_new_proof=False,
        qualification_requirements=retained['qualification_requirements'],
        attempt=attempt, independent_native_observations=0,
        mechanism_obligations_closed=0, product_obligations_closed=0,
        gates={g: dict(proved=False, code='S341_' + g.upper().replace('-', '_') + '_UNPROVED')
               for g in GATES},
        new_builds=0, new_player_launches=0, new_attaches=0, new_memory_reads=0,
        new_helper_installations=0, new_captures=0, other_ranks_executed=[],
        full_as_proven=False, fixed_suffix_threshold=None,
        next_required_evidence='Independently bind one loaded closure/body, owner and closure '
                               'generations and activation through a replacement-surviving '
                               'dispatcher-continuation channel. Distinguish normal return, '
                               'unwind and termination, and done-producing from closing '
                               'invocations. Qualify observer off/on before terminal inventory.')



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for gate in GATES:
        parser.add_argument('--require-' + gate, action='store_true')
    args = parser.parse_args()
    try:
        result = diagnose()
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, 'S341_EVIDENCE_INVALID: ' + str(exc) + '\n')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    failed = [result['gates'][g]['code'] for g in GATES
              if getattr(args, 'require_' + g.replace('-', '_'))]
    print('; '.join(failed) if failed else
          'S341_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
