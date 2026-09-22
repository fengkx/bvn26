# Native boot/menu probe r15

Fresh source-preserving build (not a metadata-only copy) with real native Flash input.

- Run ID: `boot-ready-r15-20260921`
- SWF SHA256: `3955598e3e07b152d9b30d76a000d4aedf46e4365d6899da78c2ec31442a6ebb`
- Build SHA256: `0fd6a56d589336ed274cb578ba83e42705807e8b0ddc032e74f9684e8b541cfe`
- Capture: 684 events, `done=true`
- Native input: macOS virtual key 38 (`J`), 300 ms held; source binding is `_root.j=74`.

Observed event sequence: `root_frame_1`, `root_frame_10`, `selection`, `battle_entry`, `intro_load`, `intro_poll`, `ready_begin`, `game_running`, and `done/ready_horizon`.

Screenshots are immediate window captures from the same run. The evidence covers the source default path through Ready; it does not claim full fighter/UI parity.
