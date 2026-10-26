import unittest
import json
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from tools.probes.probe_owned_debugger import require_unique_owned, debugger_script, probe, validate_debugger_timeout


class OwnedDebuggerTests(unittest.TestCase):
    def test_timeout_is_bounded(self):
        self.assertEqual(validate_debugger_timeout(45),45)
        for value in (0,-1,46,float('inf')):
            with self.assertRaises(ValueError):validate_debugger_timeout(value)

    def test_stale_output_rejected_before_native_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'output';output.mkdir();(output/'debugger-result.json').write_text('{}')
            with patch('tools.probes.probe_owned_debugger.preflight') as preflight:
                with self.assertRaises(ValueError):
                    probe(Path(folder)/'build', output, Path(folder)/'player')
                preflight.assert_not_called()

    def test_exact_unique_fresh_owner_required(self):
        self.assertEqual(require_unique_owned(set(),{123},123),123)
        for before,current,expected in (({123},{123},123),(set(),{123,124},123),(set(),{124},123),(set(),set(),123)):
            with self.assertRaises(RuntimeError):require_unique_owned(before,current,expected)

    def test_generated_script_writes_valid_json_for_denied_attach(self):
        error = SimpleNamespace(Success=lambda: False)
        target = SimpleNamespace(AttachToProcessWithID=lambda listener, pid, err: None)
        fake = SimpleNamespace(SBError=lambda: error, debugger=SimpleNamespace(CreateTarget=lambda path: target, GetListener=lambda: None))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'result.json'
            with patch.dict('sys.modules', {'lldb': fake}):
                exec(debugger_script(123, Path('/fixture/player'), path), {})
            result = json.loads(path.read_text())
            self.assertFalse(result['attached'])
            self.assertFalse(result['detach_attempted'])
            self.assertTrue(path.read_bytes().endswith(bytes([10])))

    def test_generated_script_detaches_after_successful_register_read(self):
        detached = []
        error = SimpleNamespace(Success=lambda: True)
        frame = SimpleNamespace(FindRegister=lambda name: SimpleNamespace(GetValue=lambda: '0x1'))
        process = SimpleNamespace(IsValid=lambda: True, GetState=lambda: 5, GetSelectedThread=lambda: SimpleNamespace(GetFrameAtIndex=lambda i: frame), Detach=lambda: detached.append(True) or error)
        target = SimpleNamespace(AttachToProcessWithID=lambda listener, pid, err: process, GetTriple=lambda: 'x86_64-apple-macosx')
        fake = SimpleNamespace(SBError=lambda: error, debugger=SimpleNamespace(CreateTarget=lambda path: target, GetListener=lambda: None), SBDebugger=SimpleNamespace(StateAsCString=lambda state: 'stopped'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'result.json'
            with patch.dict('sys.modules', {'lldb': fake}):
                exec(debugger_script(123, Path('/fixture/player'), path), {})
            result = json.loads(path.read_text())
            self.assertTrue(result['attached'] and result['registers_available'] and result['detached'])
            self.assertEqual(detached, [True])

    def test_detach_in_finally_no_breakpoint_or_target_expression(self):
        script=debugger_script(123,Path('/fixture/player'),Path('/fixture/result.json'))
        compile(script,'fixture','exec')
        self.assertIn('finally:',script)
        self.assertIn('process.Detach()',script)
        self.assertNotIn('BreakpointCreate',script)
        self.assertNotIn('EvaluateExpression',script)
        self.assertNotIn('WriteMemory',script)


if __name__ == '__main__':unittest.main()
