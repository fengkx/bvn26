"""Contract checks for the source-derived selectable artifact registry."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_character_selection import build_available  # noqa: E402


class SelectionRegistryTests(unittest.TestCase):
    def test_published_roster_matches_complete_base_artifacts(self):
        first = build_available(ROOT)
        second = build_available(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(
            set(first["fighters"]),
