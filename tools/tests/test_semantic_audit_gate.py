"""A partial AS audit must not advertise a successful acceptance exit."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'importer'))
from audit_importer import audit_exit_code, audit_xml


class SemanticAuditGateTests(unittest.TestCase):
    def test_incomplete_and_failed_scopes_reject(self):
        complete = {'status': 'passed', 'swfs': [{'failures': []}],
                    'shipped_contexts': [{'status': 'passed'}],
                    'visual_checks': [{'status': 'passed'}], 'source_scripts': [], 'skip_sites': []}
        self.assertEqual(audit_exit_code(complete), 0)
        for key, value in [('status', 'incomplete_semantic_audit'),
                           ('swfs', [{'failures': [{'source': 'a.swf/frame_1'}]}]),
                           ('visual_checks', [{'status': 'failed'}]),
                           ('shipped_contexts', [{'status': 'failed'}]),
                           ('source_scripts', [{'status': 'requires_complete_owner_review'}]),
                           ('skip_sites', [{'status': 'requires_review'}])]:
            result = deepcopy(complete)
            result[key] = value
            with self.subTest(scope=key):
                self.assertEqual(audit_exit_code(result), 1)

    def test_recognized_stop_does_not_hide_action_block(self):
        # ActionStop followed by ActionEnd: even a recognized control is not a
        # complete ownership certificate for its containing source scope.
        root = ET.fromstring('<swf><tags><item type="DoActionTag" actionBytes="0700"/></tags></swf>')
        result = audit_xml(root, 'fixture.swf')
        self.assertFalse(result['failures'])
        row, = result['nonvisual_action_blocks']
        self.assertEqual(row['source'], 'fixture.swf/root/frame_1')
        self.assertEqual(row['visual_control_count'], 1)
        self.assertEqual(row['status'], 'requires_complete_owner_review')


if __name__ == '__main__':
    unittest.main()
