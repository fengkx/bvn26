import json
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_energy_presentation_is_source_bound():
    spec = json.loads((ROOT / "godot/generated/main/energy/presentation.json").read_text())
    assert spec["source"]["sha256"] == "707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d"
    assert spec["source_invariants"] == {
        "ql_callback": "scripts/main.json:DefineSprite_1774/frame_1/DoAction.as",
        "stock_callback": "scripts/main.json:DefineSprite_1774/frame_1/DoAction.as",
        "ql_index": "round(ql)+1",
        "stock_index": "floor(ql/100)+1",
        "interval_ms": 300,
    }
    assert spec["qt_frames"] == 301
    assert spec["qt_nested"] == {"symbol": 1763, "frames": 10, "loop": True, "placed_at_qt_frame": 301, "red_frames": [1, 2, 3, 4], "yellow_frames": [5, 6, 7, 8, 9, 10]}
    assert spec["background_bounds_twips"] == {"xmin": 0, "ymin": 0, "xmax": 3820, "ymax": 1220}
    assert spec["qt_layers"]["composite_order"] == [1, 2, 4]
    assert spec["qt_layers"]["depth1_base"]["symbol"] == 1759
    assert spec["qt_layers"]["depth2_nested"]["symbol"] == 1763
    assert spec["qt_layers"]["depth2_nested"]["matrix"]["translateX"] == 6
    assert spec["qt_layers"]["depth4_overlay"]["symbol"] == 1756
    assert spec["wrapper_bounds"]["source_pixels"] == {"minX": 43.7, "minY": -4.0, "maxX": 234.7, "maxY": 57.0}
    assert spec["wrapper_bounds"]["local_composite_bounds"]["maxX"] == 191.0
    assert spec["bss_source_bounds_twips"]["1773"]["xmin"] == -13
    assert spec["bss_frames"] == 4
    qt = spec["wrappers"]["p1"]["placements"]["qt"]
    assert {key: qt[key] for key in ("character_id", "x", "y")} == {"character_id": 1764, "x": 83.7, "y": 29.0}
    assert spec["outer_instances"]["p1"] == {"character_id": 1782, "depth": 17, "nn": 1, "scaleX": 0.6065521, "scaleY": 0.6065521, "translateX": -651, "translateY": 8049}
    assert spec["outer_instances"]["p2"] == {"character_id": 1774, "depth": 1, "nn": 2, "scaleX": -0.6065521, "scaleY": 0.6065521, "translateX": 12658, "translateY": 8049}
    assert spec["wrappers"]["p1"]["placements"]["bss"]["character_id"] == 1781
    assert spec["layout"]["root_xuetiao"] == {
        "character_id": 1815, "depth": 71, "scaleX": 1.0, "scaleY": 1.0,
        "translateX": -22, "translateY": 40, "translate_units": "twips",
        "source": "main.xml root/tags/item[name=xuetiao]",
    }
    assert spec["layout"]["active_frame"] == 5
    assert spec["layout"]["active_outer_instances"]["p1"] == {
        "character_id": 1782, "depth": 17, "nn": 1,
        "scaleX": 0.6065521, "scaleY": 0.6065521,
        "translateX": 149, "translateY": 7249,
    }
    assert spec["layout"]["active_outer_instances"]["p2"] == {
        "character_id": 1774, "depth": 1, "nn": 2,
        "scaleX": -0.6065521, "scaleY": 0.6065521,
        "translateX": 11858, "translateY": 7249,
    }
    assert spec["layout"]["wrapper_composite_bounds"] == {
        "minX": -4.0, "minY": -4.0, "maxX": 234.7, "maxY": 57.0,
        "units": "source_pixels",
        "derived_from": "recursive first-frame child union from main.xml",
    }
    assert spec["wrappers"]["p2"]["placements"]["bss"]["character_id"] == 1773
