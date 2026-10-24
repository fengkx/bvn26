"""Blend modes with a native renderer implementation; never fall back silently."""

from __future__ import annotations

SUPPORTED_BLEND_MODES = frozenset({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14})


def validate_blend_mode(mode: int, source: str = "placement") -> int:
    if mode not in SUPPORTED_BLEND_MODES:
        raise ValueError(f"Unsupported Flash blend mode {mode} in {source}")
    return mode


def validate_timeline_blends(value, source: str) -> None:
    if isinstance(value, dict):
        if "blend_mode" in value:
            validate_blend_mode(value["blend_mode"], source)
        for child in value.values():
            validate_timeline_blends(child, source)
    elif isinstance(value, list):
        for child in value:
            validate_timeline_blends(child, source)
