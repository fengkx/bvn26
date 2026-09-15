#!/usr/bin/env node

// Exercise the production shell's JSON export path with a native Main capture.
// This is deliberately not a browser-capture or DOM-behavior test.

import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import vm from 'node:vm';

const [runtimePath, sidecarPath, outputPath] = process.argv.slice(2);
if (!runtimePath || !sidecarPath || !outputPath) {
    throw new Error('Usage: node export_diagnostics_shell_vm.mjs <native-v2.json> <build-metadata.json> <output-v2.json>');
}

const runtimeReport = JSON.parse(await readFile(runtimePath, 'utf8'));
const sidecar = JSON.parse(await readFile(sidecarPath, 'utf8'));
assert.equal(runtimeReport.schemaVersion, 2, 'input must be a real structured runtime capture');
assert.ok(Array.isArray(runtimeReport.runtime?.events), 'input has no runtime event array');
assert.equal(runtimeReport.buildID, sidecar.buildID, 'native runtime build must match exported sidecar');

const html = await readFile(new URL('../../godot/web/shell.html', import.meta.url), 'utf8');
const shellScript = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/)?.[1];
assert.ok(shellScript, 'production shell script was not found');

function element(id = '') {
    const handlers = new Map();
    const attributes = new Map();
    const classes = new Set();
    const children = [];
    return {
        id, handlers, attributes, children, dataset: {}, style: {}, hidden: false, disabled: false,
        value: '', width: 0, height: 0, textContent: '', href: '', download: '',
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
        appendChild(child) { children.push(child); this.lastChild = child; },
        removeChild(child) { const index = children.indexOf(child); if (index >= 0) children.splice(index, 1); },
        contains(target) { return target === this; },
        matches() { return false; },
        focus() {}, remove() {}, click() { this.clicked = true; },
        getBoundingClientRect() { return { width: 900, height: 600 }; },
    };
}

const elements = new Map();
for (const id of ['player', 'canvas', 'fullscreen', 'feedback', 'edge-indicator', 'toolbar',
    'audio-control', 'audio-toggle', 'mute-toggle', 'volume-panel', 'volume-slider',
    'volume-value', 'volume-status', 'viewport', 'status', 'status-splash', 'status-progress', 'download']) {
    elements.set(id, element(id));
}
let now = 0;
let savedBlob = null;
const documentHandlers = new Map();
const windowHandlers = new Map();
const document = {
    baseURI: 'http://127.0.0.1:8766/', fullscreenEnabled: false, fullscreenElement: null,
    visibilityState: 'visible', activeElement: null,
    getElementById: id => elements.get(id) || element(id),
    addEventListener(name, callback) {
        if (!documentHandlers.has(name)) documentHandlers.set(name, []);
        documentHandlers.get(name).push(callback);
    },
    createElement: tag => element(tag), createTextNode: text => ({ textContent: String(text) }),
    body: { appendChild() {} },
};
const window = {
    devicePixelRatio: 2, innerWidth: 1280, innerHeight: 720,
    addEventListener(name, callback) {
        if (!windowHandlers.has(name)) windowHandlers.set(name, []);
        windowHandlers.get(name).push(callback);
    },
};
const urlApi = Object.assign(class extends URL {}, {
    createObjectURL(blob) { savedBlob = blob; return 'blob:diagnostics-vm'; },
    revokeObjectURL() {},
});
const context = vm.createContext({
    window, document,
    navigator: { userAgent: 'native-runtime-shell-vm', language: 'zh-CN', serviceWorker: undefined },
    location: { origin: 'http://127.0.0.1:8766', pathname: '/' },
    performance: { now: () => now },
    innerWidth: 1280, innerHeight: 720, devicePixelRatio: 2,
    localStorage: { getItem: () => null, setItem() {} },
    console: { log() {}, info() {}, warn() {}, error() {} },
    URL: urlApi, Blob, TextEncoder, AbortController,
    ResizeObserver: class { observe() {} },
    fetch: async () => ({ ok: true, json: async () => sidecar }),
    setTimeout, clearTimeout, Date, Math,
    crypto: { randomUUID: () => 'native-shell-vm-session' }, Promise,
});
vm.runInContext(shellScript, context, { timeout: 1000 });
await new Promise(resolve => setImmediate(resolve));

const startEvent = runtimeReport.runtime.events.find(event => event.type === 'match_started');
assert.ok(startEvent, 'native capture has no match_started event');
const resourceVersion = startEvent.payload.match.resourceVersion;
const snapshotMatch = runtimeReport.runtime.snapshot?.match;
assert.ok(snapshotMatch, 'native capture has no match snapshot');
assert.equal(resourceVersion, sidecar.resourceVersion, 'native resources must match exported sidecar');

window.bvnDiagnosticsRegister((command, requestId) => {
    if (command === 'visibility') return;
    assert.equal(command, 'snapshot');
    window.bvnDiagnosticsSetSnapshot(JSON.stringify({
        requestId,
        buildID: runtimeReport.buildID,
        resourceVersion,
        match: snapshotMatch,
    }));
});
for (const event of runtimeReport.runtime.events) {
    now = Math.max(now, Number(event.monoMs) || 0);
    assert.equal(window.bvnDiagnosticsPush(JSON.stringify(event)), true, `shell rejected runtime event ${event.seq}`);
}
for (const entry of runtimeReport.entries || []) window.bvnLog(entry.level || 'log', entry.message || '');
await elements.get('download').dispatch('click');
assert.ok(savedBlob, 'production shell did not create its exported JSON blob');
const exported = JSON.parse(await savedBlob.text());
assert.equal(exported.schemaVersion, 2);
assert.equal(exported.build.status, 'match');
assert.equal(exported.build.buildID, sidecar.buildID);
assert.equal(exported.build.pckSha256, sidecar.pckSha256);
assert.equal(exported.runtime.snapshotStatus, 'acknowledged');
assert.equal(exported.runtime.events.length, runtimeReport.runtime.events.length);
assert.equal(exported.runtime.inputTape.length, runtimeReport.runtime.inputTape.length);
assert.equal(exported.runtime.snapshot.match.fightTick, snapshotMatch.fightTick);
await writeFile(outputPath, JSON.stringify(exported, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({
    mode: 'production-shell-vm-bridge; not browser capture',
    buildID: exported.build.buildID,
    pckSha256: exported.build.pckSha256,
    runtimeEvents: exported.runtime.events.length,
    inputTape: exported.runtime.inputTape.length,
    snapshotStatus: exported.runtime.snapshotStatus,
    output: outputPath,
}));
