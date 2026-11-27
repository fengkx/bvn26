"""Reduce peak memory in the pinned Godot 4.7.2 Web export."""

import sys
from pathlib import Path


def optimize(loader: str) -> str:
    # Read directly into the final buffer. The stock Response.arrayBuffer()
    # assembles a second contiguous copy after queueing all the response chunks.
    stock = "const tr = getTrackedResponse(response, tracker[file]);"
    streaming = """if (!raw && file.endsWith('.pck') && fileSize > 0 && response.body) {
                const bytes = new Uint8Array(fileSize);
                const reader = response.body.getReader();
                const status = tracker[file];
                return (async () => {
                    try {
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            bytes.set(value, status.loaded);
                            status.loaded += value.byteLength;
                        }
                        if (status.loaded !== fileSize) throw new Error('Incomplete game pack');
                        status.done = true;
                        return bytes.buffer;
                    } catch (error) {
                        await reader.cancel().catch(() => {});
                        throw error;
                    } finally {
                        reader.releaseLock();
                    }
                })();
            }
            """ + stock
    # Only internally downloaded packs can transfer their backing store to MEMFS.
    # Keep copy semantics for buffers supplied through the public Engine API.
    replacements = (
        # This game creates one engine per document. A cloned fetch response
        # queues the Wasm on an unread branch during streaming compilation.
        ("this.config = new InternalConfig(initConfig);",
         "this.config = new InternalConfig(initConfig);\n\t\tthis.bvnSingleUseWasm = initConfig?.bvnSingleUseWasm === true;"),
        ("new Response(response.clone().body,", "new Response((me.bvnSingleUseWasm && me.config.unloadAfterInit ? response : response.clone()).body,"),
        (stock, streaming),
        ("buffer: buf,", "buffer: buf,\n                        ownPack: pathOrBuffer.endsWith('.pck'),"),
        ("copy_to_fs:function(path,buffer){", "copy_to_fs:function(path,buffer,canOwn=false){"),
        ("FS.writeFile(path,new Uint8Array(buffer))", "FS.writeFile(path,new Uint8Array(buffer),{canOwn})"),
        ("['copyToFS'](file.path, file.buffer)", "['copyToFS'](file.path, file.buffer, file.ownPack)"),
        ('const text=evt.clipboardData.getData("text");',
         'if(!window.bvnEnginePasteEvents?.has(evt))return;const text=evt.clipboardData.getData("text");'),
        # The single-thread template supplies synchronous subarray views of HEAPF32.
        # copyToChannel already copies these samples into Web Audio-owned storage.
        ("audioBuffer.copyToChannel(new Float32Array(subLeft),0,0)", "audioBuffer.copyToChannel(subLeft,0,0)"),
        ("audioBuffer.copyToChannel(new Float32Array(subRight),1,0)", "audioBuffer.copyToChannel(subRight,1,0)"),
        # Each playback owns its source node, offset and loop settings. The
        # registered PCM is read-only and can be shared even by overlapping sounds.
        ("getAudioBuffer(){return this._duplicateAudioBuffer()}", """getAudioBuffer() {
            if (this._audioBuffer == null) throw new Error("Audio sample was cleared");
            return this._audioBuffer;
        }"""),
    )
    for before, after in replacements:
        if loader.count(before) != 1:
            raise ValueError(f"Unexpected Godot Web loader at {before!r}")
        loader = loader.replace(before, after)
    return loader


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(optimize(path.read_text()))
