import copy
import gzip
import tempfile
import json
from pathlib import Path
import unittest

from tools.probes.helper_init_observer import SITES, analyze, configuration, instrument

ROOT = Path(__file__).resolve().parents[2]


def fixture():
    rows = []
    for slot, asset, selection in [("p1", "woailuo", "我爱罗"), ("p2", "kon", "魂")]:
        url = "file:///fixture/" + asset + ".swf"
        target = "/game/" + slot + "fz"
        rows.extend([
            {"kind": "helper_init_request", "value": f"{slot},{selection},{url},{target}"},
            {"kind": "helper_init_load_complete", "value": f"{slot},{target},{url}"},
            {"kind": "helper_init_frame_tail", "value": f"{slot},{asset},{target},{url},1,true,false"}])
    rows.append({"kind": "ready", "value": ""})
    return numbered(rows)


def numbered(rows):
    return [dict(row, sequence=i, run_id="synthetic") for i, row in enumerate(rows, 1)]


class HelperInitTests(unittest.TestCase):
    def setUp(self):
        self.config = configuration("我爱罗", "魂")
        self.rows = fixture()

    def check_refused(self, rows, config=None):
        result = analyze(rows, self.config if config is None else config, "synthetic")
        self.assertEqual(result["status"], "refused")
        self.assertFalse(result["source_frame_initialization_observed"])
        self.assertFalse(result["oracle_accepted"])

    def test_explicit_selection_required(self):
        for pair in [(None, None), ("我爱罗", None), ("魂", "我爱罗")]:
            with self.assertRaises(ValueError):
                configuration(*pair)
        self.assertEqual(configuration("woailuo", "kon"), self.config)

    def test_builder_rejects_implicit_config_before_output(self):
        from tools.probes.build_ai_reference import build
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "must-not-exist"
            with self.assertRaises(ValueError):
                build(Path(directory) / "unused.jar", output, "synthetic", 600,
                      helper_init_observer=True)
            self.assertFalse(output.exists())

    def test_source_anchors_and_call_preservation(self):
        for (bundle, path) in SITES:
            data = json.loads((ROOT / f"scripts/{bundle}.json").read_text())
            source = next(s["source"] for s in data["scripts"] if s["path"] == path)
            patched = instrument(source, source, bundle, path)
            self.assertEqual(source.count("loadClip("), patched.count("loadClip("))
            self.assertEqual(source.count("stop();"), patched.count("stop();"))
            self.assertEqual(source.count("loadSteps[loadStep]();"), patched.count("loadSteps[loadStep]();"))
            if bundle != "main":
                self.assertTrue(patched.startswith(source))
                self.assertIn('"helper_init_frame_tail"', patched[len(source):])
            else:
                self.assertLess(patched.index('"helper_init_request"'), patched.index('_this._loader.loadClip(_root.fzDir'))
                self.assertIn('target === _root.game.p1fz', patched)
            with self.assertRaises(ValueError):
                instrument(source + " ", source, bundle, path)
            with self.assertRaises(ValueError):
                instrument(source, patched, bundle, path)
        self.assertEqual(instrument("unchanged", "unchanged", "main", "unrelated"), "unchanged")

    def test_complete_synthetic_chain_is_scoped_not_admitted(self):
        result = analyze(self.rows, self.config, "synthetic")
        self.assertTrue(result["source_frame_initialization_observed"])
        reordered = copy.deepcopy(self.config)
        reordered["columns"] = dict(reversed(list(reordered["columns"].items())))
        self.assertEqual(analyze(self.rows, reordered, "synthetic"), result)
        for flag in ["native_initialization_complete", "production_admitted", "native_parity_proven",
                     "oracle_accepted", "certified_global_tick", "os_input_join_proven"]:
            self.assertIs(result[flag], False)

    def test_missing_each_stage_refuses(self):
        for i in range(6):
            self.check_refused(numbered(self.rows[:i] + self.rows[i+1:]))

    def test_duplicate_or_reload_refuses(self):
        self.check_refused(numbered(self.rows[:1] + self.rows))
        self.check_refused(numbered(self.rows[:6] + self.rows[:3] + self.rows[6:]))

    def test_order_and_ready_cutoff_refuse(self):
        rows = copy.deepcopy(self.rows)
        rows[1], rows[2] = rows[2], rows[1]
        self.check_refused(numbered(rows))
        self.check_refused(numbered(self.rows[:2] + self.rows[6:] + self.rows[2:6]))

    def test_identity_and_state_changes_refuse(self):
        for i, old, new in [(0,"我爱罗","魂"), (1,"woailuo.swf","kon.swf"),
                            (2,"/game/p1fz","/game/p2fz"), (2,",1,true,false",",2,true,false"),
                            (2,",1,true,false",",1,undefined,false")]:
            rows = copy.deepcopy(self.rows)
            rows[i]["value"] = rows[i]["value"].replace(old, new)
            self.check_refused(rows)

    def test_foreign_and_gap_refuse(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["run_id"] = "foreign"
        self.check_refused(rows)
        self.check_refused(self.rows[1:])
        self.check_refused(self.rows, {})

    def test_historical_r13_is_not_backfilled(self):
        path = ROOT / "evidence/ai/input-binary-r13"
        rows = [json.loads(line) for line in (path / "events.jsonl").read_text().splitlines()]
        result = analyze(rows, self.config, "input-binary-r13")
        self.assertEqual(result["reason"], "incomplete_helper_initialization")
        self.assertFalse(result["oracle_accepted"])

    def test_new_observer_is_not_clean_full_acceptance(self):
        from tools.probes.validate_ai_continuous_replay import validate
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            replay = directory / "replay.json"
            replay.write_bytes(gzip.decompress((ROOT / "evidence/oracle/replay-ready-report/replay.json.gz").read_bytes()))
            build = directory / "synthetic-build.json"
            # Isolate the new intervention flag; this is not a source receipt.
            build.write_text(json.dumps({"frames_after_ready": 600, "configuration": {"p2cpu": True},
                                         "helper_init_observer": self.config}))
            result = validate(ROOT / "evidence/ai/input-binary-r13/events.jsonl", replay, 600, build)
            self.assertEqual(result["source_build_provenance"]["intervention_flags"], ["helper_init_observer"])
            self.assertEqual(result["first_reason"], "source_build_provenance_not_clean")
            self.assertEqual(result["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
