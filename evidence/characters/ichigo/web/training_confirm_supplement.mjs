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
async function key(name) {const [key,code,windowsVirtualKeyCode]=keys[name];await call('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode});await delay(160);await call('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode});await delay(1000);}
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
// The training menu uses P1 confirm for both fighters and both helpers.
// Supplement the first runner's three confirms without changing runtime state.
try {
  await delay(20000);
  await screenshot('training-helper-confirm');
  await key('j'); await delay(4000);
  await key('j'); await delay(4000);
  await screenshot('training-entered');
  console.log('TRAINING_CONFIRM_SUPPLEMENT_COMPLETE');
} finally {socket.close();}
