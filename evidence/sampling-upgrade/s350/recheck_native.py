"""Re-extract the route from any receipt-matching player without host-path identity."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
RECEIPT = HERE.parent / 's346/native-route.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path)
    args = parser.parse_args()
    # The historical receipt supplies only a local default, never identity.
    binary = args.binary
    if binary is None:
        receipt = json.loads(RECEIPT.read_text())
        binary = Path(receipt['regions']['dispatch_arm']['command'][-1])
    with tempfile.TemporaryDirectory(prefix='s350-native-') as tmp:
        subprocess.run([sys.executable, str(HERE / 'extract_native.py'), str(binary),
                        '--output-dir', tmp], check=True, timeout=60)
        expected = json.loads((HERE / 'native-route.json').read_text())
        actual = json.loads((Path(tmp) / 'native-route.json').read_text())
        if actual != expected:
            raise ValueError('Re-extracted route or disassembler output differs')
    print('S350_REEXTRACT_MATCH; disk bytes only, no live callback proof')


if __name__ == '__main__':
    main()
