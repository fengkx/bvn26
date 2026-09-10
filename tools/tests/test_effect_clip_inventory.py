import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


inspect_swf = load_module("inspect_swf", ROOT / "tools/inspect_swf.py")
hit_receive = load_module(
    "hit_receive", ROOT / "tools/importer/compile_hit_receive.py"
)
stage_music = load_module(
    "stage_music", ROOT / "tools/importer/materialize_stage_music.py"
)


def main_swf_exports() -> dict[str, int]:
    exports = inspect_swf.inspect(ROOT / "game/main.swf")["exports"]
    return {export["name"]: export["character_id"] for export in exports}


def shared_hit_fx() -> dict:
    bundle = hit_receive.load_bundle(ROOT / "scripts/main.json")
    return hit_receive.compile_shared_hit_receive(bundle)["hit_fx"]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ElementAndSuperClipTests(unittest.TestCase):
    def test_substitution_effects_keep_source_flash_and_unload(self):
        source = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
        for clip, end in [('XG_tishen', 35), ('XG_tishen2', 20)]:
            directory = ROOT / 'godot/generated/effects' / clip
            model = json.loads((directory / 'effect.json').read_text())
            self.assertEqual(model['sprite_id'], main_swf_exports()[clip])
            events = model['presentation_events']
            self.assertEqual(events[-1]['op'], 'unload')
            self.assertEqual(events[-1]['frame'], end)
            self.assertEqual(source[events[-1]['source_path']].strip(), 'this.unloadMovie();')
            if clip == 'XG_tishen':
                self.assertEqual((events[0]['op'], events[0]['frame']), ('shine', 3))
                self.assertEqual(source[events[0]['source_path']].strip(), '_root.shine();')
            for asset in json.loads((directory / 'assets.json').read_text())['assets']:
                self.assertEqual(file_sha256(directory / asset['path']), asset['sha256'])

    def test_ghost_effect_keeps_source_lifetime(self):
        directory = ROOT / 'godot/generated/effects/XG_xdash'
        model = json.loads((directory / 'effect.json').read_text())
        self.assertEqual(model['sprite_id'], main_swf_exports()['XG_xdash'])
        source = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
        self.assertEqual(model['presentation_events'][0]['frame'], 25)
        self.assertEqual(source[model['presentation_events'][0]['source_path']].strip(), 'this.unloadMovie();')
        for script in model['nested_terminal_scripts']:
            self.assertEqual(script['source'], source[script['path']])
        assets = json.loads((directory / 'assets.json').read_text())
        for asset in assets['assets']:
            self.assertEqual(file_sha256(directory / asset['path']), asset['sha256'])

    def test_hit_spark_random_offsets_keep_source_call_order(self):
        events = shared_hit_fx()['clips']['XG_qdj']['presentation_events']
        first = [event for event in events if event['frame'] == 1]
        self.assertEqual([event['op'] for event in first], ['shake_root', 'random_offset', 'random_offset'])
        self.assertEqual([(event['axis'], event['positive_factor'], event['negative_factor'])
                          for event in first[1:]], [('x', 10, 10), ('y', 20, 30)])
        prefix = 'main#DefineSprite_256_XG_qdj/frame_1/DoAction.as:'
        self.assertEqual([site for event in first[1:] for site in event['random_sites']],
                         [prefix + str(i) for i in range(1, 5)])

    def test_unknown_effect_random_expression_fails_compilation(self):
        bundle = hit_receive.load_bundle(ROOT / 'scripts/main.json')
        source = next(script for script in bundle['scripts']
                      if script['path'] == 'DefineSprite_256_XG_qdj/frame_1/DoAction.as')
        source['source'] += '\n_rotation = Math.random() * 180;\n'
        with self.assertRaisesRegex(ValueError, 'Unsupported hit-effect random expression'):
            hit_receive.compile_hit_fx(bundle)

    def test_source_element_color_operations(self):
        effects = shared_hit_fx()["color_effects"]
        self.assertEqual(set(effects), {7, 8, 9, 10})
        self.assertEqual(effects[7]["colors"], [{"rb": 255, "gb": 25, "bb": -255}, {"rb": 255, "gb": 86, "bb": -255}])
        self.assertEqual(effects[8]["colors"], [{"rb": 0, "gb": 153, "bb": 255}, {"rb": 0, "gb": 198, "bb": 255}])
        self.assertEqual(effects[9]["colors"], [{"rb": 71, "gb": 91, "bb": 255}, {"rb": 178, "gb": 142, "bb": 255}])
        self.assertEqual(effects[10]["matrix"], [0.3086, 0.6094, 0.082, 0, 0] * 3 + [0, 0, 0, 1, 0])
        for relative in ("data/actions/hit_receive.json", "godot/generated/main/hit_receive.json"):
            compiled = json.loads((ROOT / relative).read_text())["hit_fx"]["color_effects"]
            self.assertEqual(compiled, {str(k): v for k, v in effects.items()})

    # bdxg cases 7-9 are the element tiers; bsd()/cbsd() attach the super
    # clips. Sound ids are the frame 1 StartSoundTag in each sprite.
    CLIPS = {
        "XG_fire": (423, 396),
        "XG_ice": (358, 337),
        "XG_leidian": (334, 317),
        "XG_bs": (459, 444),
        "XG_cbs": (441, 426),
    }

    def test_clip_names_match_export_assets(self):
        # Locks the imported directory against the sprite the SWF exports
        # under that name, which is how the XG_mfdj / XG_mfdjx swap showed up.
        exports = main_swf_exports()
        for clip, (sprite_id, _) in self.CLIPS.items():
            self.assertEqual(exports.get(clip), sprite_id, clip)
            timeline = json.loads(
                (ROOT / "godot/generated/effects" / clip / "timeline.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(timeline["sprite_id"], sprite_id, clip)

    def test_clips_keep_frame_one_start_sound(self):
        for clip, (_, sound_id) in self.CLIPS.items():
            directory = ROOT / "godot/generated/effects" / clip
            timeline = json.loads((directory / "timeline.json").read_text(encoding="utf-8"))
            events = [
                event
                for event in timeline["frames"][0]["events"]
                if event["type"] == "start_sound"
            ]
            self.assertEqual([event["sound_id"] for event in events], [sound_id], clip)
            assets = json.loads((directory / "assets.json").read_text(encoding="utf-8"))
            materialized = {asset["character_id"]: asset["path"] for asset in assets["assets"]}
            self.assertEqual(materialized.get(sound_id), f"{sound_id}.mp3", clip)
            self.assertTrue((directory / f"{sound_id}.mp3").is_file(), clip)

    def test_every_bitmap_fill_is_materialized(self):
        # A clip whose fills point at missing bitmaps renders empty. 0xFFFF is
        # the SWF "no bitmap" fill id and has nothing to copy.
        for clip in self.CLIPS:
            directory = ROOT / "godot/generated/effects" / clip
            timeline = json.loads((directory / "timeline.json").read_text(encoding="utf-8"))
            needed = {
                int(fill["bitmap_id"])
                for definition in timeline["definitions"]
                for fill in definition.get("bitmap_fills", [])
                if int(fill["bitmap_id"]) != 0xFFFF
            }
            assets = json.loads((directory / "assets.json").read_text(encoding="utf-8"))
            materialized = {int(asset["character_id"]) for asset in assets["assets"]}
            self.assertEqual(needed - materialized, set(), clip)
            self.assertTrue(needed, clip)

    def test_element_tiers_point_at_imported_clips(self):
        hit_fx = shared_hit_fx()
        self.assertEqual(hit_fx["bdxg"][7], "XG_fire")
        self.assertEqual(hit_fx["bdxg"][8], "XG_ice")
        self.assertEqual(hit_fx["bdxg"][9], "XG_leidian")
        for clip in ("XG_fire", "XG_ice", "XG_leidian"):
            self.assertTrue(hit_fx["clips"][clip]["imported"], clip)
            self.assertTrue((ROOT / "godot/generated/effects" / clip).is_dir(), clip)

    def test_stone_tier_has_no_sprite_in_the_source(self):
        # bdxg case 10 names XG_stone, but main.swf exports no such clip, so
        # attachMovie finds nothing in the original. jumpxg() and luodixg()
        # name clips that are missing the same way. None of them may be
        # substituted with homemade art.
        exports = main_swf_exports()
        for clip in ("XG_stone", "XG_jump", "XG_luodi"):
            self.assertNotIn(clip, exports)
            self.assertFalse((ROOT / "godot/generated/effects" / clip).exists(), clip)
        hit_fx = shared_hit_fx()
        self.assertEqual(hit_fx["bdxg"][10], "XG_stone")
        self.assertFalse(hit_fx["clips"]["XG_stone"]["imported"])
        self.assertIsNone(hit_fx["clips"]["XG_stone"]["source_prefix"])

    def test_super_clip_sound_keeps_in_and_out_points(self):
        # SOUNDINFO InPoint / OutPoint count 44.1 kHz samples, so 444.mp3
        # (11025 Hz, 1.202 s) is trimmed to 0.116 s .. 1.164 s rather than
        # played whole.
        timeline = json.loads(
            (ROOT / "godot/generated/effects/XG_bs/timeline.json").read_text(encoding="utf-8")
        )
        event = next(
            item for item in timeline["frames"][0]["events"] if item["type"] == "start_sound"
        )
        self.assertEqual(event["in_point"], 5100)
        self.assertEqual(event["out_point"], 51340)
        timeline = json.loads(
            (ROOT / "godot/generated/effects/XG_cbs/timeline.json").read_text(encoding="utf-8")
        )
        event = next(
            item for item in timeline["frames"][0]["events"] if item["type"] == "start_sound"
        )
        self.assertNotIn("in_point", event)
        self.assertEqual(event["out_point"], 51892)


class StageMusicTests(unittest.TestCase):
    MANIFEST = ROOT / "godot/generated/music/music.json"

    def report(self) -> dict:
        return json.loads(self.MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_keeps_load_sound_order(self):
        # loadSound(): p2selt music at Math.random() < 0.8, then bleach or
        # naruto music at < 0.5, otherwise getMapData(curStage).music.
        selection = self.report()["selection"]
        self.assertEqual(selection["p2selt"], "一护")
        self.assertEqual(selection["cur_stage"], "现世")
        self.assertFalse(selection["is_naruto"])
        self.assertEqual(
            selection["steps"],
            [
                {
                    "random_below": 0.8,
                    "random_site": "main#DefineSprite_1900/frame_1/DoAction.as:1",
                    "file": "ichigo.mp3",
                    "source": "fighter_catalog.一护.music",
                },
                {"random_below": 0.5, "random_site": "main#DefineSprite_1900/frame_1/DoAction.as:2",
                 "file": "bleach.mp3", "source": "bleachMusic"},
                {"otherwise": True, "file": "city.mp3", "source": "map_catalog.现世.music"},
            ],
        )

    def test_naruto_opponent_takes_naruto_music(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        steps, is_naruto = stage_music.selection_steps(manifest, "鸣人", "木叶村")
        self.assertTrue(is_naruto)
        self.assertEqual(
            [step["file"] for step in steps],
            ["minren.mp3", "naruto.mp3", "village.mp3"],
        )

    def test_catalog_entry_without_music_skips_the_first_draw(self):
        # 仙鸣 has no music key, so loadSound never draws for step 1.
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        steps, _ = stage_music.selection_steps(manifest, "仙鸣", "火影瀑布")
        self.assertEqual(
            steps,
            [
                {"random_below": 0.5, "random_site": "main#DefineSprite_1900/frame_1/DoAction.as:2",
                 "file": "naruto.mp3", "source": "narutoMusic"},
                {
                    "otherwise": True,
                    "file": "pubu.mp3",
                    "source": "map_catalog.火影瀑布.music",
                },
            ],
        )

    def test_playback_matches_start_game(self):
        # startGame(): stageSound.start(0,999) then setVolume(80).
        self.assertEqual(
            self.report()["playback"],
            {"start_offset_seconds": 0, "loops": 999, "volume_percent": 80},
        )

    def test_materialized_files_match_the_locked_music(self):
        for entry in self.report()["files"]:
            source = ROOT / "game/music" / entry["file"]
            copied = self.MANIFEST.parent / entry["path"]
            self.assertTrue(copied.is_file(), entry["file"])
            self.assertEqual(file_sha256(source), entry["sha256"], entry["file"])
            self.assertEqual(file_sha256(copied), entry["sha256"], entry["file"])


if __name__ == "__main__":
    unittest.main()
