"""Verify native Orochimaru cache boundaries against unchanged component references."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from tools.probes.analyze_component_cache_boundaries import decode
from tools.probes.analyze_jiraiya_filter_boundary import ROOT, comparison


def compact_score(actual, expected):
    result = comparison(actual, expected)
    result["first_failures"] = result.pop("failures")[:16]
    return result


def analyze(native_root):
    cases = json.loads((ROOT / "evidence/importer-loud-fail/r32/components/orochimaru/cases.json").read_text())
    results = []
    for case in cases:
        native = native_root / case["id"] / "components/orochimaru"
        build, images, matrices, access, properties = decode(native)
        # A singleton export renumbers the synthetic wrapper, never the authored symbol.
        assert build["case"] == case
        assert case["symbol"] == 342 and case["placement"]["character_id"] == 342
        assert case["placement"]["filters"] == [
            {"type": "BLURFILTER", "blurX": 0.0, "blurY": 20.0, "passes": 1}
        ]
        expected_properties = []
        for phase in range(3):
            expected_properties.extend([
                [f"{phase}-authored", "true", "1", "0", "20", "1"],
                [f"{phase}-clear", "false", "0"],
                [f"{phase}-cache", "true", "0"],
            ])
        assert properties == expected_properties
        pinned = []
        composed = [
            [red + 96 * (256 - alpha) // 256,
             green + 96 * (256 - alpha) // 256,
             blue + 96 * (256 - alpha) // 256, 255]
            for red, green, blue, alpha in images["1-authored"]
        ]
        for tick in case["samples"]:
            path = ROOT / "evidence/importer-loud-fail/r21/components/orochimaru" / f"{case['id']}-{tick:03d}.native.png"
            image = Image.open(path).convert("RGBA")
            assert image.size == (600, 400)
            pinned.append({
                "reference": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **compact_score(composed, list(image.getdata())),
            })
        results.append({
            "id": case["id"], "matrices_and_local_bounds": matrices,
            "shape_access": access, "properties": properties,
            "pinned_complete_images": pinned,
            "clear_vs_cache": [compact_score(images[f"{i}-clear"], images[f"{i}-cache"]) for i in range(3)],
            "clear_vs_authored": [compact_score(images[f"{i}-clear"], images[f"{i}-authored"]) for i in range(3)],
        })
    pinned = [score for result in results for score in result["pinned_complete_images"]]
    return {
        "cases": results,
        "pinned_images_exact": sum(score["exact"] == score["samples"] for score in pinned),
        "pinned_images_total": len(pinned),
        "pinned_pixels_exact": sum(score["exact"] for score in pinned),
        "pinned_pixels_total": sum(score["samples"] for score in pinned),
        "source_texture_from_reference": False,
        "production_admitted": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print({key: value for key, value in result.items() if key != "cases"})
    raise SystemExit(0 if result["pinned_images_exact"] == result["pinned_images_total"] else 1)
