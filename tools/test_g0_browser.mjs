#!/usr/bin/env node
// Use a dedicated Chromium debugging endpoint, never an existing user session.
import {writeFile} from 'node:fs/promises';
const [endpoint, url, output] = process.argv.slice(2);
if (!endpoint || !url || !output) throw new Error('Usage: node tools/test_g0_browser.mjs ENDPOINT URL REPORT');
const targets = await (await fetch(`${endpoint}/json/list`)).json();
const target = targets.find(x => x.type === 'page');
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve => socket.addEventListener('open', resolve, {once:true}));
let id = 0, loaded = false;
const calls = new Map(), errors = [];
socket.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (message.method === 'Page.loadEventFired') loaded = true;
  if (message.id) { const pending = calls.get(message.id); calls.delete(message.id); message.error ? pending.reject(message.error) : pending.resolve(message.result); }
  if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
  if (message.method === 'Runtime.consoleAPICalled') {
    const text = message.params.args.map(x => x.value ?? x.description ?? '').join(' ');
    if (message.params.type === 'error' || /SCRIPT ERROR|Parse Error|Assertion failed/.test(text)) errors.push(text);
  }
});
function send(method, params = {}) { return new Promise((resolve,reject) => { calls.set(++id,{resolve,reject}); socket.send(JSON.stringify({id,method,params})); }); }
async function evaluate(expression) { return (await send('Runtime.evaluate',{expression,returnByValue:true})).result.value; }
try {
  await send('Runtime.enable'); await send('Page.enable');
  await send('Network.enable'); await send('Network.setCacheDisabled', {cacheDisabled:true});
  await send('Emulation.setDeviceMetricsOverride', {width:800,height:650,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate', {url});
  const deadline = Date.now()+180000;
  let started = false, report;
  while (Date.now() < deadline) {
    if (loaded && !started && await evaluate("document.readyState === 'complete' && typeof g0 !== 'undefined'")) {
      await send('Runtime.evaluate', {expression:"document.querySelector('#start').click()",userGesture:true}); started = true;
    }
    if (started) report = await evaluate("typeof g0 !== 'undefined' && g0.report");
    if (report) break;
    if (errors.length) throw new Error(JSON.stringify(errors));
    await new Promise(resolve=>setTimeout(resolve,1000));
  }
  if (!report) throw new Error('Timed out: '+await evaluate("document.querySelector('#status')?.textContent"));
  if (errors.length) throw new Error(JSON.stringify(errors));
  const ticks = report.samples.flatMap(row => row.ticks);
  if (ticks.length !== 900 || !ticks.some(t => t.advance_total_us > 0) || !ticks.some(t => t.materialize_in_advance_us > 0)) throw new Error('Missing workload/timing coverage');
  if (!ticks.some(t => t.super_active)) throw new Error('Heavy-effect workload did not enter a super');
  report.dry_run = 'headless Chromium on development machine; not-a-pass';
  await writeFile(output, JSON.stringify(report));
  console.log(JSON.stringify({g0_passed:false,submits:report.samples.length,report:output}));
} finally { socket.close(); }
