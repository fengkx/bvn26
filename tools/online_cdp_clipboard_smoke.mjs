#!/usr/bin/env node

const endpoint = new URL("http://127.0.0.1:9234");
const pageUrl = "http://127.0.0.1:8000/";
const testText = "BVN_CLIPBOARD_TEST_9234";
const timeoutMs = 15_000;

if (endpoint.hostname !== "127.0.0.1" || endpoint.port !== "9234") {
  throw new Error("Clipboard smoke is restricted to its dedicated loopback Chrome");
}

const versionResponse = await fetch(new URL("/json/version", endpoint));
if (!versionResponse.ok) throw new Error("Dedicated Chrome CDP endpoint unavailable");
const browserVersion = await versionResponse.json();
const browser = await openCdp(browserVersion.webSocketDebuggerUrl);
let targetId = "";
let page;

try {
  const target = await call(browser, "Target.createTarget", { url: "about:blank" });
  targetId = target.targetId;
  const targetsResponse = await fetch(new URL("/json/list", endpoint));
  if (!targetsResponse.ok) throw new Error("Cannot inspect dedicated Chrome tabs");
  const pageTarget = (await targetsResponse.json()).find(
    (item) => item.id === targetId && item.type === "page",
  );
  if (!pageTarget) throw new Error("Dedicated clipboard test page was not created");
  page = await openCdp(pageTarget.webSocketDebuggerUrl);

  await call(page, "Network.enable");
  await call(page, "Runtime.enable");
  await call(page, "Page.enable");
  await call(page, "Emulation.setFocusEmulationEnabled", { enabled: true });
  await call(page, "Page.setWebLifecycleState", { state: "active" });
  await call(page, "Page.addScriptToEvaluateOnNewDocument", {
    source: buildTestSeam(testText),
  });
  await call(page, "Page.navigate", { url: pageUrl });

  await waitForPage(page);
  const initial = await evaluate(page, buildSetup(testText));
  if (!initial?.focused || !initial?.visible) {
    throw new Error("Clipboard test field did not receive page focus");
  }

  await sendShortcut(page, "Meta", 4);
  await sendShortcut(page, "Control", 2);
  const activeResult = await evaluate(page, "JSON.stringify(window.__bvnClipboardProbe)");

  const inactiveResult = await evaluate(page, `(() => {
    const state = window.__bvnClipboardProbe;
    const priorCallbacks = state.callbacks.length;
    window.bvnOnlinePasteTargetActive = false;
    const field = document.getElementById("bvn-clipboard-test-ime");
    field.focus();
    const transfer = new DataTransfer();
    transfer.setData("text/plain", ${JSON.stringify(testText)});
    const paste = new ClipboardEvent("paste", {
      bubbles: true,
      cancelable: true,
      clipboardData: transfer,
    });
    field.dispatchEvent(paste);
    return JSON.stringify({
      callbackCount: state.callbacks.length,
      priorCallbacks,
      pasteDefaultPrevented: paste.defaultPrevented,
    });
  })()`);

  const outsideResult = await evaluate(page, `(() => {
    const state = window.__bvnClipboardProbe;
    const priorCallbacks = state.callbacks.length;
    window.bvnOnlinePasteTargetActive = true;
    const button = document.getElementById("bvn-clipboard-test-outside");
    button.focus();
    const transfer = new DataTransfer();
    transfer.setData("text/plain", ${JSON.stringify(testText)});
    const paste = new ClipboardEvent("paste", {
      bubbles: true,
      cancelable: true,
      clipboardData: transfer,
    });
    button.dispatchEvent(paste);
    return JSON.stringify({
      callbackCount: state.callbacks.length,
      priorCallbacks,
      pasteDefaultPrevented: paste.defaultPrevented,
      activeElement: document.activeElement?.id || "",
    });
  })()`);

  const active = JSON.parse(activeResult);
  const inactive = JSON.parse(inactiveResult);
  const outside = JSON.parse(outsideResult);
  const result = summarize(active, inactive, outside, testText);
  console.log(JSON.stringify({
    marker: "ONLINE_CDP_CLIPBOARD_SMOKE",
    chrome: browserVersion.Browser,
    page: pageUrl,
    testTextUsedOnlyInPageMemory: true,
    systemClipboardApiCalled: false,
    result,
  }));
  if (!result.passed) process.exitCode = 1;
} finally {
  if (page) page.close();
  if (targetId) {
    try { await call(browser, "Target.closeTarget", { targetId }); } catch {}
  }
  browser.close();
}

