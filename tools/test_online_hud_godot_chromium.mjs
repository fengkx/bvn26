#!/usr/bin/env node

import { writeFile } from 'node:fs/promises';

const endpoint = 'http://127.0.0.1:9234';
const pageUrl = 'http://127.0.0.1:8017/';
const browserInfo = await (await fetch(`${endpoint}/json/version`)).json();
const browser = await connect(browserInfo.webSocketDebuggerUrl);
const target = await browser.call('Target.createTarget', { url: 'about:blank' });
const targets = await (await fetch(`${endpoint}/json/list`)).json();
const tab = await connect(targets.find((item) => item.id === target.targetId).webSocketDebuggerUrl);

try {
    await tab.call('Page.enable');
    await tab.call('Runtime.enable');
    await tab.call('Emulation.setFocusEmulationEnabled', { enabled: true });
    await tab.call('Page.setWebLifecycleState', { state: 'active' });
    await tab.call('Emulation.setDeviceMetricsOverride', {
        width: 1280, height: 960, deviceScaleFactor: 1, mobile: false,
    });
    await tab.call('Page.navigate', { url: pageUrl });
    const harness = await waitForValue(tab, 'window.__onlineHudGodotSmoke', 60_000);
    assert(harness.phase === 'ready' && harness.registered && harness.active,
        `Godot HUD bridge did not start: ${JSON.stringify(harness)}`);
    assert(!harness.fallbackHudVisible, 'Godot fallback HUD should be hidden when the shell bridge is active');

    const windowMetrics = JSON.parse(await evaluate(tab, `JSON.stringify((() => {
        const controls = document.querySelector('#online-controls');
        const toolbar = document.querySelector('#toolbar');
        const canvas = document.querySelector('#canvas');
        const a = controls.getBoundingClientRect(), b = canvas.getBoundingClientRect();
        const overlap = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left))
            * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
        return { visible: !controls.hidden, toolbarOwnsControls: toolbar.contains(controls), overlap,
            controlsBottom: a.bottom, canvasTop: b.top, controlsHeight: a.height };
    })())`));
    assert(windowMetrics.visible && windowMetrics.toolbarOwnsControls && windowMetrics.overlap === 0
        && windowMetrics.controlsBottom <= windowMetrics.canvasTop + 1,
        `Window HUD overlaps the game canvas: ${JSON.stringify(windowMetrics)}`);
    await screenshot(tab, '/private/tmp/online-hud-godot-window.png');

    await click(tab, '#online-pause');
    const paused = await waitForValue(tab, 'window.__onlineHudGodotSmoke', 5_000,
        (value) => value.pauseRequests === 1);
    assert(paused.pauseRequests === 1, 'Shell pause button did not reach the fake Godot coordinator');

    await click(tab, '#fullscreen');
    await waitFor(tab, 'document.fullscreenElement?.id === "player"', 'Fullscreen was not entered');
    await tab.call('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 640, y: 480 });
    await waitFor(tab, "getComputedStyle(document.querySelector('#toolbar')).opacity === '0'",
        'Fullscreen toolbar did not tuck after pointer left it');
    const fullscreen = JSON.parse(await evaluate(tab, `JSON.stringify({
        toolbarOpacity: getComputedStyle(document.querySelector('#toolbar')).opacity,
        edgeVisible: getComputedStyle(document.querySelector('#edge-indicator')).display !== 'none',
        controlsVisible: !document.querySelector('#online-controls').hidden,
        canvasRatio: (() => { const r = document.querySelector('#canvas').getBoundingClientRect(); return r.width / r.height; })(),
    })`));
    assert(fullscreen.toolbarOpacity === '0' && fullscreen.edgeVisible && fullscreen.controlsVisible,
        `Fullscreen toolbar did not tuck while retaining its online controls: ${JSON.stringify(fullscreen)}`);
    await screenshot(tab, '/private/tmp/online-hud-godot-fullscreen.png');

    await tab.call('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 1210, y: 5 });
    await waitFor(tab, "getComputedStyle(document.querySelector('#toolbar')).opacity === '1'",
        'Fullscreen edge did not reveal the toolbar for exit');
    await click(tab, '#fullscreen');
    await waitFor(tab, '!document.fullscreenElement', 'Could not leave fullscreen for the narrow viewport check');
    await tab.call('Emulation.setDeviceMetricsOverride', {
        width: 390, height: 844, deviceScaleFactor: 1, mobile: false,
    });
    await waitFor(tab, 'innerWidth === 390', 'Narrow viewport emulation did not apply');
    await evaluate(tab, 'new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    const narrowMetrics = JSON.parse(await evaluate(tab, `JSON.stringify((() => {
        const controls = document.querySelector('#online-controls').getBoundingClientRect();
        const buttons = [...document.querySelectorAll('#online-controls button')]
            .filter(button => !button.hidden).map(button => button.getBoundingClientRect().right);
        return { viewport: innerWidth, documentWidth: document.documentElement.scrollWidth,
            bodyWidth: document.body.scrollWidth, controlsRight: controls.right,
            lastButtonRight: Math.max(...buttons), overflowers: [...document.querySelectorAll('body *')]
                .map(node => { const rect = node.getBoundingClientRect(); return { tag: node.tagName,
                    id: node.id, className: typeof node.className === 'string' ? node.className : '',
                    left: Math.round(rect.left), right: Math.round(rect.right), width: Math.round(rect.width),
                    scrollWidth: node.scrollWidth, clientWidth: node.clientWidth,
                    text: (node.innerText || '').slice(0, 36) }; })
                .filter(node => node.right > innerWidth + 1 || node.left < -1).slice(0, 8) };
    })())`));
    await screenshot(tab, '/private/tmp/online-hud-godot-narrow.png');
    assert(narrowMetrics.documentWidth <= 390 && narrowMetrics.bodyWidth <= 390
        && narrowMetrics.controlsRight <= 391 && narrowMetrics.lastButtonRight <= 391,
        `Narrow viewport has horizontal overflow: ${JSON.stringify(narrowMetrics)}`);

    console.log(JSON.stringify({
        marker: 'ONLINE_HUD_GODOT_CHROMIUM_OK', chrome: browserInfo.Browser, page: pageUrl,
        harness, windowMetrics, pauseCallback: paused.pauseRequests, fullscreen, narrowMetrics,
        screenshots: ['/private/tmp/online-hud-godot-window.png', '/private/tmp/online-hud-godot-fullscreen.png', '/private/tmp/online-hud-godot-narrow.png'],
        scope: 'production OnlineLobby + JavaScriptBridge + Web shell; fake coordinator; no service or gameplay network',
    }));
} finally {
    try { await tab.close(); } catch {}
    try { await browser.call('Target.closeTarget', { targetId: target.targetId }); } catch {}
    browser.close();
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

async function evaluate(tab, expression) {
    const result = await tab.call('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || 'Browser evaluation failed');
    return result.result?.value;
}

async function waitForValue(tab, expression, timeoutMs, predicate = () => true) {
    const deadline = Date.now() + timeoutMs;
    let last;
    while (Date.now() < deadline) {
        const raw = await evaluate(tab, `JSON.stringify(${expression} ?? null)`);
        last = raw ? JSON.parse(raw) : null;
        if (last && predicate(last)) return last;
        await delay(100);
    }
    throw new Error(`Timed out waiting for Godot HUD bridge: ${JSON.stringify(last)}`);
}

async function waitFor(tab, condition, message) {
    const deadline = Date.now() + 5_000;
    while (Date.now() < deadline) {
        if (await evaluate(tab, condition)) return;
        await delay(100);
    }
    throw new Error(message);
}

async function click(tab, selector) {
    const box = JSON.parse(await evaluate(tab, `JSON.stringify((() => {
        const node = document.querySelector(${JSON.stringify(selector)});
        if (!node || node.hidden || node.disabled) return null;
        const rect = node.getBoundingClientRect();
        return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
    })())`));
    assert(box, `Button unavailable: ${selector}`);
    await tab.call('Input.dispatchMouseEvent', { type: 'mouseMoved', x: box.x, y: box.y });
    await tab.call('Input.dispatchMouseEvent', { type: 'mousePressed', x: box.x, y: box.y, button: 'left', clickCount: 1 });
    await tab.call('Input.dispatchMouseEvent', { type: 'mouseReleased', x: box.x, y: box.y, button: 'left', clickCount: 1 });
    await delay(180);
}

async function screenshot(tab, path) {
    const result = await tab.call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    await writeFile(path, Buffer.from(result.data, 'base64'));
}

function assert(condition, message) {
    if (!condition) throw new Error(message);
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
