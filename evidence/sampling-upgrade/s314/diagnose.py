"""Audit observation independence for the single archived root callback."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'dfdbdcd5d1de59b27194b21e6fc138ef91bc37ae'
LOGGER = 'patches/main/frame_1/DoAction.as'
GATES = {
    'observer-qualification': 'S314_OBSERVER_QUALIFICATION_UNPROVED',
    'callback-completion': 'S314_CALLBACK_COMPLETION_UNPROVED',
    'terminal-completeness': 'S314_TERMINAL_COMPLETENESS_UNPROVED',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def locked_module():
    spec = importlib.util.spec_from_file_location('s304_locked', HERE.parent / 's304/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_channel(logger, callback):
    bound = locked_module().source_bounds(callback)
    lines = logger.splitlines()
    assignment = '_root.aiEvent = function(kind, value)'
    if lines.count(assignment) != 1:
        raise ValueError('ambiguous logger assignment')
    start = lines.index(assignment)
    expected = [assignment, '{',
                '   trace("AIREF|" + aiRun + "|" + (++aiSeq) + "|" + getTimer() + "|" + aiDisplay + "|" + aiFight + "|" + kind + "|" + value);',
                '};']
    if lines[start:start + 4] != expected:
        raise ValueError('changed logger serialization')
    points = bound['lines']
    # These are source operations, not a reconstruction of native activations.
    boundaries = []
    for key in ('assignment', 'guard', 'closure_marker', 'replace_callback',
                'disable_logger', 'explicit_return', 'done_marker', 'arm_guard', 'timeout_guard'):
        line = points[key]
        boundaries.append({'operation': key, 'line': line,
                           'source': callback.splitlines()[line - 1],
                           'independent_activation_witness': None})
    return {
        'logger_member': LOGGER, 'logger_member_sha256': sha(logger.encode()),
        'logger_line_start': start + 1, 'logger_line_end': start + 4,
        'logger_source': '\n'.join(expected),
        'serialized_fields': ['literal AIREF', 'run ID', 'event sequence', 'getTimer()',
                              'display counter', 'fight counter', 'kind', 'value'],
        'callback_member': bound['archive_member'], 'callback_sha256': bound['sha256'],
        'boundaries': boundaries,
        'guard_after_marker': [
            {'line': n, 'source': callback.splitlines()[n - 1]}
            for n in range(points['replace_callback'], points['explicit_return'] + 1)],
        'source_identity_is_loaded_body_identity': False,
        'aiEvent_independent_of_callback_mutation': False,
        'host_copy_independent_of_event_producer': False,
        'host_copy_limit': 'Independent host custody copies the same AIREF producer; it supplies no callback entry/dispatcher-return observation.',
        'return_paths': bound['exits'],
        'same_clock_limit': 'Guard precedes aiDisplay increment. A closing invocation can retain the done invocation clock values; those counters cannot identify an activation.',
    }


def diagnose():
    for path, expected in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError('locked input changed: ' + path)
    prior = locked_module().diagnose()
    if prior != json.loads((HERE.parent / 's304/diagnosis.json').read_text()):
        raise ValueError('locked s304 diagnosis mismatch')
    with tarfile.open(HERE.parent / 's293/held/native-build.tar.gz') as archive:
        logger_bytes = archive.extractfile(LOGGER).read()
    channel = audit_channel(logger_bytes.decode(), prior['source_callback']['source'])
    requirements = {
        'loaded_body': 'Resolve executing body bytes to the archived callback, not merely a source/SWF hash.',
        'owner_generation': 'Bind root owner lifetime, defining scope and closure generation across property replacement.',
        'activation_entry': 'Observe entry with an invocation identity independent of shared tick/display and aiEvent.',
        'dispatcher_return': 'Match that same invocation at the dispatcher continuation; distinguish return, unwind and termination.',
        'observer_preservation': 'Qualify observer-off/on effects and retained observation after aiEvent replacement.',
    }
    return {
        'base': BASE, 'scope': 'AFTER-s308 rank #6 only; one archived instrumentation callback',
        'production_admitted': False, 'native_parity_proven': False, 'M0-02': 'pending',
        'product_obligations_closed': 0, 'locked_s304_reproduced': True,
        'independent_pair_proved_and_closed': prior['independent_pair_proved_and_closed'],
        'channel_audit': channel,
        'runs': prior['runs'],
        'qualification_requirements': {
            name: {'requirement': requirement, 'qualified_witness': None}
            for name, requirement in requirements.items()},
        'observer_qualified': False, 'callback_completion_proved': False,
        'terminal_inventory_executed': False, 'terminal_completeness_proved': False,
        'first_unmet_prerequisite': 'Independent loaded-body/owner-generation/activation resolver with matched dispatcher return.',
        'blocker': 'The retained channel is disabled by the callback itself; neither source identity nor host custody supplies an independent activation entry-to-dispatcher-return witness.',
        'facility_search_scope': 'Locked s304 source/diagnosis and its s293 held archive/normal-held logs only; not a claim that no external facility can exist.',
        'next_discriminator': 'Qualify the five independent witness obligations for this callback before any capture. Keep done and closing invocations distinct; normal return, unwind and process termination need separate outcomes. Full terminal dispatch inventory remains deferred.',
        'gates': {name: {'proved': False, 'code': code} for name, code in GATES.items()},
        'new_builds': 0, 'new_player_launches': 0, 'new_process_attaches': 0,
        'new_captures': 0, 'new_memory_reads': 0, 'other_ranks_executed': False,
        'fixed_read_threshold': None, 'full_as_proven': False,
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
        parser.exit(1, 'S314_EVIDENCE_INVALID: ' + str(error) + '\n')
    failed = [code for name, code in GATES.items()
              if getattr(args, 'require_' + name.replace('-', '_'))]
    if failed:
        parser.exit(1, '\n'.join(failed) + '\n')
    print('S314_DIAGNOSIS_OK production_admitted=false native_parity_proven=false M0-02=pending')


if __name__ == '__main__':
    main()
