import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from tools.probes.monitor_owned_native import monitor_owned


class NativeMonitorTests(unittest.TestCase):
    def run_monitor(self, owners):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder); log=path/'log';log.write_text('AIREF|owned-run|1|0|0|0|profile|fixture\n')
            completed=SimpleNamespace(returncode=0,stdout='123 R fixture',stderr='')
            with patch('tools.probes.monitor_owned_native.LOG',log), \
                 patch('tools.probes.monitor_owned_native.matching_players',side_effect=owners), \
                 patch('tools.probes.monitor_owned_native.subprocess.run',return_value=completed) as run:
                result=monitor_owned(123,path/'movie',path/'binary','owned-run',path)
                return result,[item.args[0] for item in run.call_args_list]

    def test_exact_owner_gets_one_bounded_sample(self):
        result,commands=self.run_monitor([{123},{123},{123}])
        self.assertTrue(result['sample_requested'])
        samples=[c for c in commands if c[0]=='/usr/bin/sample']
        self.assertEqual(len(samples),1)
        self.assertEqual(samples[0][1:4],['123','1','1'])
        self.assertEqual(len(result['observations']),3)

    def test_absent_or_changed_owner_is_never_sampled(self):
        for owners in ([set()],[{123},{124}],[{123},{123,124}]):
            result,commands=self.run_monitor(owners)
            self.assertFalse(result['sample_requested'])
            self.assertFalse(any(c[0]=='/usr/bin/sample' for c in commands))

class DetachTimingTests(unittest.TestCase):
    def test_instrumentation_only_brackets_the_existing_detach(self):
        import ast
        from tools.probes.probe_owned_source_monitor import timed_factory
        source="import time\nresult={}\nerror=process.Detach()\nresult['detached']=error.Success()\n"
        output=timed_factory(lambda *args:source)(1,Path('/binary'),Path('/result'))
        tree=ast.parse(output)
        self.assertEqual(len([n for n in ast.walk(tree) if isinstance(n,ast.Call)
                              and isinstance(n.func,ast.Attribute) and n.func.attr=='Detach']),1)
        self.assertLess(output.index('detach_call_start_monotonic'),output.index('process.Detach()'))
        self.assertLess(output.index('process.Detach()'),output.index('detach_call_end_monotonic'))
        with self.assertRaises(ValueError):timed_factory(lambda *args:'pass')(1,None,None)
