"""Synthetic preflight recipe tests; never execute Godot."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analyze_diagnostics as diagnostics


class RecipePlayerTests(unittest.TestCase):
    def test_list_identity_must_survive_without_discarding_rows(self):
        digest = 'a' * 64
        players = [dict(slot=slot, fighter='fixture', resourcePath='res://generated/fighters/fixture')
                   for slot in ('p1', 'p2')]
        match = dict(mode=3, modeName='versus', p1cpu=False, p2cpu=False,
                     resourceVersion=digest, map='fixture', players=players)
        report = dict(schemaVersion=2, build=dict(status='match', buildID=digest,
                      sidecarBuildID=digest, resourceVersion=digest,
                      pckSha256=digest, pckHashKind='exported_artifact'),
                      runtime=dict(events=[dict(type='match_started', buildID=digest,
                                                payload=dict(match=match))]))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path, value in {
                'generated/build_metadata.json': dict(schemaVersion=1, buildID=digest,
                                                     resourceVersion=digest, sourceTreeSha256=digest),
                'generated/main/character_selection/available.json': dict(fighters={'fixture': 'fixture'}, helpers={}),
                'generated/stages/catalog/catalog.json': dict(stages=[dict(id='fixture')]),
            }.items():
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(value))
            # Isolate recipe validation from unrelated capture coverage/hash tests.
            with mock.patch.object(diagnostics, 'analyze_report', return_value={
                    'replayability': {'executorEligibility': 'ready_for_executor'}}), \
                    mock.patch.object(diagnostics, 'sha256_tree', return_value=digest):
                for valid in (players, list(reversed(players)), {p['slot']: p for p in players}):
                    match['players'] = valid
                    self.assertEqual(diagnostics.replay_preflight(report, root), [])
                for invalid in ([dict(players[0], resourcePath='res://wrong'), *players],
                                [players[0], *players], [None, *players],
                                [players[0]], [], [dict(players[0], slot='p3'), players[1]]):
                    with self.subTest(players=invalid):
                        match['players'] = invalid
                        problems = diagnostics.replay_preflight(report, root)
                        self.assertTrue(any('exactly p1 and p2' in p for p in problems), problems)


if __name__ == '__main__':
    unittest.main()
