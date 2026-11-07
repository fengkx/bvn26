"""Recheck the bounded import association using a receipt-matching binary."""
import argparse
import json
from pathlib import Path
from extract_native import extract

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path)
    args = parser.parse_args()
    receipt = json.loads((HERE.parent / 's266/native-receipt.json').read_text())
    binary = args.binary or Path(receipt['engine'])
    actual = extract(binary.read_bytes())
    if actual != json.loads((HERE / 'native-route.json').read_text()):
        raise ValueError('Re-extracted import association differs')
    print('S358_REEXTRACT_MATCH; static import only, executed consumer unproved')


if __name__ == '__main__':
    main()
