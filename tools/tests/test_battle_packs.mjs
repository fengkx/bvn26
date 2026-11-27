import assert from 'node:assert/strict';
import {createHash, webcrypto} from 'node:crypto';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

test('forms share one verified download, including retries on an old deployment', async () => {
    const bytes = new Uint8Array([1, 2, 3]);
    const sha = createHash('sha256').update(bytes).digest('hex');
    const requests = [];
    const files = [];
    let damaged = true;
    const context = {
        battlePackConfig: {
            owners: {kenshin: 'kenshin', 'kenshin-3': 'kenshin'},
            packs: {kenshin: {file: 'kenshin-' + sha + '.pck', size: bytes.length, sha}},
            origin: 'https://old.example'
        },
        window: {}, URL, AbortController, crypto: webcrypto, setTimeout, clearTimeout,
        console: {error() {}}, document: {baseURI: 'https://game.example/'},
        location: {origin: 'https://game.example'},
        engine: {rtenv: {copyToFS(path, data, canOwn) {
            assert.equal(canOwn, true);
            files.push([path, Array.from(new Uint8Array(data))]);
        }}},
        async fetch(url) {
            requests.push(url.origin);
            if (url.origin === 'https://game.example') return new Response(null, {status: 404});
            return new Response(damaged ? new Uint8Array([2, 1, 3]) : bytes);
        }
    };
    vm.runInNewContext(readFileSync(new URL('../../godot/web/battle_packs.js', import.meta.url), 'utf8'), context);
    const loader = context.window.bvnBattlePacks;
    const checkMemory = (files, mounted) => {
        const sample = loader.memorySnapshot();
        assert.equal(sample.battlePackFileBytes, files);
        assert.equal(sample.mountedBattlePackBytes, mounted);
    };
    async function finish(expected) {
        for (let i = 0; i < 100 && loader.state('kenshin') === 'loading'; i++) {
            await new Promise(resolve => setTimeout(resolve, 1));
        }
        assert.equal(loader.state('kenshin'), expected);
    }
    loader.start('kenshin-3');
    loader.start('kenshin');
    await finish('failed');
    assert.equal(files.length, 0);
    checkMemory(0, 0);
    damaged = false;
    loader.start('kenshin');
    await finish('ready');
    checkMemory(bytes.length, 0);
    loader.mounted('kenshin');
    loader.mounted('kenshin-3');
    loader.start('kenshin-3');
    checkMemory(bytes.length, bytes.length);
    assert.equal(loader.needed('kenshin-3'), false);
    assert.deepEqual(requests, ['https://game.example', 'https://old.example',
        'https://game.example', 'https://old.example']);
    assert.deepEqual(files, [['/kenshin-' + sha + '.pck', [1, 2, 3]]]);
});
