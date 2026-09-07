import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


inspect_swf = load_module("inspect_swf_probe_test", ROOT / "tools/inspect_swf.py")
probe_builder = load_module(
    "probe_builder", ROOT / "tools/probes/build_minimal_swf.py"
)


class ProbeBuilderTests(unittest.TestCase):
    def inspect_bytes(self, data: bytes) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.swf"
            path.write_bytes(data)
            return inspect_swf.inspect(path)

    def test_builds_three_frame_as2_container(self):
        result = self.inspect_bytes(probe_builder.build(3))
        self.assertEqual(result["swf_version"], 8)
        self.assertEqual(result["header_fps"], 30.0)
        self.assertEqual(result["root_frames"], 3)
        self.assertEqual(result["tag_counts"][12], 3)

    def test_builds_enter_frame_clip_lifecycle(self):
        result = self.inspect_bytes(probe_builder.build(3, True))
        self.assertEqual(result["tag_counts"][39], 1)
        self.assertEqual(result["tag_counts"][26], 1)
        self.assertEqual(result["tag_counts"][28], 1)
        self.assertEqual(len(result["clip_action_tags"]), 1)

    def test_preserves_external_movie_frame_rate(self):
        result = self.inspect_bytes(probe_builder.build(6, frame_rate=24))
        self.assertEqual(result["header_fps"], 24.0)
        self.assertEqual(result["root_frames"], 6)


if __name__ == "__main__":
    unittest.main()
