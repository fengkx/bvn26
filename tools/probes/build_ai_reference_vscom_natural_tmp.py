"""Temporary source-only VS COM capture builder for the You/Renji case."""

from pathlib import Path
import runpy


module = runpy.run_path(str(Path(__file__).with_name("build_ai_reference_vscom_tmp.py")))
build = module["build"]
main = module["main"]


if __name__ == "__main__":
    main()
