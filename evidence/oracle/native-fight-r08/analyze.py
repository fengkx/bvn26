"""No live receipt or existing onLoadInit proof is available in this preparation."""
import argparse
import json

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-oracle',action='store_true')
    parser.parse_args()
    print(json.dumps(dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False,refusal='No r08 live capture; no existing source onLoadInit; onLoadComplete is not initialization completion')))
    raise SystemExit(1)
