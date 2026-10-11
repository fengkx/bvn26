import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import vm from 'node:vm';

const shellPath = new URL('../../godot/web/shell.html', import.meta.url);
const html = await readFile(shellPath, 'utf8');
const shellScript = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/)?.[1];
assert.ok(shellScript, 'expected the shell bootstrap script');

function createElement(id = '') {
    const handlers = new Map();
    const attributes = new Map();
    const classes = new Set();
    return {
        id,
        handlers,
        attributes,
        dataset: {},
        style: {},
        hidden: false,
        disabled: false,
        value: '',
        width: 0,
        height: 0,
        textContent: '',
        classList: {
            add: name => classes.add(name),
            remove: name => classes.delete(name),
            contains: name => classes.has(name),
            toggle(name, force = !classes.has(name)) {
                if (force) classes.add(name);
                else classes.delete(name);
                return force;
            },
        },
        addEventListener(name, callback) {
            if (!handlers.has(name)) handlers.set(name, []);
            handlers.get(name).push(callback);
        },
        async dispatch(name, event = {}) {
            let result;
            for (const callback of handlers.get(name) || []) result = callback(event);
            return await result;
        },
        setAttribute(name, value) { attributes.set(name, value); },
        contains(target) { return target === this; },
        matches() { return false; },
        focus() { this.focused = true; },
        remove() {},
        click() { this.clicked = true; },
        getBoundingClientRect() { return { width: 900, height: 600 }; },
    };
}

function createPage(buildSidecar, fetchImpl = null, rtcConstructor = undefined) {
    let now = 0;
    let nextIntervalId = 1;
    const intervalCallbacks = new Map();
    const elements = new Map();
    for (const id of ['player', 'canvas', 'fullscreen', 'feedback', 'edge-indicator', 'toolbar',
        'online-controls', 'online-status', 'online-request', 'online-pause', 'online-accept-pause',
        'online-refuse-pause', 'online-skip-intro', 'online-exit', 'online-collapse-tools', 'edge-label',
        'audio-control', 'audio-toggle', 'mute-toggle', 'volume-panel', 'volume-slider',
        'volume-value', 'volume-status', 'viewport', 'status', 'status-splash', 'status-progress', 'download']) {
        elements.set(id, createElement(id));
    }
    const player = elements.get('player');
    const viewport = elements.get('viewport');
    elements.get('edge-indicator').querySelector = selector => selector === '.edge-label' ? elements.get('edge-label') : null;
    const documentHandlers = new Map();
    const windowHandlers = new Map();
    let capturedBlob = null;
    const document = {
        baseURI: 'http://localhost/',
        fullscreenEnabled: false,
        fullscreenElement: null,
        visibilityState: 'visible',
        activeElement: null,
        getElementById: id => elements.get(id) || createElement(id),
        addEventListener(name, callback) {
            if (!documentHandlers.has(name)) documentHandlers.set(name, []);
            documentHandlers.get(name).push(callback);
        },
        createElement: tag => createElement(tag),
        body: { appendChild() {} },
    };
    const window = {
        devicePixelRatio: 2,
        innerWidth: 1280,
        innerHeight: 720,
        RTCPeerConnection: rtcConstructor,
        addEventListener(name, callback) {
            if (!windowHandlers.has(name)) windowHandlers.set(name, []);
            windowHandlers.get(name).push(callback);
        },
    };
    const localStorage = { getItem: () => null, setItem() {} };
    const urlApi = Object.assign(class extends URL {}, {
        createObjectURL(blob) { capturedBlob = blob; return 'blob:diagnostics'; },
        revokeObjectURL() {},
    });
    const context = vm.createContext({
        window,
        document,
        navigator: { userAgent: 'diagnostics-test', language: 'zh-CN' },
        location: { origin: 'http://localhost', pathname: '/' },
        performance: { now: () => now },
        setNow(value) { now = value; },
        innerWidth: 1280,
        innerHeight: 720,
        devicePixelRatio: 2,
        localStorage,
        console: { log() {}, info() {}, warn() {}, error() {} },
        URL: urlApi,
        Blob,
        TextEncoder,
        AbortController,
        ResizeObserver: class { observe() {} },
        fetch: fetchImpl || (async () => ({ ok: true, json: async () => buildSidecar })),
        setTimeout: (callback, delay, ...args) => setTimeout(callback, Math.min(delay, 25), ...args),
        clearTimeout,
        Date,
        Math,
        crypto: { randomUUID: () => 'test-session-id' },
        Promise,
        setInterval(callback) {
            const id = nextIntervalId++;
            intervalCallbacks.set(id, callback);
            return id;
        },
        clearInterval(id) { intervalCallbacks.delete(id); },
    });
    vm.runInContext(shellScript, context, { timeout: 1000 });
    return {
        context, window, elements, player, document, documentHandlers, windowHandlers,
        getBlob: () => capturedBlob,
        advanceIntervals() { for (const callback of [...intervalCallbacks.values()]) callback(); },
        get intervalCount() { return intervalCallbacks.size; },
    };
}

