"""Web supersample raster budget helpers.

Flash stage is 600×400. HIGH sample_grid is 4, so a 1:1 Flash-scale raster is
2400×1600 (3.84 MP). HiDPI web canvases (~1785×1190 at DPR 2) times that grid
reach ~34 MP and miss the 30 Hz clock; WebGL texture_limit only prevents OOM.

Keep this formula aligned with godot/render_surface.gd.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

FLASH_STAGE = (600, 400)
HIGH_SAMPLE_GRID = 4
# 600 * 400 * 4 * 4
WEB_RASTER_PIXEL_BUDGET = FLASH_STAGE[0] * FLASH_STAGE[1] * HIGH_SAMPLE_GRID * HIGH_SAMPLE_GRID

ROOT = Path(__file__).resolve().parents[1]
RENDER_SURFACE = ROOT / "godot" / "render_surface.gd"


def fit_physical_to_raster_budget(
    physical_width: int,
    physical_height: int,
    sample_grid: int,
    pixel_budget: int = WEB_RASTER_PIXEL_BUDGET,
) -> tuple[int, int]:
    """Scale physical size so (physical * grid) stays within pixel_budget megapixels."""
    width = max(int(physical_width), 1)
    height = max(int(physical_height), 1)
    grid = max(int(sample_grid), 1)
    budget = max(int(pixel_budget), 1)
    raster_pixels = float(width) * float(height) * float(grid * grid)
    if raster_pixels <= float(budget):
        return width, height
    scale = math.sqrt(float(budget) / raster_pixels)
    return max(1, int(width * scale)), max(1, int(height * scale))


def raster_pixels(physical_width: int, physical_height: int, sample_grid: int) -> int:
    width, height = max(int(physical_width), 1), max(int(physical_height), 1)
    grid = max(int(sample_grid), 1)
    return width * height * grid * grid


def parse_render_surface_budget(source: str | None = None) -> int:
    text = RENDER_SURFACE.read_text(encoding="utf-8") if source is None else source
    match = re.search(
        r"const WEB_RASTER_PIXEL_BUDGET:\s*int\s*=\s*([0-9_]+)",
        text,
    )
    if not match:
        raise ValueError("WEB_RASTER_PIXEL_BUDGET missing from render_surface.gd")
    return int(match.group(1).replace("_", ""))


if __name__ == "__main__":
    fitted = fit_physical_to_raster_budget(1785, 1190, 4)
    print(
        {
            "budget": WEB_RASTER_PIXEL_BUDGET,
            "uncapped_mp": raster_pixels(1785, 1190, 4) / 1_000_000,
            "fitted_physical": fitted,
            "fitted_raster": (fitted[0] * 4, fitted[1] * 4),
            "fitted_mp": raster_pixels(fitted[0], fitted[1], 4) / 1_000_000,
        }
    )
