import ast
import json
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from pathlib import Path
from tools.probes.probe_owned_hardware_entry import ENTRY, ENTRY_BYTES, RUNTIME, script_for_edges


class HardwareEntryTests(unittest.TestCase):
    def test_denied_attach_writes_closed_receipt_without_operand_reads(self):
        error = SimpleNamespace(Success=lambda: False)
        target = SimpleNamespace(AttachToProcessWithID=lambda listener, pid, err: None)
        fake = SimpleNamespace(SBError=lambda: error, debugger=SimpleNamespace(
            CreateTarget=lambda path: target, GetListener=lambda: None))
        factory = script_for_edges([{'return_pc':'0x1000f28e0','target':hex(ENTRY)}])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'result.json'
            with patch.dict('sys.modules', {'lldb':fake}):
                exec(factory(123,Path('/fixture/player'),path),{})
            result = json.loads(path.read_text())
            self.assertFalse(result['attached'])
            self.assertFalse(result['hardware_entry_verified'])
            self.assertNotIn('input_matrix_bytes',result)
            self.assertIsNone(result['detached'])

    def test_cleanup_exceptions_do_not_skip_other_ids_or_detach(self):
        tree = ast.parse(RUNTIME)
        final = next(node.finalbody for node in tree.body if isinstance(node,ast.Try))
        detached = []
        deleted = []
        def delete(identifier):
            deleted.append(identifier)
            if identifier == 1:
                raise RuntimeError('deletion failed')
            return True
        def stop():
            raise RuntimeError('stop failed')
        error = SimpleNamespace(Success=lambda: True)
        process = SimpleNamespace(GetState=lambda: 6,Stop=stop,
            Detach=lambda: detached.append(True) or error)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'result.json'
            namespace = {'result':{'attached':True},'created_ids':[1,2],
                'target':SimpleNamespace(BreakpointDelete=delete),'process':process,
                'lldb':SimpleNamespace(eStateRunning=6),'Path':Path,'RESULT':str(path),'json':json}
            exec(compile(ast.Module(body=final,type_ignores=[]),'cleanup','exec'),namespace)
            result = json.loads(path.read_text())
        self.assertEqual(deleted,[1,2])
        self.assertEqual(detached,[True])
        self.assertTrue(result['detached'])
        self.assertIn('cleanup_stop_error',result)

    def test_only_verified_compose_edges_are_embedded(self):
        edges = [{'return_pc':'0x1000f28e0','target':hex(ENTRY),'site':'0x1000f28db'},
                 {'return_pc':'0x10015e7a7','target':'0x10029de20'}]
        script = script_for_edges(edges)(123,Path('/exact/player'),Path('/fresh/result.json'))
        tree = ast.parse(script)
        returns = next(node for node in tree.body if isinstance(node,ast.Assign)
                       and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='RETURNS')
        self.assertEqual(set(ast.literal_eval(returns.value)),{0x1000f28e0})
        with self.assertRaises(ValueError):
            script_for_edges(edges[1:])

    def test_fixed_entry_and_bounded_abi_reads(self):
        self.assertEqual(len(bytes.fromhex(ENTRY_BYTES)),16)
        self.assertTrue(ENTRY_BYTES.startswith('554889e5'))
        self.assertIn("if size not in (8, 16, 28)",RUNTIME)
        self.assertIn("read(regs[name],28)",RUNTIME)
        self.assertNotIn("read(regs['rdx']",RUNTIME)
        self.assertLess(RUNTIME.index("result['hardware_entry_verified'] = True"),
                        RUNTIME.index("result['input_matrix_bytes']"))

    def test_hardware_only_and_truthful_cleanup(self):
        self.assertIn('breakpoint set --hardware --address ',RUNTIME)
        self.assertIn('not bp.IsHardware()',RUNTIME)
        self.assertIn('process.GetStopID() != prior_stop',RUNTIME)
        self.assertIn('frame.GetPC() != load',RUNTIME)
        self.assertIn('time.monotonic()+5',RUNTIME)
        self.assertIn('finally:',RUNTIME)
        self.assertIn('target.BreakpointDelete(breakpoint_id)',RUNTIME)
        self.assertIn('process.Detach()',RUNTIME)
        self.assertIn("['physical_entry_bytes_independently_verified'] = False",RUNTIME)
        for forbidden in ('WriteMemory','EvaluateExpression','BreakpointCreateByAddress','watchpoint'):
            self.assertNotIn(forbidden,RUNTIME)
