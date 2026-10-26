"""Sample only the owned native cache probe; profiling is not a pixel reference."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time
from tools.probes.capture_native_player import capture, matching_players, player_binary, preflight, LOG


def profile(build, output, app):
    build = Path(build).resolve()
    output = Path(output).resolve()
    app = Path(app).resolve()
    preflight(app)
    movie = (build/'game/main.swf').resolve()
    binary = player_binary(app)
    before = matching_players(movie,binary)
    if before:
        raise RuntimeError('Refusing to profile a pre-existing player for this movie')
    output.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=1) as executor:
        run = executor.submit(capture,build,build/'native.log',60,app)
        deadline = time.monotonic()+15
        owned = set()
        while time.monotonic()<deadline and not run.done():
            owned = matching_players(movie,binary)-before
            if owned:break
            time.sleep(0.1)
        if len(owned)!=1:
            raise RuntimeError('Expected exactly one owned native player')
        pid = owned.pop()
        metadata = json.loads((build/'build.json').read_text())
        prefix = 'AIREF|' + metadata['run_id'] + '|'
        while time.monotonic()<deadline and not run.done():
            if LOG.exists() and any(line.startswith(prefix) and '|profile|' in line for line in LOG.read_text(errors='replace').splitlines()):
                break
            time.sleep(0.05)
        else:
            raise RuntimeError('No probe-start marker before profiling deadline')
        command = ['/usr/bin/sample',str(pid),'3','1','-file',str(output/'sample.txt')]
        sampled = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15)
        (output/'sample-command.log').write_text(sampled.stdout)
        captured = run.result()
    result = {'sample_command':command,'sample_exit':sampled.returncode,'capture_complete':captured,
              'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
              'movie_sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),
              'pixel_reference':False,'execution_routing_verified':False,'production_admitted':False}
    (output/'profile.json').write_text(json.dumps(result,indent=2)+'\n')
    if sampled.returncode or not captured:
        raise RuntimeError('Native profile did not complete; no routing claim is allowed')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--player-app',type=Path,required=True);p.add_argument('--allow-window-activation',action='store_true')
    a=p.parse_args()
    if not a.allow_window_activation:p.error('Native player may activate; explicit authorization flag required')
    print(json.dumps(profile(a.build.resolve(),a.output.resolve(),a.player_app),indent=2))
