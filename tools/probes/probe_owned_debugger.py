"""Check debugger attachment only on a freshly owned, source-pinned native probe."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time
from tools.probes.capture_native_player import capture, matching_players, player_binary, preflight, LOG
from tools.probes.extract_cache_affine_binary import BINARY_SHA256

REGISTERS = ('rip', 'rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9')


def require_unique_owned(before, current, expected=None):
    if before or len(current) != 1 or (expected is not None and current != {expected}):
        raise RuntimeError('Probe process ownership is absent, ambiguous, or changed')
    return next(iter(current))


def debugger_script(pid, binary, result_path):
    return f'''import json
import lldb
from pathlib import Path
result = {{'attached': False, 'registers_available': False, 'detach_attempted': False, 'detached': False, 'pid': {pid}, 'pixel_reference': False, 'routing_verified': False}}
process = None
try:
    target = lldb.debugger.CreateTarget({str(binary)!r})
    error = lldb.SBError()
    process = target.AttachToProcessWithID(lldb.debugger.GetListener(), {pid}, error)
    result['attach_error'] = str(error)
    result['attached'] = error.Success() and process.IsValid()
    if result['attached']:
        result['target_triple'] = target.GetTriple()
        result['state'] = lldb.SBDebugger.StateAsCString(process.GetState())
        frame = process.GetSelectedThread().GetFrameAtIndex(0)
        result['registers'] = {{name: frame.FindRegister(name).GetValue() for name in {REGISTERS!r}}}
        result['registers_available'] = all(value is not None for value in result['registers'].values())
except BaseException as error:
    result['error'] = repr(error)
finally:
    if result['attached'] and process is not None:
        result['detach_attempted'] = True
        error = process.Detach()
        result['detach_error'] = str(error)
        result['detached'] = error.Success()
    Path({str(result_path)!r}).write_text(json.dumps(result, indent=2)+chr(10))
'''


def validate_debugger_timeout(value):
    if not 0 < value <= 45:
        raise ValueError('Debugger timeout must be positive and at most45 seconds')
    return value


def probe(build, output, app, debugger_timeout=15, *, script_factory=debugger_script,
          explicit_breakpoints_requested=False):
    debugger_timeout = validate_debugger_timeout(debugger_timeout)
    build,output,app = build.resolve(),output.resolve(),app.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Debugger output directory must be fresh')
    output.mkdir(parents=True,exist_ok=True)
    preflight(app)
    binary = player_binary(app)
    if hashlib.sha256(binary.read_bytes()).hexdigest() != BINARY_SHA256:
        raise ValueError('Native executable differs from pinned baseline')
    movie = (build/'game/main.swf').resolve()
    metadata = json.loads((build/'build.json').read_text())
    if metadata.get('swf_sha256') != hashlib.sha256(movie.read_bytes()).hexdigest():
        raise ValueError('Probe movie differs from its build record')
    if metadata.get('fixture_sha256') != hashlib.sha256((build/'fixture.json').read_bytes()).hexdigest():
        raise ValueError('Probe fixture differs from its build record')
    if metadata.get('raw_tags_preserved') is not True:
        raise ValueError('Owned probe must preserve original source tags')
    before = matching_players(movie,binary)
    if before:
        raise RuntimeError('Refusing a pre-existing player')
    observations = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(capture,build,build/'native.log',90,app)
        deadline = time.monotonic()+20
        pid = None
        while time.monotonic()<deadline and not future.done():
            current = matching_players(movie,binary)
            if current:
                pid = require_unique_owned(before,current)
                break
            time.sleep(.1)
        if pid is None:
            raise RuntimeError('No owned probe process before deadline')
        prefix = 'AIREF|'+metadata['run_id']+'|'
        while time.monotonic()<deadline and not future.done():
            if LOG.exists() and any(line.startswith(prefix) and '|profile|' in line for line in LOG.read_text(errors='replace').splitlines()):
                break
            time.sleep(.05)
        else:
            raise RuntimeError('No run-specific profile marker')
        require_unique_owned(before,matching_players(movie,binary),pid)
        observations.append({'pid':pid,'movie':str(movie),'binary':str(binary),'run_id':metadata['run_id'],'ownership_checked_immediately_before_attach':True})
        script = output/'lldb-readonly.py'
        script.write_text(script_factory(pid,binary,output/'debugger-result.json'))
        command = ['xcrun','lldb','--batch','-o',f'script exec(compile(open({str(script)!r}).read(), {str(script)!r}, "exec"))']
        try:
            completed = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=debugger_timeout)
            transcript,exit_code,timed_out = completed.stdout,completed.returncode,False
        except subprocess.TimeoutExpired as error:
            transcript = error.stdout or b''
            if isinstance(transcript,bytes):transcript=transcript.decode(errors='replace')
            exit_code,timed_out = None,True
        (output/'lldb.log').write_text(transcript)
        captured = future.result()
    result_path = output/'debugger-result.json'
    result = json.loads(result_path.read_text()) if result_path.exists() else {'attached':None,'detached':None,'registers_available':None,'result_missing':True}
    final = {'ownership':observations,'debugger':result,'debugger_exit':exit_code,'debugger_timed_out':timed_out,'debugger_timeout_seconds':debugger_timeout,
             'capture_complete':captured,'owned_processes_remaining':sorted(matching_players(movie,binary)),
             'binary_sha256':BINARY_SHA256,'movie_sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),
             'explicit_breakpoints_requested':explicit_breakpoints_requested,'target_memory_writes_requested':False,'lldb_internal_memory_writes_verified':False,'pixel_reference':False,
             'operand_semantics_proved':False,'production_admitted':False}
    (output/'feasibility.json').write_text(json.dumps(final,indent=2)+'\n')
    return final


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--debugger-timeout',type=float,default=15);p.add_argument('--player-app',type=Path,required=True);p.add_argument('--allow-window-activation',action='store_true');args=p.parse_args()
    if not args.allow_window_activation:p.error('Explicit native window activation authorization required')
    result=probe(args.build,args.output,args.player_app,args.debugger_timeout);print(json.dumps(result,indent=2))
    if not result['capture_complete'] or result['owned_processes_remaining']:raise SystemExit(1)
