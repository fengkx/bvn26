"""Observe only the still-owned native probe after its debugger has detached."""
import subprocess
import time
from tools.probes.capture_native_player import matching_players, LOG
from tools.probes.probe_owned_debugger import require_unique_owned


def monitor_owned(pid, movie, binary, run_id, output):
    report = {'pid':pid,'movie':str(movie),'binary':str(binary),'run_id':run_id,
              'debugger_reattachment_requested':False,'sample_requested':False,
              'observations':[]}

    def state(label):
        checked = time.monotonic()
        current = matching_players(movie,binary)
        prefix = 'AIREF|'+run_id+'|'
        marker = LOG.exists() and any(line.startswith(prefix) and '|profile|' in line for line in LOG.read_text(errors='replace').splitlines())
        if current != {pid} or not marker:
            report['observations'].append({'label':label,'monotonic':checked,
                                          'ownership_matches':False,'run_marker_present':marker,'matching_pids':sorted(current)})
            return False
        require_unique_owned(set(),current,pid)
        completed = subprocess.run(['/bin/ps','-p',str(pid),'-o','pid=,state=,etime=,command='],
                                   capture_output=True,text=True,timeout=3)
        report['observations'].append({'label':label,'monotonic':checked,'ownership_matches':True,
                                      'ps_returncode':completed.returncode,'ps_stdout':completed.stdout,
                                      'ps_stderr':completed.stderr})
        return True

    if not state('before_sample'):
        return report
    if not state('immediately_before_sample'):
        return report
    report['sample_requested'] = True
    report['sample_start_monotonic'] = time.monotonic()
    command = ['/usr/bin/sample',str(pid),'1','1','-file',str(output/'post-detach-sample.txt')]
    try:
        completed = subprocess.run(command,capture_output=True,text=True,timeout=8)
        report['sample'] = {'command':command,'returncode':completed.returncode,
                            'stdout':completed.stdout,'stderr':completed.stderr,'timed_out':False}
    except subprocess.TimeoutExpired as error:
        report['sample'] = {'command':command,'timed_out':True,
                            'stdout':str(error.stdout or ''),'stderr':str(error.stderr or '')}
    report['sample_end_monotonic'] = time.monotonic()
    state('after_sample')
    return report
