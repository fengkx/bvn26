#!/usr/bin/env node

import { writeFile } from 'node:fs/promises';

const endpoint = 'http://127.0.0.1:9240';
const pageBase = 'http://127.0.0.1:8017/?peer=';
const browserInfo = await (await fetch(`${endpoint}/json/version`)).json();
const browser = await connect(browserInfo.webSocketDebuggerUrl);
let host;
let guest;
let hostTarget;
let guestTarget;
let hostCode;
let result;

try {
    ({ targetId: hostTarget, tab: host } = await createPage('host'));
    await navigate(host, `${pageBase}host`);
    progress('host page loaded; creating room');
    const hostInitialRoom = await waitStatus(host, (status) => status?.inviteReady === true, 60_000, 'host room admission');
    progress(`host initial room options collapsed=${hostInitialRoom.advancedCollapsed}`);
    progress('host room created; waiting for guest admission');
    hostCode = await evaluate(host, 'window.__bvnOnlinePairInviteCode || ""');
    assert(typeof hostCode === 'string' && hostCode.length > 0, 'host invite code unavailable');

    ({ targetId: guestTarget, tab: guest } = await createPage('guest'));
    await navigate(guest, `${pageBase}guest`);
    await evaluate(guest, `window.__bvnOnlinePairInviteCode=${JSON.stringify(hostCode)}`);
    hostCode = '';
    const admitted = await Promise.all([
        waitStatus(host, (status) => status?.admitted === true, 20_000, 'host guest admission'),
        waitStatus(guest, (status) => status?.admitted === true, 20_000, 'guest room admission'),
    ]);
    progress(`both room views initialized; advancedCollapsed=${admitted.map((status) => status.advancedCollapsed).join(',')}`);
    progress('both room seats admitted; waiting for visible enabled connect controls');
    const connectControls = await Promise.all([
        waitStatus(host, (status) => status?.canConnect === true && status?.busy === false, 15_000, 'host connect control enabled'),
        waitStatus(guest, (status) => status?.canConnect === true && status?.busy === false, 15_000, 'guest connect control enabled'),
    ]);
    assert(connectControls.every((status) => status.canConnect && !status.busy), 'connect controls were not ready');

    await Promise.all([
        evaluate(host, 'window.__bvnOnlinePairConnect=true'),
        evaluate(guest, 'window.__bvnOnlinePairConnect=true'),
    ]);
    progress('both connect controls enabled; request sent through production Lobby handlers');
    const connectionStarted = await Promise.all([
        waitStatus(host, (status) => status?.connectAttempted === true, 8_000, 'host connection request entered'),
        waitStatus(guest, (status) => status?.connectAttempted === true, 8_000, 'guest connection request entered'),
    ]);
    const connectionProgress = await Promise.all([
        waitStatus(host, (status) => status?.connectionStarting === true || status?.connectionReady === true || Boolean(status?.connectionIssue), 8_000, 'host connection startup'),
        waitStatus(guest, (status) => status?.connectionStarting === true || status?.connectionReady === true || Boolean(status?.connectionIssue), 8_000, 'guest connection startup'),
    ]);
    progress(`both production handlers entered; startup=${connectionProgress.map((status) => status.connectionState || status.connectionIssue || 'ready').join(',')}`);
    assert(connectionStarted.every((status) => status.connectAttempted), 'connection request did not enter both handlers');
    assert(connectionProgress.every((status) => status.connectionStarting || status.connectionReady || status.connectionIssue), 'connection startup did not begin');
    const connected = await Promise.all([
        waitStatus(host, (status) => status?.connectionReady === true, 65_000, 'host WebRTC data channels'),
        waitStatus(guest, (status) => status?.connectionReady === true, 65_000, 'guest WebRTC data channels'),
    ]);
    await Promise.all([
        waitStatus(host, (status) => status?.selectionActive === true && status?.selectionPhase === 0, 12_000, 'host fighter selection UI'),
        waitStatus(guest, (status) => status?.selectionActive === true && status?.selectionPhase === 0, 12_000, 'guest fighter selection UI'),
    ]);
    progress('both WebRTC channels open and fighter selection active; activating each real canvas');
    await Promise.all([clickCanvas(host), clickCanvas(guest)]);
    await screenshot(host, '/private/tmp/online-vshuman/selection-fighters.png');

    await pressKey(host, 'd');
    await pressKey(guest, 'd');
    await delay(150);
    await pressKey(host, 'j');
    await pressKey(guest, 'j');
    await waitStatus(host, (status) => status?.selectionActive && status.selectionPhase === 1, 8_000, 'host helper selection phase');
    await waitStatus(guest, (status) => status?.selectionActive && status.selectionPhase === 1, 8_000, 'guest helper selection phase');
    progress('both adapters entered helper selection');
    await screenshot(host, '/private/tmp/online-vshuman/selection-helpers.png');

    await pressKey(host, 'd');
    await pressKey(guest, 'd');
    await delay(150);
    await pressKey(host, 'j');
    await pressKey(guest, 'j');
    const committed = await Promise.all([
        waitStatus(host, (status) => status?.committed === true, 25_000, 'host persisted role/helper selections'),
        waitStatus(guest, (status) => status?.committed === true, 25_000, 'guest persisted role/helper selections'),
    ]);
    assert(committed[0].committedChoices.length === 2 && committed[1].committedChoices.length === 2,
        'room projection did not contain both committed choices');
    progress('both players committed fighter and helper choices to room state');

    const initialMaps = await Promise.all([
        waitStatus(host, (status) => status?.mapSelectionVisible === true && status?.mapSelectionStage, 12_000, 'host online map selection UI'),
        waitStatus(guest, (status) => status?.mapSelectionVisible === true && status?.mapSelectionStage, 12_000, 'guest online map selection UI'),
    ]);
    const renderedMaps = await Promise.all([
        waitStatus(host, (status) => status?.mapSourceFrame >= status?.mapStopFrame, 8_000, 'host map source transition'),
        waitStatus(guest, (status) => status?.mapSourceFrame >= status?.mapStopFrame, 8_000, 'guest map source transition'),
    ]);
    assert(initialMaps[0].mapSelectionStage === initialMaps[1].mapSelectionStage,
        'guest map selection did not mirror the host initial stage');
    assert(initialMaps[0].mapSelectionEnabled === true && initialMaps[0].mapHostAuthority === true,
        'host map selection was not enabled with authority');
    assert(initialMaps[1].mapSelectionEnabled === false && initialMaps[1].mapHostAuthority === false,
        'guest map selection accepted local input');
    assert(renderedMaps.every((status) => status.mapSourceFrame >= status.mapStopFrame),
        'map selection screenshot was taken before the source transition completed');
    progress('production map selection visible on both peers; host authority and guest mirror verified');
    await clickCanvas(host);
    await clickCanvas(guest);
    await screenshot(host, '/private/tmp/online-vshuman/selection-map.png');

    const previousStage = initialMaps[0].mapSelectionStage;
    await clickCanvas(host);
    // MapSelection repeats every five 30 Hz logic frames; a longer hold can
    // move twice and return to the original sparse-grid cell.
    await pressKey(host, 'd', 75);
    const hostMapMoved = await waitStatus(
        host,
        (status) => status?.mapSelectionVisible === true && status?.mapSelectionStage !== previousStage,
        8_000,
        'host keyboard map movement',
    );
    const guestMapMirrored = await waitStatus(
        guest,
        (status) => status?.mapSelectionVisible === true && status?.mapSelectionStage === hostMapMoved.mapSelectionStage,
        8_000,
        'guest mirrored host map movement',
    );
    assert(hostMapMoved.mapSelectionStage === guestMapMirrored.mapSelectionStage,
        'guest did not display the host-selected map');
    assert(hostMapMoved.serviceStage === previousStage,
        'map movement changed the service stage before host confirmation');
    progress('host moved map selection by keyboard; guest mirrored the pending stage');

    await clickCanvas(guest);
    await pressKey(guest, 'd', 75);
    const guestInputRejected = await waitStatus(
        guest,
        (status) => status?.mapSelectionVisible === true && status?.mapSelectionStage === hostMapMoved.mapSelectionStage,
        3_000,
        'guest local map input rejection',
    );
    assert(guestInputRejected.serviceStage === previousStage,
        'guest input unexpectedly committed a map to the service');

    await clickCanvas(host);
    await pressKey(host, 'j');
    const configuredMaps = await Promise.all([
        waitStatus(host, (status) => status?.serviceStage === hostMapMoved.mapSelectionStage
            && status?.mapHandshakeComplete === true && status?.mapSelectionVisible === false,
        20_000, 'host map confirmation handshake and service projection'),
        waitStatus(guest, (status) => status?.serviceStage === hostMapMoved.mapSelectionStage
            && status?.mapHandshakeComplete === true && status?.mapSelectionVisible === false,
        20_000, 'guest map confirmation handshake and service projection'),
    ]);
    assert(configuredMaps.every((status) => status.phase === 'lobby'),
        'map confirmation left the lobby before ready');
    progress(`host confirmed map ${hostMapMoved.mapSelectionStage}; service stage matched on both peers`);
    await screenshot(host, '/private/tmp/online-vshuman/room-before-ready.png');
    progress(`compact room default state verified; advancedCollapsed=${configuredMaps[0].advancedCollapsed}; scroll visible in screenshot`);

    await Promise.all([
        waitStatus(host, (status) => status?.canReady === true && status?.busy === false, 12_000, 'host ready control enabled'),
        waitStatus(guest, (status) => status?.canReady === true && status?.busy === false, 12_000, 'guest ready control enabled'),
    ]);
    progress('both ready controls visible and enabled');
    await evaluate(host, 'window.__bvnOnlinePairReady=true');
    const hostReady = await waitStatus(host, (status) => status?.ready?.[0] === true, 15_000, 'host ready commit');
    await evaluate(guest, 'window.__bvnOnlinePairReady=true');
    const ready = await Promise.all([
        waitStatus(host, (status) => status?.ready?.[0] === true && status?.ready?.[1] === true, 15_000, 'both ready state on host'),
        waitStatus(guest, (status) => status?.ready?.[0] === true && status?.ready?.[1] === true, 15_000, 'both ready state on guest'),
    ]);
    progress('both ready commits visible on both room projections');
    const prepareAccepted = await Promise.all([
        waitStatus(host, (status) => status?.sawPreparePhase === true, 20_000, 'host automatic prepare accepted by service'),
        waitStatus(guest, (status) => status?.sawPreparePhase === true, 20_000, 'guest observed service prepare phase'),
    ]);
    assert(prepareAccepted.every((status) => ['preparing', 'active'].includes(status.phase)),
        'service left startup before the automatic prepare phase could be observed');
    progress('both players ready; host automatic prepare accepted and visible to both clients');
    result = {
        marker: 'ONLINE_VSHUMAN_TWO_CHROME_MAP_AUTOPREPARE_OK',
        chrome: browserInfo.Browser,
        transport: 'real RoomClient signaling + WebRTC data channels, same-machine Chrome pages, LAN host-candidate opt-in with ICE_SERVERS=[]',
        hostConnected: connected[0].connectionReady,
        guestConnected: connected[1].connectionReady,
        hostAndGuestSelectionsCommitted: committed.every((status) => status.committed),
        committedChoices: committed[0].committedChoices,
        mapInitiallyMatched: initialMaps[0].mapSelectionStage === initialMaps[1].mapSelectionStage,
        hostKeyboardMapStage: hostMapMoved.mapSelectionStage,
        guestMirroredMapStage: guestMapMirrored.mapSelectionStage,
        guestLocalMapInputRejected: guestInputRejected.mapSelectionStage === hostMapMoved.mapSelectionStage,
        serviceMapStage: configuredMaps[0].serviceStage,
        hostReadyBeforeGuest: hostReady.ready[0] === true,
        bothReadyOnBothPeers: ready.every((status) => status.ready[0] && status.ready[1]),
        automaticPrepareAccepted: prepareAccepted.every((status) => status.sawPreparePhase),
        observedPhaseAtCleanup: prepareAccepted.map((status) => status.phase),
        screenshots: [
            '/private/tmp/online-vshuman/selection-fighters.png',
            '/private/tmp/online-vshuman/selection-helpers.png',
            '/private/tmp/online-vshuman/selection-map.png',
            '/private/tmp/online-vshuman/room-before-ready.png',
        ],
        roomBeforeReady: {
            advancedCollapsed: configuredMaps[0].advancedCollapsed,
            scrollLayout: 'visually captured in room-before-ready.png; no numeric scroll position is claimed',
        },
        scope: 'real production RenderSurface + OnlineLobby + character/map selection adapters + real local matchmaking Worker; both ready and host automatic prepare accepted by service, no battle completion claim; no cross-city/NAT/TURN acceptance',
    };
    console.log(JSON.stringify(result));

    await evaluate(guest, 'window.__bvnOnlinePairLeave=true');
    await waitStatus(guest, (status) => status?.hasRoom === false, 30_000, 'guest room credential cleanup');
    await evaluate(host, 'window.__bvnOnlinePairLeave=true');
    await waitStatus(host, (status) => status?.hasRoom === false, 30_000, 'host room credential cleanup');
    console.log('ONLINE_VSHUMAN_TEST_ROOMS_CLEANED=true');
} catch (error) {
    const safeHost = host ? await safeStatus(host) : null;
    const safeGuest = guest ? await safeStatus(guest) : null;
    const cleanup = { guest: false, host: false };
    if (guest && safeGuest?.hasRoom) {
        try {
            await evaluate(guest, 'window.__bvnOnlinePairLeave=true');
            await waitStatus(guest, (status) => status?.hasRoom === false, 30_000, 'guest failure cleanup');
            cleanup.guest = true;
        } catch {}
    }
    if (host && safeHost?.hasRoom) {
        try {
            await evaluate(host, 'window.__bvnOnlinePairLeave=true');
            await waitStatus(host, (status) => status?.hasRoom === false, 30_000, 'host failure cleanup');
            cleanup.host = true;
        } catch {}
    }
    console.error(JSON.stringify({
        marker: 'ONLINE_VSHUMAN_TWO_CHROME_MAP_AUTOPREPARE_FAILED',
        error: String(error?.message || error),
        host: safeHost,
        guest: safeGuest,
        cleanup,
    }));
    if (host) await screenshot(host, '/private/tmp/online-vshuman/failure-host.png').catch(() => {});
    if (guest) await screenshot(guest, '/private/tmp/online-vshuman/failure-guest.png').catch(() => {});
    throw error;
} finally {
    if (hostCode) hostCode = '';
    if (host) host.close();
    if (guest) guest.close();
    if (hostTarget) await browser.call('Target.closeTarget', { targetId: hostTarget }).catch(() => {});
    if (guestTarget) await browser.call('Target.closeTarget', { targetId: guestTarget }).catch(() => {});
    browser.close();
}

