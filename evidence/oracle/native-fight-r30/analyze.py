"""Offline initialization audit; this is not a debugger client or producer test."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r30_sources', HERE.parent / 'native-fight-r29/analyze.py')
r29 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r29)
PLAYER = 'modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java'
EXPECTED_SENDERS = [
    'sendStopWarning', 'sendStopOnFault', 'sendEnumerateOverride',
    'sendFailureNotify', 'sendInvokeSetters', 'sendSwfloadNotify',
    'sendGetterTimeout', 'sendSetterTimeout', 'sendSquelch',
    'sendConcurrentDebugger', 'sendWideLineDebugger',
]
EXPECTED_OPTIONS = [
    'disable_script_stuck_dialog', 'disable_script_stuck', 'break_on_fault',
    'enumerate_override', 'notify_on_failure', 'invoke_setters', 'swf_load_messages',
    'getter_timeout', 'setter_timeout', 'concurrent_debugger', 'wide_line_debugger',
]


def audit_initialization(source):
    # Narrow reviewed source regions, not a general Java/control-flow parser.
    bind = source.split('public boolean bind() throws VersionException', 1)[1].split(
        'public void unbind()', 1)[0]
    senders = re.findall(r'\b(send\w+)\(', bind)
    if senders != EXPECTED_SENDERS:
        raise ValueError('Initialization command inventory changed; review required')
    options = []
    for sender in EXPECTED_SENDERS:
        if sender == 'sendSquelch':
            continue
        body = source.split('void ' + sender + '()', 1)[1].split('\n\t}', 1)[0]
        options.extend(re.findall(r'\boption = "([^"]+)"', body))
    if options != EXPECTED_OPTIONS:
        raise ValueError('Initialization option inventory changed; review required')
    if not (bind.index('sendStopWarning();') < bind.index('sendSquelch(true')
            < bind.index('t.start();') < bind.index('if (!responded)')):
        raise ValueError('Version-failure ordering changed')
    unbind = source.split('private boolean unbind(boolean requestTerminate)', 1)[1].split('\n\t}', 1)[0]
    if 'DMessage.OutExit' not in unbind or 'sendOptionMessage(' in unbind:
        raise ValueError('Disconnect preservation review changed')
    return {'sender_order': senders, 'option_names': options,
            'adjustments_precede_version_failure_check': True,
            'prior_option_restoration_in_reviewed_unbind': False,
            'player_reset_on_disconnect': 'unproved',
            'behavior_preserving_connection_qualified': False}


def read_new_sources(directory=HERE):
    sources = {}
    for row in json.loads((directory / 'source-receipts.json').read_text())['sources']:
        raw = gzip.decompress((directory / row['snapshot']).read_bytes())
        if hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Qualification source hash mismatch')
        sources[row['path'].rsplit('/', 1)[-1]] = raw.decode('utf8')
    return sources


def audit_id_chain(sources, additional):
    manager = sources[PLAYER.replace('PlayerSession.java', 'DManager.java')]
    atom = manager.split('case DMessage.kMovieClipType: {', 1)[1].split('break;', 1)[0]
    required = ['long oid = msg.getPtr();', 'value = new Long(oid);',
                'vType = VariableType.MOVIECLIP;']
    if not all(token in atom for token in required):
        raise ValueError('MovieClip atom ID decoding changed')
    if ('getValue(((Long) value).longValue(), isolateId)' not in manager
            or 'VariableAttribute.HAS_GETTER' not in manager
            or 'return ((Long)m_value).longValue();' not in additional['DValue.java']):
        raise ValueError('Value ID/cache mapping changed')
    return {'movieclip_atom_to_value_id_client_chain_qualified': True,
            'cache_scope': 'isolate; cache insertion excludes HAS_GETTER',
            'lifecycle_message_namespace_equivalence': 'unproved',
            'allocation_generation': None}


def analyze():
    sources = r29.read_sources()
    result = dict(r29.FLAGS, classification='client-contract-qualified-producer-namespace-and-preservation-unproved',
                  initialization_review=audit_initialization(sources[PLAYER]),
                  id_review=audit_id_chain(sources, read_new_sources()),
                  exact_player_producer_qualified=False,
                  placement_remove_value_namespace_equivalence_proven=False,
                  generation_or_activation_mapping_proven=False,
                  native_boundary=None, native_return_proven=False,
                  live_started=False, player_connection_started=False,
                  m0_02_status='pending')
    # Existing gate is a regression only, never new semantic qualification.
    result['historical_structural_refusal'] = r29.analyze()['historical_structural_refusal']
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['classification'])
    print(result['historical_structural_refusal'])
    raise SystemExit(1)
