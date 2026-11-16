// Local isolated headless export check using the repository's Chromium test transport.
import {writeFile} from 'node:fs/promises';
const folder = new URL(process.env.BVN_WEB_OUTPUT || './', import.meta.url);
const pages = await fetch('http://127.0.0.1:58731/json/list').then(r => r.json());
const target = pages.find(p => p.type === 'page');
if (!target) throw new Error('Dedicated test page missing');
const socket = new WebSocket(target.webSocketDebuggerUrl);
const pending = new Map();
const messages = [];
let sequence = 0;
socket.addEventListener('message', event => {
  const msg = JSON.parse(event.data);
  if (pending.has(msg.id)) {
    const {resolve, reject} = pending.get(msg.id); pending.delete(msg.id);
    if (msg.error) reject(new Error(JSON.stringify(msg.error))); else resolve(msg.result);
  } else if (msg.method === 'Runtime.consoleAPICalled') {
    messages.push(msg.params.args.map(x => x.value ?? x.description).join(' '));
  }
});
await new Promise((resolve, reject) => {socket.addEventListener('open', resolve, {once:true});socket.addEventListener('error', reject, {once:true});});
function call(method, params={}) { return new Promise((resolve,reject) => { const id=++sequence; pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));}); }
const delay = ms => new Promise(resolve => setTimeout(resolve,ms));
async function evaluate(expression) {const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function key(key, code, virtualKey) {
  await call('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode:virtualKey});
  await delay(100);
  await call('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode:virtualKey});
  await delay(800);
}
const keys={d:['d','KeyD',68],s:['s','KeyS',83],w:['w','KeyW',87],a:['a','KeyA',65],j:['j','KeyJ',74],n:['1','Numpad1',97]};
await call('Runtime.enable'); await call('Page.enable');
await call('Network.enable');
await call('Network.setCacheDisabled',{cacheDisabled:true});
await call('Emulation.setDeviceMetricsOverride',{width:1100,height:850,deviceScaleFactor:1,mobile:false});
const mode=process.argv[2];
await call('Page.bringToFront');
await call('Emulation.setFocusEmulationEnabled',{enabled:true});
try {
  if(mode==='key') {
    await evaluate('document.querySelector("canvas").focus()');
    await delay(1500);
    await key(...keys[process.argv[3]]);
    await delay(Number(process.env.BVN_WEB_SETTLE_MS || 3000));
  } else if(mode==='boot') {
    await call('Page.navigate',{url:'http://127.0.0.1:58730/?temari-r25'});
    messages.length=0;
    const deadline=Date.now()+180000;
    while(!messages.some(x=>x.startsWith('M0_BOOT_OK'))) { if(Date.now()>deadline)throw new Error('Boot timeout');await delay(500); }
    await delay(10000);
    await evaluate('document.querySelector("canvas").focus()');
  } else if(mode==='select') {
    await call('Input.dispatchMouseEvent',{type:'mousePressed',x:500,y:400,button:'left',clickCount:1});
    await call('Input.dispatchMouseEvent',{type:'mouseReleased',x:500,y:400,button:'left',clickCount:1});
    await delay(1000);
    for(const k of ['s','s','j'])await key(...keys[k]);
    await delay(10000);
    for(const k of ['d','d','w'])await key(...keys[k]);
  } else if(mode==='confirm') {
    for(const k of ['j','n'])await key(...keys[k]);await delay(1400);
    for(const k of ['j','n'])await key(...keys[k]);await delay(1400);
    await key(...keys.j);await delay(1500);
  } else if(mode==='charge') {
    await evaluate('document.querySelector("canvas").focus()');
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'o',code:'KeyO',windowsVirtualKeyCode:79});
    await delay(8000);
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'o',code:'KeyO',windowsVirtualKeyCode:79});
  } else if(mode==='super') {
    await evaluate('document.querySelector("canvas").focus()');
    await delay(1500);
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'i',code:'KeyI',windowsVirtualKeyCode:73});
    await delay(12000);
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'i',code:'KeyI',windowsVirtualKeyCode:73});
    await delay(3000);
  } else if(mode==='snapshot') {
    const report = await evaluate(`(async()=>{let resolve;const result=new Promise(r=>resolve=r);const original=URL.createObjectURL;const click=HTMLAnchorElement.prototype.click;URL.createObjectURL=blob=>{blob.text().then(text=>resolve(JSON.parse(text)));return 'blob:shouju-test';};HTMLAnchorElement.prototype.click=function(){};try{document.getElementById('download').click();return await result;}finally{URL.createObjectURL=original;HTMLAnchorElement.prototype.click=click;}})()`);
    await writeFile(new URL('browser-diagnostic.json',folder),JSON.stringify(report,null,2));
    console.log(JSON.stringify({build:report.build,scene:report.runtime.snapshot?.match?.modeName,players:report.runtime.snapshot?.match?.players,pause:report.runtime.snapshot?.match?.pause}));
  }
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(new URL(`browser-${mode}.png`,folder),Buffer.from(shot.data,'base64'));
  await writeFile(new URL(`browser-${mode}-console.json`,folder),JSON.stringify(messages,null,2));
  console.log('BROWSER_STEP_OK',mode);
} finally {socket.close();}
