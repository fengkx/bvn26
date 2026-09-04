#!/usr/bin/env node

import { writeFile } from "node:fs/promises";

const endpoint = process.argv[2] ?? "http://127.0.0.1:9222";
const targetUrl = process.argv[3] ?? "http://127.0.0.1:8060/";
const screenshotPath = process.argv[4];
const expectedConsolePrefix = process.argv[5] ?? "M0_BOOT_OK ";
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
      ...evaluated.result.value,
      console: consoleMessages,
      screenshot: screenshotPath ?? null,
    },
    null,
    2
  )
);
socket.close();
