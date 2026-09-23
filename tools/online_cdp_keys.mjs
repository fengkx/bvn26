#!/usr/bin/env node

const endpoint = new URL(process.env.BVN_CDP_ENDPOINT ?? "http://127.0.0.1:9232");
const targetId = process.env.BVN_CDP_TARGET_ID;
const [action = "list", ...args] = process.argv.slice(2);
const timeoutMs = 10_000;

if (
  endpoint.protocol !== "http:" ||
  !["127.0.0.1", "localhost"].includes(endpoint.hostname) ||
  endpoint.port !== "9232"
) {
  throw new Error("Only the dedicated loopback CDP endpoint on port 9232 is allowed");
}

const allowedPage = (value) => {
  try {
    const url = new URL(value);
    return (
      url.protocol === "http:" &&
      ["127.0.0.1", "localhost"].includes(url.hostname) &&
      ["8000", "8787"].includes(url.port)
    );
  } catch {
    return false;
  }
};

const targetsResponse = await fetch(new URL("/json/list", endpoint));
if (!targetsResponse.ok) throw new Error(`Cannot list CDP targets: HTTP ${targetsResponse.status}`);
const pages = (await targetsResponse.json()).filter((target) => target.type === "page");
const page = targetId
  ? pages.find((target) => target.id === targetId && allowedPage(target.url))
  : pages.find((target) => allowedPage(target.url));

if (action === "list") {
  console.log(JSON.stringify(pages.map(({ id, url }) => ({ id, url: allowedPage(url) ? url : "<not an approved local page>" }))));
  process.exit(0);
}
if (!page) {
  throw new Error(targetId
    ? "The requested CDP target is missing or is not on an approved local page"
    : "No page open on the approved localhost:8000 or localhost:8787 origins");
}

const socket = new WebSocket(page.webSocketDebuggerUrl);
const pending = new Map();
const handlers = new Set();
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
  for (const handler of handlers) handler(message);
});
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("Timed out opening the CDP page connection")), timeoutMs);
  socket.addEventListener("open", () => { clearTimeout(timer); resolve(); }, { once: true });
  socket.addEventListener("error", (event) => { clearTimeout(timer); reject(event); }, { once: true });
});

function call(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`Timed out waiting for CDP ${method}`));
    }, timeoutMs);
    pending.set(id, {
      resolve: (value) => { clearTimeout(timer); resolve(value); },
      reject: (error) => { clearTimeout(timer); reject(error); },
    });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function safeKeyUp(key, code, vk) {
  try {
    await sendKey("keyUp", key, code, Number(vk));
  } catch {
    // Preserve the original failure if the target has already closed.
  }
}

async function focusCanvas() {
  const result = await call("Runtime.evaluate", {
    expression: `(() => { const canvas = document.querySelector("canvas"); canvas?.focus(); return !!canvas && document.activeElement === canvas; })()`,
    returnByValue: true,
  });
  if (!result.result.value) throw new Error("Game canvas not found or cannot receive focus");
}

function safePath(rawUrl) {
  const url = new URL(rawUrl);
  if (!allowedPage(url.href)) return null;
  return url.pathname
    .replace(/\/rooms?\/[^/]+/g, (match) => `${match.split("/").slice(0, 2).join("/")}/<id>`)
    .replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi, "<id>");
}

