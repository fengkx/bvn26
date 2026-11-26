// Inlined alongside this release's manifest by the export step.
window.bvnBattlePacks = (() => {
    const mounted = new Set();
    const jobs = new Map();
    let queue = Promise.resolve();
    function family(id) {
        return battlePackConfig.owners[id];
    }
    async function download(pack, job) {
        const urls = [new URL(pack.file, document.baseURI)];
        if (battlePackConfig.origin && location.origin !== battlePackConfig.origin) {
            urls.push(new URL(pack.file, battlePackConfig.origin));
        }
        let lastError;
        for (const url of urls) {
            const controller = new AbortController();
            let timeout;
            const resetTimeout = () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => controller.abort(), 30000);
            };
            try {
                resetTimeout();
                const response = await fetch(url, {signal: controller.signal});
                if (!response.ok) throw new Error('HTTP ' + response.status);
                const reader = response.body.getReader();
                const bytes = new Uint8Array(pack.size);
                let offset = 0;
                try {
                    while (true) {
                        const {done, value} = await reader.read();
                        if (done) break;
                        bytes.set(value, offset);
                        offset += value.length;
                        job.progress = offset / pack.size;
                        resetTimeout();
                    }
                } finally {
                    await reader.cancel().catch(() => {});
                }
                if (offset !== pack.size) throw new Error('Incomplete pack');
                const hash = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
                if (Array.from(hash, b => b.toString(16).padStart(2, '0')).join('') !== pack.sha) {
                    throw new Error('Pack checksum mismatch');
                }
                engine.copyToFS('/' + pack.file, bytes.buffer);
                return;
            } catch (error) {
                lastError = error;
            } finally {
                clearTimeout(timeout);
            }
        }
        throw lastError;
    }
    return {
        needed(id) { return !!battlePackConfig.packs[family(id)] && !mounted.has(family(id)); },
        start(id) {
            const owner = family(id);
            const pack = battlePackConfig.packs[owner];
            if (!pack || mounted.has(owner)) return;
            const previous = jobs.get(owner);
            if (previous && previous.state !== 'failed') return;
            const job = {state: 'loading', progress: 0};
            jobs.set(owner, job);
            queue = queue.then(() => download(pack, job)).then(() => {
                job.state = 'ready';
            }, error => {
                console.error('Battle pack download failed', pack.file, String(error));
                job.state = 'failed';
            });
        },
        path(id) { return '/' + battlePackConfig.packs[family(id)].file; },
        mounted(id) { mounted.add(family(id)); },
        memorySnapshot() {
            let battlePackFileBytes = 0;
            let mountedBattlePackBytes = 0;
            for (const [owner, job] of jobs) {
                if (job.state !== 'ready') continue;
                const size = battlePackConfig.packs[owner].size;
                battlePackFileBytes += size;
                if (mounted.has(owner)) mountedBattlePackBytes += size;
            }
            return { battlePackFileBytes, mountedBattlePackBytes };
        },
        state(id) { return jobs.get(family(id)).state; },
        progress(id) { return jobs.get(family(id)).progress; }
    };
})();
