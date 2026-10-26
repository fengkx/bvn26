"""Bounded hardware-only stop at a pinned matrix-composition entry; no renderer admission."""
import argparse
import json
import inspect
from pathlib import Path
from tools.probes.audit_affine_static_callers import analyze
from tools.probes.probe_owned_debugger import probe
from tools.probes.read_owned_guest_memory import read_guest_entry

ENTRY = 0x10029dad0
ENTRY_BYTES = '554889e54157415641554154538b4718'


def script_for_edges(edges):
    returns = {int(e['return_pc'], 16): e for e in edges if int(e['target'], 16) == ENTRY}
    if not returns:
        raise ValueError('No independently verified compose callers')

    def factory(pid, binary, result_path):
        setup = f"PID={pid}\nBINARY={str(binary)!r}\nRESULT={str(result_path)!r}\nENTRY={ENTRY}\nENTRY_BYTES={ENTRY_BYTES!r}\nRETURNS={returns!r}\n"
        return setup + inspect.getsource(read_guest_entry) + RUNTIME
    return factory


RUNTIME = r'''
import json, struct, time
from pathlib import Path
import lldb
result = {'attached': False, 'detached': None, 'hardware_entry_verified': False,
          'guest_virtual_entry_bytes_independently_verified': False,
          'physical_entry_bytes_independently_verified': False,
          'explicit_memory_writes_requested': False, 'pixel_reference': False,
          'operand_semantics_proved': False, 'production_admitted': False}
process = None
bp = None
created_ids = []
def read(address, size):
    if size not in (8, 16, 28):
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
    result['guest_entry_before'] = read_guest_entry(PID, load)
    if not result['guest_entry_before']['guest_virtual_read_verified'] or result['guest_entry_before'].get('mach_port_deallocate_return') != 0 or result['guest_entry_before']['bytes_hex'] != ENTRY_BYTES:
        raise RuntimeError('Independent guest virtual entry read denied, incomplete, or mismatched')
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
    result['hardware_entry_verified'] = True
    result['stop_id'] = process.GetStopID()
    result['stop_reason'] = int(thread.GetStopReason())
    result['entry_at_stop_hex'] = read(load, 16).hex()
    if result['entry_at_stop_hex'] != ENTRY_BYTES:
        raise RuntimeError('Entry byte readback changed')
    # LLDB documents that ReadMemory removes software traps from its returned bytes.
    result['guest_entry_at_stop'] = read_guest_entry(PID, load)
    if not result['guest_entry_at_stop']['guest_virtual_read_verified'] or result['guest_entry_at_stop'].get('mach_port_deallocate_return') != 0 or result['guest_entry_at_stop']['bytes_hex'] != ENTRY_BYTES:
        raise RuntimeError('Independent stopped guest entry read denied, incomplete, or mismatched')
    result['guest_virtual_entry_bytes_independently_verified'] = True
    result['entry_readback_matches'] = True
    result['physical_entry_bytes_independently_verified'] = False
    result['entry_readback_caveat'] = 'SBProcess.ReadMemory masks software traps; our sole breakpoint is verified hardware, independent Mach reads separately verify guest virtual bytes only, never physical or translated instructions.'
    regs = {}
    for name in ('rip','rsp','rdi','rsi','rdx'):
        value = frame.FindRegister(name)
        if not value.IsValid() or not value.GetError().Success() or value.GetValue() is None:
            raise RuntimeError('Unavailable entry register: '+name)
        regs[name] = value.GetValueAsUnsigned()
    if regs['rip'] != load:
        raise RuntimeError('RIP register differs from verified entry PC')
    result['entry_registers'] = {k: hex(v) for k,v in regs.items()}
    return_load = struct.unpack('<Q',read(regs['rsp'],8))[0]
    return_address = target.ResolveLoadAddress(return_load)
    result['caller_return_load'] = hex(return_load)
    return_file = return_address.GetFileAddress()
    same_module = return_address.GetModule().GetUUIDString() == module.GetUUIDString()
    result['verified_direct_caller'] = RETURNS.get(return_file) if same_module else None
    result['caller_return_file'] = hex(return_file)
    if result['verified_direct_caller'] is None:
        raise RuntimeError('Caller is not an independently verified same-module direct edge')
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