async function createPage(role) {
    const { targetId } = await browser.call('Target.createTarget', { url: 'about:blank' });
    const targets = await (await fetch(`${endpoint}/json/list`)).json();
    const target = targets.find((entry) => entry.id === targetId);
    assert(target?.webSocketDebuggerUrl, `${role} Chrome tab did not expose a CDP websocket`);
    const tab = await connect(target.webSocketDebuggerUrl);
    await tab.call('Page.enable');
    await tab.call('Runtime.enable');
    await tab.call('Network.enable');
    await tab.call('Emulation.setFocusEmulationEnabled', { enabled: true });
    await tab.call('Page.setWebLifecycleState', { state: 'active' });
    await tab.call('Emulation.setDeviceMetricsOverride', {
        width: 1280, height: 900, deviceScaleFactor: 1, mobile: false,
    });
    return { targetId, tab };
}

async function navigate(tab, url) {
    await tab.call('Page.navigate', { url });
    await waitStatus(tab, (status) => status?.role !== undefined, 30_000, 'Godot Web fixture startup');
    await evaluate(tab, 'document.getElementById("canvas")?.focus()');
}

async function pressKey(tab, key, holdMs = 250) {
    await tab.call('Page.bringToFront');
    await evaluate(tab, 'document.getElementById("canvas")?.focus()');
    const upper = key.toUpperCase();
    const virtualKey = upper.charCodeAt(0);
    await tab.call('Input.dispatchKeyEvent', {
        type: 'rawKeyDown', key, code: `Key${upper}`, windowsVirtualKeyCode: virtualKey,
    });
    await delay(holdMs);
    await tab.call('Input.dispatchKeyEvent', {
        type: 'keyUp', key, code: `Key${upper}`, windowsVirtualKeyCode: virtualKey,
    });
    await delay(350);
}

