"""Combined-order and foreign-tag gates for root, side, and literal channels."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from analyze import HERE, validate_combined_bytes

R20 = HERE.parent / 'native-fight-r20'


class CombinedGateTests(unittest.TestCase):
  def setUp(self):
    self.tag = json.loads((R20 / 'build.json').read_text())['run_id']

  def fixture_bytes(self):
    pre = (R20 / 'run-01/flashlog.prelaunch.log').read_bytes()
    baseline = (R20 / 'run-01/flashlog.input-baseline.log').read_bytes()
    final = (R20 / 'run-01/flashlog.after.log').read_bytes()
    raw = (R20 / 'run-01/tagged.log').read_bytes()
    combined = (R20 / 'run-01/combined.log').read_bytes()
    return pre, baseline, final, combined, raw

  def test_historical_r20_log_passes_without_literal(self):
    validate_combined_bytes(*self.fixture_bytes(), self.tag)

  def test_literal_in_prelaunch_refused(self):
    pre, baseline, final, combined, raw = self.fixture_bytes()
    pre += b'M002LITERAL|' + self.tag.encode() + b'|doAllAction|before\n'
    with self.assertRaisesRegex(ValueError, 'not fresh'):
      validate_combined_bytes(pre, baseline, final, combined, raw, self.tag)

  def test_foreign_literal_refused(self):
    pre, baseline, final, combined, raw = self.fixture_bytes()
    combined = combined + b'M002LITERAL|foreign|doAllAction|after\n'
    final = combined
    with self.assertRaisesRegex(ValueError, 'Foreign literal'):
      validate_combined_bytes(pre, baseline, final, combined, raw, self.tag)

  def test_combined_reorder_refused(self):
    pre, baseline, final, combined, raw = self.fixture_bytes()
    combined = b'\n'.join(reversed(combined.splitlines())) + b'\n'
    with self.assertRaisesRegex(ValueError, 'Combined raw order'):
      validate_combined_bytes(pre, baseline, final, combined, raw, self.tag)


class FacilityTests(unittest.TestCase):
  def test_r20_session_refused_by_r22_analyzer(self):
    import analyze as module
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      for name in ['session.json', 'flashlog.prelaunch.log', 'flashlog.input-baseline.log',
                   'flashlog.after.log', 'tagged.log', 'combined.log']:
        shutil.copyfile(R20 / 'run-01' / name, directory / name)
      with self.assertRaisesRegex(ValueError, 'Build/session'):
        module.analyze(directory)


if __name__ == '__main__':
  unittest.main()
