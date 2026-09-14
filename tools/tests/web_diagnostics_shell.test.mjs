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
        focus() {},
        remove() {},
        click() { this.clicked = true; },
        getBoundingClientRect() { return { width: 900, height: 600 }; },
    };
}

function createPage(buildSidecar, fetchImpl = null) {
    let now = 0;
    const elements = new Map();
    for (const id of ['player', 'canvas', 'fullscreen', 'feedback', 'edge-indicator', 'toolbar',
        'audio-control', 'audio-toggle', 'mute-toggle', 'volume-panel', 'volume-slider',
        'volume-value', 'volume-status', 'viewport', 'status', 'status-splash', 'status-progress', 'download']) {
        elements.set(id, createElement(id));
    }
    const player = elements.get('player');
    const viewport = elements.get('viewport');
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
    });
    vm.runInContext(shellScript, context, { timeout: 1000 });
    return { context, window, elements, player, document, documentHandlers, windowHandlers, getBlob: () => capturedBlob };
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
