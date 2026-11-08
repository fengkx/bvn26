"""Inspect one disk instruction at a time, stopping at the first control transfer."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def discover():
    receipt = json.loads((HERE.parent / 's303/native-audit.json').read_text())
    binary = Path(receipt['binary'])
    if hashlib.sha256(binary.read_bytes()).hexdigest() != receipt['binary_sha256']:
        raise ValueError('Player custody differs')
    tool = Path(shutil.which('lldb')).resolve()
    commands, logs = [], []
    address = 0x1000d227d
    while address < 0x1000d227d + 64:
        command = [str(tool), '--batch', '-o', f'target create --no-dependents "{binary}"',
                   '-o', f'disassemble --start-address {address:#x} --count 1 --bytes']
        start = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        commands.append(dict(command=command, exit_code=result.returncode,
                             wall_seconds=time.monotonic() - start))
        logs.append(result.stdout + result.stderr)
        matches = re.findall(r'0x([0-9a-f]+)\]? <[^>]*>:\s+((?:[0-9a-f]{2} )+)\s+(\w+)\s*(.*)', result.stdout)
        rows = [row for row in matches if int(row[0], 16) == address]
        if len(rows) != 1:
            raise ValueError('Instruction parsing failed: ' + result.stdout)
        _, encoded, mnemonic, operands = rows[0]
        address += len(bytes.fromhex(encoded))
        if mnemonic.startswith('j') or mnemonic.startswith('ret') or mnemonic.startswith('call'):
            break
    else:
        raise ValueError('64-byte frontier reached without a control transfer')
    (HERE / 'selected-disassembly.txt').write_text('\n'.join(logs))
    record = dict(tool_path=str(tool), tool_sha256=hashlib.sha256(tool.read_bytes()).hexdigest(),
                  version=subprocess.check_output([str(tool), '--version'], text=True),
                  commands=commands, start=0xd227d, end_exclusive=address - 0x100000000,
                  purpose='Disk-only one-instruction requests; stop at first control transfer; no launch or attach')
    (HERE / 'disassembly-receipt.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    discover()
