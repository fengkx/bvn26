"""Bound witness feasibility from locked source and retained capabilities only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('r27_prior', HERE.parent / 'native-fight-r26/analyze.py')
r26 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r26)
FLAGS = r26.FLAGS


def source_inventory(bundle):
    """Lexical exported-source scope, not proof about every dynamic handler."""
    callbacks, unload_calls = [], []
    for row in bundle['scripts']:
        if 'onUnload' in row['source'] or 'onClipEvent(unload)' in row['source'] or 'onClipEvent(unload)' in row['path']:
            callbacks.append(row['path'])
        calls = [line.strip() for line in row['source'].splitlines()
                 if re.search(r'\b(?:removeMovieClip|unloadMovie|unloadMovieNum)\s*\(', line)]
        if calls:
            unload_calls.append(dict(path=row['path'], calls=calls))
    return dict(scope='lexical exported paths/source only', unload_callbacks=callbacks,
                explicit_calls=unload_calls)


def assess(inventories, attach, hardware, memory):
    return dict(**FLAGS, status='not-ready-from-available-evidence',
                global_impossibility_proven=False, new_live=False, new_observer=False,
                native_return_proven=False, removal_edge_proven=False,
                inherited_classification='body-target-observed-dispatch-identity-unjoined',
                source_inventories=inventories,
                historical_capabilities=dict(
                    owned_attach_registers_detach=bool(attach['debugger']['attached'] and
                        attach['debugger']['registers_available'] and attach['debugger']['detached']),
                    generic_hardware_entry=hardware['hardware_entry_verified'],
                    independent_guest_read=memory['guest_entry_before']['guest_virtual_read_verified'],
                    historical_task_for_pid_return=memory['guest_entry_before']['task_for_pid_return'],
                    current_permission_state='not tested',
                    per_instance_dispatch_binding_proven=False),
                candidates=[
                    dict(route='existing-source-unload-callback', ready=False,
                         missing='No lexical callback in locked main/yihu exports; no existing target helper callback to wrap.'),
                    dict(route='new-unload-callback', ready=False,
                         missing='Documented event encoding is not qualified native removal/interrupt identity; adding a callback changes the observed event path and requires independent binding/noninterference.'),
                    dict(route='parent-depth-token-or-polling', ready=False,
                         missing='Source placement tokens/readbacks cannot supply a native destruction or dispatch edge; path/depth reuse and missing samples remain.'),
                    dict(route='owned-native-debugger', ready=False,
                         missing='Historical generic stops have no verified helper owner/generation/activation schema or removal/dispatch entry/outcome binding; current permissions and preservation untested.')])


def replay():
    for name, digest in json.loads((HERE / 'input-pins.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned input changed: ' + name)
    def read(name):
        return json.loads((ROOT / name).read_text())
    inventories = {name: source_inventory(read(name)) for name in ['scripts/main.json', 'scripts/fighter/yihu.json']}
    result = assess(inventories,
                    read('evidence/importer-loud-fail/r244/retry/debugger/feasibility.json'),
                    read('evidence/importer-loud-fail/r245/debugger/debugger-result.json'),
                    read('evidence/importer-loud-fail/r246/debugger/debugger-result.json'))
    prior = r26.replay()
    result['r25_identity_refusal'] = prior['targets']
    result['structural_refusal'] = prior['structural_refusal']
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = replay()
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(result['status'])
    print(result['structural_refusal'])
    raise SystemExit(1)
