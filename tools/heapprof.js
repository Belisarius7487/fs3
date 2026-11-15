// Sampling heap profile of the game in a headless browser (not part of the game).
// node tools/heapprof.js <logic.html> <query> [warm ticks] [ticks]
// e.g. node tools/heapprof.js hlp_shooter_v287_logic.html m=6 600 600
// Lists where the game allocates memory (function:line in the logic file <- callers).
// Ships are grey stand-ins here, so the 3D drawing is not measured.
const fs = require('fs'), path = require('path'), os = require('os');
const R = path.join(__dirname, '..');
const { chromium } = require('playwright');
const [logic, query, warm, frames] = process.argv.slice(2);
let html = fs.readFileSync(logic, 'utf8');
html = html.replace(/<script([^>]*)>/, '<script$1>\nconst MOUNTS=' + JSON.stringify(JSON.parse(fs.readFileSync(R + '/hlp_mounts_final.json', 'utf8'))) + ';\n');
html = html.replace(/<script([^>]*)>/, '<script$1>\nconst OUTLINES=' + JSON.stringify(JSON.parse(fs.readFileSync(R + '/hlp_outlines.json', 'utf8'))) + ';\n');
const tmp = path.join(os.tmpdir(), 'prof_' + process.pid + '.html'); fs.writeFileSync(tmp, html);
const fsrc = fs.readFileSync(R + '/fieldsim.js', 'utf8');
const HELPERS = fsrc.slice(fsrc.indexOf('const HELPERS = `') + 17, fsrc.indexOf('};`;', fsrc.indexOf('const HELPERS')) + 2);
(async () => {
  const browser = await chromium.launch(); const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto('file://' + tmp + '?' + query); await page.waitForTimeout(300);
  await page.evaluate(HELPERS + '\nwindow.FS=FS; FS.fakeImages(); launchGame(); FS.step(' + (warm||600) + ');');
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('HeapProfiler.enable');
  await cdp.send('HeapProfiler.startSampling', { samplingInterval: 2048, includeObjectsCollectedByMajorGC: true, includeObjectsCollectedByMinorGC: true });
  const t = await page.evaluate('(function(){const a=performance.now(); for(let i=0;i<' + (frames||600) + ';i++){ player.hp=player.maxHp; update(); if(i%2===0) draw(); } return [performance.now()-a, enemies.length];})()');
  const { profile } = await cdp.send('HeapProfiler.stopSampling');
  const agg = {}; let total = 0;
  (function walk(n, stack){ const cf = n.callFrame; const name = (cf.functionName || '(anon)') + ':' + (cf.lineNumber+1);
    const s = stack.concat(cf.functionName || '(anon)');
    if (n.selfSize) { total += n.selfSize; const k = name + '  <- ' + s.slice(-4, -1).reverse().join(' < '); agg[k] = (agg[k]||0) + n.selfSize; }
    for (const c of n.children) walk(c, s); })(profile.head, []);
  console.log('frames', frames, 'ms', Math.round(t[0]), 'enemies', t[1], 'sampled MB', (total/1048576).toFixed(1));
  Object.entries(agg).sort((a,b)=>b[1]-a[1]).slice(0, 30).forEach(([k,v]) => console.log((v/1048576).toFixed(2).padStart(7), k));
  await browser.close(); fs.unlinkSync(tmp);
})();
