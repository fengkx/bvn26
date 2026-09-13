import unittest

from tools.probes.compare_start_sound_observations import observed_start_sounds


class StartSoundObservationTests(unittest.TestCase):
    def test_logs_tag_when_observed_playhead_enters_source_frame(self):
        rows = [
            {"tick": 1, "slot": "p1", "frame": 187},
            {"tick": 2, "slot": "p1", "frame": 188},
            {"tick": 3, "slot": "p1", "frame": 189},
            {"tick": 4, "slot": "p1", "frame": 188},
        ]
        events = {188: [{"type": "start_sound", "sound_id": 105}]}

        observed = observed_start_sounds(rows, events, "p1")

        self.assertEqual([(row["tick"], row["frame"], row["sound_id"]) for row in observed],
                         [(2, 188, 105), (4, 188, 105)])

    def test_ignores_other_slot(self):
        rows = [{"tick": 2, "slot": "p2", "frame": 188}]

        self.assertEqual(observed_start_sounds(
            rows, {188: [{"type": "start_sound", "sound_id": 105}]}, "p1"), [])


if __name__ == "__main__":
    unittest.main()