async function clickCanvas(tab) {
    const bounds = await evaluate(tab, `(() => {
        const rect = document.getElementById('canvas')?.getBoundingClientRect();
        return rect ? {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2} : null;
    })()`);
    assert(bounds && Number.isFinite(bounds.x) && Number.isFinite(bounds.y), 'Godot canvas bounds unavailable');
    await tab.call('Page.bringToFront');
    await tab.call('Input.dispatchMouseEvent', {
        type: 'mousePressed', x: bounds.x, y: bounds.y, button: 'left', clickCount: 1,
    });
    await tab.call('Input.dispatchMouseEvent', {
        type: 'mouseReleased', x: bounds.x, y: bounds.y, button: 'left', clickCount: 1,
    });
    await delay(250);
}

async function waitStatus(tab, predicate, timeoutMs, label) {
    const deadline = Date.now() + timeoutMs;
    let last = null;
    while (Date.now() < deadline) {
        last = await safeStatus(tab);
        if (last && predicate(last)) return last;
        await delay(100);
    }
    throw new Error(`${label} timed out; safe status=${JSON.stringify(last)}`);
}

function progress(message) {
    console.log(`ONLINE_VSHUMAN_PROGRESS ${message}`);
}

async function safeStatus(tab) {
    const raw = await evaluate(tab, 'JSON.stringify(window.__bvnOnlinePairStatus ?? null)').catch(() => 'null');
    if (!raw || raw === 'null') return null;
    return JSON.parse(raw);
}