function fakeRTCClass(getStats = async () => new Map()) {
    return class FakeRTCPeerConnection {
        static instances = [];
        static initialConnectionState = 'new';
        static initialIceConnectionState = 'new';

        constructor(configuration) {
            assert.equal(new.target, FakeRTCPeerConnection, 'constructor new.target should remain unchanged');
            this.configuration = configuration;
            this.connectionState = FakeRTCPeerConnection.initialConnectionState;
            this.iceConnectionState = FakeRTCPeerConnection.initialIceConnectionState;
            this.listeners = new Map();
            this.getStatsImpl = getStats;
            this.getStatsCalls = 0;
            FakeRTCPeerConnection.instances.push(this);
        }

        addEventListener(name, callback) {
            if (!this.listeners.has(name)) this.listeners.set(name, []);
            this.listeners.get(name).push(callback);
        }

        removeEventListener(name, callback) {
            const callbacks = this.listeners.get(name) || [];
            this.listeners.set(name, callbacks.filter(existing => existing !== callback));
        }

        dispatch(name) {
            for (const callback of this.listeners.get(name) || []) callback();
        }

        setStates(connectionState, iceConnectionState) {
            this.connectionState = connectionState;
            this.iceConnectionState = iceConnectionState;
            this.dispatch('connectionstatechange');
            this.dispatch('iceconnectionstatechange');
        }

        getStats() {
            this.getStatsCalls++;
            return this.getStatsImpl();
        }
    };
}

async function flushPromises() {
    await Promise.resolve();
    await new Promise(resolve => setImmediate(resolve));
}

const sha = 'a'.repeat(64);
const sidecar = {
    schemaVersion: 1,
    buildID: sha,
    gitCommit: 'deadbeef',
    dirty: true,
    dirtyPaths: ['godot/fighter_runtime.gd'],
    resourceVersion: 'b'.repeat(64),
    pckSha256: 'c'.repeat(64),
    pckHashKind: 'exported_artifact',
    builtAt: '2026-09-15T00:00:00Z',
    exportedAt: '2026-09-15T00:00:10Z',
};