function safeException(details) {
  const exception = details.exception ?? {};
  const rawDescription = String(exception.description ?? details.text ?? "");
  const lines = rawDescription.split(/\r?\n/);
  const sensitive = /authorization|bearer|invite[_ -]?token|session[_ -]?token|credential|password|\bsdp\b|ice[_ -]?candidate|request[_ -]?body|headers?/i;
  const sanitizeLine = (value) => {
    if (sensitive.test(value)) return "<redacted sensitive error text>";
    return value
      .replace(/https?:\/\/[^\s)]+/gi, "<url>")
      .replace(/\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, "<redacted>")
      .replace(/\b[a-f0-9]{8}-[a-f0-9-]{27,}\b/gi, "<id>")
      .replace(/\b[A-Za-z0-9_-]{48,}\b/g, "<redacted>")
      .slice(0, 240);
  };
  const callFrames = details.stackTrace?.callFrames ?? [];
  const stackFunctions = callFrames.map((frame) => {
    const name = String(frame.functionName ?? "<anonymous>");
    return /^[A-Za-z0-9_.$<>-]{1,100}$/.test(name) ? name : "<anonymous>";
  }).filter(Boolean).slice(0, 5);
  const sourceLocation = callFrames[0] ? {
    line: Number(callFrames[0].lineNumber) + 1,
    column: Number(callFrames[0].columnNumber) + 1,
  } : null;
  if (stackFunctions.length === 0) {
    stackFunctions.push(...lines.slice(1).map((line) => {
    const match = line.match(/\bat\s+([^\s(]+)/);
    return match && /^[A-Za-z0-9_.$<>-]{1,100}$/.test(match[1]) ? match[1] : null;
    }).filter(Boolean).slice(0, 5));
  }
  const className = /^[A-Za-z][A-Za-z0-9]{0,40}$/.test(exception.className ?? "") ? exception.className : "Error";
  return { name: className, message: sanitizeLine(lines[0] ?? "<no message>"), stackFunctions, sourceLocation };
}

async function watch(durationMs, afterEnable = async () => {}) {
  const events = [];
  const requests = new Map();
  const onMessage = (message) => {
    if (message.method === "Network.requestWillBeSent") {
      const path = safePath(message.params.request.url);
      if (path === null) return;
      const request = { method: message.params.request.method, path };
      requests.set(message.params.requestId, request);
      events.push({ event: "request", ...request });
    } else if (message.method === "Network.responseReceived") {
      const request = requests.get(message.params.requestId);
      if (!request) return;
      events.push({ event: "response", ...request, status: Number(message.params.response.status) });
    } else if (message.method === "Network.loadingFailed") {
      const request = requests.get(message.params.requestId);
      if (!request) return;
      events.push({ event: "failed", ...request, error: String(message.params.errorText ?? "unknown") });
      requests.delete(message.params.requestId);
    } else if (message.method === "Network.loadingFinished") {
      requests.delete(message.params.requestId);
    } else if (message.method === "Runtime.consoleAPICalled") {
      const values = (message.params.args ?? []).map((arg) => String(arg.value ?? arg.description ?? ""));
      const text = values.join(" ");
      const prefix = "Online HTTP diagnostic (redacted): ";
      if (text.includes(prefix)) {
        const suffix = text.slice(text.indexOf(prefix) + prefix.length);
        try {
          const parsed = JSON.parse(suffix);
          events.push({ event: "redacted_http_diagnostic", phase: String(parsed.phase ?? "unknown"),
            transportResult: parsed.transportResult ?? "unknown", httpStatus: Number(parsed.httpStatus ?? 0),
            requestErrorCode: Number(parsed.requestErrorCode ?? -1) });
        } catch {
          events.push({ event: "redacted_http_diagnostic", parseError: true });
        }
      } else if (["warning", "error", "assert"].includes(message.params.type)) {
        events.push({ event: "console", severity: message.params.type, message: "<suppressed>" });
      }
    } else if (message.method === "Runtime.exceptionThrown") {
      events.push({ event: "console", severity: "exception", ...safeException(message.params.exceptionDetails ?? {}) });
    }
  };
  handlers.add(onMessage);
  try {
    await call("Network.enable");
    await call("Runtime.enable");
    await afterEnable();
    await new Promise((resolve) => setTimeout(resolve, durationMs));
    return events;
  } finally {
    handlers.delete(onMessage);
  }
}

async function sendKey(type, key, code, virtualKeyCode, raw = false) {
  if (!key || !code || !Number.isInteger(virtualKeyCode)) {
    throw new Error("Expected key, code, and integer virtual-key-code");
  }
  await call("Input.dispatchKeyEvent", {
    type: type === "keyUp" ? "keyUp" : raw ? "rawKeyDown" : "keyDown",
    key,
    code,
    windowsVirtualKeyCode: virtualKeyCode,
    nativeVirtualKeyCode: virtualKeyCode,
  });
}

