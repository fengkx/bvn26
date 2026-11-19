"""Offline checks for the HiDPI web supersample megapixel cap."""
from __future__ import annotations

import math
import unittest

from tools.web_raster_budget import (
    WEB_RASTER_PIXEL_BUDGET,
    fit_physical_to_raster_budget,
    parse_render_surface_budget,
    raster_pixels,
)


class WebRasterBudgetTests(unittest.TestCase):
    def test_budget_matches_flash_high_stage_pixels(self) -> None:
        self.assertEqual(WEB_RASTER_PIXEL_BUDGET, 600 * 400 * 4 * 4)
        self.assertEqual(WEB_RASTER_PIXEL_BUDGET, 3_840_000)

    def test_gdscript_constant_stays_aligned(self) -> None:
        self.assertEqual(parse_render_surface_budget(), WEB_RASTER_PIXEL_BUDGET)

    def test_flash_scale_high_is_unchanged(self) -> None:
        self.assertEqual(fit_physical_to_raster_budget(600, 400, 4), (600, 400))
        self.assertEqual(raster_pixels(600, 400, 4), WEB_RASTER_PIXEL_BUDGET)

    def test_low_dpi_medium_window_unchanged_when_under_budget(self) -> None:
        # 900×600 × grid 2 = 3.24 MP < 3.84 MP
        self.assertEqual(fit_physical_to_raster_budget(900, 600, 2), (900, 600))

    def test_production_hidpi_high_case_binds(self) -> None:
        # Diagnosis canvas: 1785×1190 at DPR 2 with default HIGH sample_grid=4.
        uncapped = raster_pixels(1785, 1190, 4)
        self.assertGreater(uncapped, WEB_RASTER_PIXEL_BUDGET)
        self.assertAlmostEqual(uncapped / 1_000_000, 33.9864, places=3)

        fitted_w, fitted_h = fit_physical_to_raster_budget(1785, 1190, 4)
        fitted = raster_pixels(fitted_w, fitted_h, 4)
        self.assertLess(fitted_w, 1785)
        self.assertLess(fitted_h, 1190)
        self.assertLessEqual(fitted, WEB_RASTER_PIXEL_BUDGET)
        # Stay near the Flash HIGH budget rather than collapsing to LOW (~2.1 MP).
        self.assertGreaterEqual(fitted, int(WEB_RASTER_PIXEL_BUDGET * 0.98))
        expected_scale = math.sqrt(WEB_RASTER_PIXEL_BUDGET / uncapped)
        self.assertEqual(fitted_w, max(1, int(1785 * expected_scale)))
        self.assertEqual(fitted_h, max(1, int(1190 * expected_scale)))

    def test_texture_limit_alone_would_not_bind_this_case(self) -> None:
        # Typical WebGL2 MAX_TEXTURE_SIZE is 8192–16384. The HiDPI HIGH raster
        # edge is 7140, so an OOM clamp does not protect the 30 Hz budget.
        physical = (1785, 1190)
        grid = 4
        raster_edge = max(physical) * grid
        for texture_limit in (8192, 16384):
            self.assertLessEqual(raster_edge, texture_limit)
            maximum_grid = 4
            maximum_output = texture_limit // maximum_grid
            fit = min(1.0, maximum_output / max(physical))
            self.assertEqual(fit, 1.0)

    def test_low_quality_on_same_canvas_stays_under_budget(self) -> None:
        self.assertEqual(fit_physical_to_raster_budget(1785, 1190, 1), (1785, 1190))
        self.assertLess(raster_pixels(1785, 1190, 1), WEB_RASTER_PIXEL_BUDGET)

    def test_capped_high_composite_is_coarser_than_capped_medium(self) -> None:
        # Budget keeps sample_grid semantics but shrinks the composite grid.
        # On this HiDPI canvas both MEDIUM and HIGH bind; HIGH's resolve target
        # (600×400 upscaled) is coarser than MEDIUM's (1200×800) even though
        # HIGH still runs more supersample taps per fragment.
        high = fit_physical_to_raster_budget(1785, 1190, 4)
        medium = fit_physical_to_raster_budget(1785, 1190, 2)
        self.assertEqual(medium, (1200, 800))
        self.assertEqual(high, (600, 400))
        self.assertLess(high[0] * high[1], medium[0] * medium[1])
        self.assertEqual(raster_pixels(*high, 4), raster_pixels(*medium, 2))


if __name__ == "__main__":
    unittest.main()