test('exports a v2 report with legacy fields, bounded runtime events, tape, and matched artifact metadata', async () => {
    const page = createPage(sidecar);
    const { window, elements, context, getBlob } = page;
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(JSON.parse(window.bvnDiagnosticsGetContext()).runId, 'test-session-id');
    window.bvnDiagnosticsPush(JSON.stringify({ seq: 1, type: 'input_consumed', monoMs: 10, fightTick: 1, buildID: sha, payload: { slot: 1, pressed: ['J'] } }));
    context.setNow(30_000);
    window.bvnDiagnosticsPush(JSON.stringify({ seq: 2, type: 'pause_state', monoMs: 30_000, buildID: sha, payload: { paused: true } }));
    window.bvnDiagnosticsPush(JSON.stringify({ seq: 3, type: 'input_consumed', monoMs: 30_001, fightTick: 30, buildID: sha, payload: { slot: 2, pressed: ['L'] } }));
    context.setNow(61_000);
    window.bvnDiagnosticsPush(JSON.stringify({ seq: 4, type: 'action_transition', monoMs: 61_000, buildID: sha, payload: { action: '站立' } }));
    const visibilitySignals = [];
    window.bvnDiagnosticsRegister((command, requestId) => {
        if (command === 'visibility') { visibilitySignals.push(requestId); return; }
        assert.equal(command, 'snapshot');
        window.bvnDiagnosticsSetSnapshot(JSON.stringify({
            requestId,
            buildID: sha,
            match: { mode: 'vs_com', map: '現世', players: [{ slot: 1, fighter: '卡卡西', state: { action: '站立', hp: 900 } }] },
            pause: { globalSuper: false },
        }));
    });
    page.document.visibilityState = 'hidden';
    for (const callback of page.documentHandlers.get('visibilitychange') || []) callback();
    await elements.get('download').dispatch('click');
    const report = JSON.parse(await getBlob().text());
    assert.equal(report.schemaVersion, 2);
    assert.equal(report.runId, 'test-session-id');
    assert.ok(Array.isArray(report.entries));
    assert.equal(report.messageLimit, 8192);
    assert.equal(report.build.status, 'match');
    assert.equal(report.build.pckHashKind, 'exported_artifact');
    assert.equal(report.build.pckSha256, 'c'.repeat(64));
    assert.equal(report.runtime.snapshotStatus, 'acknowledged');
    assert.equal(report.runtime.snapshot.match.players[0].state.hp, 900);
    assert.deepEqual(report.runtime.inputTape.map(event => event.seq), [3]);
    assert.deepEqual(report.runtime.criticalEvents.map(event => event.type), ['pause_state']);
    assert.equal(report.runtime.criticalIncidents.length, 1);
    assert.deepEqual(report.runtime.criticalIncidents[0].events.map(event => event.seq), [2, 3]);
    assert.equal(report.runtime.buffer.dropped.age, 1);
    assert.ok(report.runtime.buffer.coverageMs <= 60_000);
    assert.equal(report.webrtc.available, false);
    assert.equal(report.webrtc.constructorHookStatus, 'native_constructor_unavailable');
    assert.deepEqual(report.webrtc.connections, []);
    assert.deepEqual(visibilitySignals, ['visible', 'hidden']);
    const visibilityEvent = report.runtime.events.find(event => event.type === 'page_visibility');
    assert.equal(visibilityEvent.origin, 'shell');
    assert.equal(visibilityEvent.shellSeq, 1);
    assert.equal(visibilityEvent.seq, undefined);
});

test('does not fabricate build identity when runtime and sidecar disagree', async () => {
    const page = createPage(sidecar);
    const { window, elements, getBlob } = page;
    await new Promise(resolve => setImmediate(resolve));
    window.bvnDiagnosticsPush(JSON.stringify({ seq: 1, type: 'runtime_boot', buildID: 'd'.repeat(64), payload: {} }));
    window.bvnDiagnosticsRegister((command, requestId) => {
        if (command === 'visibility') return;
        window.bvnDiagnosticsSetSnapshot(JSON.stringify({ requestId, buildID: 'd'.repeat(64), match: {} }));
    });
    await elements.get('download').dispatch('click');
    const report = JSON.parse(await getBlob().text());
    assert.equal(report.build.status, 'mismatch');
    assert.equal(report.build.buildID, 'd'.repeat(64));
    assert.equal(report.build.sidecarBuildID, 'a'.repeat(64));
});

