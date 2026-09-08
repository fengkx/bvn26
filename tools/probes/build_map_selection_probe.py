"""Build a native Flash map-selection input oracle without changing locked files."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffdec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixtures = Path(__file__).parent / "as2/map_selection"
    patch = args.output / "patch"
    shutil.copytree(fixtures, patch, dirs_exist_ok=True)
    scripts = json.loads(Path("scripts/main.json").read_text())["scripts"]
    source = next(
        s["source"]
        for s in scripts
        if s["path"] == "DefineSprite_1505/frame_1/DoAction.as"
    )
    controller = patch / "scripts/DefineSprite_1505/frame_1/DoAction.as"
    controller.parent.mkdir(parents=True, exist_ok=True)
    # Replace only the input read: keep the original repeat counter, navigation,
    # enable flags, confirmation timer and transition code intact.
    controller.write_text(source.replace("Key.isDown(", "_root.mapKeyIsDown("))
    subprocess.run(
        [
            "java",
            "-Djava.awt.headless=true",
            "-jar",
            str(args.ffdec),
            "-importScript",
            "game/main.swf",
            str(args.output / "input.swf"),
            str(patch),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
