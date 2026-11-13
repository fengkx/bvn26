#!/usr/bin/env node
// Dedicated testing browsers only. This is a local wiring check, never a performance gate.
import { writeFile } from "node:fs/promises";
import {
  rtcDiagnostics,
  localPermissionOrigin,
} from "./authority_browser_diagnostics.mjs";
const [firstEndpoint, secondEndpoint, url, output] = process.argv.slice(2);
if (!output) throw new Error("Usage: ENDPOINT1 ENDPOINT2 TEST_URL REPORT");
const localIcePermissionOverride = process.env.BVN_LOCAL_ICE_PERMISSION === "1";
const permissionOrigin = localIcePermissionOverride
  ? localPermissionOrigin(url)
  : null;
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
  const evaluate = async (expression) => {
    const result = await send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result.value;
  };
  await send("Runtime.enable");
  await send("Page.enable");
  const browserVersion = (await send("Browser.getVersion")).product;
  if (permissionOrigin)
    await send("Browser.grantPermissions", {
      origin: permissionOrigin,
      permissions: ["audioCapture"],
    });
  await send("Page.addScriptToEvaluateOnNewDocument", {
    source: `globalThis.authorityRtc=[]; const Native=globalThis.RTCPeerConnection; globalThis.RTCPeerConnection=new Proxy(Native,{construct(target,args){const peer=new target(...args);authorityRtc.push(peer);peer.authorityChannels=[];peer.authorityCalls=[];for(const name of ['createOffer','setLocalDescription','setRemoteDescription']){const call=peer[name].bind(peer);peer[name]=(...v)=>{peer.authorityCalls.push(name);return call(...v).catch(error=>{peer.authorityCalls.push(name+':'+error.name+':'+error.message);throw error})}};const create=peer.createDataChannel.bind(peer);peer.createDataChannel=(...values)=>{const channel=create(...values);peer.authorityChannels.push(channel);return channel};peer.addEventListener('datachannel',event=>peer.authorityChannels.push(event.channel));return peer}});`,
  });
  await send("Emulation.setDeviceMetricsOverride", {
    width: 900,
    height: 700,
    deviceScaleFactor: 1,
    mobile: false,
  });
  return { socket, send, evaluate, errors, consoleLines, browserVersion };
}
const offline = url.includes("offline=1");
const peers = await Promise.all([
  connect(firstEndpoint),
  connect(secondEndpoint),
]);
let outcome = "failed";
let inputCheck = null;
let reports = [],
  status = [],
  guestStarted = false;
try {
  await Promise.all(
    peers.map((p) => p.send("Page.navigate", { url: "about:blank" })),
  );
  await new Promise((resolve) => setTimeout(resolve, 100));
  for (const peer of peers) {
    await peer.send("Runtime.discardConsoleEntries");
    peer.errors.length = 0;
    peer.consoleLines.length = 0;
  }
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
          `(async()=>({status:globalThis.authorityStatus,rtc:await (${rtcDiagnostics.toString()})()}))()`,
        ),
      ),
    );
    if (!guestStarted && reports[0]?.invite) {
      await peers[1].send("Page.navigate", {
        url: url + "?invite=" + encodeURIComponent(reports[0].invite),
      });
      guestStarted = true;
    }
    if (
      !offline &&
      !inputCheck &&
      reports.every(
        (report) => report?.phase === "playing" && report.localTicks >= 120,
      )
    ) {
      const slot = 1 - reports[0].authority;
      if (reports[slot].rightKey !== 68)
        throw new Error("Smoke requires fresh default D/right binding");
      inputCheck = {
        slot,
        startX: reports[slot].positions[slot],
        released: false,
        releaseAt: Date.now() + 1000,
      };
      await peers[slot].evaluate("document.querySelector('canvas').focus()");
      await peers[slot].send("Input.dispatchKeyEvent", {
        type: "keyDown",
        code: "KeyD",
        key: "d",
        windowsVirtualKeyCode: 68,
      });
    }
    if (
      inputCheck &&
      !inputCheck.released &&
      Date.now() >= inputCheck.releaseAt
    ) {
      await peers[inputCheck.slot].send("Input.dispatchKeyEvent", {
        type: "keyUp",
        code: "KeyD",
        key: "d",
        windowsVirtualKeyCode: 68,
      });
      inputCheck.released = true;
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
    for (const peer of status) {
      if (
        !peer.rtc.some(
          (connection) =>
            connection.connection === "connected" &&
            connection.selectedPair?.state === "succeeded" &&
            ["reliable", "input", "state"].every((label) =>
              connection.channels?.some(
                (channel) =>
                  channel.label === label && channel.state === "open",
              ),
            ),
        )
      )
        throw new Error("Three connected WebRTC channels not observed");
    }
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
    if (
      !inputCheck?.released ||
      !host.remoteRightSeen ||
      !(guest.positions[inputCheck.slot] > inputCheck.startX)
    )
      throw new Error(
        "Guest keyboard input did not reach host simulation and guest display",
      );
  }
  outcome = "passed";
  console.log(
    offline
      ? "AUTHORITY_BROWSER_PROJECTION_OK not-a-pass"
      : "AUTHORITY_BROWSER_PAIR_OK not-a-pass",
  );
} finally {
  if (inputCheck && !inputCheck.released)
    await peers[inputCheck.slot]
      .send("Input.dispatchKeyEvent", {
        type: "keyUp",
        code: "KeyD",
        key: "d",
        windowsVirtualKeyCode: 68,
      })
      .catch(() => {});
  await writeFile(
    output,
    JSON.stringify(
      {
        outcome,
        inputCheck,
        localIcePermissionOverride,
        browsers: peers.map((peer) => peer.browserVersion),
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