test('routes online edit shortcuts and lets Godot receive the native text paste event', async () => {
    const page = createPage(sidecar);
    const { window, elements, documentHandlers, windowHandlers } = page;
    window.bvnOnlinePasteTargetActive = true;
    const shortcuts = [];
    let pasteCalls = 0;
    window.bvnOnlineShortcutCallback = key => shortcuts.push(key);
    window.bvnOnlinePasteCallback = (...args) => {
        assert.equal(args.length, 0, 'paste bridge must not duplicate clipboard text');
        pasteCalls++;
    };

    const onlineKeydown = documentHandlers.get('keydown').find(handler =>
        handler.toString().includes('bvnOnlinePasteTargetActive'));
    const onlinePaste = windowHandlers.get('paste').find(handler =>
        handler.toString().includes('bvnOnlinePasteTargetActive'));
    assert.ok(onlineKeydown);
    assert.ok(onlinePaste);

    function keyEvent(overrides = {}) {
        return {
            target: elements.get('canvas'),
            key: 'a',
            code: 'KeyA',
            metaKey: true,
            ctrlKey: false,
            shiftKey: false,
            altKey: false,
            isComposing: false,
            stopped: false,
            prevented: false,
            stopImmediatePropagation() { this.stopped = true; },
            stopPropagation() { this.stopped = true; },
            preventDefault() { this.prevented = true; },
            ...overrides,
        };
    }

    const selectAll = keyEvent();
    onlineKeydown(selectAll);
    assert.deepEqual(shortcuts, ['a']);
    assert.equal(selectAll.stopped, true);
    assert.equal(selectAll.prevented, true);

    const pasteKey = keyEvent({ key: 'v', code: 'KeyV' });
    onlineKeydown(pasteKey);
    assert.equal(pasteKey.stopped, true);
    assert.equal(pasteKey.prevented, false, 'native browser paste must still fire');

    const shifted = keyEvent({ shiftKey: true });
    onlineKeydown(shifted);
    assert.equal(shortcuts.length, 1, 'unsupported modifier combinations must be ignored');
    assert.equal(shifted.stopped, false);

    let bubbled = false;
    const textPaste = {
        target: elements.get('canvas'),
        clipboardData: {
            types: ['text/plain'],
            getData() { throw new Error('shell must leave clipboard extraction to Godot'); },
        },
        prevented: false,
        stopped: false,
        preventDefault() { this.prevented = true; },
        stopImmediatePropagation() { this.stopped = true; },
        stopPropagation() { this.stopped = true; },
    };
    onlinePaste(textPaste);
    bubbled = !textPaste.stopped;
    assert.equal(textPaste.prevented, true, 'paste must not fall through to hidden IME content');
    assert.equal(bubbled, true, 'Godot bubble-phase paste handler must still receive the event');
    assert.equal(pasteCalls, 1);

    const imagePaste = {
        ...textPaste,
        clipboardData: { types: ['image/png'] },
        stopped: false,
        prevented: false,
    };
    onlinePaste(imagePaste);
    assert.equal(imagePaste.prevented, true);
    assert.equal(imagePaste.stopped, false);
    assert.equal(pasteCalls, 1, 'image-only clipboard data must not trigger text paste');
});

test('preserves bounded error incidents beyond the rolling window and closes post-trigger capture', async () => {
    const page = createPage(sidecar);
    const { window, elements, context, getBlob } = page;
    await new Promise(resolve => setImmediate(resolve));
    window.bvnLog('error', 'WebGL context lost');
    context.setNow(60_001);
    window.bvnDiagnosticsPush(JSON.stringify({ seq: 1, type: 'pause_state', buildID: sha, payload: { paused: true } }));
    context.setNow(65_002);
    window.bvnDiagnosticsPush(JSON.stringify({ seq: 2, type: 'action_transition', buildID: sha, payload: { action: '站立' } }));
    await elements.get('download').dispatch('click');
    const report = JSON.parse(await getBlob().text());
    assert.deepEqual(report.runtime.criticalEvents.map(event => event.type), ['diagnostic_exception', 'pause_state']);
    assert.equal(report.runtime.criticalEvents[0].origin, 'shell');
    assert.equal(report.runtime.criticalIncidents.length, 2);
    assert.equal(report.runtime.criticalIncidents[0].status, 'window_complete');
    assert.equal(report.runtime.criticalIncidents[1].status, 'window_complete');
    assert.ok(report.runtime.criticalIncidents[1].events.some(event => event.type === 'pause_state'));
    assert.ok(!report.entries.some(entry => entry.message.includes('WebGL context lost')));
});

test('caps incident count and reports oldest incident drops', async () => {
    const page = createPage(sidecar);
    const { window, elements, getBlob } = page;
    await new Promise(resolve => setImmediate(resolve));
    for (let seq = 1; seq <= 10; seq++) {
        window.bvnDiagnosticsPush(JSON.stringify({ seq, type: 'diagnostic_exception', buildID: sha, payload: { reason: 'synthetic' } }));
    }
    await elements.get('download').dispatch('click');
    const report = JSON.parse(await getBlob().text());
    assert.equal(report.runtime.criticalIncidents.length, 8);
    assert.equal(report.runtime.buffer.incidentDropped, 2);
    assert.equal(report.runtime.criticalIncidents[0].trigger.seq, 3);
});

