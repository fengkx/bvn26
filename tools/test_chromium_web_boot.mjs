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

if (scenario === "shell") {
  const checked = await call("Runtime.evaluate", {
    expression: `(async () => {
      const assert = (condition, message) => { if (!condition) throw new Error(message); };
      const canvas = document.querySelector("canvas");
      const button = document.querySelector("#fullscreen");
      const audioToggle = document.querySelector("#audio-toggle");
      const muteToggle = document.querySelector("#mute-toggle");
      const volumePanel = document.querySelector("#volume-panel");
      const volumeSlider = document.querySelector("#volume-slider");
      const volumeStatus = document.querySelector("#volume-status");
      const originalAudioSettings = localStorage.getItem("bvn26.audio.v1");
      assert(!document.fullscreenElement, "Must start windowed");
      const bounds = canvas.getBoundingClientRect();
      assert(bounds.top > 50 && bounds.width < innerWidth, "Toolbar and page margins must remain accessible");
      assert(document.querySelector("#audio-control") && volumeSlider, "Persistent volume controls must be present");
      audioToggle.click();
      await new Promise(resolve => setTimeout(resolve, 120));
      assert(!volumePanel.hidden, "Volume popover did not open");
      assert(volumeStatus.textContent.startsWith("音乐与音效"), "Godot did not acknowledge applied audio settings");
      volumeSlider.value = "37";
      volumeSlider.dispatchEvent(new Event("input", { bubbles: true }));
      await new Promise(resolve => setTimeout(resolve, 120));
      assert(volumeStatus.textContent === "音乐与音效 37%", "Slider did not reach the Godot Master bus");
      muteToggle.click();
      await new Promise(resolve => setTimeout(resolve, 120));
      assert(volumeStatus.textContent === "音乐与音效已静音", "Mute did not reach the Godot Master bus");
      muteToggle.click();
      await new Promise(resolve => setTimeout(resolve, 120));
      assert(volumeStatus.textContent === "音乐与音效 37%", "Unmute did not restore the previous level");
      volumeSlider.value = "0";
      volumeSlider.dispatchEvent(new Event("input", { bubbles: true }));
      await new Promise(resolve => setTimeout(resolve, 120));
      assert(volumeStatus.textContent === "音乐与音效 0%", "Zero slider level was not applied");
      const silentSetting = JSON.parse(localStorage.getItem("bvn26.audio.v1"));
      assert(silentSetting.volume === 0 && silentSetting.lastNonzero === 37, "Audio setting persistence is incorrect");
      muteToggle.click();
      await new Promise(resolve => setTimeout(resolve, 120));
      assert(volumeStatus.textContent === "音乐与音效 37%", "One click from zero must restore the previous level");
      const context = new MouseEvent("contextmenu", { bubbles: true, cancelable: true });
      assert(document.querySelector("#toolbar").dispatchEvent(context), "Toolbar must allow browser context menu");
      button.click();
      await new Promise(resolve => setTimeout(resolve, 300));
      assert(document.fullscreenElement?.id === "player", "Fullscreen entry failed");
      const fullBounds = canvas.getBoundingClientRect();
      assert(Math.abs(fullBounds.width / fullBounds.height - 1.5) < .01, "Fullscreen must preserve aspect ratio");
      assert(Math.abs(fullBounds.width - innerWidth) < 2 || Math.abs(fullBounds.height - innerHeight) < 2, "Game must fill a screen dimension");
      assert(getComputedStyle(document.querySelector("#toolbar")).position === "absolute", "Toolbar must not consume fullscreen space");
      assert(getComputedStyle(document.querySelector("#toolbar")).opacity === "0", "Fullscreen controls must start hidden");
      assert(parseFloat(getComputedStyle(document.querySelector("#edge-indicator")).opacity) > 0, "Fullscreen edge hint must remain visible");
      const indicatorBounds = document.querySelector("#edge-indicator").getBoundingClientRect();
      assert(indicatorBounds.top === 0 && indicatorBounds.height <= 12 && getComputedStyle(document.querySelector("#edge-indicator")).backgroundColor === "rgba(0, 0, 0, 0)", "Fullscreen hint must be a slim transparent top-edge hit area");
      document.querySelector("#player").dispatchEvent(new PointerEvent("pointermove", { bubbles: true, clientX: innerWidth - 80, clientY: 5 }));
      await new Promise(resolve => setTimeout(resolve, 300));
      assert(getComputedStyle(document.querySelector("#toolbar")).opacity === "1", "Top-edge movement must reveal tools");
      const edge = document.querySelector("#edge-indicator");
      edge.dispatchEvent(new PointerEvent("pointerenter", { pointerType: "mouse" }));
      await new Promise(resolve => setTimeout(resolve, 800));
      assert(getComputedStyle(document.querySelector("#toolbar")).opacity === "1", "Dock must stay visible while the pointer rests on its edge target");
      edge.dispatchEvent(new PointerEvent("pointerleave", { pointerType: "mouse" }));
      await new Promise(resolve => setTimeout(resolve, 800));
      assert(getComputedStyle(document.querySelector("#toolbar")).opacity === "0", "Dock must tuck after leaving the edge target");
      edge.dispatchEvent(new PointerEvent("pointerenter", { pointerType: "mouse" }));
      audioToggle.click();
      assert(!volumePanel.hidden, "Fullscreen volume popover did not open");
      volumeSlider.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }));
      assert(volumePanel.hidden, "Escape should close the popover when the browser delivers the key event");
      edge.dispatchEvent(new PointerEvent("pointerleave", { pointerType: "mouse" }));
      audioToggle.click();
      document.querySelector("#toolbar").dispatchEvent(new PointerEvent("pointerleave", { pointerType: "mouse" }));
      await new Promise(resolve => setTimeout(resolve, 800));
      assert(volumePanel.hidden && getComputedStyle(document.querySelector("#toolbar")).opacity === "0", "Popover must close when the pointer leaves the dock");
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true }));
      assert(document.querySelector("#toolbar").classList.contains("keyboard-focus"), "Keyboard modality should protect focused tools");
      document.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, pointerType: "mouse" }));
      assert(!document.querySelector("#toolbar").classList.contains("keyboard-focus"), "Mouse focus must not pin the toolbar open");
      button.click();
      await new Promise(resolve => setTimeout(resolve, 300));
      assert(!document.fullscreenElement, "Fullscreen exit failed");
      // Read the exact Blob passed to the download, without changing its contents.
      const original = URL.createObjectURL;
      let report;
      URL.createObjectURL = blob => { report = blob; return original(blob); };
      console.error("SHELL_TEST_ERROR");
      document.querySelector("#download").click();
      let data = JSON.parse(await report.text());
      assert(data.entries.some(e => e.message.includes("M0_BOOT_OK")), "Engine output missing");
      assert(data.entries.some(e => e.message.includes("SHELL_TEST_ERROR")), "Errors missing");
      assert(data.userAgent && data.startedAt && data.canvas.width, "Environment missing");
      assert(!data.page.includes("?"), "Query parameters must be omitted");
      for (let i = 0; i < 2100; i++) window.bvnLog("test", i);
      document.querySelector("#download").click();
      data = JSON.parse(await report.text());
      assert(data.entries.length === 2000 && data.droppedEntries > 0, "Log must be bounded");
      URL.createObjectURL = original;
      assert(document.activeElement === canvas, "Game focus must be restored");
      return { passed: true, retainedEntries: data.entries.length, originalAudioSettings };
    })()`,
    awaitPromise: true,
    userGesture: true,
    returnByValue: true,
  });
  if (checked.exceptionDetails) throw new Error(JSON.stringify(checked.exceptionDetails));
  const audioSettingsSnapshot = checked.result.value;
  console.log(JSON.stringify({ shell: { passed: audioSettingsSnapshot.passed, retainedEntries: audioSettingsSnapshot.retainedEntries } }));
  const savedSettings = JSON.stringify(audioSettingsSnapshot.originalAudioSettings);
  await call("Runtime.evaluate", {
    expression: `(() => { const saved = ${savedSettings}; if (saved === null) localStorage.removeItem("bvn26.audio.v1"); else localStorage.setItem("bvn26.audio.v1", saved); return true; })()`,
    returnByValue: true,
  });
  const previousBoots = consoleMessages.filter(message => message.startsWith(expectedConsolePrefix)).length;
  await call("Page.reload");
  const reloadDeadline = Date.now() + timeoutMs;
  while (consoleMessages.filter(message => message.startsWith(expectedConsolePrefix)).length <= previousBoots) {
    if (Date.now() >= reloadDeadline) throw new Error("Page did not reload after restoring saved audio settings");
    await new Promise(resolve => setTimeout(resolve, 100));
  }
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
