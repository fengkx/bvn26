// Run only under the lane's exclusive foreground lock against a local Web export.
import { spawn, execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';

const out = resolve(process.argv[2]);
await mkdir(out, { recursive: true });
const port = 19182, httpPort = 18082;
const delay = ms => new Promise(r => setTimeout(r, ms));
const profile = `/tmp/bvn-lane2-chrome-${Date.now()}`;
const server = spawn('/opt/homebrew/bin/python3', ['-m', 'http.server', `${httpPort}`, '--bind', '127.0.0.1', '--directory', 'dist/web']);
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  `--user-data-dir=${profile}`, `--remote-debugging-port=${port}`, '--no-first-run',
  '--no-default-browser-check', '--window-size=1100,800', 'about:blank'
]);
let socket, next = 1;
const pending = new Map(), consoleLog = [], errors = [], requests = [], inputs = [];
let serverLog = '', chromeLog = '';
server.stderr.on('data', d => serverLog += d); chrome.stderr.on('data', d => chromeLog += d);
async function until(fn, message, budget = 120000) {
  const end = Date.now() + budget;
  while (Date.now() < end) { if (await fn()) return; await delay(200); }
  throw new Error(message);
}
function call(method, params = {}) {
  const id = next++;
  return new Promise((resolve, reject) => { pending.set(id, { resolve, reject }); socket.send(JSON.stringify({ id, method, params })); });
}
async function evaluate(expression) {
  const result = await call('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  assert(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function key(letter, down) {
  inputs.push({ at: Date.now(), key: letter, down });
  await call('Input.dispatchKeyEvent', { type: down ? 'keyDown' : 'keyUp', key: letter,
    code: `Key${letter.toUpperCase()}`, windowsVirtualKeyCode: letter.toUpperCase().charCodeAt(0) });
}
async function tap(letter, hold = 110, settle = 600) { await key(letter, true); await delay(hold); await key(letter, false); await delay(settle); }
async function screenshot(name) { const r = await call('Page.captureScreenshot', { format: 'png' }); await writeFile(`${out}/${name}.png`, Buffer.from(r.data, 'base64')); execFileSync('/usr/sbin/screencapture', ['-x', `${out}/${name}-desktop.png`]); }
async function snapshot() {
  return evaluate(`(async()=>{let resolve;const result=new Promise(r=>resolve=r);
    const original=URL.createObjectURL, click=HTMLAnchorElement.prototype.click;
    URL.createObjectURL=blob=>{blob.text().then(text=>resolve(JSON.parse(text)));return 'blob:minrenx-test';};
    HTMLAnchorElement.prototype.click=function(){};
    try{document.getElementById('download').click();return await result;}
    finally{URL.createObjectURL=original;HTMLAnchorElement.prototype.click=click;}})()`);
}
let result = { status: 'failed', scope: 'Local release Web export, headed CDP keyboard events; no physical OS-input or Flash pixel/audio parity proof', profile };
try {
  let pages;
  await until(async () => { try { pages = await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json()); return pages.length; } catch { return false; } }, 'Chrome startup');
  socket = new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((r,j)=>{socket.addEventListener('open',r,{once:true});socket.addEventListener('error',j,{once:true});});
  socket.addEventListener('message', e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result); }
    if (m.method==='Runtime.consoleAPICalled') consoleLog.push(m.params.args.map(a=>a.value??a.description).join(' '));
    if (m.method==='Runtime.exceptionThrown') errors.push(m.params);
    if (m.method==='Network.requestWillBeSent') requests.push(m.params.request.url);
  });
  for (const domain of ['Runtime','Page','Network']) await call(`${domain}.enable`);
  await call('Browser.setDownloadBehavior', {behavior:'deny'});
  await call('Page.navigate', {url:`http://127.0.0.1:${httpPort}/`});
  await until(()=>consoleLog.some(x=>x.startsWith('M0_BOOT_OK ')), 'Web did not boot',180000);
  execFileSync('/usr/bin/osascript', ['-l','JavaScript','-e',
    `ObjC.import('AppKit'); $.NSRunningApplication.runningApplicationWithProcessIdentifier(${chrome.pid}).activateWithOptions($.NSApplicationActivateIgnoringOtherApps);`]);
  await call('Page.bringToFront');
  await evaluate('document.querySelector("canvas").focus()');
  const focus=await evaluate(`({visibility:document.visibilityState,focused:document.hasFocus(),active:document.activeElement?.id})`);
  await writeFile(`${out}/focus.json`,JSON.stringify(focus,null,2));
  assert(focus.focused && focus.visibility==='visible' && focus.active==='canvas',JSON.stringify(focus));
  const bounds=await evaluate(`(()=>{let r=document.querySelector('canvas').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  for (const type of ['mousePressed','mouseReleased']) await call('Input.dispatchMouseEvent',{type,...bounds,button:'left',clickCount:1});
  await delay(5000); await screenshot('title');
  // The implemented menu initially skips hidden SINGLE PLAY to item two; training is item four.
  for (let i=0;i<2;i++) await tap('s',110,650);
  await tap('j',110,1600);
  // Source SelectionGrid route from Ichigo (5,7) to Sage Naruto (13,-2).
  for (const k of ['d','d','s','d']) await tap(k);
  await delay(1200); await screenshot('selection');
  await tap('j',110,1000); await tap('a'); await tap('j',110,1000);
  await tap('j',110,1000); await tap('j',110,1200); await tap('j',110,1200);
  let initial;
  await until(async()=>{initial=await snapshot();return initial?.runtime?.snapshot?.match?.mode === 4 && initial?.runtime?.snapshot?.match?.players?.p1 && initial.runtime.snapshot.match.matchId && initial.runtime.snapshot.match.players.p1.action==='站立';},'No match snapshot',60000);
  await writeFile(`${out}/initial-report.json`,JSON.stringify(initial,null,2));
  assert.equal(initial.runtime.snapshot.match.players.p1.fighter,'仙鸣');
  assert.equal(initial.runtime.snapshot.match.players.p1.resourcePath,'res://generated/fighters/minrenx');
  await screenshot('natural-opening');
  await delay(10000);
  await tap('d',400,1000); await tap('j',900,2500); await tap('i',150,5000);
  await screenshot('base-fight');
  const base=await snapshot(); await writeFile(`${out}/base-report.json`,JSON.stringify(base,null,2));
  const actions=base.runtime.events.filter(e=>e.type==='action_transition' && e.payload.slot==='p1').map(e=>e.payload.after.action);
  assert(actions.includes('走') && actions.some(a=>a.startsWith('砍')) && actions.includes('必杀'),JSON.stringify(actions));
  await until(async()=>{const r=await snapshot();return r?.runtime?.snapshot?.match?.players?.p1?.action==='站立';},'Base move did not recover',60000);
  await Promise.all([key('j',true),key('k',true)]);await delay(180);await Promise.all([key('j',false),key('k',false)]);
  let final; await until(async()=>{final=await snapshot();return final?.runtime?.snapshot?.match?.players?.p1?.resourcePath==='res://generated/forms/minrenx-2' && final.runtime.snapshot.match.players.p1.action==='站立';},'Transformation did not recover',60000);
  await screenshot('transformed'); await writeFile(`${out}/final-report.json`,JSON.stringify(final,null,2));
  assert.equal(final.runtime.snapshot.match.players.p1.resourcePath,'res://generated/forms/minrenx-2');
  assert.equal(final.build.status,'match');
  assert.equal(errors.length,0);
  assert(!requests.some(url=>/\.(swf|as2)(?:[?#]|$)|ruffle/i.test(url)));
  result={...result,status:'passed_targeted_keyboard_and_transformation',build:JSON.parse(await readFile('dist/web/build-metadata.json','utf8'))};
} catch(error) {
  result.error=String(error.stack??error);
  if(socket?.readyState===1) { try {await screenshot('failure');await writeFile(`${out}/failure-report.json`,JSON.stringify(await snapshot(),null,2));} catch {} }
}
finally {
  await writeFile(`${out}/execution.json`,JSON.stringify({...result,inputs,errors,requests:[...new Set(requests)],console:consoleLog},null,2));
  await writeFile(`${out}/server.log`,serverLog);await writeFile(`${out}/chrome.log`,chromeLog);
  if(socket?.readyState===1) { try {await Promise.race([call('Browser.close'),delay(3000)]);} catch {} socket.close(); }
  if(chrome.exitCode===null) chrome.kill('SIGTERM');
  server.kill('SIGTERM');
}
if(result.status==='failed') process.exitCode=1;
