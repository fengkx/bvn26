"""Protect evidence classification, not hypothetical Flash allocation behavior."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s325', HERE / 'diagnose.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.table = json.loads((HERE / 'native-symbol-table.json').read_text())
        self.symbols = (HERE / 'native-symbols.txt').read_text()
        self.commands = (HERE / 'native-load-commands.txt').read_text()
        self.facility = json.loads((HERE / 'native-inventory.json').read_text())

    def audit(self):
        return m.audit_inventory(self.table, self.symbols, self.commands, self.facility)

    def test_inventory_is_not_layout(self):
        r = self.audit()
        self.assertEqual((r['symbol_table_entries'], r['nm_visible_entries'], r['undefined_symbol_count']), (1039, 1038, 1032))
        self.assertEqual(len(r['defined_symbols']), 6)
        self.assertEqual(r['debug_entries_omitted_by_nm'][0]['name'], 'radr://5614542')
        self.assertIsNone(r['independent_slot_layout'])
        self.assertIsNone(r['independent_reference_layout'])
        self.assertIsNone(r['pool_generation_coverage'])

    def test_missing_entry(self):
        self.table['symbol_table']['entries'].pop()
        with self.assertRaises(ValueError): self.audit()

    def test_reordered_entry(self):
        self.table['symbol_table']['entries'].reverse()
        with self.assertRaises(ValueError): self.audit()

    def test_changed_bytes(self):
        self.table['symbol_table']['entries'][1]['n_value'] += 1
        with self.assertRaises(ValueError): self.audit()

    def test_import_is_not_definition(self):
        self.symbols = self.symbols.replace('(undefined)', '(__TEXT,__text)', 1)
        with self.assertRaises(ValueError): self.audit()

    def test_live_claim_rejected(self):
        for key in ['live_module_binding', 'object_layout']:
            with self.subTest(key=key):
                t = copy.deepcopy(self.table)
                t[key] = {'address': 1}
                with self.assertRaises(ValueError):
                    m.audit_inventory(t, self.symbols, self.commands, self.facility)

    def test_cross_binary_rejected(self):
        self.facility['binary_sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.audit()

    def test_full_replay_keeps_gates_closed(self):
        r = m.diagnose()
        self.assertTrue(r['locked_s316_reproduced'])
        for k in ['production_admitted', 'native_parity_proven', 'slot_reference_proved', 'content_clearing_proved', 'replacement_proved', 'allocation_identity_proved']:
            self.assertIs(r[k], False)
        self.assertEqual(r['rank_9_status'], 'planning')


if __name__ == '__main__':
    unittest.main()