test('enforces event count and byte limits while rejecting oversized events', async () => {
    const countPage = createPage(sidecar);
    await new Promise(resolve => setImmediate(resolve));
    for (let seq = 1; seq <= 50_003; seq++) {
        countPage.window.bvnDiagnosticsPush(JSON.stringify({ seq, type: 'runtime_tick', payload: { tick: seq } }));
    }
    await countPage.elements.get('download').dispatch('click');
    const countReport = JSON.parse(await countPage.getBlob().text());
    assert.equal(countReport.runtime.buffer.retainedEvents, 50_000);
    assert.equal(countReport.runtime.buffer.dropped.count, 3);

    const bytePage = createPage(sidecar);
    await new Promise(resolve => setImmediate(resolve));
    const padding = 'x'.repeat(30_000);
    for (let seq = 1; seq <= 560; seq++) {
        bytePage.window.bvnDiagnosticsPush(JSON.stringify({ seq, type: 'runtime_tick', payload: { padding } }));
    }
    bytePage.window.bvnDiagnosticsPush(JSON.stringify({ type: 'runtime_tick', payload: { padding: 'x'.repeat(33_000) } }));
    await bytePage.elements.get('download').dispatch('click');
    const byteReport = JSON.parse(await bytePage.getBlob().text());
    assert.ok(byteReport.runtime.buffer.retainedBytes <= byteReport.runtime.buffer.byteLimit);
    assert.ok(byteReport.runtime.buffer.dropped.bytes > 0);
    assert.equal(byteReport.runtime.buffer.rejectedEvents, 1);
});

test('labels snapshot timeout, missing runtime, and unavailable sidecar explicitly', async () => {
    const sidecarPage = createPage(null, async () => { throw new Error('offline'); });
    await new Promise(resolve => setImmediate(resolve));
    await sidecarPage.elements.get('download').dispatch('click');
    const sidecarReport = JSON.parse(await sidecarPage.getBlob().text());
    assert.equal(sidecarReport.runtime.snapshotStatus, 'runtime_unavailable');
    assert.equal(sidecarReport.build.status, 'unknown');
    assert.equal(sidecarReport.build.pckSha256, null);

    const timeoutPage = createPage(sidecar);
    await new Promise(resolve => setImmediate(resolve));
    timeoutPage.window.bvnDiagnosticsRegister(command => {
        if (command === 'visibility') return;
    });
    await timeoutPage.elements.get('download').dispatch('click');
    const timeoutReport = JSON.parse(await timeoutPage.getBlob().text());
    assert.equal(timeoutReport.runtime.snapshotStatus, 'timeout');
});

function onlineSnapshot(overrides = {}) {
    return {
        schemaVersion: 1,
        active: true,
        session: 'online-session-1',
        revision: 1,
        status: '对局进行中',
        pauseLabel: '请求暂停',
        canPause: true,
        canResume: false,
        pauseRequest: null,
        canAcceptPause: false,
        canRefusePause: false,
        canSkipIntro: true,
        canExit: true,
        exitLabel: '退出本局',
        ...overrides,
    };
}

test('renders online controls and routes only current-session actions with revision and request id', () => {
    const page = createPage(sidecar);
    const { window, elements } = page;
    const calls = [];
    const token = window.bvnOnlineControlsRegister((...args) => calls.push(args));
    assert.equal(token, 1);
    assert.equal(window.bvnOnlineControlsUpdate(JSON.stringify(onlineSnapshot()), token), true);
    assert.equal(elements.get('online-controls').hidden, false);
    assert.equal(elements.get('online-status').textContent, '对局进行中');
    assert.equal(elements.get('online-pause').textContent, '请求暂停');
    assert.equal(elements.get('online-pause').hidden, false);
    assert.equal(elements.get('online-skip-intro').hidden, false);
    elements.get('online-pause').dispatch('click');
    elements.get('online-skip-intro').dispatch('click');
    assert.deepEqual(calls, [
        ['pause', 'online-session-1', 1, ''],
        ['skip_intro', 'online-session-1', 1, ''],
    ]);
    assert.equal(elements.get('canvas').focused, true);

    const request = onlineSnapshot({
        revision: 2,
        status: '<img src=x onerror=alert(1)>',
        pauseLabel: '请求恢复',
        canPause: false,
        canResume: true,
        pauseRequest: { id: 'request-7', text: '<b>对方请求暂停</b>' },
        canAcceptPause: true,
        canRefusePause: true,
    });
    assert.equal(window.bvnOnlineControlsUpdate(JSON.stringify(request), token), true);
    assert.equal(elements.get('online-status').textContent, request.status, 'untrusted labels render as text');
    assert.equal(elements.get('online-request').textContent, request.pauseRequest.text);
    assert.equal(elements.get('online-accept-pause').hidden, false);
    elements.get('online-accept-pause').dispatch('click');
    elements.get('online-refuse-pause').dispatch('click');
    elements.get('online-pause').dispatch('click');
    assert.deepEqual(calls.slice(2), [
        ['accept_pause', 'online-session-1', 2, 'request-7'],
        ['refuse_pause', 'online-session-1', 2, 'request-7'],
        ['resume', 'online-session-1', 2, ''],
    ]);
});