async function evaluate(tab, expression) {
    const response = await tab.call('Runtime.evaluate', {
        expression, awaitPromise: true, returnByValue: true,
    });
    if (response.exceptionDetails) throw new Error('Browser test evaluation failed');
    return response.result?.value;
}

async function screenshot(tab, path) {
    const response = await tab.call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    await writeFile(path, Buffer.from(response.data, 'base64'));
}

function connect(url) {
    const socket = new WebSocket(url);
    const pending = new Map();
    let nextId = 1;
    socket.addEventListener('message', (event) => {
        const message = JSON.parse(event.data);
        if (!message.id || !pending.has(message.id)) return;
        const entry = pending.get(message.id);
        pending.delete(message.id);
        if (message.error) entry.reject(new Error(message.error.message));
        else entry.resolve(message.result);
    });
    return new Promise((resolve, reject) => {
        socket.addEventListener('open', () => resolve({
            socket,
            close: () => socket.close(),
            call(method, params = {}) {
                const id = nextId++;
                return new Promise((done, fail) => {
                    pending.set(id, { resolve: done, reject: fail });
                    socket.send(JSON.stringify({ id, method, params }));
                });
            },
        }), { once: true });
        socket.addEventListener('error', reject, { once: true });
    });
}

function assert(condition, message) {
    if (!condition) throw new Error(message);
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
