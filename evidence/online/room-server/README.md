# Local Durable Object server evidence

2026-09-22. Scope: the standalone TypeScript room service, not complete online
battle acceptance. See [implementation status](../../../docs/online-multiplayer/SERVER_IMPLEMENTATION.md)
and [runbook/protocol](../../../services/matchmaking/README.md).

Commands run from `services/matchmaking/`:

```sh
npm ci --ignore-scripts
npm run format:check
npm test
WRANGLER_SEND_METRICS=false WRANGLER_LOG_PATH=/tmp/bvn-matchmaking-wrangler.log npm run build
```

`npm test` includes strict TypeScript checking, the current menu catalog check,
workerd/SQLite contract scenarios, and a separate real Wrangler startup plus
WebSocket check. The [retained 14-test output](test-output.txt) is the
2026-09-22 baseline. The 2026-09-23 short-code follow-up passed 17 tests; see
[short-code validation](short-code-validation.md) for its scope and commands.
The restart scenario disposes workerd, starts a new process with the same
explicit persistence directory, and compares the epoch/room state before
reconnecting two new network WebSockets. This is persistence recovery, not a
claim that a socket survives process termination.

The alarm fixture moves the stored deadline into the past and schedules a real
runtime alarm without a follow-up room request. Other cases call the production
alarm handler against controlled stored deadlines to distinguish lobby expiry,
active matches, preparation timeout and lease expiry. The test-only subclass
and control route are outside the production entry point.

[Source hashes and tool versions](verification.json) identify the measured backend.
Raw test databases, built workers, CLI logs, invite/seat/TURN secrets and SDP are
not retained. No cloud resource was created. Provider connectivity, deployed
natural hibernation/failover, ten-room battle soak and Godot/Chrome two-machine
integration remain unmeasured. Test duration is not a gameplay performance result.

Repository verification additionally runs `tools/verify.py`,
`tools/check_handoff.py` and `tools/validate_contracts.py`. The latter validates
existing game schemas/examples; server protocol rejection is exercised by its
TypeScript/Zod contract tests, not by those game schemas.

The backend checks and repository handoff/schema checks passed. The full
`tools/verify.py` run was blocked by concurrent unrelated worktree hash changes
in `godot/timeline_preview.gd`, `godot/stage_hit_runtime.gd`, `godot/main.gd`,
`godot/hit_effect_runtime.gd` and `godot/shadow_snapshot.gd`. This server change
did not rewrite those files or their manifest entries to hide the mismatch.
Only the changed `docs/STATUS.md` hash was refreshed for this task.
