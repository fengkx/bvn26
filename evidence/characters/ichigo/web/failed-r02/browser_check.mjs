// Programmatic input against an isolated local export; no runtime state writes.
import {writeFile, readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const folder = new URL('./', import.meta.url);
const [debugPort, port] = process.argv.slice(2);
const pages = await fetch(`http://127.0.0.1:${debugPort}/json/list`).then(r => r.json());
const target = pages.find(p => p.type === 'page');
assert(target, 'Dedicated test page missing');
const socket = new WebSocket(target.webSocketDebuggerUrl);
const pending = new Map(), messages = [], exceptions = [];
let sequence = 0;
socket.addEventListener('message', event => {
  const msg = JSON.parse(event.data);
  if (pending.has(msg.id)) {
    const {resolve, reject} = pending.get(msg.id); pending.delete(msg.id);
    if (msg.error) reject(new Error(JSON.stringify(msg.error))); else resolve(msg.result);
  } else if (msg.method === 'Runtime.consoleAPICalled') {
    messages.push(msg.params.args.map(x => x.value ?? x.description).join(' '));
  } else if (msg.method === 'Runtime.exceptionThrown') {
    exceptions.push(msg.params.exceptionDetails);
  }
});
await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
function call(method, params={}) { return new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));}); }
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
async function evaluate(expression) {const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
const keys={s:['s','KeyS',83],a:['a','KeyA',65],j:['j','KeyJ',74],k:['k','KeyK',75],n:['1','Numpad1',97]};
async function key(name) {const [key,code,windowsVirtualKeyCode]=keys[name];await call('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode});await delay(160);await call('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode});await delay(220);}
async function screenshot(name) {const r=await call('Page.captureScreenshot',{format:'png'});await writeFile(new URL(name+'.png',folder),Buffer.from(r.data,'base64'));}
async function snapshot() {return await evaluate(`(async()=>{let resolve;const result=new Promise(r=>resolve=r);const original=URL.createObjectURL;const click=HTMLAnchorElement.prototype.click;URL.createObjectURL=blob=>{blob.text().then(text=>resolve(JSON.parse(text)));return 'blob:ichigo-test';};HTMLAnchorElement.prototype.click=function(){};try{document.getElementById('download').click();return await result;}finally{URL.createObjectURL=original;HTMLAnchorElement.prototype.click=click;}})()`);}
async function waitSnapshot(predicate, name) {
  const deadline=Date.now()+90000;
  let report;
  while(Date.now()<deadline) {report=await snapshot();if(predicate(report)){await writeFile(new URL(name+'.json',folder),JSON.stringify(report,null,2));return report;}await delay(1000);}
  await writeFile(new URL(name+'-failed.json',folder),JSON.stringify(report,null,2));
  throw new Error('Snapshot condition timed out: '+name);
}
const actor = report => report.runtime.snapshot?.match?.players?.p1;
try {
  await call('Runtime.enable');await call('Page.enable');
  await call('Page.bringToFront');
  await call('Emulation.setDeviceMetricsOverride',{width:1100,height:850,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:`http://127.0.0.1:${port}/`});
  const deadline=Date.now()+90000;
  while(!messages.some(x=>x.startsWith('M0_BOOT_OK'))){assert(Date.now()<deadline,'Boot timeout');await delay(500);}
  await call('Page.bringToFront');
  await evaluate('document.querySelector("canvas").focus()');
  const rect=await evaluate('(()=>{const r=document.querySelector("canvas").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()');
  await call('Input.dispatchMouseEvent',{type:'mousePressed',...rect,button:'left',clickCount:1});
  await call('Input.dispatchMouseEvent',{type:'mouseReleased',...rect,button:'left',clickCount:1});
  // Source menu controller is placed at frame 63; boot alone is not menu readiness.
  await delay(6000);
  await screenshot('menu-ready');
  for(const k of ['s','s','j'])await key(k);
  await delay(1600);
  // Source SelectionGrid: from (5,7), four left moves then down wrap -> (-1,-2).
  for(const k of ['a','a','a','a','s'])await key(k);
  await delay(1200);await screenshot('selection');
  for(const k of ['j','n'])await key(k);await delay(1400);
  for(const k of ['j','n'])await key(k);await delay(1400);
  await key('j');
  const before=await waitSnapshot(r=>actor(r)?.resourcePath==='res://generated/fighters/ichigo' && actor(r)?.energy===300 && actor(r)?.action==='站立','before-transform');
  await screenshot('before-transform');
  await Promise.all(['j','k'].map(name=>{const [key,code,windowsVirtualKeyCode]=keys[name];return call('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode});}));
  await delay(500);
  for(const name of ['j','k']) {const [key,code,windowsVirtualKeyCode]=keys[name];await call('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode});}
  const after=await waitSnapshot(r=>actor(r)?.resourcePath==='res://generated/forms/ichigo-2' && actor(r)?.action==='站立' && !r.runtime.snapshot.match.pause.globalSuperPaused,'after-transform');
  await screenshot('after-transform');
  const drained=await waitSnapshot(r=>actor(r)?.resourcePath==='res://generated/forms/ichigo-2' && actor(r)?.hp<1000,'hp-drain');
  await key('k');
  const jumping=await waitSnapshot(r=>actor(r)?.resourcePath==='res://generated/forms/ichigo-2' && actor(r)?.sourceFrame>=36 && actor(r)?.sourceFrame<=122,'form-jump');
  await screenshot('form-jump');
  const metadata=JSON.parse(await readFile(new URL('build-metadata.json',folder)));
  assert.equal(after.build.buildID,metadata.buildID);
  assert.equal(after.build.pckSha256,metadata.pckSha256);
  assert.equal(exceptions.length,0,'Browser runtime exception');
  assert(!messages.some(line=>/SCRIPT ERROR|Parse Error|No loader found/.test(line)),'Browser script/resource error');
  await writeFile(new URL('browser-check.json',folder),JSON.stringify({status:'observed_pass',build:after.build,browser:await evaluate('navigator.userAgent'),url:`http://127.0.0.1:${port}/`,input:'Programmatic browser keys, not physical OS-input proof',before:actor(before),after:actor(after),drained:actor(drained),jumping:actor(jumping),pause:after.runtime.snapshot.match.pause,production_admitted:false,native_parity_proven:false,oracle_accepted:false,certified_global_tick:false,os_input_join_proven:false,native_initialization_complete:false},null,2));
  console.log('ICHIGO_WEB_TRANSFORMATION_OK');
} finally {
  await writeFile(new URL('console.json',folder),JSON.stringify(messages,null,2));
  await writeFile(new URL('exceptions.json',folder),JSON.stringify(exceptions,null,2));
  socket.close();
}
