import unittest
from tools.probes import run_jinye_wrapper_cpu as original
from tools.probes.run_jinye_static_wrapper import MODEL,partition

class StaticWrapperTests(unittest.TestCase):
    def test_optional_provider_keeps_default_identity(self):
        import inspect
        self.assertIsNone(inspect.signature(original.render_leaf).parameters['row_builder'].default)
        self.assertIsNone(inspect.signature(original.run).parameters['row_builder'].default)

    def test_partition_keeps_outside_failures(self):
        result=partition({'samples':4,'exact':3,'failures':[{'x':1,'y':1}]},({(0,0)},set()),(2,2))
        self.assertEqual(result['outside'],{'samples':3,'exact':2,'failures':1})

if __name__=='__main__':unittest.main()
