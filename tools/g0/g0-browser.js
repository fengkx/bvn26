/* Browser clocks are separate from Godot ticks. Never subtract their epochs. */
const g0 = (() => {
  const frames = [], longTasks = [], invalidations = [];
  let active = false, previous = null, request, observer;
  const environment = () => ({userAgent: navigator.userAgent, dpr: devicePixelRatio,
    canvas: [canvas.width, canvas.height], css: [canvas.clientWidth, canvas.clientHeight],
    hardwareConcurrency: navigator.hardwareConcurrency, visibility: document.visibilityState});
  function raf(now) {
    if (!active) return;
    if (previous !== null) frames.push({end_ms: now, interval_ms: now - previous, long_stall: now - previous > 100});
    previous = now;
    request = requestAnimationFrame(raf);
  }
  document.addEventListener('visibilitychange', () => { if (active) invalidations.push('visibility_changed'); });
  window.addEventListener('resize', () => { if (active) invalidations.push('resized'); });
  return {
    start() {
      this.initial = environment(); active = true; request = requestAnimationFrame(raf);
      if (PerformanceObserver.supportedEntryTypes.includes('longtask')) {
        observer = new PerformanceObserver(list => longTasks.push(...list.getEntries().map(x => ({start_ms:x.startTime,duration_ms:x.duration}))));
        observer.observe({type:'longtask'});
      }
    },
    async finish(report) {
      active = false; cancelAnimationFrame(request);
      if (observer) { longTasks.push(...observer.takeRecords().map(x => ({start_ms:x.startTime,duration_ms:x.duration}))); observer.disconnect(); }
      const identity = await (await fetch('g0-identity.json')).json();
      const artifacts = await (await fetch('g0-artifacts.json')).json();
      Object.assign(report, {identity, artifacts, browser: this.initial, browser_end: environment(),
        invalidations, raf_frames: frames, long_tasks: observer ? longTasks : 'UNKNOWN',
        input_baseline: 'offline sampled-input to corresponding frame_post_draw; not OS event latency, causal action latency, GPU completion or photons'});
      this.report = report;
      document.querySelector('#status').textContent = `Complete: ${report.samples.length} submits. G0 NOT PASSED. Invalidations: ${invalidations.join(', ') || 'none'}`;
      document.querySelector('#save').disabled = false;
      document.querySelector('#save').onclick = () => {
        const url = URL.createObjectURL(new Blob([JSON.stringify(report)], {type:'application/json'}));
        const link = document.createElement('a'); link.href = url; link.download = 'g0-not-a-pass.json'; link.click(); URL.revokeObjectURL(url);
      };
    }
  };
})();
// Fixed audio policy and local diagnostic sink; this shell has no online controls.
window.bvnRegisterAudioSettings = callback => callback(1.0, false);
window.bvnUnregisterAudioSettings = () => {};
window.bvnAudioSettingsApplied = () => {};
window.bvnDiagnosticsRegister = () => {};
window.bvnDiagnosticsUnregister = () => {};
window.bvnDiagnosticsPush = () => {};
window.bvnDiagnosticsSetSnapshot = () => {};
