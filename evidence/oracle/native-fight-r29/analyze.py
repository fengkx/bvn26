"""Inspect pinned public client sources; never connect a debugger or infer producer semantics."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FLAGS = {k: False for k in ('production_admitted', 'native_parity_proven', 'oracle_accepted',
                           'certified_global_tick', 'os_input_join_proven')}


def read_sources(directory=HERE):
    receipt = json.loads((directory / 'source-receipts.json').read_text())
    sources = {}
    for row in receipt['sources']:
        raw = gzip.decompress((directory / row['snapshot']).read_bytes())
        if hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Public source snapshot mismatch: ' + row['path'])
        sources[row['path']] = raw.decode('utf8')
    return sources


def inspect_client(sources):
    prefix = 'modules/debugger/src/java/flash/tools/debugger/'
    message = sources[prefix + 'concrete/DMessage.java']
    manager = sources[prefix + 'concrete/DManager.java']
    session = sources[prefix + 'Session.java']
    value = sources[prefix + 'Value.java']
    frame = sources[prefix + 'Frame.java']
    stack = sources[prefix + 'concrete/DStackContext.java']
    player = sources[prefix + 'concrete/PlayerSession.java']
    constants = {}
    for name in ['InPlaceObject', 'InRemoveObject', 'InNewObject', 'InFrame', 'InBreakAtExt']:
        matches = re.findall(r'public static final int\s+' + name + r'\s*=\s*(\d+)\s*;', message)
        if len(matches) != 1:
            raise ValueError('Nonunique message declaration')
        constants[name] = int(matches[0])
    for name, operation in [('InPlaceObject', 'placeObject'), ('InRemoveObject', 'removeObject')]:
        section = manager.split('case DMessage.' + name + ': {', 1)[1].split('\n\t\t}', 1)[0]
        if 'long objId = msg.getPtr();' not in section or '// m_bag.' + operation not in section:
            raise ValueError('Object-message handler changed')
        if name == 'InPlaceObject' and 'String path = msg.getString();' not in section:
            raise ValueError('Placement path field missing')
    checks = {
        'value_alias_contract': 'same underlying object' in value,
        'id_stability_scoped_to_value_life': "A Value's id is maintained for the life" in session,
        'null_can_mean_out_of_scope': 'go out of scope are no longer accessible' in session,
        'legacy_as2_pseudo_ids': 'exists in AS2, not AS3.' in value,
        'frame_only_while_suspended': 'only valid when execution has suspended' in frame,
        'frame_mapping_heuristic': 'attempting to guess' in manager and 'oldFrame.getCallSignature()' in manager,
        'incoming_this_id_discarded': 'thisId /* bogus */' in stack and 'm_this = null;' in stack,
        'client_sends_script_stuck_options': 'sendStopWarning();' in player and 'disable_script_stuck_dialog' in player,
        'avmplus_spec_is_avm2': '\\page AVM2' in sources['doc/avmspec/intro.dox'],
    }
    if not all(checks.values()):
        raise ValueError('Public semantic anchor changed')
    return dict(**FLAGS, independent_source_semantics_found=True,
                message_constants=constants, source_checks=checks,
                consumer_wire_shapes={'InPlaceObject': ['getPtr object ID', 'getString path'],
                                      'InRemoveObject': ['getPtr object ID']},
                event_retention='Client bag updates commented out in the inspected handlers',
                possible_next_route='qualify placement/removal producer and version semantics before a client experiment',
                pinned_player_emission_proven=False, native_boundary=None,
                owner_native_mapping=None, generation_native_mapping=None, activation_native_mapping=None,
                native_return_proven=False, target_call_join_proven=False,
                current_host_compatibility_tested=False, live_started=False,
                status='public-protocol-lead-found-native-binding-unproved')


def analyze():
    result = inspect_client(read_sources())
    # Regression only: retain the old full-prefix refusal, not new native evidence.
    pins = json.loads((HERE / 'historical-gate-pins.json').read_text())
    for name, digest in pins.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Historical gate input changed')
    spec = importlib.util.spec_from_file_location('r29_r05', HERE.parent / 'native-fight-r05/analyze.py')
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    live = HERE.parent / 'native-fight-r25'
    try:
        gate.validate_rows((live / 'run-01/tagged.log').read_bytes(), json.loads((live / 'build.json').read_text()))
    except ValueError as exc:
        result['historical_structural_refusal'] = str(exc)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--require-oracle', action='store_true')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    result = analyze()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])
    print(result.get('historical_structural_refusal', 'Full oracle remains unproved'))
    raise SystemExit(1)
