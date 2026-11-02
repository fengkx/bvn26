"""Recompute s279's bounded facility gap without inventing native identity."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def verify_pins(root, pins):
    for name, expected in pins.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed evidence: ' + name)


def diagnose():
    verify_pins(ROOT, json.loads((HERE / 'input-sha256.json').read_text()))
    spec = importlib.util.spec_from_file_location('s267_diagnose', HERE.parent / 's267/diagnose.py')
    prior_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior_module)
    prior = prior_module.diagnose()
    facility = json.loads((HERE / 'facility/audit.json').read_text())
    verify_pins(HERE / 'facility', {c['log']: c['sha256'] for c in facility['checks'].values()})
    imports = json.loads((HERE / 'allocator-import-pins.json').read_text())
    return {
        'scope': 'AFTER-s272 rank 7 only', 'base': 'd49485dd63c34524e1d1e04220f7733870f12f01',
        'production_admitted': False, 'native_parity_proven': False,
        'mapping_fix_proved': False, 'product_obligations_closed': 0,
        'status': 'unproved_slot_saved_reference_and_generation_facility',
        'retained_capture': prior['retained_capture'],
        'allocation_observability': prior['allocation_observability'],
        'facility': {
            'binary_sha256': facility['binary_sha256'],
            'module_uuid_hex': imports['module_uuid_hex'],
            'allocator_import_stubs_byte_pinned': 4,
            'slot_resolver': None, 'saved_reference_resolver': None,
            'native_object_layout': None, 'allocation_free_ledger': None,
            'retained_content_clear_qualified': False, 'same_depth_replacement_qualified': False,
            'allocation_events_observed': 0, 'new_captures': 0,
            'absence_of_possible_resolver_proved': False,
        },
        'next_discriminator': [
            'Derive native parent/depth lookup and saved AS2 reference dereference independently on the pinned module; retain relative addresses, instruction bytes, layout and live provenance. Import stubs do not resolve either.',
            'Establish object allocation/destruction and pool reuse coverage before control creation. System malloc/free alone may miss pooled object lifetimes. Track allocation generations, not pointer equality.',
            'Qualify the same resolver/ledger on actual retained-content clearing and same-name/depth replacement. Record independent retention/free/reuse evidence and saved-reference referents; deleting a property is insufficient.',
            'Only then capture the unchanged s261 tape at source-equivalent last-nonzero/first-zero boundaries with complete lifecycle ordering. Preserve actual roots and all events; no numeric-root assumption, alias or unloaded exemption.'
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-allocation-identity', action='store_true')
    args = parser.parse_args()
    report = diagnose()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    if args.require_allocation_identity:
        print('ALLOCATION_IDENTITY_UNPROVED: slot/saved-reference resolver and both native generation controls missing')
        return 1
    print('DIAGNOSIS_RECOMPUTED: import bytes pinned; native identity unproved')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
