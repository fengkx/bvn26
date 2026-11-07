"""Extract only the six s311 edge targets; no process launch or memory read."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
REGIONS = {
    'stack_join': (0x1264b9, 0x12657c),
    'stack_call_frontier': (0x12696b, 0x12698d),
    'carrier_lookup': (0x98b8e0, 0x98ba8c),
    'carrier_store': (0x12f580, 0x12f708),
}


def main():
    start = time.monotonic()
    spec = importlib.util.spec_from_file_location('s320_macho', HERE.parent / 's303/audit_native.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    locked = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    raw = Path(locked['binary']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != locked['binary_sha256']:
        raise ValueError('binary does not match locked s303 receipt')
    module = prior.macho(raw)
    if module != locked['module']:
        raise ValueError('module metadata changed')
    regions = {}
    for name, (begin, end) in REGIONS.items():
        offset = prior.file_offset(module, locked['image_base'] + begin, end - begin)
        data = raw[offset:offset + end - begin]
        command = ['objdump', '-d', '--x86-asm-syntax=intel',
                   '--start-address=' + hex(locked['image_base'] + begin),
                   '--stop-address=' + hex(locked['image_base'] + end), locked['binary']]
        tick = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=60, check=True)
        log = name + '.txt'
        (HERE / log).write_bytes(result.stdout + result.stderr)
        regions[name] = dict(module_relative=begin, file_offset=offset, size=len(data),
                             hex=data.hex(), sha256=prior.sha(data), disassembly=log,
                             disassembly_sha256=prior.sha(result.stdout + result.stderr),
                             command=command, exit_code=result.returncode,
                             wall_seconds=time.monotonic() - tick)
    report = dict(binary=locked['binary'], binary_sha256=locked['binary_sha256'],
                  binary_size=len(raw), module_uuid=module['uuid'], image_base=locked['image_base'],
                  regions=regions, elapsed_seconds=time.monotonic() - start,
                  player_launches=0, memory_reads=0,
                  limit='Static file bytes only; call fallthrough is conditional on machine return. No live binding.')
    (HERE / 'native-audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
