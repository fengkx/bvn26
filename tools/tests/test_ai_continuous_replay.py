import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.probes.validate_ai_continuous_replay import validate


class ContinuousReplayValidationTests(unittest.TestCase):
    def test_nonzero_source_random_index_maps_local_cursor_and_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "events.jsonl"
            replay = root / "replay.json"
            build = root / "build.json"
            output = root / "acceptance.json"
            events = [
                {"sequence": 1, "kind": "random", "fight_tick": -1,
                 "value": "1,main#music,f:1:0:0:0"},
                {"sequence": 2, "kind": "intro_poll_state", "fight_tick": -1,
                 "display_tick": 9, "value": "0,true,0,0,1,1"},
                {"sequence": 3, "kind": "random", "fight_tick": -1,
                 "value": "2,fighter/Byakuya#ai:1,f:1:-1:100663296:0"},
                {"sequence": 4, "kind": "ready", "fight_tick": 0,
                 "display_tick": 10, "value": ""},
            ]
            for tick in range(2):
                for slot, frame in (("p1", 7 + tick), ("p2", 2 + tick)):
                    events.append({"sequence": len(events) + 1, "kind": "state",
                                   "fight_tick": tick, "display_tick": 10 + tick,
                                   "value": f"{slot},{frame},f:1:0:0:0,f:1:0:0:0,f:1:6:104857600:0,0,f:1:9:131072000:0,f:1:0:0:0,false,true,true,0,false,0,false"})
                events.append({"sequence": len(events) + 1, "kind": "input_next_display",
                               "fight_tick": tick, "display_tick": 10 + tick,
                               "value": "right=false"})
                events.append({"sequence": len(events) + 1, "kind": "helper_state",
                               "fight_tick": tick, "display_tick": 10 + tick,
                               "value": "p1,1,f:1:4:83886080:0,f:-1:7:104857600:0,f:1:6:104857600:0,false,undefined,undefined,undefined,undefined,undefined"})
                events.append({"sequence": len(events) + 1, "kind": "helper_state",
                               "fight_tick": tick, "display_tick": 10 + tick,
                               "value": "p2,1,f:1:4:83886080:0,f:-1:7:104857600:0,f:1:6:104857600:0,false,undefined,undefined,undefined,undefined,undefined"})
            events.extend([
                {"sequence": len(events) + 1, "kind": "random", "fight_tick": 1,
                 "value": "3,fighter/Byakuya#ai:2,f:1:-2:67108864:0"},
                {"sequence": len(events) + 2, "kind": "done", "fight_tick": 1,
                 "display_tick": 11, "value": ""},
            ])
            source.write_text("\n".join(json.dumps(event) for event in events) + "\n")
            build.write_text(json.dumps({"frames_after_ready": 1,
                                         "configuration": {"p2cpu": True}}))
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            rows = []
            for tick in range(2):
                rows.append({"display_tick": 10 + tick, "matches": True})
            state_rows = [{"display_tick": 10 + tick, "differences": {}}
                          for tick in range(2) for _ in range(2)]
            geometry_rows = [{"display_tick": 10 + tick, "delta": {"x": 0, "y": 0, "xscale": 0}}
                             for tick in range(2) for _ in range(2)]
            replay.write_text(json.dumps({
                "reference_sha256": sha,
                "original_ready": [{"slot": "p1", "frame": 7, "display_tick": 10},
                                    {"slot": "p2", "frame": 2, "display_tick": 10}],
                "native_ready": [{"slot": "p1", "frame": 7, "display_tick": 10},
                                  {"slot": "p2", "frame": 2, "display_tick": 10}],
                "native_checkpoint": {"display_tick": 10, "fight_tick": 0,
                                       "actors": [{}, {}], "battle_intro_active": False,
                                       "pending_frame_actions": [0, 0],
                                       "random_absolute_index": 1},
                "frame_comparisons": rows,
                "state_comparisons": state_rows,
                "geometry_comparisons": geometry_rows,
                "random_original_indices": [2, 3],
                "random_consumed": [{"site": "fighter/Byakuya#ai:1", "value": 0.75},
                                     {"site": "fighter/Byakuya#ai:2", "value": 0.25}],
                "random_tape_complete": True, "random_failure": "",
                "clock_tape_complete": True,
            }))
            result = validate(source, replay, 1, build)
            self.assertEqual(result["status"], "unknown")
            self.assertTrue(result["checks"]["random_consumers"]["scope_complete"])
            self.assertEqual(result["checks"]["random_consumers"]["local_cursor_offset"], 1)
            self.assertFalse(result["checks"]["post_ready_helpers"]["matched"])
            self.assertEqual(result["first_reason"], "ready_checkpoint_restore_incomplete")


if __name__ == "__main__":
    unittest.main()
