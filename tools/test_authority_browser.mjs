#!/usr/bin/env node
// Dedicated testing browsers only. This is a local wiring check, never a performance gate.
import { writeFile } from "node:fs/promises";
const [firstEndpoint, secondEndpoint, url, output] = process.argv.slice(2);
if (!output) throw new Error("Usage: ENDPOINT1 ENDPOINT2 TEST_URL REPORT");
async function connect(endpoint) {
  const targets = await (await fetch(endpoint + "/json/list")).json();
  const socket = new WebSocket(
    targets.find((x) => x.type === "page").webSocketDebuggerUrl,
  );
  await new Promise((resolve) =>
    socket.addEventListener("open", resolve, { once: true }),
  );
  const calls = new Map(),
    errors = [],
    consoleLines = [];
  let id = 0;
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const call = calls.get(message.id);
      calls.delete(message.id);
      message.error ? call.reject(message.error) : call.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown")
      errors.push(message.params.exceptionDetails);
    if (message.method === "Runtime.consoleAPICalled") {
      const line = message.params.args
        .map((x) => x.value ?? x.description ?? "")
        .join(" ");
      consoleLines.push(line);
      if (/SCRIPT ERROR|Parse Error|Assertion failed|^ERROR:/.test(line))
        errors.push(line);
    }
  });
  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      calls.set(++id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params }));
    });
  const evaluate = async (expression) =>
    (await send("Runtime.evaluate", { expression, returnByValue: true })).result
      .value;
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Page.addScriptToEvaluateOnNewDocument", {
    source: `globalThis.authorityRtc=[]; const Native=globalThis.RTCPeerConnection; globalThis.RTCPeerConnection=new Proxy(Native,{construct(target,args){const peer=new target(...args);authorityRtc.push(peer);peer.authorityChannels=[];peer.authorityCalls=[];for(const name of ['createOffer','setLocalDescription','setRemoteDescription']){const call=peer[name].bind(peer);peer[name]=(...v)=>{peer.authorityCalls.push(name);return call(...v).catch(error=>{peer.authorityCalls.push(name+':'+error.name+':'+error.message);throw error})}};const create=peer.createDataChannel.bind(peer);peer.createDataChannel=(...values)=>{const channel=create(...values);peer.authorityChannels.push(channel);return channel};peer.addEventListener('datachannel',event=>peer.authorityChannels.push(event.channel));return peer}});`,
  });
  await send("Emulation.setDeviceMetricsOverride", {
    width: 900,
    height: 700,
    deviceScaleFactor: 1,
    mobile: false,
  });
  return { socket, send, evaluate, errors, consoleLines };
}
const offline = url.includes("offline=1");
const peers = await Promise.all([
  connect(firstEndpoint),
  connect(secondEndpoint),
]);
let reports = [],
  status = [],
  guestStarted = false;
try {
  await Promise.all(
    peers.map((p) => p.send("Page.navigate", { url: "about:blank" })),
  );
  await new Promise((resolve) => setTimeout(resolve, 100));
  await peers[0].send("Page.navigate", { url });
  const deadline = Date.now() + 180000;
  let lastLog = 0;
  while (Date.now() < deadline) {
    reports = await Promise.all(
      peers.map((p) => p.evaluate("globalThis.authoritySmoke")),
    );
    status = await Promise.all(
      peers.map((p) =>
        p.evaluate(
          "({status:globalThis.authorityStatus,rtc:globalThis.authorityRtc?.map(p=>({connection:p.connectionState,ice:p.iceConnectionState,signaling:p.signalingState,calls:p.authorityCalls,channels:p.authorityChannels.map(c=>({label:c.label,state:c.readyState}))}))})",
        ),
      ),
    );
    if (!guestStarted && reports[0]?.invite) {
      await peers[1].send("Page.navigate", {
        url: url + "?invite=" + encodeURIComponent(reports[0].invite),
      });
      guestStarted = true;
    }
    if (Date.now() - lastLog > 10000) {
      console.log(JSON.stringify({ reports, status }));
      lastLog = Date.now();
    }
    if (peers.some((p) => p.errors.length)) throw new Error("Browser errors");
    if (status.some((x) => x?.status?.status?.includes("操作未完成")))
      throw new Error("Startup failed");
    if (reports.some((x) => x?.phase === "failed"))
      throw new Error("Harness failed");
    if (
      (offline ? [reports[0]] : reports).every((x) => x?.phase === "complete")
    )
      break;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  if (!(offline ? [reports[0]] : reports).every((x) => x?.phase === "complete"))
    throw new Error("Browser pair timed out");
  if (offline) {
    if (
      reports[0].hostTicks !== 900 ||
      reports[0].guestTicks !== 0 ||
      reports[0].superTicks <= 0
    )
      throw new Error("Offline display coverage missing");
  } else {
    if (reports[0].authority !== reports[1].authority)
      throw new Error("Authority differs");
    const host = reports[reports[0].authority],
      guest = reports[1 - reports[0].authority];
    if (
      !host.running ||
      !guest.running ||
      host.simTicks < 180 ||
      guest.simTicks !== 0 ||
      guest.receivedStates < 180 ||
      reports.some((x) => x.error)
    )
      throw new Error("Missing host/presenter coverage");
  }
  console.log(
    offline
      ? "AUTHORITY_BROWSER_PROJECTION_OK not-a-pass"
      : "AUTHORITY_BROWSER_PAIR_OK not-a-pass",
  );
} finally {
  await writeFile(
    output,
    JSON.stringify(
      {
        notAPass: true,
        g0Passed: false,
        weakMachineAccepted: false,
        twoMachinePerformanceAccepted: false,
        reports,
        status,
        errors: peers.map((p) => p.errors),
        console: peers.map((p) => p.consoleLines),
      },
      null,
      2,
    ),
  );
  for (const peer of peers) peer.socket.close();
}
