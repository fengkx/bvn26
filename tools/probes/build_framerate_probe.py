"""Build the 30 FPS host and 24 FPS externally loaded AVM1 probe."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from build_minimal_swf import build


def compile_swf(ffdec: Path, base: Path, output: Path, scripts: Path) -> None:
    subprocess.run(
        [
            "java",
            "-Djava.awt.headless=true",
            "-jar",
            str(ffdec),
            "-importScript",
            str(base),
            str(output),
            str(scripts),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffdec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_root = Path(__file__).resolve().parent / "as2" / "framerate"
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bvn-framerate-probe-") as directory:
        temporary = Path(directory)
        host_base = temporary / "host-base.swf"
        assist_base = temporary / "assist-base.swf"
        host_base.write_bytes(build(1, frame_rate=30))
        assist_base.write_bytes(build(6, frame_rate=24))
        compile_swf(args.ffdec, host_base, args.output / "host.swf", source_root / "host")
        compile_swf(
            args.ffdec,
            assist_base,
            args.output / "assist.swf",
            source_root / "assist",
        )


if __name__ == "__main__":
    main()
