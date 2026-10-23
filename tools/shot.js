// Headless screenshot from the game itself (not part of the game).
// node tools/shot.js <logic.html> <query> <out.png> <setup.js> [WxH] [clip x,y,w,h]
// setup.js runs in the page after launchGame() with the fieldsim helpers
// (FS.fakeImages, FS.step, FS.until); it may be async. Ships are grey
// stand-ins: the models come from the server and are not served here.
const fs = require('fs'), path = require('path'), os = require('os');
const { chromium } = require('playwright');
const [logic, query, out, setup, size, clip] = process.argv.slice(2);
let html = fs.readFileSync(logic, 'utf8');
const M = fs.readFileSync(path.join(__dirname, '..', 'hlp_mounts_final.json'), 'utf8');
html = html.replace(/<script([^>]*)>/, '<script$1>\nconst MOUNTS=' + JSON.stringify(JSON.parse(M)) + ';\n');
const tmp = path.join(os.tmpdir(), 'shot_' + process.pid + '.html');
fs.writeFileSync(tmp, html);
// the helpers of fieldsim.js, taken from there so both stay the same
const fsrc = fs.readFileSync(path.join(__dirname, '..', 'fieldsim.js'), 'utf8');
const HELPERS = fsrc.slice(fsrc.indexOf('const HELPERS = `') + 17, fsrc.indexOf('};`;', fsrc.indexOf('const HELPERS')) + 2);
(async () => {
  const [vw, vh] = (size || '1280x720').split('x').map(Number);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: vw, height: vh } });
  const errs = [];
  page.on('pageerror', e => errs.push(String(e.message || e)));
  await page.goto('file://' + tmp + '?' + query);
  await page.waitForTimeout(300);
  await page.evaluate(HELPERS + '\nFS.fakeImages(); launchGame();\n(async function(){' + fs.readFileSync(setup, 'utf8') + '})()');
  await page.waitForTimeout(200);
  const opt = { path: out };
  if (clip) { const [x, y, w, h] = clip.split(',').map(Number); opt.clip = { x, y, width: w, height: h }; }
  await page.screenshot(opt);
  if (errs.length) console.log('page errors:\n  ' + errs.slice(0, 4).join('\n  '));
  await browser.close(); fs.unlinkSync(tmp);
})();
