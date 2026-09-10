# Kakashi base super source capture r02

- Fixture: `/tmp/kakashi-cases-r01/kakashi-863-super-down-special.json`
- Build and capture: `/tmp/bvn-kakashi-super-probe-r02`
- Marker: `original_capture_completed_not_port_parity`
- Input delivery: `down` pressed 5 reads, `special` pressed 1 read; `frames_after_ready=1100`.
- Source state coverage: p1 source frame 863 at fight tick 13, 864 at 14, and 887 at 37.
- Frame 900 is a conditional `gotoAndStop("超必杀2"); play();`; the capture transitions from frame 899 at tick 49 to label frame 921 at tick 50, proving the branch reached the label without an independent frame-900 state sample.
- Source frame range reached: 1..1093; the capture reaches the required 864/887/900 semantic checkpoints.
- This is original-player source observation only. Production replay comparison: `/tmp/bvn-kakashi-super-probe-r02/production-comparison-1100.json`, complete with 2202/2202 states but different; first difference is tick 90, p1 x original 301.35 vs native 324.0 (1011 x-field differences).
