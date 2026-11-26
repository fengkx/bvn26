// The Web build embeds the same actor names used on the selection screen.
window.bvnCrashArchive = (() => {
    const names = /* BVN_DIAGNOSTIC_NAMES */ {};
    const journalPrefix = 'bvn26.crash-run.';
    const batchLimit = 96 * 1024;
    const batchSlots = 60;
    const runLimit = 8;
    let connection;

    function database() {
        if (!connection) connection = new Promise((resolve, reject) => {
            const request = indexedDB.open('bvn26-crash-archive', 1);
            let expired = false;
            const timeout = setTimeout(() => {
                expired = true;
                reject(new Error('Archive open timed out'));
            }, 2000);
            request.onupgradeneeded = () => {
                const db = request.result;
                db.createObjectStore('runs', { keyPath: 'runId' }).createIndex('updated', 'updatedAt');
                db.createObjectStore('chunks', { keyPath: ['runId', 'slot'] });
            };
            request.onsuccess = () => {
                clearTimeout(timeout);
                const db = request.result;
                if (expired) { db.close(); return; }
                db.onversionchange = () => { db.close(); connection = null; };
                resolve(db);
            };
            request.onerror = () => { clearTimeout(timeout); reject(request.error); };
        });
        return connection.catch(error => {
            connection = null;
            throw error;
        });
    }

    const range = id => IDBKeyRange.bound([id, 0], [id, batchSlots - 1]);

    function createRecorder(metadata) {
        let pending = [], size = 0, discarded = 0, sequence = 0, busy = false;
        const status = { state: 'pending', committedBatches: 0, discardedEvents: 0,
            overwrittenBatches: 0, intervalMs: 1000, batchSlots, batchByteLimit: batchLimit };
        let lastFailure = -Infinity, lastFlush = -Infinity;
        function append(encoded, bytes) {
            if (size + bytes > batchLimit || pending.length >= 768) {
                // Retain the most recent activity even when storage cannot keep up.
                discarded += pending.length;
                pending = [];
                size = 0;
            }
            pending.push(encoded);
            size += bytes;
            if ((size >= batchLimit * .7 || pending.length >= 512) && performance.now() - lastFlush >= 250) flush();
        }
        async function flush() {
            if (busy || !pending.length || performance.now() - lastFailure < 10000) return;
            busy = true;
            lastFlush = performance.now();
            const writing = pending;
            pending = [];
            size = 0;
            try {
                const db = await database();
                const run = metadata();
                const tx = db.transaction(['runs', 'chunks'], 'readwrite');
                const runs = tx.objectStore('runs'), chunks = tx.objectStore('chunks');
                const done = new Promise((resolve, reject) => {
                    tx.oncomplete = resolve;
                    tx.onabort = () => reject(tx.error || new Error('Archive transaction aborted'));
                });
                const serial = sequence + 1;
                const batch = { runId: run.runId, slot: sequence % batchSlots, serial,
                    events: writing, discardedBefore: discarded };
                chunks.put(batch);
                runs.put({ ...run, archive: { ...status, state: 'available', committedBatches: serial,
                    discardedEvents: discarded, overwrittenBatches: Math.max(0, serial - batchSlots) } });
                const count = runs.count();
                count.onsuccess = () => {
                    let excess = count.result - runLimit;
                    if (excess <= 0) return;
                    const oldest = runs.index('updated').openKeyCursor();
                    oldest.onsuccess = () => {
                        const cursor = oldest.result;
                        if (!cursor || excess <= 0) return;
                        if (cursor.primaryKey !== run.runId) {
                            chunks.delete(range(cursor.primaryKey));
                            runs.delete(cursor.primaryKey);
                            excess--;
                        }
                        cursor.continue();
                    };
                };
                await done;
                sequence = serial;
                Object.assign(status, {state: 'available', committedBatches: serial,
                    overwrittenBatches: Math.max(0, serial - batchSlots)});
            } catch (error) {
                discarded += writing.length;
                status.state = 'unavailable';
                status.error = error?.name || 'StorageError';
                lastFailure = performance.now();
            } finally {
                status.discardedEvents = discarded;
                busy = false;
            }
        }
        setInterval(flush, status.intervalMs);
        return { append, flush, status };
    }

    function requestResult(request) {
        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    function mergeTail(run) {
        if (!run) return run;
        try {
            const tail = JSON.parse(localStorage.getItem('bvn26.crash-tail.' + run.runId));
            const last = run.checkpoints?.at(-1)?.recordSeq || 0;
            if (tail?.runId !== run.runId || !(tail.checkpoints?.at(-1)?.recordSeq > last)) return run;
            return {...run, ...tail, checkpoints: [...(run.checkpoints || []),
                ...tail.checkpoints.filter(c => c.recordSeq > last)].slice(-12)};
        } catch (_) { return run; }
    }

    async function listRuns() {
        const byId = new Map();
        let readable = false;
        try {
            const db = await database();
            for (const run of await requestResult(db.transaction('runs').objectStore('runs').getAll())) {
                byId.set(run.runId, run);
            }
            readable = true;
        } catch (_) { /* Earlier players stored only the journal. */ }
        try {
            for (const key of Object.keys(localStorage).filter(key => key.startsWith(journalPrefix))) {
                let run;
                try { run = mergeTail(JSON.parse(localStorage.getItem(key))); } catch (_) { continue; }
                if (run?.runId !== key.slice(journalPrefix.length)) continue;
                const archived = byId.get(run.runId);
                byId.set(run.runId, {...archived, ...run,
                    archive: archived?.archive || run.archive, updatedAt: [archived?.updatedAt, run.updatedAt].filter(Boolean).sort().at(-1)});
            }
            readable = true;
        } catch (_) { /* The asynchronous archive may still be readable. */ }
        if (!readable) throw new Error('Browser storage unavailable');
        return [...byId.values()].sort((a,b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
    }
    async function detail(runId) {
        try {
            const db = await database();
            const tx = db.transaction(['runs', 'chunks']);
            const [run, chunks] = await Promise.all([requestResult(tx.objectStore('runs').get(runId)),
                requestResult(tx.objectStore('chunks').getAll(range(runId)))]);
            const events = [];
            for (const chunk of chunks.sort((a,b) => a.serial - b.serial)) {
                for (const encoded of chunk.events) events.push(JSON.parse(encoded));
            }
            return { status: run ? 'saved' : 'no_committed_batch', events, archive: run?.archive };
        } catch (error) {
            return { status: 'unavailable', error: error?.name, events: [] };
        }
    }

    // Normalize older snapshots on export, keeping source IDs for replay tools.
    function nameFields(key, value) {
        if (key === 'message' && typeof value === 'string' && value.startsWith('COMBAT_EVENT ')) {
            try {
                const event = JSON.parse(value.slice(13));
                if (typeof event.event === 'string' && event.event.startsWith('summon_') && event.event !== 'summon_requested') {
                    event.sourceCommandHelperId = event.event.slice(7);
                    event.event = 'summon_requested';
                } else if (typeof event.event === 'string' && event.event.startsWith('helper_activate_')) {
                    event.event = 'helper_activate';
                }
                return 'COMBAT_EVENT ' + JSON.stringify(nameFields('', event));
            } catch (_) { return value; }
        }
        if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
        const path = value.resourcePath;
        const helper = typeof value.helper === 'string' ? value.helper : key === 'helper' ? value.id : null;
        const source = value.sourceId || helper || (typeof value.fighter === 'string' ? value.fighter : null);
        if (!source) return value;
        const known = value.displayName || names[path] || names[(helper ? 'helper:' : 'fighter:') + source];
        if (!known) return value;
        const identity = {displayName: known, sourceId: value.sourceId || source};
        if (typeof value.helper === 'string') return {...value, helper: known, ...identity};
        if (key === 'helper') return {...value, id: path?.split('/').at(-1) || value.id, ...identity};
        return {...value, fighter: known, ...identity};
    }

    function download(report) {
        const blob = new Blob([JSON.stringify(report, nameFields)], {type: 'application/json'});
        const url = URL.createObjectURL(blob), link = document.createElement('a');
        link.href = url;
        link.download = 'bvn26-log-' + report.exportedAt.replace(/[:.]/g, '-') + '.json';
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 10000);
    }

    async function recoveredReport(run) {
        const saved = await detail(run.runId);
        const events = saved.events;
        const checkpoint = run.checkpoints?.at(-1);
        const last = run.lastCheckpoint && (!checkpoint || run.lastCheckpoint.at > checkpoint.at)
            ? run.lastCheckpoint : checkpoint;
        const snapshot = run.snapshot || null;
        return {schemaVersion: 2, reportKind: 'saved_run', runId: run.runId, startedAt: run.startedAt,
            exportedAt: new Date().toISOString(), userAgent: run.userAgent, build: run.build || {buildID: run.buildID},
            entries: run.consoleTail || [], runtime: {snapshotStatus: snapshot ? 'persisted' : 'unavailable', snapshot,
                events, inputTape: events.filter(e => e.type === 'input_consumed'),
                criticalEvents: events.filter(e => e.type === 'diagnostic_exception' || e.type === 'pause_state')},
            reloadDiagnostics: {currentRun: run, previousRuns: [], persistedDetail: {...saved, events: undefined},
                lastCheckpoint: last || null, cause: 'unconfirmed'}};
    }
    return {createRecorder, mergeTail, listRuns, detail, download, recoveredReport, nameFields};
})();
