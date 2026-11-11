# Initialization preservation review (not an approved connection plan)

Scope: Apache Flex SDK commit `ba414443032b49c45ff11b61db452c8a8f428bd8`, retained byte-for-byte in r29. This review executes no Java, protocol message, socket, player, debugger or SWF. It qualifies **client command intent/order only**. Producer response, defaults, effective state and restoration on Flash32 remain unmeasured.

## Exact bind path

[PlayerSession.bind lines337–386](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L337-L386) sets the connected flag, adds the listener, starts protocol reception, then issues the following adjustments. `sendSquelch` response supplies the `responded` value; `VersionException` is thrown only after options, capability work and reader-thread startup. A failed version check therefore does not imply no outgoing adjustments occurred. This is control flow in source, not an observed connection.

| Sender / option intent | Supplied value | Preservation obligation still missing |
|---|---|---|
| sendStopWarning / disable_script_stuck_dialog | on (comment explicitly AS2) | Prior/effective timeout-dialog policy, time spent paused and recovery behavior |
| sendStopWarning / disable_script_stuck | on | Prior/effective timeout notification policy; AS3 motivation in comment does not prove AVM1 ignores it |
| sendStopOnFault / break_on_fault | on | Fault/suspension behavior and elapsed-time consequences |
| sendEnumerateOverride / enumerate_override | on | Producer interpretation and enumeration effects; name alone is not a specification |
| sendFailureNotify / notify_on_failure | on | Producer notification conditions, ordering and overhead |
| sendInvokeSetters / invoke_setters | on | Whether inspection can invoke setters and cause game-visible effects |
| sendSwfloadNotify / swf_load_messages | on | SWF notification conditions; not a per-MovieClip placement subscription |
| sendGetterTimeout / getter_timeout | client preference | Effective value/default and effect on evaluation/timing |
| sendSetterTimeout / setter_timeout | client preference | Effective value/default and effect on evaluation/timing |
| sendSquelch / OutSetSquelch | DWORD 1 | Producer suppression semantics, acknowledgement scope and reversibility |
| sendConcurrentDebugger / concurrent_debugger | on, capability conditional | Worker/isolate handling and effects; not AVM1 helper generation |
| sendWideLineDebugger / wide_line_debugger | on, capability conditional | Version-specific encoding agreement; local wide-lines also enabled |

All option sends use `OutSetOption` and wait for `InOption`; the wrapper does not establish that the desired value became the effective value or save a prior value for restoration. Sources: [senders lines1864–1984](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L1864-L1984). The reviewed bind starts an SWF/SWD-reader thread as additional activity; this table is **not** a complete wire allowlist or a safe minimal client implementation.

[unbind lines406–426](https://github.com/apache/flex-sdk/blob/ba414443032b49c45ff11b61db452c8a8f428bd8/modules/debugger/src/java/flash/tools/debugger/concrete/PlayerSession.java#L406-L426) sends `OutExit`, unbinds and closes the socket. This function contains no prior-option restoration sequence. Whether the player resets options itself is unproved; disconnect cannot be certified as restoration from this client code. This does not assert that options persist after disconnect.

## Preservation decision

**not-qualified-for-behavior-preserving-connection**. No option was changed in this slice. Static review is possible without changing observed behavior; executing the reviewed initialization is not certified behavior-preserving. Merely suppressing selected sends would create a different, unqualified protocol client and is not a justified correction here.

Before any separately authorized experiment, obtain producer/version evidence defining each effective option, acknowledgement, original-value query and reset/restore behavior, plus mandatory handshake/reader traffic. Require an explicit refusal if any relevant original value cannot be recovered. Then independently review command coverage, suspend/resume/clock effects, trace loss/ordering, getters/setters, fault behavior, cleanup and equivalent-input baseline controls. All controls are **unexecuted**. A successful cleanup or byte-identical assets would not prove game behavior preserved. No connection or future live is authorized by this plan; if producer evidence cannot be obtained, keep the route unqualified rather than probing by default.
