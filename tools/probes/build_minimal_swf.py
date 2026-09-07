"""Build a tiny AS2 SWF container whose scripts can be replaced by JPEXS."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def tag(code: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    if length < 63:
        return struct.pack("<H", code << 6 | length) + payload
    return struct.pack("<HI", code << 6 | 63, length) + payload


def rect(xmin: int, xmax: int, ymin: int, ymax: int) -> bytes:
    values = (xmin, xmax, ymin, ymax)
    nbits = max(1, max(value.bit_length() + 1 for value in values))
    mask = (1 << nbits) - 1
    bits = f"{nbits:05b}" + "".join(f"{value & mask:0{nbits}b}" for value in values)
    bits += "0" * (-len(bits) % 8)
    return int(bits, 2).to_bytes(len(bits) // 8, "big")


def enter_frame_clip(depth: int) -> tuple[bytes, bytes]:
    sprite = struct.pack("<HH", 1, 1) + tag(1) + tag(0)
    define_sprite = tag(39, sprite)

    # CLIPEVENTFLAGS is a bit field written most-significant bit first within
    # each byte. In the serialized little-endian UI32, enterFrame is value 2.
    enter_frame = 0x02
    clip_actions = (
        struct.pack("<HI", 0, enter_frame)
        + struct.pack("<II", enter_frame, 1)
        + b"\x00"
        + struct.pack("<I", 0)
    )
    flags = 0x80 | 0x20 | 0x04 | 0x02
    placement = (
        bytes([flags])
        + struct.pack("<HH", depth, 1)
        + b"\x00"
        + ("child" if depth == 1 else f"child{depth}").encode("ascii")
        + b"\x00"
        + clip_actions
    )
    return define_sprite, tag(26, placement)


def build(
    frame_count: int, with_enter_frame_clip: bool = False, frame_rate: int = 30
) -> bytes:
    # A non-zero stage survives JPEXS script replacement without being normalized
    # to the invalid zero-bit RECT encoding produced for an empty stage.
    frame_size = rect(0, 20, 0, 20)
    tags = bytearray()
    clip_count = int(with_enter_frame_clip)
    if clip_count:
        definition, placement = enter_frame_clip(1)
        tags.extend(definition)
        tags.extend(placement)
        for depth in range(2, clip_count + 1):
            _definition, placement = enter_frame_clip(depth)
            tags.extend(placement)
    for frame in range(frame_count):
        if clip_count and frame == frame_count - 1:
            for depth in range(1, clip_count + 1):
                tags.extend(tag(28, struct.pack("<H", depth)))
        tags.extend(tag(12, b"\x00"))
        tags.extend(tag(1))
    tags.extend(tag(0))
    body = frame_size + struct.pack("<HH", frame_rate * 256, frame_count) + tags
    return b"FWS" + bytes([8]) + struct.pack("<I", 8 + len(body)) + body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--enter-frame-clip", action="store_true")
    args = parser.parse_args()
    if args.frames < 1:
        raise ValueError("frames must be positive")
    if not 1 <= args.fps <= 255:
        raise ValueError("fps must be between 1 and 255")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build(args.frames, args.enter_frame_clip, args.fps))


if __name__ == "__main__":
    main()
