#!/usr/bin/env node

import { writeFile } from "node:fs/promises";

const endpoint = process.argv[2] ?? "http://127.0.0.1:9222";
const targetUrl = process.argv[3] ?? "http://127.0.0.1:8060/";
const screenshotPath = process.argv[4];
const expectedConsolePrefix = process.argv[5] ?? "M0_BOOT_OK ";
const scenario = process.argv[6];
const timeoutMs = 20_000;

const targets = await fetch(`${endpoint}/json/list`).then((response) => {
  if (!response.ok) {
    throw new Error(`Cannot list Chromium targets: HTTP ${response.status}`);
  }
  return response.json();
});
const target = targets.find((candidate) => candidate.type === "page");
if (!target) {
  throw new Error("No Chromium page target is available");
}

const socket = new WebSocket(target.webSocketDebuggerUrl);
const pending = new Map();
const consoleMessages = [];
let nextId = 1;

socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) reject(new Error(message.error.message));
    else resolve(message.result);
    return;
  }
  if (message.method === "Runtime.consoleAPICalled") {
    consoleMessages.push(
      message.params.args.map((argument) => argument.value ?? argument.description).join(" ")
    );
  }
});

await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

function call(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

await call("Runtime.enable");
await call("Page.enable");
consoleMessages.length = 0;
await call("Page.navigate", { url: targetUrl });

const deadline = Date.now() + timeoutMs;
while (!consoleMessages.some((message) => message.startsWith(expectedConsolePrefix))) {
  if (Date.now() >= deadline) {
    throw new Error(
      `Timed out waiting for ${expectedConsolePrefix}. Console: ${JSON.stringify(consoleMessages)}`
    );
  }
  await new Promise((resolve) => setTimeout(resolve, 100));
}

if (scenario === "combat") {
  await call("Page.bringToFront");
  const canvasBounds = await call("Runtime.evaluate", {
    expression: `(() => {
      const rect = document.querySelector("canvas")?.getBoundingClientRect();
      return rect ? { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 } : null;
    })()`,
    returnByValue: true,
  });
  if (!canvasBounds.result.value) throw new Error("Combat canvas is missing");
  const { x, y } = canvasBounds.result.value;
  await call("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await call("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
  async function sendKey(type, key, code, windowsVirtualKeyCode) {
    await call("Input.dispatchKeyEvent", {
      type,
      key,
      code,
      windowsVirtualKeyCode,
      nativeVirtualKeyCode: windowsVirtualKeyCode,
    });
  }
  async function holdKey(key, code, windowsVirtualKeyCode, durationMs) {
    await sendKey("keyDown", key, code, windowsVirtualKeyCode);
    await new Promise((resolve) => setTimeout(resolve, durationMs));
    await sendKey("keyUp", key, code, windowsVirtualKeyCode);
  }
  async function waitForActionAfter(action, afterIndex, waitMs = 5_000) {
    const deadline = Date.now() + waitMs;
    while (
      !consoleMessages
        .slice(afterIndex)
        .some((message) => message.includes(`"action":"${action}"`))
    ) {
      if (Date.now() >= deadline) {
        throw new Error(`Timed out waiting for ${action}: ${JSON.stringify(consoleMessages)}`);
      }
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }

  for (const [key, code, keyCode] of [
    ["d", "KeyD", 68],
    ["j", "KeyJ", 74],
    ["k", "KeyK", 75],
    ["s", "KeyS", 83],
    ["u", "KeyU", 85],
    ["i", "KeyI", 73],
  ]) {
    await sendKey("keyUp", key, code, keyCode);
  }

  const walkStart = consoleMessages.length;
  await sendKey("keyDown", "d", "KeyD", 68);
  await waitForActionAfter("走", walkStart);
  await new Promise((resolve) => setTimeout(resolve, 500));
  await sendKey("keyUp", "d", "KeyD", 68);
  const comboStart = consoleMessages.length;
  await sendKey("keyDown", "j", "KeyJ", 74);
  await waitForActionAfter("砍3", comboStart);
  await sendKey("keyUp", "j", "KeyJ", 74);
  await waitForActionAfter("站立", comboStart);
  const jumpStart = consoleMessages.length;
  await sendKey("keyDown", "k", "KeyK", 75);
  await waitForActionAfter("跳", jumpStart);
  await sendKey("keyUp", "k", "KeyK", 75);
  await waitForActionAfter("站立", jumpStart);
  const guardStart = consoleMessages.length;
  await sendKey("keyDown", "s", "KeyS", 83);
  await waitForActionAfter("防御2", guardStart);
  await new Promise((resolve) => setTimeout(resolve, 250));
  await sendKey("keyUp", "s", "KeyS", 83);
  await waitForActionAfter("站立", guardStart);
  const rangedStart = consoleMessages.length;
  await sendKey("keyDown", "u", "KeyU", 85);
  await waitForActionAfter("招1", rangedStart);
  await new Promise((resolve) => setTimeout(resolve, 250));
  await sendKey("keyUp", "u", "KeyU", 85);
  if (screenshotPath) {
    const rangedScreenshot = await call("Page.captureScreenshot", { format: "png" });
    await writeFile(
      screenshotPath.replace(/\.png$/i, "-ranged.png"),
      Buffer.from(rangedScreenshot.data, "base64")
    );
  }
  await waitForActionAfter("站立", rangedStart);
  const specialStart = consoleMessages.length;
  await sendKey("keyDown", "i", "KeyI", 73);
  await waitForActionAfter("必杀", specialStart);
  await sendKey("keyUp", "i", "KeyI", 73);
  for (const action of ["跳", "防御", "招1", "必杀"]) {
    if (!consoleMessages.some((message) => message.includes(`"action":"${action}"`))) {
      throw new Error(`Combat scenario did not reach ${action}: ${JSON.stringify(consoleMessages)}`);
    }
  }
}

// The boot marker is emitted from _ready; allow the browser compositor to present
// the first rendered frame before inspecting the canvas or taking a screenshot.
await new Promise((resolve) => setTimeout(resolve, 1_000));

const evaluated = await call("Runtime.evaluate", {
  expression: `(() => {
    const canvas = document.querySelector("canvas");
    return {
      title: document.title,
      canvas: canvas ? {
        width: canvas.width,
        height: canvas.height,
        clientWidth: canvas.clientWidth,
        clientHeight: canvas.clientHeight,
        visible: getComputedStyle(canvas).visibility === "visible"
      } : null
    };
  })()`,
  returnByValue: true,
});

if (screenshotPath) {
  const screenshot = await call("Page.captureScreenshot", { format: "png" });
  await writeFile(screenshotPath, Buffer.from(screenshot.data, "base64"));
}

console.log(
  JSON.stringify(
    {
      status: "passed",
      url: targetUrl,
      expectedConsolePrefix,
      scenario: scenario ?? null,
      ...evaluated.result.value,
      console: consoleMessages,
      screenshot: screenshotPath ?? null,
    },
    null,
    2
  )
);
socket.close();
