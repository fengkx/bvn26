"""Bounded hardware stop at a source-profile-observed direct compose callsite."""
import argparse
import json
from pathlib import Path
from tools.probes.audit_affine_static_callers import analyze
from tools.probes.probe_owned_debugger import probe

CALLEE = 0x10029dad0
ENTRY = 0x1000f28db
ENTRY_BYTES = 'e8f0b11a00488bb3d000000031d24883'
SETUP_BYTES = '488d7b48488d95d0fdffff4c89f6'


def script_for_edges(edges):
    matches = [e for e in edges if int(e['site'],16) == ENTRY and int(e['target'],16) == CALLEE]
    if len(matches) != 1 or matches[0]['bytes'] != ENTRY_BYTES[:10]:
        raise ValueError('Source-profile-selected direct call edge is not uniquely pinned')
    edge = matches[0]

    def factory(pid, binary, result_path):
        setup = f"PID={pid}\nBINARY={str(binary)!r}\nRESULT={str(result_path)!r}\nENTRY={ENTRY}\nENTRY_BYTES={ENTRY_BYTES!r}\nEDGE={edge!r}\nSETUP_BYTES={SETUP_BYTES!r}\n"
        return setup + RUNTIME
    return factory


RUNTIME = r'''
import json, struct, time
from pathlib import Path
import lldb
result = {'attached': False, 'detached': None, 'hardware_callsite_verified': False,
          'guest_virtual_entry_bytes_independently_verified': False,
          'physical_entry_bytes_independently_verified': False,
          'explicit_memory_writes_requested': False, 'pixel_reference': False,
          'operand_semantics_proved': False, 'source_fill_ownership_proved': False, 'production_admitted': False}
process = None
bp = None
created_ids = []
def read(address, size):
    if size not in (14, 16, 28):
        raise ValueError('Read size outside declared ABI bounds')
    region = lldb.SBMemoryRegionInfo()
    err = process.GetMemoryRegionInfo(address, region)
    if not err.Success() or not region.IsReadable() or address+size > region.GetRegionEnd():
        raise ValueError('Declared operand read is not wholly readable')
    err = lldb.SBError()
    data = process.ReadMemory(address, size, err)
    if not err.Success() or len(data) != size:
        raise ValueError('Incomplete declared operand read')
    return data
try:
    target = lldb.debugger.CreateTarget(BINARY)
    error = lldb.SBError()
    process = target.AttachToProcessWithID(lldb.debugger.GetListener(), PID, error)
    result['attach_error'] = str(error)
    result['attached'] = error.Success() and process.IsValid()
    if not result['attached']:
        raise RuntimeError('Attachment failed')
    result['target_triple'] = target.GetTriple()
    if not result['target_triple'].startswith('x86_64-'):
        raise RuntimeError('Pinned entry ABI requires x86_64')
    modules = [target.GetModuleAtIndex(i) for i in range(target.GetNumModules())
               if str(target.GetModuleAtIndex(i).GetFileSpec()) == BINARY]
    if len(modules) != 1:
        raise RuntimeError('Pinned executable module is not unique')
    module = modules[0]
    address = module.ResolveFileAddress(ENTRY)
    load = address.GetLoadAddress(target)
    if not address.IsValid() or load == lldb.LLDB_INVALID_ADDRESS:
        raise RuntimeError('No loaded entry address')
    result['entry_file_address'] = hex(ENTRY)
    result['entry_load_address'] = hex(load)
    result['entry_before_hex'] = read(load, 16).hex()
    if result['entry_before_hex'] != ENTRY_BYTES:
        raise RuntimeError('Entry bytes differ before breakpoint')
    result['setup_before_hex'] = read(load-14,14).hex()
    if result['setup_before_hex'] != SETUP_BYTES:
        raise RuntimeError('Pinned argument setup readback differs')
    before_ids = {target.GetBreakpointAtIndex(i).GetID() for i in range(target.GetNumBreakpoints())}
    command = lldb.SBCommandReturnObject()
    lldb.debugger.GetCommandInterpreter().HandleCommand('breakpoint set --hardware --address '+hex(load), command)
    result['hardware_command'] = {'success': command.Succeeded(), 'output': command.GetOutput(), 'error': command.GetError()}
    created = [target.GetBreakpointAtIndex(i) for i in range(target.GetNumBreakpoints())
               if target.GetBreakpointAtIndex(i).GetID() not in before_ids]
    created_ids = [item.GetID() for item in created]
    if len(created) == 1:
        bp = created[0]
    if not command.Succeeded() or bp is None or not bp.IsHardware() or bp.GetNumLocations() != 1:
        raise RuntimeError('Hardware breakpoint unavailable; no software fallback')
    location = bp.GetLocationAtIndex(0)
    if not location.IsResolved() or location.GetAddress().GetLoadAddress(target) != load:
        raise RuntimeError('Hardware location is not exact entry')
    result['hardware_requested_and_reported'] = True
    result['breakpoint_id'] = bp.GetID()
    prior_stop = process.GetStopID()
    lldb.debugger.SetAsync(True)
    error = process.Continue()
    if not error.Success():
        raise RuntimeError('Continue failed: '+str(error))
    deadline = time.monotonic()+5
    while time.monotonic() < deadline:
        if process.GetState() == lldb.eStateStopped and process.GetStopID() != prior_stop:
            break
        if process.GetState() in (lldb.eStateExited, lldb.eStateDetached):
            raise RuntimeError('Probe exited before entry stop')
        time.sleep(.01)
    else:
        process.Stop()
        raise RuntimeError('No new entry stop within five seconds')
    hits = []
    for i in range(process.GetNumThreads()):
        thread = process.GetThreadAtIndex(i)
        ids = [thread.GetStopReasonDataAtIndex(j) for j in range(thread.GetStopReasonDataCount())]
        if thread.GetStopReason() == lldb.eStopReasonBreakpoint and len(ids) % 2 == 0 and (bp.GetID(), location.GetID()) in list(zip(ids[::2],ids[1::2])):
            hits.append(thread)
    result['matching_stopped_threads'] = len(hits)
    if len(hits) != 1:
        raise RuntimeError('Stop reason does not uniquely identify our breakpoint')
    thread = hits[0]
    frame = thread.GetFrameAtIndex(0)
    if frame.GetPC() != load or not bp.IsHardware():
        raise RuntimeError('Stopped PC/hardware state differs from entry')
    result['hardware_callsite_verified'] = True
    result['stop_id'] = process.GetStopID()
    result['stop_reason'] = int(thread.GetStopReason())
    result['entry_at_stop_hex'] = read(load, 16).hex()
    if result['entry_at_stop_hex'] != ENTRY_BYTES:
        raise RuntimeError('Entry byte readback changed')
    # LLDB documents that ReadMemory removes software traps from its returned bytes.
    result['entry_readback_matches'] = True
    result['physical_entry_bytes_independently_verified'] = False
    result['entry_readback_caveat'] = 'SBProcess.ReadMemory masks software traps; our sole breakpoint is verified hardware, independent raw guest-byte proof remains unmet after the r246 task-port denial.'
    regs = {}
    for name in ('rip','rbx','rbp','r14','rdi','rsi','rdx'):
        value = frame.FindRegister(name)
        if not value.IsValid() or not value.GetError().Success() or value.GetValue() is None:
            raise RuntimeError('Unavailable entry register: '+name)
        regs[name] = value.GetValueAsUnsigned()
    if regs['rip'] != load:
        raise RuntimeError('RIP register differs from verified entry PC')
    result['entry_registers'] = {k: hex(v) for k,v in regs.items()}
    relations = {'rdi_from_rbx_48': regs['rdi'] == regs['rbx']+0x48,
                 'rsi_from_r14': regs['rsi'] == regs['r14'],
                 'rdx_from_rbp_minus_230': regs['rdx'] == regs['rbp']-0x230}
    result['pinned_argument_relations'] = relations
    if not all(relations.values()):
        raise RuntimeError('Actual argument pointers violate pinned pre-CALL setup')
    result['verified_direct_call'] = EDGE
    result['anticipated_return_file'] = EDGE['return_pc']
    result['precall_stack_return_read'] = False
    result['input_matrix_bytes'] = {name: read(regs[name],28).hex() for name in ('rdi','rsi')}
    result['output_pointer_only'] = hex(regs['rdx'])
except BaseException as error:
    result['error'] = repr(error)
finally:
    result['breakpoint_cleanup'] = []
    for breakpoint_id in created_ids:
        try:
            removed = target.BreakpointDelete(breakpoint_id)
            result['breakpoint_cleanup'].append({'id': breakpoint_id, 'removed': removed})
        except BaseException as error:
            result['breakpoint_cleanup'].append({'id': breakpoint_id, 'error': repr(error)})
    if result['attached'] and process is not None:
        try:
            if process.GetState() == lldb.eStateRunning:
                process.Stop()
        except BaseException as error:
            result['cleanup_stop_error'] = repr(error)
        finally:
            try:
                error = process.Detach()
                result['detached'] = error.Success()
                result['detach_error'] = str(error)
            except BaseException as error:
                result['detach_exception'] = repr(error)
    Path(RESULT).write_text(json.dumps(result,indent=2)+chr(10))
'''


def capture_accepted(result):
    debugger = result['debugger']
    breakpoint_id = debugger.get('breakpoint_id')
    cleanup = debugger.get('breakpoint_cleanup')
    return (result['capture_complete'] is True and not result['owned_processes_remaining']
            and result.get('debugger_exit') == 0 and result.get('debugger_timed_out') is False
            and debugger.get('hardware_callsite_verified') is True
            and debugger.get('detached') is True and not debugger.get('error')
            and type(breakpoint_id) is int
            and cleanup == [{'id': breakpoint_id, 'removed': True}])



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build','output','player-app','disassembly'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--allow-window-activation',action='store_true')
    args = parser.parse_args()
    if not args.allow_window_activation:
        parser.error('Explicit native window activation authorization required')
    from tools.probes.capture_native_player import player_binary
    static = analyze(player_binary(args.player_app),args.disassembly,{})
    result = probe(args.build,args.output,args.player_app,45,
                   script_factory=script_for_edges(static['direct_edges']),explicit_breakpoints_requested=True)
    (args.output/'static-callers.json').write_text(json.dumps(static,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not capture_accepted(result):
        raise SystemExit(1)
