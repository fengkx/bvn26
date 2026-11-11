"""Audit pinned client response semantics offline; never send protocol messages."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = 'modules/debugger/src/java/flash/tools/debugger/concrete/'
spec = importlib.util.spec_from_file_location('r31_pins', HERE.parent / 'native-fight-r29/analyze.py')
r29 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r29)


def read_counter(directory=HERE):
    row = json.loads((directory / 'source-receipts.json').read_text())['sources'][0]
    raw = gzip.decompress((directory / row['snapshot']).read_bytes())
    if hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('Counter source hash mismatch')
    return raw.decode('utf8')


def audit(sources, counter):
    player = sources[PREFIX + 'PlayerSession.java']
    manager = sources[PREFIX + 'DManager.java']
    response = player.split('boolean simpleRequestResponseMessage(DMessage msg, int msgType, int timeout)', 1)[1].split('// use default timeout', 1)[0]
    option = manager.split('case DMessage.InOption: {', 1)[1].split('break;', 1)[0]
    process = player.split('case DMessage.InProcessTag:', 1)[1].split('break;', 1)[0]
    checks = {
        'response_uses_type_isolate_count': all(x in response for x in [
            'long expect = num+1;', 'getMessageInCount(msgCounter, isolate, msgType) >= expect']),
        'counter_increments_type_slot': 'm_inCounts[type] += 1;' in counter,
        'option_cache_keys_name': 'm_options.put(s, v);' in option,
        'getter_reads_cached_name': 'optionValue = m_manager.getOption(optionName);' in player,
        'set_option_discards_response_boolean': 'simpleRequestResponseMessage(dm, DMessage.InOption);' in player.split('void sendOptionMessage(', 1)[1].split('\n\t}', 1)[0],
        'process_tag_automatically_replies': 'sendMessageIsolate(DMessage.OutProcessedTag, msg.getTargetIsolate());' in process,
    }
    if not all(checks.values()):
        raise ValueError('Reviewed response semantics changed')
    return dict(**r29.FLAGS, classification='producer-contract-unavailable-response-and-reset-qualification-refused',
                source_checks=checks, exact_producer_lifecycle_qualified=False,
                lifecycle_value_id_namespace_qualified=False, id_reuse_rules_qualified=False,
                effective_option_state_qualified=False, reset_semantics_qualified=False,
                behavior_preserving_connection_qualified=False,
                native_boundary=None, native_return_proven=False,
                m0_02_status='pending', live_started=False, connection_started=False,
                observed_response_mismatch=False,
                limitation='Client acceptance rules do not prove producer effects; no mismatch was observed.')


def analyze():
    result = audit(r29.read_sources(), read_counter())
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
