# Retained diagnostics

The initial 120-second native captures for air ranged, guard and interruption
were incomplete. Busy external locks are not capture failures and do not appear
in these results. Later complete captures are kept independently.

The background air-ranged run completed, but both Flash actors changed `sw`
to true at tick 131. From the ready observation (29,365 ms) to tick 131
(150,547 ms), 121,182 ms of wall time elapsed. Main Sprite 1813 uses a
1,000 ms wall-clock countdown; Sprite 1848 frame 2 sets both actors' `sw`.
The following winner timeline is also visible in the retained state trace.
The same first divergence occurs at tick 265 in cancel-super and tick 189
in guard. These are failed full-window comparisons, not passing shortened
windows. No input, field, baseline or tolerance was changed.

A separate scratch capture wrapper removes only LaunchServices `-g` and
extends the watchdog to 600 seconds. It retains source identity checks,
unique per-case paths, process ownership checks and cleanup. It runs under
the same exclusive lock, with window activation explicitly approved. This
changes the capture window launch environment, not SWF or game timers.

The initial interruption fixture has a mistaken super target label despite
normal attack input. Its immutable build remains diagnostic. A separate
`interrupt-normal` fixture keeps the input and declares the actual normal
attack target; its separate corrected capture completed on 2026-11-14 and matched.

The receive-guard source capture completed while its batch parent was paused.
The child saved its environment and original log and exited normally. Its
collector was then run explicitly. The parent's unpersisted capture stdout
is absent; no synthetic capture log is substituted.

The 2026-11-14 unlocked foreground recapture matched all twelve unchanged
intended fixtures. The historical failures above remain unmodified; see the
parent acceptance matrix and dated source-build directories.
