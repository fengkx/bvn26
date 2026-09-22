#!/usr/bin/env python3
"""Export the source ql/bss HUD clips and their authored placements."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-swf", type=Path, required=True)
    parser.add_argument("--ffdec-jar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.source_swf.is_file() or not args.ffdec_jar.is_file():
        raise SystemExit("source SWF and FFDec jar are required")
    with tempfile.TemporaryDirectory(prefix="energy-presentation-") as temp:
        temp_path = Path(temp)
        sprites = temp_path / "sprites"
        shapes = temp_path / "shapes"
        for command in [
            ["java", "-Djava.awt.headless=true", "-jar", str(args.ffdec_jar),
             "-selectid", "1763,1764,1773,1781", "-format", "image:png",
             "-export", "sprite", str(sprites), str(args.source_swf)],
            ["java", "-Djava.awt.headless=true", "-jar", str(args.ffdec_jar),
             "-format", "shape:png", "-export", "shape", str(shapes), str(args.source_swf)],
        ]:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        args.output.mkdir(parents=True, exist_ok=True)
        for name, source_id in (("qt", "1764"), ("bss-p1", "1773"), ("bss-p2", "1781")):
            target = args.output / name
            target.mkdir(exist_ok=True)
            for image in sorted((sprites / f"DefineSprite_{source_id}").glob("*.png"), key=lambda p: int(p.stem)):
                shutil.copy2(image, target / image.name)
        nested = args.output / "qt-nested"
        nested.mkdir(exist_ok=True)
        for image in sorted((sprites / "DefineSprite_1763").glob("*.png"), key=lambda p: int(p.stem)):
            shutil.copy2(image, nested / image.name)
        shutil.copy2(shapes / "1748.png", args.output / "background.png")
        layers = args.output / "qt-layers"
        layers.mkdir(exist_ok=True)
        shutil.copy2(shapes / "1759.png", layers / "base-1759.png")
        shutil.copy2(shapes / "1756.png", layers / "overlay-1756.png")
    spec = {
        "source": {"swf": str(args.source_swf), "sha256": sha256(args.source_swf)},
        "scale": 20,
        "background_bounds_twips": {"xmin": 0, "ymin": 0, "xmax": 3820, "ymax": 1220},
        "outer_matrix": {"scaleX": 0.6065521, "scaleY": 0.6065521, "translateX": 12658, "translateY": 8049},
        # These values are compiled from the locked main.xml display list:
        # root xuetiao -> DefineSprite_1815 frame 5 -> 1774/1782. Keep the
        # source path and SWF hash beside the fields so a stale export cannot
        # silently fall back to the old hand-sized HUD layout.
        "layout": {
            "scale": 20,
            "root_xuetiao": {
                "character_id": 1815, "depth": 71, "scaleX": 1.0, "scaleY": 1.0,
                "translateX": -22, "translateY": 40, "translate_units": "twips",
                "source": "main.xml root/tags/item[name=xuetiao]"
            },
            "active_frame": 5,
            "active_outer_instances": {
                "p1": {"character_id": 1782, "depth": 17, "nn": 1, "scaleX": 0.6065521, "scaleY": 0.6065521, "translateX": 149, "translateY": 7249},
                "p2": {"character_id": 1774, "depth": 1, "nn": 2, "scaleX": -0.6065521, "scaleY": 0.6065521, "translateX": 11858, "translateY": 7249}
            },
            "wrapper_composite_bounds": {
                "minX": -4.0, "minY": -4.0, "maxX": 234.7, "maxY": 57.0,
                "units": "source_pixels",
                "derived_from": "recursive first-frame child union from main.xml"
            },
            "wrapper_composite_size": [238.7, 61.0],
            "root_matrix_source_sha256": sha256(args.source_swf)
        },
        "wrapper_bounds": {
            "source_pixels": {"minX": 43.7, "minY": -4.0, "maxX": 234.7, "maxY": 57.0},
            "local_composite_bounds": {"minX": 0.0, "minY": 0.0, "maxX": 191.0, "maxY": 61.0, "derived_from": "DefineSprite_1774/1782 authored wrapper bounds and placement union"},
            "derived_from": {
                "background_placement": [43.7, -4.0],
                "background_source_bounds_twips": [0, 0, 3820, 1220],
                "background_alpha_bbox": [4, 4, 187, 57],
                "qt_placement": [83.7, 29.0],
                "qt_alpha_bbox": [0, 0, 141, 18],
                "bss_placement_p1": [54.7, 8.0],
                "bss_placement_p2": [54.05, 8.0],
                "bss_source_bounds_twips": {"1773": [-13, 0, 500, 760], "1781": [0, 0, 480, 760]}
            }
        },
        "bss_source_bounds_twips": {"1773": {"xmin": -13, "ymin": 0, "xmax": 500, "ymax": 760}, "1781": {"xmin": 0, "ymin": 0, "xmax": 480, "ymax": 760}},
        "outer_instances": {
            "source_path": "game/main.swf:DefineSprite_1815/frame_1",
            "p1": {"character_id": 1782, "depth": 17, "nn": 1, "scaleX": 0.6065521, "scaleY": 0.6065521, "translateX": -651, "translateY": 8049},
            "p2": {"character_id": 1774, "depth": 1, "nn": 2, "scaleX": -0.6065521, "scaleY": 0.6065521, "translateX": 12658, "translateY": 8049}
        },
        "source_invariants": {
            "ql_callback": "scripts/main.json:DefineSprite_1774/frame_1/DoAction.as",
            "stock_callback": "scripts/main.json:DefineSprite_1774/frame_1/DoAction.as",
            "ql_index": "round(ql)+1",
            "stock_index": "floor(ql/100)+1",
            "interval_ms": 300,
        },
        "wrappers": {
            "p1": {"character_id": 1782, "placements": {"background": {"character_id": 1748, "x": 43.7, "y": -4.0}, "qt": {"character_id": 1764, "matrix": {"scaleX": 1, "scaleY": 1, "rotateSkew0": 0, "rotateSkew1": 0, "translateX": 1674, "translateY": 580}, "x": 83.7, "y": 29.0}, "bss": {"character_id": 1781, "matrix": {"scaleX": 1, "scaleY": 1, "rotateSkew0": 0, "rotateSkew1": 0, "translateX": 1094, "translateY": 160}, "x": 54.7, "y": 8.0}}, "background": 1748},
            "p2": {"character_id": 1774, "placements": {"background": {"character_id": 1748, "x": 43.7, "y": -4.0}, "qt": {"character_id": 1764, "matrix": {"scaleX": 1, "scaleY": 1, "rotateSkew0": 0, "rotateSkew1": 0, "translateX": 1674, "translateY": 580}, "x": 83.7, "y": 29.0}, "bss": {"character_id": 1773, "matrix": {"scaleX": 1, "scaleY": 1, "rotateSkew0": 0, "rotateSkew1": 0, "translateX": 1094, "translateY": 160}, "x": 54.05, "y": 8.0}}, "background": 1748},
        },
        "qt_frames": 301,
        "qt_nested": {"symbol": 1763, "frames": 10, "loop": True, "placed_at_qt_frame": 301, "red_frames": [1, 2, 3, 4], "yellow_frames": [5, 6, 7, 8, 9, 10]},
        "qt_layers": {
            "source": "game/main.swf:DefineSprite_1764/frame_301",
            "composite_order": [1, 2, 4],
            "depth4_overlay": {"symbol": 1756, "path": "qt-layers/overlay-1756.png", "bounds_twips": [0, 0, 2800, 360], "matrix": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0}},
            "depth1_base": {"symbol": 1759, "path": "qt-layers/base-1759.png", "bounds_twips": [6, 0, 2806, 360], "matrix": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0}},
            "depth2_nested": {"symbol": 1763, "path": "qt-nested/{frame}.png", "bounds_twips": [0, 0, 2800, 360], "matrix": {"scaleX": 1, "scaleY": 1, "translateX": 6, "translateY": 0}}
        },
        "bss_frames": 4,
    }
    (args.output / "presentation.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