function buildTestSeam(value) {
  return `(() => {
    const testText = ${JSON.stringify(value)};
    const state = {
      trustedShortcuts: [],
      syntheticPasteEvents: [],
      callbacks: [],
      shortcutCallbacks: [],
      inputTargetKeydowns: 0,
    };
    window.__bvnClipboardProbe = state;
    window.addEventListener("keydown", (event) => {
      const key = String(event.key || "").toLowerCase();
      if (key !== "v" || (!event.metaKey && !event.ctrlKey)) return;
      const target = event.target;
      const isTestInput = target?.id === "bvn-clipboard-test-ime";
      const enabled = window.bvnOnlinePasteTargetActive === true;
      state.trustedShortcuts.push({
        trusted: event.isTrusted,
        key,
        meta: event.metaKey,
        control: event.ctrlKey,
        target: target?.id || "",
        enabled,
      });
      if (isTestInput) event.preventDefault();
      if (!isTestInput || !enabled) return;
      const transfer = new DataTransfer();
      transfer.setData("text/plain", testText);
      const paste = new ClipboardEvent("paste", {
        bubbles: true,
        cancelable: true,
        clipboardData: transfer,
      });
      target.dispatchEvent(paste);
      state.syntheticPasteEvents.push({
        trusted: paste.isTrusted,
        hasPlainText: transfer.types.includes("text/plain"),
        defaultPrevented: paste.defaultPrevented,
      });
    }, true);
  })();`;
}

function buildSetup(value) {
  return `(() => {
    const state = window.__bvnClipboardProbe;
    const input = document.createElement("textarea");
    input.id = "bvn-clipboard-test-ime";
    input.className = "ime";
    input.value = "left|right";
    input.style.cssText = "position:fixed;left:8px;top:8px;width:220px;height:32px;z-index:999999";
    input.addEventListener("keydown", () => state.inputTargetKeydowns++);
    document.body.appendChild(input);
    const outside = document.createElement("button");
    outside.id = "bvn-clipboard-test-outside";
    outside.textContent = "test focus target";
    outside.style.cssText = "position:fixed;left:8px;top:48px;z-index:999999";
    document.body.appendChild(outside);
    window.bvnOnlinePasteTargetActive = true;
    window.bvnOnlinePasteCallback = (text) => state.callbacks.push(String(text));
    window.bvnOnlineShortcutCallback = (key) => state.shortcutCallbacks.push(String(key));
    input.focus();
    return JSON.stringify({
      focused: document.activeElement === input,
      visible: document.visibilityState === "visible" && document.hasFocus(),
      activeElement: document.activeElement?.id || "",
      navigatorClipboardTouched: false,
      expectedTextPresentOnlyInClosure: ${JSON.stringify(value)}.length > 0,
    });
  })()`;
}

