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
    const script = await readFile(new URL('../../godot/web/crash_archive.js', import.meta.url));
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
        return {first: rolled.events[0].seq, last: rolled.events.at(-1).seq, count: rolled.events.length,
            overwritten: rolled.archive.overwrittenBatches, runs: retainedRunCount,
            evicted: (await archive.detail('active')).status, dropped: burst.archive.discardedEvents,
            accounted: burst.events.length + burst.archive.discardedEvents,
            mergedAt: merged.updatedAt, committedAt: rolled.committedAt, checkpoint: merged.checkpoints[0].fightTick,
            drained: durable.events.map(e => e.seq), through: durable.archive.committedThroughEvent,
            startupBatches: startup.archive.committedBatches, survivedRestarts: (await archive.detail('battle')).events.length};
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
            res.setHeader('Content-Type', req.url === '/archive.js' ? 'text/javascript' : 'text/html');
            res.end(req.url === '/archive.js' ? script : page);
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
