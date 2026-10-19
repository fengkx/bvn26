"""Verify retained recovery proof and unchanged Flash references without running engines."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from test_prep_counter_super import AUDIT, DEVIATIONS, compare, recovery, source_rows


def main():
    report = json.loads((HERE / 'results.json').read_text())
    assert len(report['results']) == 44
    matched = deviated = additional = 0
    for result in report['results']:
        name = result['id']
        fixture = ROOT / result['fixture']
        assert hashlib.sha256(fixture.read_bytes()).hexdigest() == result['fixture_sha256']
        native = HERE / 'traces' / (name + '.json.gz')
        raw = gzip.decompress(native.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == result['native_sha256']
        data = json.loads(fixture.read_text())
        if 'original_sha256' in result:
            source = AUDIT / 'traces' / (name + '.original.jsonl.gz')
            assert hashlib.sha256(gzip.decompress(source.read_bytes())).hexdigest() == result['original_sha256']
            comparison = compare(source, native)
            assert comparison['complete'] and comparison['source_states'] == 482
            if name in DEVIATIONS:
                assert comparison['differences'][0]['tick'] == 38
                assert all(row['paused'] for row in source_rows(source) if row['tick'] >= 25)
                deviated += 1
            else:
                assert comparison['status'] == 'matched', name
                matched += 1
        else:
            additional += 1
        if result['expectation'] == 'intentional_flash_deviation_recovery':
            assert recovery(json.loads(raw), data['slot']) == result['recovery']
    assert (matched, deviated, additional) == (38, 2, 4)
    print('RETAINED_PREP_RECOVERY_OK parity=38 deviations=2 additional=4')


if __name__ == '__main__':
    main()
