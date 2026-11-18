import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { setTimeout as delay } from "node:timers/promises";

const [endpoint, url, output] = process.argv.slice(2);
if (!output) throw new Error("Usage: node browser_keys.mjs CDP_ENDPOINT GAME_URL OUTPUT_DIR");
const targets = await (await fetch(new URL("/json/list", endpoint))).json();
const page = targets.find((target) => target.type === "page");
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve) => socket.addEventListener("open", resolve, { once: true }));

let nextId = 0;
let finished = false;
let failure;
const pending = new Map();
const lines = [];

function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function observe(message) {
  if (message.id) {
    const call = pending.get(message.id);
    if (!call) return;
    pending.delete(message.id);
    if (message.error) call.reject(new Error(message.error.message));
    else call.resolve(message.result);
    return;
  }
  if (message.method === "Runtime.exceptionThrown") {
    throw new Error(message.params.exceptionDetails.text);
  }
  if (message.method !== "Runtime.consoleAPICalled") return;
  const line = message.params.args.map((arg) => arg.value ?? arg.description).join(" ");
  lines.push(line);
  if (line.startsWith("LIVE_KEY ")) {
    await send("Runtime.evaluate", { expression: 'document.querySelector("canvas").focus()' });
    const key = { key: "o", code: "KeyO", windowsVirtualKeyCode: 79, nativeVirtualKeyCode: 79 };
    await send("Input.dispatchKeyEvent", { type: "keyDown", ...key });
    await delay(300);
    await send("Input.dispatchKeyEvent", { type: "keyUp", ...key });
  } else if (line.startsWith("LIVE_SCREEN ")) {
    const name = line.slice("LIVE_SCREEN ".length);
    const { data } = await send("Page.captureScreenshot", { format: "jpeg", quality: 88 });
    writeFileSync(join(output, name + ".jpg"), Buffer.from(data, "base64"));
  } else if (line.startsWith("LIVE_FAIL ")) {
    throw new Error(line);
  } else if (line === "LIVE_DONE") {
    finished = true;
  }
}

socket.addEventListener("message", (event) => {
  observe(JSON.parse(event.data)).catch((error) => { failure = error; });
});
try {
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Page.navigate", { url });
  const deadline = Date.now() + 720_000;
  while (!finished && !failure && Date.now() < deadline) await delay(250);
  if (failure) throw failure;
  if (!finished) throw new Error("Timed out waiting for LIVE_DONE");
} finally {
  writeFileSync(join(output, "browser-console.json"), JSON.stringify(lines));
  socket.close();
}
