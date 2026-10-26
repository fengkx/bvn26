import json
import lldb
from pathlib import Path
result = {'attached': False, 'registers_available': False, 'detach_attempted': False, 'detached': False, 'pid': 88332, 'pixel_reference': False, 'routing_verified': False}
process = None
try:
    target = lldb.debugger.CreateTarget('/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger')
    error = lldb.SBError()
    process = target.AttachToProcessWithID(lldb.debugger.GetListener(), 88332, error)
    result['attach_error'] = str(error)
    result['attached'] = error.Success() and process.IsValid()
    if result['attached']:
        result['target_triple'] = target.GetTriple()
        result['state'] = lldb.SBDebugger.StateAsCString(process.GetState())
        frame = process.GetSelectedThread().GetFrameAtIndex(0)
        result['registers'] = {name: frame.FindRegister(name).GetValue() for name in ('rip', 'rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9')}
        result['registers_available'] = all(value is not None for value in result['registers'].values())
except BaseException as error:
    result['error'] = repr(error)
finally:
    if result['attached'] and process is not None:
        result['detach_attempted'] = True
        error = process.Detach()
        result['detach_error'] = str(error)
        result['detached'] = error.Success()
    Path('/private/tmp/bvn-r244/debugger/debugger-result.json').write_text(json.dumps(result, indent=2)+'\n')
