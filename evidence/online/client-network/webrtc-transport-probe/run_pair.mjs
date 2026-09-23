const endpoint = new URL("http://127.0.0.1:9234");
const testPage = "http://127.0.0.1:8000/_webrtc_transport/index.html";
const serviceOrigin = "http://127.0.0.1:8787";
const timeoutMs = 110_000;
const runStartedAt = Date.now();
const runId = crypto.randomUUID();

const versionResponse = await fetch(new URL("/json/version", endpoint));
if (!versionResponse.ok) throw new Error("Dedicated Chrome CDP endpoint unavailable");
const browserVersion = await versionResponse.json();
const browser = await openCdp(browserVersion.webSocketDebuggerUrl);
const targetA = await call(browser, "Target.createTarget", { url: "about:blank" });
const targetB = await call(browser, "Target.createTarget", { url: "about:blank" });
const pages = await Promise.all([
  openPage(targetA.targetId, "owner"),
  openPage(targetB.targetId, "guest"),
]);

for (const page of pages) {
  await call(page.socket, "Network.enable");
  await call(page.socket, "Network.setCacheDisabled", { cacheDisabled: false });
  await call(page.socket, "Runtime.enable");
  await call(page.socket, "Log.enable");
  await call(page.socket, "Page.enable");
  await call(page.socket, "Emulation.setFocusEmulationEnabled", { enabled: true });
  await call(page.socket, "Page.setWebLifecycleState", { state: "active" });
}

await Promise.all(pages.map((page) => call(page.socket, "Page.navigate", {
  url: `${testPage}?role=${page.role}&run=${encodeURIComponent(runId)}`,
})));

const deadline = Date.now() + timeoutMs;
while (Date.now() < deadline && pages.some((page) => !page.report)) {
  await Promise.all(pages.map(async (page) => {
    if (page.report) return;
    try {
      const result = await call(page.socket, "Runtime.evaluate", {
        expression: "JSON.stringify(window.__bvnTransportResult || null)",
        returnByValue: true,
        awaitPromise: true,
      });
      if (typeof result.result?.value === "string") {
        const value = JSON.parse(result.result.value);
        if (value && value.phase === "done") page.report = sanitizeReport(value);
        else if (value) page.phase = String(value.phase ?? "unknown");
      }
    } catch {
      page.phase = "cdp_read_failed";
    }
  }));
  if (pages.some((page) => !page.report)) await delay(300);
}

const reportsComplete = pages.every((page) => page.report);
const cleanupComplete = reportsComplete && pages.every((page) => page.report.cleanupComplete);
const success = reportsComplete && pages.every((page) => page.report.ok && page.report.cleanupComplete);
if (cleanupComplete) {
  await Promise.all(pages.map((page) => call(browser, "Target.closeTarget", { targetId: page.targetId })));
}

console.log(JSON.stringify({
  marker: "ONLINE_WEBRTC_CHROME_PAIR_RESULT",
  chrome: browserVersion.Browser,
  mode: "headless_dedicated_profile",
  transport: "production_room_client_and_peer_transport",
  service: serviceOrigin,
  iceServers: 0,
  reportsComplete,
  cleanupComplete,
  success,
  elapsedMs: Date.now() - runStartedAt,
  pages: pages.map((page) => ({
    role: page.role,
    phase: page.phase,
    report: page.report,
    http: page.http,
    errors: page.errors,
    elapsedMs: Date.now() - page.startedAt,
    admissionRequestIds: page.admissionRequestIds,
    targetClosed: cleanupComplete,
  })),
}));

for (const page of pages) page.socket.close();
browser.close();
if (!success) process.exitCode = 1;

async function openPage(targetId, role) {
  const targetsResponse = await fetch(new URL("/json/list", endpoint));
  if (!targetsResponse.ok) throw new Error("Cannot inspect dedicated Chrome tabs");
  const target = (await targetsResponse.json()).find((entry) => entry.id === targetId && entry.type === "page");
  if (!target) throw new Error("Dedicated Chrome tab was not created");
  const page = {
    targetId,
    role,
    phase: "created",
    startedAt: Date.now(),
    http: [],
    errors: [],
    requestById: new Map(),
    admissionRequestIds: [],
    report: null,
    socket: null,
  };
  page.socket = await openCdp(target.webSocketDebuggerUrl, handleEvent, page);
  return page;
}

