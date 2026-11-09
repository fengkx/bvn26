"""Offline preparation has no live acceptance path."""
import argparse
import json

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle',action='store_true')
    parser.parse_args()
    print(json.dumps(dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False,refusal='r07 has no live capture; corrected asset/site and initial-state ordering remain unvalidated')))
    raise SystemExit(1)
