"""Compile the AS2 scheduling probes into reproducible SWF files with JPEXS."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from build_minimal_swf import build


PROBES = {
    "goto": False,
    "enter_frame": False,
    "stop_play_timer": False,
    "clip_lifecycle": True,
    "callback_order": True,
    "sibling_order": 2,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffdec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    probe_root = Path(__file__).resolve().parent
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bvn-schedule-probes-") as directory:
        temporary = Path(directory)
        for name, needs_clip in PROBES.items():
            base = temporary / f"{name}-base.swf"
            base.write_bytes(build(3, needs_clip))
            output = args.output / f"{name}.swf"
            subprocess.run(
                [
                    "java",
                    "-Djava.awt.headless=true",
                    "-jar",
                    str(args.ffdec),
                    "-importScript",
                    str(base),
                    str(output),
                    str(probe_root / "as2" / name),
                ],
                check=True,
            )


if __name__ == "__main__":
    main()