function handleEvent(method, params, page) {
  if (method === "Network.requestWillBeSent") {
    const url = safeServiceUrl(params.request.url);
    if (url) {
      const record = { method: params.request.method, path: url.path, requestId: params.requestId };
      page.requestById.set(params.requestId, record);
      if (record.method === "POST" && record.path === "/v1/rooms") page.admissionRequestIds.push(params.requestId);
      page.http.push({ event: "request", method: record.method, path: record.path, elapsedMs: Date.now() - page.startedAt });
    }
  } else if (method === "Network.responseReceived") {
    const url = safeServiceUrl(params.response.url);
    if (url) {
      const record = page.requestById.get(params.requestId);
      page.http.push({
        event: "response",
        method: record?.method ?? "unknown",
        path: url.path,
        status: Number(params.response.status),
        elapsedMs: Date.now() - page.startedAt,
      });
    }
  } else if (method === "Network.loadingFailed") {
    const record = page.requestById.get(params.requestId);
    if (record) page.http.push({ event: "failed", ...record, error: String(params.errorText ?? "unknown") });
  } else if (method === "Runtime.consoleAPICalled") {
    const text = (params.args ?? []).map((arg) => String(arg.value ?? arg.description ?? "")).join(" ");
    const resultPrefix = "ONLINE_WEBRTC_TRANSPORT_RESULT ";
    const phasePrefix = "ONLINE_WEBRTC_TRANSPORT_PHASE ";
    const diagnosticPrefix = "Online HTTP diagnostic (redacted): ";
    if (text.startsWith(resultPrefix)) {
      try { page.report = sanitizeReport(JSON.parse(text.slice(resultPrefix.length))); } catch { page.errors.push("result_parse_failed"); }
    } else if (text.startsWith(phasePrefix)) {
      page.phase = text.slice(phasePrefix.length).replace(/^role=\w+ phase=/, "");
    } else if (text.startsWith(diagnosticPrefix)) {
      try {
        const diagnostic = JSON.parse(text.slice(diagnosticPrefix.length));
        page.http.push({ event: "room_client_diagnostic", phase: String(diagnostic.phase ?? "unknown"),
          transportResult: diagnostic.transportResult ?? "unknown", httpStatus: Number(diagnostic.httpStatus ?? 0),
          requestErrorCode: Number(diagnostic.requestErrorCode ?? -1), elapsedMs: Date.now() - page.startedAt });
      } catch { page.errors.push("http_diagnostic_parse_failed"); }
    } else if (text.startsWith("ONLINE_WEBRTC_TRANSPORT_FAIL")) {
      const code = text.match(/\bcode=([A-Za-z0-9_.-]{1,80})/);
      page.errors.push({ severity: params.type, message: code ? `ONLINE_WEBRTC_TRANSPORT_FAIL ${code[1]}` : safeMessage(text) });
    } else if (["error", "warning", "assert"].includes(params.type)) {
      page.errors.push({ severity: params.type, message: safeMessage(text) });
    }
  } else if (method === "Runtime.exceptionThrown") {
    page.errors.push(safeException(params.exceptionDetails ?? {}));
  } else if (method === "Log.entryAdded") {
    const entry = params.entry ?? {};
    if (["error", "warning"].includes(entry.level)) page.errors.push({ severity: entry.level, message: safeMessage(String(entry.text ?? "")) });
  }
}

function safeServiceUrl(raw) {
  let url;
  try { url = new URL(raw); } catch { return null; }
  if (url.origin !== serviceOrigin) return null;
  const match = url.pathname.match(/^\/v1\/rooms\/[^/]+(\/.*)?$/);
  const path = match ? `/v1/rooms/:room${match[1] ?? ""}` : url.pathname;
  return { path };
}

function sanitizeReport(value) {
  const report = structuredClone(value);
  delete report.run;
  return report;
}

function safeMessage(raw) {
  const firstLine = String(raw).split(/\r?\n/)[0];
  if (/authorization|bearer|invite[_ -]?token|session[_ -]?token|credential|password|\bsdp\b|ice[_ -]?candidate|request[_ -]?body|headers?/i.test(firstLine)) {
    return "<redacted sensitive error text>";
  }
  return firstLine
    .replace(/https?:\/\/[^\s)]+/gi, "<url>")
    .replace(/\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, "<redacted>")
    .replace(/\b[a-f0-9]{8}-[a-f0-9-]{27,}\b/gi, "<id>")
    .replace(/\b[A-Za-z0-9_-]{48,}\b/g, "<redacted>")
    .slice(0, 240);
}

function safeException(details) {
  const exception = details.exception ?? {};
  const frames = details.stackTrace?.callFrames ?? [];
  return {
    event: "exception",
    name: /^[A-Za-z][A-Za-z0-9]{0,40}$/.test(exception.className ?? "") ? exception.className : "Error",
    message: safeMessage(String(exception.description ?? details.text ?? "<no message>").split(/\r?\n/)[0]),
    stackFunctions: frames.map((frame) => {
      const name = String(frame.functionName ?? "<anonymous>");
      return /^[A-Za-z0-9_.$<>-]{1,100}$/.test(name) ? name : "<anonymous>";
    }).slice(0, 5),
    sourceLocation: frames[0] ? { line: Number(frames[0].lineNumber) + 1, column: Number(frames[0].columnNumber) + 1 } : null,
  };
}

async function openCdp(url, eventHandler, page) {
  const socket = new WebSocket(url);
  const pending = new Map();
  let nextId = 1;
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject, timer } = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(timer);
      if (message.error) reject(new Error(String(message.error.message ?? "CDP command failed")));
      else resolve(message.result ?? {});
    } else if (message.method && eventHandler && page) {
      eventHandler(message.method, message.params ?? {}, page);
    }
  });
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("CDP websocket open timed out")), 10_000);
    socket.addEventListener("open", () => { clearTimeout(timer); resolve(); }, { once: true });
    socket.addEventListener("error", () => { clearTimeout(timer); reject(new Error("CDP websocket failed")); }, { once: true });
  });
  socket.call = (method, params = {}) => {
    const id = nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error(`CDP command timed out: ${method}`));
      }, 10_000);
      pending.set(id, { resolve, reject, timer });
      socket.send(JSON.stringify({ id, method, params }));
    });
  };
  return socket;
}

function call(socket, method, params = {}) {
  return socket.call(method, params);
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
