"""Replay a historical synthetic unit fixture against old and current validators.

Only Python unit-test code runs. No capture, player, compiler or debugger is used.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import types

ROOT = Path(__file__).resolve().parents[3]
BASE = 'af538c7aafc1fa0114440c0a80c0b077c316fa4a'
TOOL = 'tools/probes/validate_ai_continuous_replay.py'
TEST = 'tools/tests/test_ai_continuous_replay.py'


def retained(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT).decode()


def exercise(validate, fixture, matching_invalid_vector=False):
    observed = {}

    class Captured(Exception):
        pass

    def checked(*args):
        if matching_invalid_vector:
            path = args[1]
            data = json.loads(path.read_text())
            data['random_original_indices'] = [1, 2, 3]
            data['random_consumed'].insert(0, {'site': 'main#music', 'value': 0.0})
            data['native_checkpoint']['random_absolute_index'] = 2
            path.write_text(json.dumps(data))
        report = validate(*args)
        observed.update(overall_status=report['status'], first_reason=report['first_reason'],
                        random_consumers=report['checks']['random_consumers'])
        # Stop after exercising the fixture; its old assertions assume the unmutated vector.
        raise Captured

    scope = {'validate': checked, '__name__': 'synthetic_regression'}
    exec(compile(fixture.replace('from tools.probes.validate_ai_continuous_replay import validate', ''), TEST, 'exec'), scope)
    case = scope['ContinuousReplayValidationTests']()
    try:
        case.test_nonzero_source_random_index_maps_local_cursor_and_value()
    except Captured:
        pass
    except ValueError as exc:
        observed.update(rejected=True, reason=str(exc))
    return observed


def main():
    old_source, fixture = retained(TOOL), retained(TEST)
    old = types.ModuleType('baseline_validator')
    exec(compile(old_source, TOOL, 'exec'), old.__dict__)
    # Import as a package so the existing numeric decoder is reused unchanged.
    import sys
    sys.path.insert(0, str(ROOT))
    from tools.probes.validate_ai_continuous_replay import validate
    return {'kind': 'synthetic-offline-regression-not-native-proof', 'base': BASE,
            'baseline_tool_sha256': hashlib.sha256(old_source.encode()).hexdigest(),
            'baseline_test_sha256': hashlib.sha256(fixture.encode()).hexdigest(),
            'fixture_defects': ['no loaded intro poll', 'duplicate terminal sequence',
                                'Math.random values 1.5 and -1.5'],
            'original_fixture_before': exercise(old.validate, fixture),
            'matching_invalid_vector_before': exercise(old.validate, fixture, True),
            'matching_invalid_vector_after': exercise(validate, fixture, True)}


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