test('rejects stale owners, malformed snapshots, and stale revisions without changing the current view', () => {
    const page = createPage(sidecar);
    const { window, elements } = page;
    const oldToken = window.bvnOnlineControlsRegister(() => {});
    const token = window.bvnOnlineControlsRegister(() => {});
    const initial = JSON.stringify(onlineSnapshot());
    assert.equal(window.bvnOnlineControlsUpdate(initial, oldToken), false);
    assert.equal(window.bvnOnlineControlsUnregister(oldToken), false);
    assert.equal(window.bvnOnlineControlsUpdate(initial, 0), false);
    assert.equal(elements.get('online-controls').hidden, true);
    assert.equal(window.bvnOnlineControlsUpdate(initial, token), true);
    assert.equal(window.bvnOnlineControlsUpdate('{broken', token), false);
    assert.equal(window.bvnOnlineControlsUpdate(JSON.stringify(onlineSnapshot({ revision: 0, status: '过期' })), token), false);
    assert.equal(window.bvnOnlineControlsUpdate(JSON.stringify(onlineSnapshot({ status: '同 revision 的冲突内容' })), token), false);
    assert.equal(window.bvnOnlineControlsUpdate(initial, oldToken), false);
    assert.equal(elements.get('online-status').textContent, '对局进行中');
    assert.equal(window.bvnOnlineControlsUnregister(token), true);
    assert.equal(elements.get('online-controls').hidden, true);
    assert.equal(elements.get('edge-indicator').classList.contains('online-active'), false);
});

test('keeps pending fullscreen controls discoverable without auto-opening and permits explicit collapse', async () => {
    const page = createPage(sidecar);
    const { window, elements, player, document } = page;
    document.fullscreenElement = player;
    const token = window.bvnOnlineControlsRegister(() => {});
    const pending = onlineSnapshot({
        pauseRequest: { id: 'request-8', text: '对方请求暂停' },
        canAcceptPause: true,
        canRefusePause: true,
    });
    assert.equal(window.bvnOnlineControlsUpdate(JSON.stringify(pending), token), true);
    assert.equal(player.classList.contains('tools-visible'), false, 'incoming request does not auto-open the toolbar');
    assert.equal(elements.get('edge-indicator').classList.contains('online-request'), true);
    assert.equal(elements.get('edge-label').textContent, '对方有操作请求');

    await elements.get('edge-indicator').dispatch('pointerenter');
    await elements.get('edge-indicator').dispatch('pointerleave');
    await new Promise(resolve => setTimeout(resolve, 40));
    assert.equal(player.classList.contains('tools-visible'), true, 'pending request keeps an opened toolbar available');

    elements.get('online-collapse-tools').dispatch('click');
    assert.equal(player.classList.contains('tools-visible'), false);
    assert.equal(player.classList.contains('tools-collapsed'), true);
    assert.equal(elements.get('canvas').focused, true);
    elements.get('edge-indicator').dispatch('click');
    assert.equal(player.classList.contains('tools-visible'), true);
    assert.equal(player.classList.contains('tools-collapsed'), false);

    const exitConfirm = onlineSnapshot({ revision: 2, exitLabel: '再点一次确认退出', pauseRequest: null });
    assert.equal(window.bvnOnlineControlsUpdate(JSON.stringify(exitConfirm), token), true);
    await elements.get('toolbar').dispatch('pointerleave');
    await new Promise(resolve => setTimeout(resolve, 40));
    assert.equal(player.classList.contains('tools-visible'), true, 'exit confirmation remains visible until resolved');
});

