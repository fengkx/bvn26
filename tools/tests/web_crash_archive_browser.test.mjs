import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

// Set CHROME_BIN to exercise real IndexedDB transactions in a disposable browser.
test('keeps ordered bounded batches across runs and reports overwritten or dropped evidence', {
    skip: !process.env.CHROME_BIN, timeout: 45_000,
}, async () => {
    const script = (await readFile(new URL('../../godot/web/crash_archive.js', import.meta.url), 'utf8'))
        .replace('/* BVN_DIAGNOSTIC_NAMES */ {}', JSON.stringify({'res://generated/helpers/jinye': '山中井野'}));
    const historyPage = await readFile(new URL('../../godot/web/diagnostics.html', import.meta.url));
    async function exercise() {
        const archive = window.bvnCrashArchive;
        const recorder = id => archive.createRecorder(() => ({runId: id, updatedAt: new Date().toISOString()}));
        const active = recorder('active');
        for (let seq = 1; seq <= 65; seq++) {
            const encoded = JSON.stringify({type: 'action_transition', seq});
            active.append(encoded, encoded.length);
            await active.flush();
        }
        const rolled = await archive.detail('active');
        const journalKey = 'bvn26.crash-run.active';
        localStorage.setItem(journalKey, JSON.stringify({runId: 'active', updatedAt: '2000-01-01',
            checkpoints: [{fightTick: 42}]}));
        const merged = (await archive.listRuns()).find(run => run.runId === 'active');
        localStorage.removeItem(journalKey);
        for (let i = 0; i < 9; i++) {
            const next = recorder('later-' + i);
            next.append('{"type":"runtime_ready"}', 24);
            await next.flush();
        }
        const newest = recorder('burst');
        for (let i = 0; i < 2000; i++) newest.append('{"type":"burst"}', 16);
        // The first capacity-triggered transaction may still be in flight.
        await new Promise(resolve => setTimeout(resolve, 100));
        await newest.flush();
        const burst = await archive.detail('burst');
        const retainedRunCount = (await archive.listRuns()).length;
        const battle = archive.createRecorder(() => ({runId: 'battle', updatedAt: new Date().toISOString(),
            lastCheckpoint: {players: [{slot: 'p1'}], fightTick: 42}}));
        battle.append('{"seq":1}', 9);
        const firstWrite = battle.flush();
        battle.append('{"seq":2}', 9);
        battle.flush();
        await firstWrite;
        // The visibility flush was requested while the first transaction was open.
        let durable;
        for (let i = 0; i < 100; i++) {
            durable = await archive.detail('battle');
            if (durable.events.length === 2) break;
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        for (let i = 0; i < 9; i++) {
            const boot = recorder('restart-' + i);
            boot.markJournalDirty();
            for (let j = 0; boot.status.state === 'pending' && j < 100; j++) {
                await new Promise(resolve => setTimeout(resolve, 10));
            }
        }
        const startup = (await archive.listRuns()).find(r => r.runId === 'restart-8');
        const metrics = {first: rolled.events[0].seq, last: rolled.events.at(-1).seq, count: rolled.events.length,
            overwritten: rolled.archive.overwrittenBatches, runs: retainedRunCount,
            evicted: (await archive.detail('active')).status, dropped: burst.archive.discardedEvents,
            accounted: burst.events.length + burst.archive.discardedEvents,
            mergedAt: merged.updatedAt, committedAt: rolled.committedAt, checkpoint: merged.checkpoints[0].fightTick,
            drained: durable.events.map(e => e.seq), through: durable.archive.committedThroughEvent,
            startupBatches: startup.archive.committedBatches, survivedRestarts: (await archive.detail('battle')).events.length};

        const game = document.createElement('iframe');
        const opened = new Promise(resolve => game.addEventListener('load', resolve, {once: true}));
        game.src = '/diagnostics.html';
        document.body.appendChild(game);
        await opened;
        const current = game.contentWindow.bvnCrashArchive.createRecorder(() => ({runId: 'live', updatedAt: new Date().toISOString()}), 'live');
        current.append('{"seq":1}', 9);
        await current.flush();
        localStorage.setItem('bvn26.crash-run.battle', JSON.stringify({runId: 'battle', matchHistory: [
            {type:'match_started', at:'2026-11-26T05:00:00Z', matchId:'first', mode:'training',
                players:[{slot:'p1',fighter:'鸣人'}, {slot:'p2',fighter:'一护'}]},
            {type:'match_ended', matchId:'first'},
        ], checkpoints:[{at:'2026-11-26T05:05:00Z', matchId:'second', mode:1, arcadeStageIndex:4, map:'楼顶',
            players:[{slot:'p2',fighter:'卡卡西'}, {slot:'p1', fighter:'日番谷', helper:{id:'松本',resourcePath:'res://generated/helpers/jinye'}}]},
            {at:'2026-11-26T05:06:00Z',scene:'MENU'}]}));
        localStorage.setItem('bvn26.crash-tail.battle', JSON.stringify({runId: 'battle'}));
        localStorage.setItem('bvn26.crash-run.legacy', JSON.stringify({runId: 'legacy'}));
        localStorage.setItem('bvn26.audio', 'keep');
        const frame = document.createElement('iframe');
        frame.width = 320;
        frame.src = '/diagnostics.html';
        document.body.appendChild(frame);
        async function ready(predicate) {
            for (let i = 0; i < 200; i++) {
                if (predicate()) return;
                await new Promise(resolve => setTimeout(resolve, 10));
            }
            throw new Error('History page did not reach ' + predicate + ': ' + control('status')?.textContent);
        }
        const control = id => frame.contentDocument?.getElementById(id);
        const battleCard = () => control('runs')?.querySelector('[data-run-id="battle"]');
        await ready(() => battleCard()?.querySelector('.remove'));
        const card = battleCard();
        metrics.title = card.querySelector('h2').textContent;
        metrics.mode = card.querySelector('.mode').textContent;
        const doc = frame.contentDocument;
        metrics.mobileFits = doc.documentElement.scrollWidth <= doc.documentElement.clientWidth;
        metrics.modes = ['single', 'vs_com', 'versus', 'training', 'versus'].map((mode, i) => archive.describeRun({
            matchHistory: [{type: 'match_started', matchId: 'one', mode, online: i === 4}],
            checkpoints: [{matchId: 'one', mode: i === 4 ? 3 : i + 1, players: {p1:{fighter:'鸣人'}}}],
        })[0].mode);
        metrics.meta = card.querySelector('.meta').textContent;
        card.querySelector('summary').click();
        metrics.earlier = card.querySelector('details[open] p').textContent;
        const view = frame.contentWindow;
        view.HTMLAnchorElement.prototype.click = function () { metrics.filename = this.download; };
        card.querySelector('.download').click();
        await ready(() => metrics.filename && !card.querySelector('.remove').disabled);
        frame.contentWindow.confirm = () => false;
        card.querySelector('.remove').click();
        metrics.cancelled = (await archive.detail('battle')).events.length;
        frame.contentWindow.confirm = () => true;
        card.querySelector('.remove').click();
        await ready(() => !control('clear').disabled && !battleCard());
        metrics.deleted = [(await archive.detail('battle')).events.length,
            localStorage.getItem('bvn26.crash-run.battle'), localStorage.getItem('bvn26.crash-tail.battle')];
        control('clear').click();
        await ready(() => !control('clear').disabled && control('runs').children.length === 1);
        const loaded = new Promise(resolve => frame.addEventListener('load', resolve, {once: true}));
        frame.contentWindow.location.reload();
        await loaded;
        await ready(() => !control('clear').disabled);
        metrics.remaining = Array.from(control('runs').children, row => row.dataset.runId);
        game.remove();
        await navigator.locks.request('bvn26.crash-run.live', () => {});
        frame.contentWindow.confirm = () => true;
        control('clear').click();
        await ready(() => control('status').textContent.includes('还没有保存'));
        metrics.empty = control('runs').children.length === 0 && control('clear').disabled;
        metrics.audio = localStorage.getItem('bvn26.audio');
        return metrics;
    }
    let settle;
    const finished = new Promise((resolve, reject) => { settle = {resolve, reject}; });
    const page = '<script src="/archive.js"></script><script>(' + exercise.toString() +
        ')().then(value => ({value}), error => ({error: String(error)})).then(result => fetch("/result", ' +
        '{method:"POST",body:JSON.stringify(result)}));</script>';
    const server = createServer(async (req, res) => {
        if (req.url === '/result') {
            let body = '';
            for await (const chunk of req) body += chunk;
            const result = JSON.parse(body);
            res.end('ok');
            if (result.error) settle.reject(new Error(result.error));
            else settle.resolve(result.value);
        } else {
            const js = ['/archive.js', '/crash_archive.js'].includes(req.url);
            res.setHeader('Content-Type', js ? 'text/javascript; charset=utf-8' : 'text/html; charset=utf-8');
            res.end(js ? script : req.url === '/diagnostics.html' ? historyPage : page);
        }
    });
    const profile = await mkdtemp(join(tmpdir(), 'bvn-archive-test-'));
    let chrome, timer;
    try {
        await new Promise((resolve, reject) => {
            server.once('error', reject);
            server.listen(0, '127.0.0.1', resolve);
        });
        chrome = spawn(process.env.CHROME_BIN, ['--headless', '--no-first-run', '--disable-background-networking',
            '--no-default-browser-check', '--user-data-dir=' + profile, 'http://127.0.0.1:' + server.address().port], {stdio: 'ignore'});
        chrome.once('error', settle.reject);
        chrome.once('exit', (code, signal) => settle.reject(new Error('Browser exited: ' + (signal || code))));
        timer = setTimeout(() => settle.reject(new Error('Archive test timed out')), 35_000);
        const result = await finished;
        assert.deepEqual([result.first, result.last, result.count, result.overwritten], [6, 65, 60, 5]);
        assert.equal(result.runs, 8);
        assert.equal(result.evicted, 'no_committed_batch');
        assert.ok(result.dropped > 0);
        assert.equal(result.accounted, 2000);
        assert.equal(result.mergedAt, result.committedAt);
        assert.equal(result.checkpoint, 42);
        assert.deepEqual(result.drained, [1, 2]);
        assert.equal(result.through, 2);
        assert.equal(result.startupBatches, 0);
        assert.equal(result.survivedRestarts, 2);
        assert.equal(result.title, '日番谷 对阵 卡卡西');
        assert.equal(result.mode, '闯关模式');
        assert.equal(result.mobileFits, true);
        assert.deepEqual(result.modes, ['闯关模式', '人机对战', '双人对战', '训练模式', '联机对战']);
        assert.match(result.meta, /第 5 关.*楼顶.*山中井野/);
        assert.match(result.earlier, /训练模式.*鸣人 对阵 一护/);
        assert.match(result.filename, /^bvn26-log-闯关模式-日番谷 对阵 卡卡西-.*\.json$/);
        assert.equal(result.cancelled, 2);
        assert.deepEqual(result.deleted, [0, null, null]);
        assert.deepEqual(result.remaining, ['live']);
        assert.equal(result.empty, true);
        assert.equal(result.audio, 'keep');
    } finally {
        clearTimeout(timer);
        if (chrome?.pid && chrome.exitCode === null && chrome.signalCode === null) {
            const closed = new Promise(resolve => chrome.once('exit', resolve));
            chrome.kill();
            await closed;
        }
        server.closeAllConnections();
        server.close();
        await rm(profile, {recursive: true, force: true, maxRetries: 3, retryDelay: 100});
    }
});
