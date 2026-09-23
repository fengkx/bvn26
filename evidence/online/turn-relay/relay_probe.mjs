import { createHash, randomBytes } from 'node:crypto';

const service = 'https://bvn26-pvp.fengkx.top';
const cdp = 'http://127.0.0.1:9240';
const token = () => randomBytes(32).toString('base64url');
const hash = (value) => createHash('sha256').update(value).digest('hex');
const secrets = { createToken: token(), sessionToken: token(), inviteToken: token() };
const compatibility = { protocol: 1, build: hash('minimal-turn-probe-build'), content: hash('minimal-turn-probe-content') };
const report = { marker: 'ONLINE_TURN_RELAY_MINIMAL', healthStatus: 0, createStatus: 0, iceStatus: 0, iceSummary: null, chrome: '', peerResult: null, cleanupStatus: 0, cleanupComplete: false };
let roomId = '';
let browserSocket;
let targetId = '';
let pageSocket;

try {
  const health = await fetch(`${service}/health`);
  report.healthStatus = health.status;
  const createResponse = await fetch(`${service}/v1/rooms`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...secrets, nickname: 'TURN relay probe', compatibility }) });
  report.createStatus = createResponse.status;
  if (!createResponse.ok) throw new Error(`create_http_${createResponse.status}`);
  const created = await createResponse.json();
  roomId = created.roomId;
  const iceResponse = await fetch(`${service}/v1/rooms/${roomId}/ice`, { method: 'POST', headers: { Authorization: `Bearer ${secrets.sessionToken}`, 'Content-Type': 'application/json' }, body: '{}' });
  report.iceStatus = iceResponse.status;
  if (!iceResponse.ok) {
    const fault = await iceResponse.json().catch(() => ({}));
    throw new Error(`ice_${iceResponse.status}_${fault.error ?? 'unknown'}`);
  }
  const ice = await iceResponse.json();
  const iceServers = Array.isArray(ice.iceServers) ? ice.iceServers : [];
  const urls = iceServers.flatMap((server) => Array.isArray(server.urls) ? server.urls : [server.urls]).filter((url) => typeof url === 'string');
  report.iceSummary = {
    serverCount: iceServers.length,
    urlSchemes: [...new Set(urls.map((url) => url.split(':', 1)[0].toLowerCase()))].sort(),
    turnUrlCount: urls.filter((url) => /^turns?:/i.test(url)).length,
    hasUsername: iceServers.some((server) => typeof server.username === 'string' && server.username.length > 0),
    hasCredential: iceServers.some((server) => typeof server.credential === 'string' && server.credential.length > 0),
    expiresIn: Number(ice.expiresIn ?? 0),
  };

  const versionResponse = await fetch(`${cdp}/json/version`);
  if (!versionResponse.ok) throw new Error('cdp_unavailable');
  const version = await versionResponse.json();
  report.chrome = version.Browser;
  browserSocket = await openCdp(version.webSocketDebuggerUrl);
  const target = await call(browserSocket, 'Target.createTarget', { url: `${service}/health`, background: false });
  targetId = target.targetId;
  const targets = await fetch(`${cdp}/json/list`).then((response) => response.json());
  const info = targets.find((item) => item.id === targetId && item.type === 'page');
  if (!info) throw new Error('page_target_missing');
  pageSocket = await openCdp(info.webSocketDebuggerUrl);
  await call(pageSocket, 'Runtime.enable');
  await call(pageSocket, 'Page.enable');
  await call(pageSocket, 'Emulation.setFocusEmulationEnabled', { enabled: true });
  await call(pageSocket, 'Page.setWebLifecycleState', { state: 'active' });
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    const ready = await evaluate(pageSocket, '({ ready: document.readyState, origin: location.origin })', 5_000);
    if (ready.ready === 'complete' && ready.origin === service) break;
    await delay(100);
  }
  const expression = `(${runRelayPair.toString()})(${JSON.stringify(iceServers)})`;
  report.peerResult = await evaluate(pageSocket, expression, 40_000);
} catch (error) {
  report.failure = safeCode(error);
} finally {
  if (roomId) {
    try {
      const stateResponse = await fetch(`${service}/v1/rooms/${roomId}/state`, { headers: { Authorization: `Bearer ${secrets.sessionToken}` } });
      if (stateResponse.ok) {
        const current = await stateResponse.json();
        const seq = Number(current.state?.members?.[0]?.seq);
        if (Number.isSafeInteger(seq) && seq >= 0) {
          const left = await fetch(`${service}/v1/rooms/${roomId}/commands`, { method: 'POST', headers: { Authorization: `Bearer ${secrets.sessionToken}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ version: 1, seq: seq + 1, operation: { type: 'leave' } }) });
          report.cleanupStatus = left.status;
          report.cleanupComplete = left.ok;
        }
      }
    } catch {}
  }
  try { if (targetId && browserSocket) await call(browserSocket, 'Target.closeTarget', { targetId }, 5_000); } catch {}
  try { pageSocket?.close(); } catch {}
  try { browserSocket?.close(); } catch {}
}

console.log(JSON.stringify(report));
if (!report.peerResult?.ok || !report.cleanupComplete) process.exitCode = 1;

function runRelayPair(iceServers) {
  return (async () => {
    const iceErrors = [];
    const candidates = { a: { total: 0, relay: 0 }, b: { total: 0, relay: 0 } };
    const pending = { a: [], b: [] };
    const remoteReady = { a: false, b: false };
    let pcA;
    let pcB;
    let channelA;
    let channelB;
    let pingReceived = false;
    let pongReceived = false;
    const result = {
      ok: false,
      relayOnly: true,
      connectionTimeoutMs: 30000,
      candidates: [],
      selectedPairs: [],
      packets: { pingSent: false, pingReceived: false, pongReceived: false },
      iceErrors,
    };
    const safeFailure = (error) => {
      const code = String(error && error.message ? error.message : 'unknown');
      return /^[A-Za-z0-9_.:-]{1,100}$/.test(code) ? code : 'unclassified_failure';
    };
    const attachIceError = (pc) => {
      pc.onicecandidateerror = (event) => {
        iceErrors.push({
          code: Number(event.errorCode) || 0,
        });
      };
    };
    const wire = (source, destination, sourceKey, destinationKey) => {
      source.onicecandidate = (event) => {
        if (!event.candidate) return;
        candidates[sourceKey].total += 1;
        if (event.candidate.type === 'relay') candidates[sourceKey].relay += 1;
        if (remoteReady[destinationKey]) destination.addIceCandidate(event.candidate).catch(() => {});
        else pending[destinationKey].push(event.candidate);
      };
    };
    const flush = async (destination, key) => {
      remoteReady[key] = true;
      const queued = pending[key].splice(0);
      for (const candidate of queued) await destination.addIceCandidate(candidate);
    };
    const waitConnected = async () => {
      const deadline = Date.now() + 30000;
      while (Date.now() < deadline) {
        if (pcA.connectionState === 'connected' && pcB.connectionState === 'connected' && channelA.readyState === 'open' && channelB && channelB.readyState === 'open') return;
        if (pcA.connectionState === 'failed' || pcB.connectionState === 'failed') throw new Error('relay_connection_failed');
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
      throw new Error('relay_connect_timeout');
    };
    const getSelectedPair = async (pc) => {
      const stats = await pc.getStats();
      const entries = Array.from(stats.values());
      const transport = entries.find((entry) => entry.type === 'transport' && entry.selectedCandidatePairId);
      let pair = transport ? stats.get(transport.selectedCandidatePairId) : null;
      if (!pair) pair = entries.find((entry) => entry.type === 'candidate-pair' && entry.state === 'succeeded' && entry.nominated);
      const local = pair ? stats.get(pair.localCandidateId) : null;
      const remote = pair ? stats.get(pair.remoteCandidateId) : null;
      return {
        state: pair ? pair.state : null,
        protocol: pair ? pair.protocol : null,
        localType: local ? local.candidateType : null,
        remoteType: remote ? remote.candidateType : null,
        bytesSent: Number(pair && pair.bytesSent ? pair.bytesSent : 0),
        bytesReceived: Number(pair && pair.bytesReceived ? pair.bytesReceived : 0),
      };
    };
    try {
      if (typeof RTCPeerConnection !== 'function') throw new Error('webrtc_unavailable');
      const config = { iceServers: iceServers, iceTransportPolicy: 'relay', bundlePolicy: 'max-bundle' };
      pcA = new RTCPeerConnection(config);
      pcB = new RTCPeerConnection(config);
      attachIceError(pcA);
      attachIceError(pcB);
      wire(pcA, pcB, 'a', 'b');
      wire(pcB, pcA, 'b', 'a');
      channelA = pcA.createDataChannel('turn-probe', { ordered: true });
      pcB.ondatachannel = (event) => {
        channelB = event.channel;
        channelB.onmessage = (message) => {
          if (message.data === 'turn-ping') {
            pingReceived = true;
            channelB.send('turn-pong');
          }
        };
      };
      channelA.onmessage = (event) => { if (event.data === 'turn-pong') pongReceived = true; };
      const offer = await pcA.createOffer();
      await pcA.setLocalDescription(offer);
      await pcB.setRemoteDescription(pcA.localDescription);
      await flush(pcB, 'b');
      const answer = await pcB.createAnswer();
      await pcB.setLocalDescription(answer);
      await pcA.setRemoteDescription(pcB.localDescription);
      await flush(pcA, 'a');
      await waitConnected();
      channelA.send('turn-ping');
      result.packets.pingSent = true;
      const packetDeadline = Date.now() + 5000;
      while (Date.now() < packetDeadline && !(pingReceived && pongReceived)) await new Promise((resolve) => setTimeout(resolve, 25));
      result.packets.pingReceived = pingReceived;
      result.packets.pongReceived = pongReceived;
      result.candidates = [candidates.a, candidates.b];
      result.selectedPairs = [await getSelectedPair(pcA), await getSelectedPair(pcB)];
      result.connectionStates = [pcA.connectionState, pcB.connectionState];
      result.dataChannelStates = [channelA.readyState, channelB ? channelB.readyState : null];
      result.iceErrors = iceErrors.slice(0, 8);
      result.ok = candidates.a.relay > 0 && candidates.b.relay > 0 && result.selectedPairs.every((pair) => pair.state === 'succeeded' && pair.localType === 'relay' && pair.remoteType === 'relay') && pingReceived && pongReceived;
      return result;
    } catch (error) {
      result.failure = safeFailure(error);
      result.candidates = [candidates.a, candidates.b];
      result.connectionStates = [pcA ? pcA.connectionState : null, pcB ? pcB.connectionState : null];
      result.iceGatheringStates = [pcA ? pcA.iceGatheringState : null, pcB ? pcB.iceGatheringState : null];
      result.iceConnectionStates = [pcA ? pcA.iceConnectionState : null, pcB ? pcB.iceConnectionState : null];
      result.selectedPairs = pcA && pcB ? [await getSelectedPair(pcA), await getSelectedPair(pcB)] : [];
      result.iceErrors = iceErrors.slice(0, 8);
      return result;
    } finally {
      try { if (channelA) channelA.close(); } catch {}
      try { if (channelB) channelB.close(); } catch {}
      try { if (pcA) pcA.close(); } catch {}
      try { if (pcB) pcB.close(); } catch {}
    }
  })();
}

function safeCode(error) {
  const code = String(error?.message ?? 'unknown');
  return /^[A-Za-z0-9_.:-]{1,100}$/.test(code) ? code : 'unclassified_failure';
}

async function evaluate(socket, expression, timeoutMs) {
  const response = await call(socket, 'Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, userGesture: true }, timeoutMs);
  if (response.exceptionDetails) throw new Error('cdp_eval_exception');
  return response.result?.value;
}

async function openCdp(url) {
  const socket = new WebSocket(url);
  const pending = new Map();
  let nextId = 1;
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('cdp_open_timeout')), 10000);
    socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
    socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('cdp_open_failed')); }, { once: true });
  });
  socket.addEventListener('message', event => {
    let message;
    try { message = JSON.parse(event.data); } catch { return; }
    if (!message.id || !pending.has(message.id)) return;
    const item = pending.get(message.id);
    pending.delete(message.id);
    clearTimeout(item.timer);
    message.error ? item.reject(new Error('cdp_command_failed')) : item.resolve(message.result ?? {});
  });
  socket.call = (method, params = {}, timeoutMs = 12000) => {
    const id = nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { pending.delete(id); reject(new Error('cdp_command_timeout')); }, timeoutMs);
      pending.set(id, { resolve, reject, timer });
      socket.send(JSON.stringify({ id, method, params }));
    });
  };
  return socket;
}

function call(socket, method, params = {}, timeoutMs = 12000) { return socket.call(method, params, timeoutMs); }
function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
