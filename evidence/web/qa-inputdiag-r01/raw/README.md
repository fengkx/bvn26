# Console evidence provenance

`page30-console-tool-output.txt` is the direct text returned by the Chrome DevTools `list_console_messages` tool. It is the primary raw console record.

`page30-normalized-excerpt.jsonl` is a manually selected and normalized excerpt. Its `seq` field is the DevTools `msgid`, not a Godot event sequence; it is not a replacement for the raw tool output.

The page30 tab was later closed by the browser session before a second archival read. The direct retrieval error is recorded in `page30-console-tool-output.txt`; the JSONL is therefore explicitly a normalized excerpt from the earlier tool response, not a raw console dump.
