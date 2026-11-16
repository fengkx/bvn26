import subprocess,sys,time,json,threading,http.server,functools
from pathlib import Path
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(exist_ok=True,parents=True)
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root/'dist/web'))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start()
profile=out/'chrome-profile';profile.mkdir(exist_ok=True)
chrome=subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--user-data-dir='+str(profile),'--remote-debugging-port=0','--no-first-run','--no-default-browser-check','--enable-unsafe-swiftshader','--window-size=1100,800','about:blank'],stdout=(out/'chrome.log').open('w'),stderr=subprocess.STDOUT)
try:
 deadline=time.monotonic()+20
 while not (profile/'DevToolsActivePort').exists():
  assert time.monotonic()<deadline;time.sleep(.1)
 port=(profile/'DevToolsActivePort').read_text().splitlines()[0]
 url='http://127.0.0.1:'+str(server.server_port)+'/'
 cmd=['/Users/fengkx/.local/share/mise/installs/node/24.18.0/bin/node',str(root/'tools/test_chromium_web_boot.mjs'),'http://127.0.0.1:'+port,url,str(out/'boot.png')]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=90);(out/'result.json').write_text(r.stdout);(out/'stderr.log').write_text(r.stderr);assert r.returncode==0,r.stderr
 result=json.loads(r.stdout);assert result['canvas']['visible'];errors=[s for s in result['console'] if 'SCRIPT ERROR' in s or 'ERROR:' in s];assert not errors,errors
 print('BROWSER_BOOT_OK',url,flush=True)
finally:
 chrome.terminate()
 try:chrome.wait(timeout=10)
 except subprocess.TimeoutExpired:chrome.kill();chrome.wait()
 server.shutdown()
