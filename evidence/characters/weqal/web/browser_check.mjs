// Local headed export check using the repository's Chromium test transport.
import {writeFile} from 'node:fs/promises';
const folder = new URL('./', import.meta.url);
const pages = await fetch('http://127.0.0.1:58720/json/list').then(r => r.json());
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
  await delay(180);
}
const keys={s:['s','KeyS',83],w:['w','KeyW',87],a:['a','KeyA',65],j:['j','KeyJ',74],n:['1','Numpad1',97]};
await call('Runtime.enable'); await call('Page.enable');
await call('Emulation.setDeviceMetricsOverride',{width:1100,height:850,deviceScaleFactor:1,mobile:false});
const mode=process.argv[2];
try {
  if(mode==='boot') {
    await call('Page.navigate',{url:'http://127.0.0.1:58719/'});
    const deadline=Date.now()+60000;
    while(!messages.some(x=>x.startsWith('M0_BOOT_OK'))) { if(Date.now()>deadline)throw new Error('Boot timeout');await delay(500); }
    await evaluate('document.querySelector("canvas").focus()');
  } else if(mode==='select') {
    for(const k of ['s','s','j'])await key(...keys[k]);
    await delay(1600);
    for(const k of ['a','a','a','a','w','w'])await key(...keys[k]);
  } else if(mode==='confirm') {
    for(const k of ['j','n'])await key(...keys[k]);await delay(1400);
    for(const k of ['j','n'])await key(...keys[k]);await delay(1400);
    await key(...keys.j);await delay(1500);
  } else if(mode==='transform') {
    await evaluate('document.querySelector("canvas").focus()');
    await Promise.all([
      call('Input.dispatchKeyEvent',{type:'keyDown',key:'j',code:'KeyJ',windowsVirtualKeyCode:74}),
      call('Input.dispatchKeyEvent',{type:'keyDown',key:'k',code:'KeyK',windowsVirtualKeyCode:75})
    ]);
    await delay(500);
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'j',code:'KeyJ',windowsVirtualKeyCode:74});
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'k',code:'KeyK',windowsVirtualKeyCode:75});
    await delay(9000);
  } else if(mode==='snapshot') {
    const report = await evaluate(`(async()=>{let resolve;const result=new Promise(r=>resolve=r);const original=URL.createObjectURL;const click=HTMLAnchorElement.prototype.click;URL.createObjectURL=blob=>{blob.text().then(text=>resolve(JSON.parse(text)));return 'blob:weqal-test';};HTMLAnchorElement.prototype.click=function(){};try{document.getElementById('download').click();return await result;}finally{URL.createObjectURL=original;HTMLAnchorElement.prototype.click=click;}})()`);
    await writeFile(new URL('browser-diagnostic.json',folder),JSON.stringify(report,null,2));
    console.log(JSON.stringify({build:report.build,scene:report.runtime.snapshot?.match?.modeName,players:report.runtime.snapshot?.match?.players,pause:report.runtime.snapshot?.match?.pause}));
  }
  const shot=await call('Page.captureScreenshot',{format:'png'});
  await writeFile(new URL(`browser-${mode}.png`,folder),Buffer.from(shot.data,'base64'));
  await writeFile(new URL(`browser-${mode}-console.json`,folder),JSON.stringify(messages,null,2));
  console.log('BROWSER_STEP_OK',mode);
} finally {socket.close();}
