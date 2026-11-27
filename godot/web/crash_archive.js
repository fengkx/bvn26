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

    const runLock = id => journalPrefix + id;

    function createRecorder(metadata, runId, onInterval) {
        // A live game keeps its log until its document is closed. Crashes release Web Locks too.
        if (runId && navigator.locks) {
            navigator.locks.request(runLock(runId), () => new Promise(() => {})).catch(() => {});
        }
        let pending = [], size = 0, discarded = 0, sequence = 0, busy = false;
        let journalDirty = false, flushAfterWrite = false;
        const status = { state: 'pending', committedBatches: 0, discardedEvents: 0,
            observedEvents: 0, committedThroughEvent: 0, overwrittenBatches: 0,
            intervalMs: 1000, batchSlots, batchByteLimit: batchLimit };
        let lastFailure = -Infinity, lastFlush = -Infinity;
        function append(encoded, bytes) {
            status.observedEvents++;
            if (size + bytes > batchLimit || pending.length >= 768) {
                // Retain the most recent activity even when storage cannot keep up.
                discarded += pending.length;
                pending = [];
                size = 0;
            }
            pending.push(encoded);
            size += bytes;
            if (!busy && (size >= batchLimit * .7 || pending.length >= 512) && performance.now() - lastFlush >= 250) flush();
        }
        function markJournalDirty() {
            journalDirty = true;
            if (!busy && performance.now() - lastFlush >= status.intervalMs) flush();
        }
        async function flush() {
            if ((!pending.length && !journalDirty) || performance.now() - lastFailure < 10000) return;
            if (busy) { flushAfterWrite = true; return; }
            busy = true;
            journalDirty = false;
            lastFlush = performance.now();
            const writing = pending;
            const through = writing.length ? status.observedEvents : status.committedThroughEvent;
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
                const serial = writing.length ? sequence + 1 : sequence;
                if (writing.length) {
                    chunks.put({ runId: run.runId, slot: sequence % batchSlots, serial,
                        events: writing, discardedBefore: discarded });
                }
                runs.put({ ...run, archive: { ...status, state: 'available', committedBatches: serial,
                    committedThroughEvent: through, discardedEvents: discarded, overwrittenBatches: Math.max(0, serial - batchSlots) } });
                const count = runs.count();
                count.onsuccess = () => {
                    const excess = count.result - runLimit;
                    if (excess <= 0) return;
                    // A restart loop can create many startup-only headers after one lost fight.
                    const oldest = runs.index('updated').getAll();
                    oldest.onsuccess = () => {
                        const hasBattle = r => Boolean(r.matchHistory?.length || r.lastCheckpoint?.players?.length);
                        const candidates = oldest.result.filter(r => r.runId !== run.runId)
                            .sort((a,b) => Number(hasBattle(a)) - Number(hasBattle(b)));
                        for (const candidate of candidates.slice(0, excess)) {
                            chunks.delete(range(candidate.runId));
                            runs.delete(candidate.runId);
                        }
                    };
                };
                await done;
                sequence = serial;
                Object.assign(status, {state: 'available', committedBatches: serial,
                    committedThroughEvent: through, overwrittenBatches: Math.max(0, serial - batchSlots)});
                delete status.error;
            } catch (error) {
                discarded += writing.length;
                journalDirty = true;
                status.state = 'unavailable';
                status.error = error?.name || 'StorageError';
                lastFailure = performance.now();
            } finally {
                status.discardedEvents = discarded;
                busy = false;
                if (flushAfterWrite) { flushAfterWrite = false; flush(); }
            }
        }
        setInterval(() => { onInterval?.(); flush(); }, status.intervalMs);
        return { append, flush, markJournalDirty, status };
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
                const latest = archived && archived.updatedAt > run.updatedAt
                    ? {...run, ...archived} : {...archived, ...run};
                byId.set(run.runId, {...latest, archive: archived?.archive || run.archive});
            }
            readable = true;
        } catch (_) { /* The asynchronous archive may still be readable. */ }
        if (!readable) throw new Error('Browser storage unavailable');
        return [...byId.values()].sort((a,b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
    }
    async function removeRuns(ids) {
        const result = {removed: 0, active: 0, incomplete: 0};
        let db;
        try { db = await database(); } catch (_) { /* Local journals may still be accessible. */ }
        for (const id of new Set(ids)) {
            async function remove() {
                let complete = Boolean(db);
                if (db) {
                    const tx = db.transaction(['runs', 'chunks'], 'readwrite');
                    tx.objectStore('runs').delete(id);
                    tx.objectStore('chunks').delete(range(id));
                    await new Promise((resolve, reject) => {
                        tx.oncomplete = resolve;
                        tx.onabort = () => reject(tx.error || new Error('Archive deletion aborted'));
                    });
                }
                try {
                    localStorage.removeItem(journalPrefix + id);
                    localStorage.removeItem('bvn26.crash-tail.' + id);
                } catch (_) { complete = false; }
                if (complete) result.removed++;
                else result.incomplete++;
            }
            if (navigator.locks) {
                await navigator.locks.request(runLock(id), {ifAvailable: true}, lock => {
                    if (lock) return remove();
                    result.active++;
                });
            } else {
                await remove();
            }
        }
        return result;
    }

    async function detail(runId) {
        try {
            const db = await database();
            const tx = db.transaction(['runs', 'chunks']);
            let unreadableEvents = 0;
            const chunks = [];
            const cursor = tx.objectStore('chunks').openCursor(range(runId));
            const readChunks = new Promise((resolve, reject) => {
                cursor.onerror = () => reject(cursor.error);
                cursor.onsuccess = () => {
                    const row = cursor.result;
                    if (!row) { resolve(); return; }
                    const chunk = row.value;
                    const events = [];
                    for (const encoded of chunk.events) {
                        try { events.push(JSON.parse(encoded)); } catch (_) { unreadableEvents++; }
                    }
                    chunks.push({serial: chunk.serial, events});
                    row.continue();
                };
            });
            const [run] = await Promise.all([requestResult(tx.objectStore('runs').get(runId)), readChunks]);
            const events = chunks.sort((a,b) => a.serial - b.serial).flatMap(chunk => chunk.events);
            return {status: chunks.length ? 'saved' : 'no_committed_batch', events, archive: run?.archive,
                committedAt: run?.updatedAt, unreadableEvents};
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
        if (!helper && typeof value.fighter !== 'string') return value;
        const source = value.sourceId || helper || (typeof value.fighter === 'string' ? value.fighter : null);
        if (!source) return value;
        const known = names[path] || names[(helper ? 'helper:' : 'fighter:') + source] || value.displayName;
        if (!known) return value;
        const identity = {displayName: known, sourceId: value.sourceId || source};
        if (typeof value.helper === 'string') return {...value, helper: known, ...identity};
        if (key === 'helper') return {...value, id: path?.split('/').at(-1) || value.id, ...identity};
        return {...value, fighter: known, ...identity};
    }

    const modeLabels = {1: '闯关模式', single: '闯关模式', 2: '人机对战', vs_com: '人机对战',
        3: '双人对战', versus: '双人对战', 4: '训练模式', training: '训练模式'};

    function describeRun(run) {
        const matches = new Map();
        function observe(record) {
            if (!record) return;
            const actors = Object.entries(record.players || {});
            if (!actors.length && record.type !== 'match_started') return;
            const id = record.matchId || '';
            const match = matches.get(id) || {fighters: {}, helpers: {}};
            for (const [key, actor] of actors) {
                const slot = actor?.slot || key;
                if (!actor || !['p1', 'p2'].includes(slot)) continue;
                const fighter = nameFields('', actor).displayName || actor.fighter;
                const helper = actor.helper && nameFields('helper', actor.helper).displayName;
                if (fighter) match.fighters[slot] = fighter;
                if (helper) match.helpers[slot] = helper;
            }
            if (record.online) match.online = true;
            match.mode = match.online ? '联机对战' : modeLabels[record.modeName] || modeLabels[record.mode] || match.mode;
            if (record.map) match.map = record.map;
            if (match.mode === '闯关模式' && Number.isInteger(record.arcadeStageIndex)) {
                match.stage = record.arcadeStageIndex + 1;
            }
            if (record.at) match.at = record.at;
            matches.set(id, match);
        }
        const snapshot = run.snapshot?.match;
        if (snapshot?.matchId) observe(snapshot);
        const observations = [...(run.matchHistory || []).filter(entry => entry.type === 'match_started'),
            ...(run.stageTransitions || []), ...(run.checkpoints || []), run.lastCheckpoint].filter(Boolean);
        observations.sort((a, b) => String(a.at || '').localeCompare(String(b.at || ''))).forEach(observe);
        const recent = [...matches.values()].reverse().sort((a, b) => String(b.at || '').localeCompare(String(a.at || '')));
        for (const match of recent) {
            const {p1, p2} = match.fighters;
            match.title = p1 || p2 ? (p1 || '角色未记录') + ' 对阵 ' + (p2 || '对手未记录') : '阵容未记录';
        }
        return recent;
    }

    function reportBlob(report) {
        // Events are individually bounded. Seal batches into immutable Blob parts
        // before visiting the next records, including tapes from an interrupted run.
        const parts = [];
        let batch = '';
        function append(text) {
            batch += text;
            if (batch.length >= 64 * 1024) {
                parts.push(new Blob([batch]));
                batch = '';
            }
        }
        function writeSection(section) {
            append('{');
            let separator = '';
            for (const [key, value] of Object.entries(section)) {
                if (value === undefined) continue;
                append(separator + JSON.stringify(key) + ':');
                separator = ',';
                if (Array.isArray(value)) {
                    append('[');
                    for (let i = 0; i < value.length; i++) {
                        if (i) append(',');
                        if (key === 'criticalIncidents') writeSection(value[i]);
                        else append(JSON.stringify(value[i], nameFields) ?? 'null');
                    }
                    append(']');
                } else if (value && ['runtime', 'reloadDiagnostics', 'savedRun'].includes(key)) {
                    writeSection(value);
                } else {
                    append(JSON.stringify(value, nameFields));
                }
            }
            append('}');
        }
        writeSection(report);
        parts.push(batch);
        return new Blob(parts, {type: 'application/json'});
    }

    function download(report) {
        const blob = reportBlob(report);
        const url = URL.createObjectURL(blob), link = document.createElement('a');
        link.href = url;
        const match = report.reportKind === 'saved_run' && describeRun(report.reloadDiagnostics.currentRun)[0];
        const label = match ? [match.mode, match.title].filter(Boolean).join('-').replace(/[\\/:*?"<>|]/g, '_').slice(0, 90) + '-' : '';
        link.download = 'bvn26-log-' + label + report.exportedAt.replace(/[:.]/g, '-') + '.json';
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 10000);
    }

    function lastCheckpoint(run) {
        const journal = run.checkpoints?.at(-1), archived = run.lastCheckpoint;
        if (!journal || !archived) return journal || archived;
        if (journal.recordSeq && archived.recordSeq) return archived.recordSeq > journal.recordSeq ? archived : journal;
        return archived.at > journal.at ? archived : journal;
    }

    // Wall-clock timestamps can also be matched against a device incident report.
    // An observed exception or GPU loss may precede a successful recovery.
    function endEvidence(run, events = [], successor) {
        const checkpoint = lastCheckpoint(run);
        const lastEvent = events.at(-1);
        const signals = run.signals || [];
        const inputs = Object.values(run.lastInputs || {});
        const times = [checkpoint?.at, lastEvent?.receivedAt, signals.at(-1)?.at, run.browserProgress?.timerAt, run.browserProgress?.animationFrameAt,
            ...inputs.map(input => input?.receivedAt), run.updatedAt].map(value => Date.parse(value)).filter(Number.isFinite);
        const end = times.length ? Math.max(...times) : NaN;
        const next = successor?.previousRunId === run.runId ? Date.parse(successor.startedAt) : NaN;
        const observations = new Map(signals.map(signal => [signal.kind, signal]));
        for (const signal of Object.values(run.browserEvidence || {})) observations.set(signal.kind, signal);
        const signalsByTime = [...observations.values()].sort((a,b) => String(b.at).localeCompare(String(a.at)));
        return {lastObservedAt: Number.isFinite(end) ? new Date(end).toISOString() : null,
            nextStartAt: next >= end ? successor.startedAt : null,
            gapMs: next >= end ? next - end : null,
            navigation: next >= end ? successor.navigation ?? null : null,
            browserReportedDiscard: next >= end ? successor.browserReportedDiscard ?? null : null,
            signals: signalsByTime.map(signal => ({...signal,
                msBeforeLastObservation: Number.isFinite(end - Date.parse(signal.at)) ? end - Date.parse(signal.at) : null}))};
    }

    async function recoveredReport(run, runs = []) {
        const saved = await detail(run.runId);
        const events = saved.events;
        const last = lastCheckpoint(run);
        const snapshot = run.snapshot || null;
        const evidence = endEvidence(run, events, runs.find(next => next.previousRunId === run.runId));
        return {schemaVersion: 2, reportKind: 'saved_run', runId: run.runId, startedAt: run.startedAt,
            exportedAt: new Date().toISOString(), userAgent: run.userAgent, build: run.build || {status: 'unknown', buildID: run.buildID},
            entries: run.consoleTail || [], runtime: {snapshotStatus: snapshot ? 'persisted' : 'unavailable', snapshot,
                events, inputTape: events.filter(e => e.type === 'input_consumed'),
                criticalEvents: events.filter(e => e.type === 'diagnostic_exception' || e.type === 'pause_state')},
            reloadDiagnostics: {currentRun: run, previousRuns: [], persistedDetail: {...saved, events: undefined},
                lastCheckpoint: last || null, endEvidence: evidence,
                cause: run.lifecycle === 'active' && evidence.browserReportedDiscard === true ? 'browser_reported_discard' : 'unconfirmed'}};
    }
    return {createRecorder, mergeTail, listRuns, removeRuns, detail, download, describeRun, recoveredReport, nameFields, lastCheckpoint, endEvidence};
})();