if (action === "focus") {
  await call("Page.bringToFront");
  await focusCanvas();
} else if (action === "watch") {
  const durationMs = Number(args[0] ?? 10_000);
  if (!Number.isInteger(durationMs) || durationMs < 1 || durationMs > 60_000) {
    throw new Error("Watch duration must be an integer from 1 to 60000 milliseconds");
  }
  await call("Page.bringToFront");
  const events = await watch(durationMs);
  console.log(JSON.stringify({ action, targetId: page.id, page: page.url, events }));
} else if (action === "probe" || action === "probe-focused") {
  const durationMs = Number(args[0] ?? 5_000);
  if (!Number.isInteger(durationMs) || durationMs < 1 || durationMs > 30_000) {
    throw new Error("Probe duration must be an integer from 1 to 30000 milliseconds");
  }
  const emulateFocus = action === "probe-focused";
  await call("Page.bringToFront");
  const cleanupExpression = `(() => {
    const handlers = window.__bvnCdpKeyProbeHandlers ?? {};
    for (const type of ["keydown", "keyup"]) {
      if (handlers[type]) removeEventListener(type, handlers[type], true);
    }
    delete window.__bvnCdpKeyProbeHandlers;
    delete window.__bvnCdpKeyProbe;
    delete window.__bvnCdpKeyProbeSummary;
    clearTimeout(window.__bvnCdpKeyProbeCleanupTimer);
    delete window.__bvnCdpKeyProbeCleanupTimer;
  })()`;
  let events = [];
  let capturedKeys = [];
  let keySummary = {};
  let focus = {};
  try {
    if (emulateFocus) await call("Emulation.setFocusEmulationEnabled", { enabled: true });
    await focusCanvas();
    const setup = await call("Runtime.evaluate", {
      expression: `(() => {
        window.__bvnCdpKeyProbe = [];
        window.__bvnCdpKeyProbeHandlers = {};
        window.__bvnCdpKeyProbeSummary = {keydown:0,keyup:0,targetTags:{}};
        const codeMap = {KeyW:"w",KeyS:"s",KeyJ:"j",KeyK:"k"};
        const keyCodeMap = {87:"w",83:"s",74:"j",75:"k"};
        for (const type of ["keydown", "keyup"]) {
          const handler = event => {
            const summary = window.__bvnCdpKeyProbeSummary;
            if (summary) {
              summary[type]++;
              const tag = event.target?.tagName ?? "<none>";
              summary.targetTags[tag] = (summary.targetTags[tag] ?? 0) + 1;
            }
            const key = codeMap[event.code] ?? keyCodeMap[event.keyCode] ?? "<unmapped>";
            if (key === "<unmapped>") return;
            if (window.__bvnCdpKeyProbe.length >= 32) return;
            const targetTag = event.target?.tagName ?? "<none>";
            window.__bvnCdpKeyProbe.push({timeMs:performance.now(), type, key, code:event.code,
              keyCode:event.keyCode, trusted:event.isTrusted, targetTag, targetIsCanvas:targetTag === "CANVAS"});
          };
          window.__bvnCdpKeyProbeHandlers[type] = handler;
          addEventListener(type, handler, true);
        }
        const canvas = document.querySelector("canvas");
        const active = document.activeElement;
        const r = canvas?.getBoundingClientRect();
        return {activeTag:active?.tagName ?? "", activeId:active?.id ?? "", activeRole:active?.getAttribute?.("role") ?? "",
          canvasPresent:!!canvas, canvasFocused:active === canvas, canvasTabIndex:canvas?.tabIndex ?? null,
          documentHasFocus:document.hasFocus(), visibilityState:document.visibilityState,
          canvasBounds:r ? {x:r.x,y:r.y,width:r.width,height:r.height} : null};
      })()`,
      returnByValue: true,
    });
    focus = setup.result.value;
    await call("Runtime.evaluate", {
      expression: `window.__bvnCdpKeyProbeCleanupTimer = setTimeout(() => {
        ${cleanupExpression}
      }, ${durationMs + 1500});`,
      returnByValue: true,
    });
    const [probeKey, probeCode, probeVkText, holdText] = args.slice(1);
    const holdMs = Number(holdText ?? "180");
    const testKey = probeKey ? async () => {
      if (!({w:true,s:true,j:true,k:true})[String(probeKey).toLowerCase()] || !probeCode || !Number.isInteger(Number(probeVkText)) || !Number.isInteger(holdMs) || holdMs < 1 || holdMs > 500) {
        throw new Error("Probe key must be W/S/J/K with code, virtual-key-code, and hold duration 1-500ms");
      }
      await sendKey("keyDown", probeKey.toLowerCase(), probeCode, Number(probeVkText), true);
      try {
        await new Promise((resolve) => setTimeout(resolve, holdMs));
      } finally {
        await safeKeyUp(probeKey.toLowerCase(), probeCode, probeVkText);
      }
    } : undefined;
    events = await watch(durationMs, testKey);
    const captured = await call("Runtime.evaluate", {
      expression: `(() => ({keys:window.__bvnCdpKeyProbe ?? [], summary:window.__bvnCdpKeyProbeSummary ?? {}}))()`, returnByValue: true,
    });
    capturedKeys = captured.result.value.keys;
    keySummary = captured.result.value.summary;
  } finally {
    try {
      const cleanup = await call("Runtime.evaluate", {
        expression: `(() => {
          ${cleanupExpression}
        })()`, returnByValue: true,
      });
      void cleanup;
    } catch {
      // The page-side timeout removes the temporary listener if CDP fails.
    }
    if (emulateFocus) {
      try {
        await call("Emulation.setFocusEmulationEnabled", { enabled: false });
      } catch {
        // The dedicated target remains isolated if its CDP connection closes.
      }
    }
  }
  console.log(JSON.stringify({ action, targetId: page.id, page: page.url,
    focus, keySummary, trustedKeys: capturedKeys, networkEvents: events }));
} else if (action === "screenshot") {
  const result = await call("Page.captureScreenshot", { format: "jpeg", quality: 35, captureBeyondViewport: false });
  console.log(JSON.stringify({ action, targetId: page.id, page: page.url, mimeType: "image/jpeg", data: result.data }));
} else if (action === "reload") {
  await call("Page.bringToFront");
  await call("Page.reload", { ignoreCache: true });
  let state = {};
  const deadline = Date.now() + 15_000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    try {
      const result = await call("Runtime.evaluate", {
        expression: `({readyState:document.readyState,canvasPresent:!!document.querySelector("canvas"),staleProbePresent:!!window.__bvnCdpKeyProbeHandlers})`,
        returnByValue: true,
      });
      state = result.result.value;
      if (state.readyState === "complete" && state.canvasPresent) break;
    } catch {
      // The old execution context can disappear while the page reloads.
    }
  }
  console.log(JSON.stringify({ action, targetId: page.id, page: page.url, state }));
} else if (action === "down" || action === "up") {
  const [key, code, vk, mode] = args;
  await call("Page.bringToFront");
  try {
    await sendKey(action === "up" ? "keyUp" : "keyDown", key, code, Number(vk), mode === "raw");
  } catch (error) {
    if (action === "down") await safeKeyUp(key, code, vk);
    throw error;
  }
} else if (action === "hold") {
  const [key, code, vk, durationText, mode] = args;
  const durationMs = Number(durationText);
  if (!Number.isInteger(durationMs) || durationMs < 1 || durationMs > 5000) {
    throw new Error("Hold duration must be an integer from 1 to 5000 milliseconds");
  }
  await call("Page.bringToFront");
  try {
    await sendKey("keyDown", key, code, Number(vk), mode === "raw");
    await new Promise((resolve) => setTimeout(resolve, durationMs));
  } finally {
    await safeKeyUp(key, code, vk);
  }
} else {
  throw new Error("Usage: online_cdp_keys.mjs list | focus | down|up <key> <code> <vk> [raw] | hold <key> <code> <vk> <ms> [raw]");
}

if (action !== "screenshot") console.log(JSON.stringify({ action, targetId: page.id, page: page.url, ok: true }));
socket.close();
