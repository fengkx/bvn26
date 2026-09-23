import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { randomBytes, randomInt } from "node:crypto";
import { once } from "node:events";
import WebSocket from "ws";

test(
  "production Wrangler configuration serves authenticated room WebSockets",
  { timeout: 45_000 },
  async (t) => {
    const directory = await mkdtemp(join(tmpdir(), "bvn-wrangler-"));
    const port = randomInt(20000, 40000);
    const process = spawn(
      globalThis.process.execPath,
      [
        "node_modules/wrangler/bin/wrangler.js",
        "dev",
        "--local",
        "--ip",
        "127.0.0.1",
        "--port",
        String(port),
        "--persist-to",
        join(directory, "state"),
      ],
      {
        env: {
          ...globalThis.process.env,
          WRANGLER_SEND_METRICS: "false",
          WRANGLER_LOG_PATH: join(directory, "wrangler.log"),
        },
        stdio: ["ignore", "pipe", "pipe"],
      },
    );
    let output = "";
    process.stdout.on("data", (chunk) => {
      output += chunk;
    });
    process.stderr.on("data", (chunk) => {
      output += chunk;
    });
    t.after(async () => {
      if (process.exitCode === null) {
        process.kill("SIGTERM");
        await once(process, "exit");
      }
      await rm(directory, { recursive: true, force: true });
    });
    const base = `http://127.0.0.1:${port}`;
    let ready = false;
    for (let attempt = 0; attempt < 150; attempt++) {
      if (process.exitCode !== null) break;
      try {
        ready = (await fetch(base + "/health")).ok;
      } catch {}
      if (ready) break;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    assert.ok(ready, output);
    const token = () => randomBytes(32).toString("base64url");
    const sessionToken = token();
    const response = await fetch(base + "/v1/rooms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        createToken: token(),
        inviteToken: token(),
        sessionToken,
        nickname: "wrangler-test",
        compatibility: {
          protocol: 1,
          build: "a".repeat(64),
          content: "b".repeat(64),
        },
      }),
    });
    assert.equal(response.status, 201, output);
    const { roomId } = await response.json();
    const ticketResponse = await fetch(`${base}/v1/rooms/${roomId}/ticket`, {
      method: "POST",
      headers: { Authorization: `Bearer ${sessionToken}` },
    });
    assert.equal(ticketResponse.status, 200);
    const { ticket } = await ticketResponse.json();
    const ws = new WebSocket(
      `${base.replace("http:", "ws:")}/v1/rooms/${roomId}/socket`,
      ["bvn.v1", ticket],
    );
    t.after(() => ws.terminate());
    const stateMessage = once(ws, "message");
    await once(ws, "open");
    assert.equal(
      JSON.parse((await stateMessage)[0]).state.members[0].nickname,
      "wrangler-test",
    );
    ws.terminate();
  },
);
