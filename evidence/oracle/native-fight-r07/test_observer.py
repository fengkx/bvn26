import unittest
from pathlib import Path
from build_observer import patch_fighter, sources, DECISION, build, ROOT, HERE
from diagnose import diagnose


class CorrectionTests(unittest.TestCase):
    def test_selected_asset_matches_registry_not_display_name_guess(self):
        report=diagnose()
        self.assertEqual(report['source_selected_asset'],'game/fighter/yihu.swf')
        self.assertNotEqual(report['source_selected_asset'],report['r05_instrumented_asset'])
        self.assertEqual(report['copies']['game/fighter/yihu.swf']['original_sha256'],report['copies']['game/fighter/yihu.swf']['captured_copy_sha256'])

    def test_early_hp_unknowns_are_retained(self):
        report=diagnose()
        self.assertEqual(len(report['incomplete_boundaries']),10)
        self.assertEqual({u['field_index'] for b in report['incomplete_boundaries'] for u in b['unknown']},{5})
        self.assertFalse(report['oracle_accepted'])

    def test_lexical_forwarding_preserves_every_original_expression(self):
        original=sources('scripts/fighter/yihu.json')
        result,sites=patch_fighter(original)
        marker='\n_root.__m002Emit("decision-installed", "yihu-sprite16," + escape(this._target));\n'
        self.assertTrue(result.endswith(marker))
        restored=result[:-len(marker)]
        for site in sites:
            restored=restored.replace(f'_root.__m002FightKey(_parent,{site["argument"]},"{site["site"]}")',f'_parent.kis({site["argument"]})')
        self.assertEqual(restored,original[DECISION])
        self.assertEqual(len(sites),39)
        self.assertEqual((HERE/'observer.as').read_text().count('owner.kis(code)'),1)

    def test_wrong_fighter_and_inventory_drift_refused(self):
        with self.assertRaises(KeyError):patch_fighter(sources('scripts/fighter/ichigo.json'))
        source=sources('scripts/fighter/yihu.json');source[DECISION]=source[DECISION].replace('_parent.kis(', '_parent.other(',1)
        with self.assertRaises(ValueError):patch_fighter(source)

    def test_repository_output_refused(self):
        with self.assertRaisesRegex(ValueError,'temporary directory'):build(Path('/missing.jar'),ROOT/'bad-output','m002-r07-test')


if __name__=='__main__':unittest.main()