function summarize(active, inactive, outside, value) {
  const shortcuts = active.trustedShortcuts;
  const callbacks = active.callbacks;
  const meta = shortcuts.find((event) => event.meta && !event.control);
  const control = shortcuts.find((event) => event.control && !event.meta);
  return {
    passed: Boolean(
      meta?.trusted && control?.trusted &&
      callbacks.length === 2 && callbacks.every((text) => text === value) &&
      active.syntheticPasteEvents.length === 2 &&
      active.syntheticPasteEvents.every((event) => !event.trusted && event.hasPlainText && event.defaultPrevented) &&
      active.shortcutCallbacks.length === 0 &&
      inactive.callbackCount === inactive.priorCallbacks &&
      outside.callbackCount === outside.priorCallbacks &&
      outside.activeElement === "bvn-clipboard-test-outside"
    ),
    trustedMetaV: Boolean(meta?.trusted && meta.target === "bvn-clipboard-test-ime"),
    trustedCtrlV: Boolean(control?.trusted && control.target === "bvn-clipboard-test-ime"),
    syntheticTextPlainReachedShellCallback: callbacks.length === 2 && callbacks.every((text) => text === value),
    shellPreventedPasteDefault: active.syntheticPasteEvents.length === 2 && active.syntheticPasteEvents.every((event) => event.defaultPrevented),
    pasteShortcutCallbackNotUsed: active.shortcutCallbacks.length === 0,
    inactiveEditTargetIgnored: inactive.callbackCount === inactive.priorCallbacks,
    nonEditTargetIgnored: outside.callbackCount === outside.priorCallbacks,
    noSystemClipboardApiUsed: true,
  };
}

async function waitForPage(socket) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    const state = await evaluate(socket, `JSON.stringify({
      ready: document.readyState === "complete",
      canvas: !!document.querySelector("canvas"),
      visible: document.visibilityState === "visible" && document.hasFocus(),
    })`);
    const parsed = JSON.parse(state);
    if (parsed.ready && parsed.canvas && parsed.visible) return;
    await delay(100);
  }
  throw new Error("Local game shell did not become focused and ready within 30 seconds");
}

async function sendShortcut(socket, modifierName, modifier) {
  let keyDownSent = false;
  try {
    await call(socket, "Input.dispatchKeyEvent", {
      type: "keyDown",
      modifiers: modifier,
      key: "v",
      code: "KeyV",
      text: "v",
      unmodifiedText: "v",
      windowsVirtualKeyCode: 86,
      nativeVirtualKeyCode: 86,
    });
    keyDownSent = true;
    await delay(50);
  } finally {
    if (keyDownSent) {
      try {
        await call(socket, "Input.dispatchKeyEvent", {
          type: "keyUp",
          modifiers: modifier,
          key: "v",
          code: "KeyV",
          windowsVirtualKeyCode: 86,
          nativeVirtualKeyCode: 86,
        });
      } catch {}
    }
  }
}

async function evaluate(socket, expression) {
  const response = await call(socket, "Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (response.exceptionDetails) throw new Error("Clipboard page evaluation failed");
  return response.result?.value;
}

function openCdp(url) {
  const socket = new WebSocket(url);
  const pending = new Map();
  let nextId = 1;
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (!message.id || !pending.has(message.id)) return;
    const waiter = pending.get(message.id);
    pending.delete(message.id);
    clearTimeout(waiter.timer);
    if (message.error) waiter.reject(new Error("CDP command failed"));
    else waiter.resolve(message.result ?? {});
  });
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("CDP WebSocket open timed out")), timeoutMs);
    socket.addEventListener("open", () => {
      clearTimeout(timer);
      socket.call = (method, params = {}) => {
        const id = nextId++;
        return new Promise((resolveCall, rejectCall) => {
          const callTimer = setTimeout(() => {
            pending.delete(id);
            rejectCall(new Error(`CDP ${method} timed out`));
          }, timeoutMs);
          pending.set(id, { resolve: resolveCall, reject: rejectCall, timer: callTimer });
          socket.send(JSON.stringify({ id, method, params }));
        });
      };
      resolve(socket);
    }, { once: true });
    socket.addEventListener("error", () => {
      clearTimeout(timer);
      reject(new Error("CDP WebSocket failed"));
    }, { once: true });
  });
}

function call(socket, method, params = {}) {
  return socket.call(method, params);
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