test('places online controls in the existing toolbar and hides inactive controls explicitly', () => {
    const toolbarStart = html.indexOf('<nav id="toolbar"');
    const onlineStart = html.indexOf('<section id="online-controls"');
    const viewportStart = html.indexOf('<div id="viewport"');
    assert.ok(toolbarStart >= 0 && onlineStart > toolbarStart && viewportStart > onlineStart);
    assert.match(html, /#online-controls\[hidden\], #online-controls \[hidden\] \{ display: none !important; \}/);
    assert.match(html, /#player:fullscreen #toolbar/);
    assert.match(html, /#edge-indicator\.online-request \.edge-label/);
});

test('tracks bounded selected ICE-pair summaries without leaking candidate or ICE configuration details', async () => {
    const stats = new Map([
        ['transport-id-private', { type: 'transport', selectedCandidatePairId: 'pair-id-private' }],
        ['pair-id-private', {
            id: 'pair-id-private',
            type: 'candidate-pair',
            localCandidateId: 'local-id-private',
            remoteCandidateId: 'remote-id-private',
            currentRoundTripTime: 0.0254,
            bytesSent: 101,
            bytesReceived: 202,
            packetsSent: 3,
            packetsReceived: 4,
            jitter: 0.02,
            packetsLost: 7,
            address: '192.0.2.80',
            port: 53421,
        }],
        ['local-id-private', {
            id: 'local-id-private',
            type: 'local-candidate',
            candidateType: 'relay',
            protocol: 'udp',
            address: '192.0.2.81',
            port: 53422,
            url: 'turn:turn-secret.example:3478?transport=udp',
            usernameFragment: 'username-secret',
            password: 'credential-secret',
        }],
        ['remote-id-private', {
            id: 'remote-id-private', type: 'remote-candidate', candidateType: 'host',
            protocol: 'udp',
            ip: '198.51.100.9', port: 53423,
        }],
        ['inbound-rtp-private', {
            id: 'inbound-rtp-private',
            type: 'inbound-rtp',
            jitter: 0.012,
            packetsLost: 2,
        }],
    ]);
    const FakeRTC = fakeRTCClass(async () => stats);
    const page = createPage(sidecar, null, FakeRTC);
    const configuration = { iceServers: [{ urls: 'turn:turn-secret.example', username: 'username-secret', credential: 'credential-secret' }] };
    const peer = new page.window.RTCPeerConnection(configuration);
    assert.ok(peer instanceof FakeRTC);
    assert.equal(peer.configuration, configuration);
    assert.equal(peer.getStatsCalls, 0);
    assert.equal(page.intervalCount, 1);

    page.context.setNow(1000);
    page.advanceIntervals();
    await flushPromises();
    assert.equal(peer.getStatsCalls, 1);

    for (let index = 0; index < 60; index++) {
        page.context.setNow(2000 + index * 1000);
        page.advanceIntervals();
        await flushPromises();
    }
    peer.setStates('connected', 'completed');
    peer.setStates('closed', 'closed');
    page.advanceIntervals();
    assert.equal(page.intervalCount, 0, 'closed peers stop the sampling timer');

    await page.elements.get('download').dispatch('click');
    const report = JSON.parse(await page.getBlob().text());
    const rtc = report.webrtc;
    assert.equal(rtc.available, true);
    assert.equal(rtc.sampleIntervalMs, 3000);
    assert.equal(rtc.roleBinding, 'unclassified');
    assert.match(rtc.rttMeaning, /not input end-to-end latency/);
    assert.equal(rtc.connections.length, 1);
    const connection = rtc.connections[0];
    assert.equal(connection.localId, 1);
    assert.equal(connection.role, 'unclassified');
    assert.equal(connection.endedReason, 'closed');
    assert.equal(connection.connectionState, 'closed');
    assert.equal(connection.sampleCount, 61);
    assert.equal(connection.samples.length, 60);
    assert.equal(connection.droppedSamples, 1);
    assert.deepEqual(connection.selectedPair, {
        localCandidateType: 'relay',
        remoteCandidateType: 'host',
        protocol: 'udp',
    });
    assert.deepEqual(connection.samples.at(-1), {
        monoMs: 61_000,
        status: 'available',
        localCandidateType: 'relay',
        remoteCandidateType: 'host',
        protocol: 'udp',
        rttMs: 25.4,
        jitterMs: 20,
        packetsLost: 7,
        bytesSent: 101,
        bytesReceived: 202,
        packetsSent: 3,
        packetsReceived: 4,
    });
    const pairEvents = report.runtime.events.filter(event => event.type === 'ice_selected_pair');
    assert.equal(pairEvents.length, 1, 'selected pair should be logged once, not per sample');
    assert.deepEqual(pairEvents[0].payload, connection.selectedPair);
    const exportedRtc = JSON.stringify(rtc);
    for (const privateValue of ['192.0.2.', '198.51.100.', '53421', 'pair-id-private',
        'local-id-private', 'turn-secret', 'username-secret', 'credential-secret']) {
        assert.equal(exportedRtc.includes(privateValue), false, `RTC report leaked ${privateValue}`);
    }
});

test('does not overlap pending getStats calls and contains rejections without exporting error details', async () => {
    let resolvePending;
    const pendingStats = new Promise(resolve => { resolvePending = resolve; });
    const FakeRTC = fakeRTCClass(() => pendingStats);
    const page = createPage(sidecar, null, FakeRTC);
    const peer = new page.window.RTCPeerConnection({});
    page.advanceIntervals();
    page.advanceIntervals();
    assert.equal(peer.getStatsCalls, 1, 'a slow getStats promise must not overlap the next interval');

    resolvePending(new Map());
    await flushPromises();
    peer.getStatsImpl = () => Promise.reject(new Error('turn:private.example username=password'));
    page.advanceIntervals();
    await flushPromises();
    assert.equal(peer.getStatsCalls, 2);

    await page.elements.get('download').dispatch('click');
    const report = JSON.parse(await page.getBlob().text());
    assert.equal(report.webrtc.connections[0].statsErrorCount, 1);
    assert.equal(report.webrtc.connections[0].lastSampleStatus, 'error');
    assert.equal(JSON.stringify(report.webrtc).includes('private.example'), false);
    assert.equal(JSON.stringify(report.webrtc).includes('username=password'), false);
});

test('ignores a getStats rejection that arrives after a connection is released', async () => {
    let rejectPending;
    const pendingStats = new Promise((_resolve, reject) => { rejectPending = reject; });
    const FakeRTC = fakeRTCClass(() => pendingStats);
    const page = createPage(sidecar, null, FakeRTC);
    const peer = new page.window.RTCPeerConnection({});
    page.advanceIntervals();
    peer.setStates('failed', 'failed');
    assert.equal(peer.listeners.get('connectionstatechange').length, 0);
    rejectPending(new Error('turn:private.example username=password'));
    await flushPromises();

    await page.elements.get('download').dispatch('click');
    const report = JSON.parse(await page.getBlob().text());
    assert.equal(report.webrtc.connections[0].endedReason, 'failed');
    assert.equal(report.webrtc.connections[0].statsErrorCount, 0);
    assert.equal(report.webrtc.connections[0].lastSampleStatus, 'pending');
});

test('caps retained RTC connections and releases live references on pagehide', async () => {
    const FakeRTC = fakeRTCClass();
    const page = createPage(sidecar, null, FakeRTC);
    const peers = [];
    for (let index = 0; index < 8; index++) peers.push(new page.window.RTCPeerConnection({}));
    new page.window.RTCPeerConnection({});
    assert.equal(page.intervalCount, 1);
    assert.deepEqual(peers[0].listeners.get('connectionstatechange').length, 1);
    peers[0].setStates('closed', 'closed');
    assert.equal(peers[0].listeners.get('connectionstatechange').length, 0,
        'closed peers detach diagnostic listeners');
    new page.window.RTCPeerConnection({});
    const pagehide = page.windowHandlers.get('pagehide')[0];
    pagehide();
    assert.equal(page.intervalCount, 0);

    await page.elements.get('download').dispatch('click');
    const report = JSON.parse(await page.getBlob().text());
    assert.equal(report.webrtc.connections.length, 8);
    assert.equal(report.webrtc.droppedConnections, 2, 'both rejected and evicted summaries are counted');
    assert.ok(report.webrtc.connections.every(connection => connection.localId !== 1));
    assert.ok(report.webrtc.connections.every(connection => connection.endedReason === 'pagehide'));
});

test('does not attach listeners or start sampling when a peer is already closed at construction', () => {
    const FakeRTC = fakeRTCClass();
    FakeRTC.initialConnectionState = 'closed';
    FakeRTC.initialIceConnectionState = 'closed';
    const page = createPage(sidecar, null, FakeRTC);
    const peer = new page.window.RTCPeerConnection({});

    assert.equal(peer.listeners.size, 0);
    assert.equal(page.intervalCount, 0);
});
