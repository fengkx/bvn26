import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'tools/probes/{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ComponentRasterInputsTests(unittest.TestCase):
    def test_input_inventory_preserves_authored_transforms_and_source_identity(self):
        builder = module('build_filter_components')
        authored = builder.inventory()
        isolated = builder.inventory(raster_input_only=True)
        self.assertEqual(len(authored), 21)
        for original, probe in zip(authored, isolated):
            self.assertTrue(probe.pop('raster_input_only'))
            placement = probe.pop('placement')
            expected = original.pop('placement')
            self.assertEqual(probe, original)
            self.assertEqual(placement, {k: v for k, v in expected.items()
                                       if k not in ('filters', 'cache_as_bitmap')})

    def test_native_removal_must_be_observed_once_for_every_case(self):
        compare = module('compare_filter_components')
        case = {'id': 'component', 'raster_input_only': True, 'placement': {'depth': 1}}
        valid = 'AIREF|run|0|0|0|0|raster_input|component,0,false\n'
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            trace = folder / 'native.log'
            trace.write_text(valid)
            compare.validate_raster_inputs(folder, [case])
            for invalid in ('', valid + valid, valid.replace(',0,false', ',1,true'),
                            valid.replace('component,', 'wrong,'),
                            valid + 'AIREF|run|1|0|0|0|input_error|component\n'):
                trace.write_text(invalid)
                with self.assertRaises(ValueError):
                    compare.validate_raster_inputs(folder, [case])
            trace.write_text(valid)
            case['placement']['filters'] = []
            with self.assertRaises(ValueError):
                compare.validate_raster_inputs(folder, [case])


if __name__ == '__main__':
    unittest.main()
