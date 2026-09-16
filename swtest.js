// Mission data test. Rebuilt in v102 from the handoff description, the
// original file was lost. Reads SCRIPT_WAVES and the known triggers,
// effects and categories straight out of the logic file, so it can never
// drift from what the game actually accepts.
// Usage: node swtest.js hlp_shooter_v102_logic.html
const fs = require('fs');
const html = fs.readFileSync(process.argv[2] || 'hlp_shooter_v102_logic.html', 'utf8');
const src = html.match(/<script[^>]*>([\s\S]*)<\/script>/)[1];

// Brace matching that skips strings and comments.
function blockEnd(from){
  let i = src.indexOf('{', from), d = 0;
  for(; i < src.length; i++){
    const ch = src[i], nx = src[i+1];
    if(ch === '/' && nx === '/'){ i = src.indexOf('\n', i); continue; }
    if(ch === '/' && nx === '*'){ i = src.indexOf('*/', i) + 1; continue; }
    if(ch === '"' || ch === "'" || ch === '`'){
      const q = ch; i++;
      while(src[i] !== q){ if(src[i] === '\\') i++; i++; }
      continue;
    }
    if(ch === '{') d++;
    else if(ch === '}'){ d--; if(d === 0) return i + 1; }
  }
  throw new Error('unbalanced at ' + from);
}
function body(head){
  const at = src.indexOf(head);
  if(at < 0) throw new Error('missing: ' + head);
  return src.slice(at, blockEnd(at));
}
const casesOf = txt => new Set([...txt.matchAll(/case\s+'(\w+)'/g)].map(m => m[1]));

const TRIGGERS = casesOf(body('function evTrig('));
const EFFECTS  = casesOf(body('function evFire('));
const CAT_FIX  = eval('(' + body('const CAT_FIX =').replace(/^const CAT_FIX =\s*/, '') + ')');
const CAT_FAC  = eval('(' + body('const CAT_FAC =').replace(/^const CAT_FAC =\s*/, '') + ')');
const W = 800, H = 500, HUD_H = 44, TICK_HZ = 100;
const SCRIPT_WAVES = eval('(' + body('const SCRIPT_WAVES =').replace(/^const SCRIPT_WAVES =\s*/, '') + ')');

// Triggers without a unit as target, and effects whose argument is a unit.
const TRIG_NO_ID  = new Set(['sek', 'erfuellt']);
const EFFECT_UNIT = new Set(['einwarpen', 'seite', 'raus', 'heilen']);

let errors = 0, missions = 0;
for(const key of Object.keys(SCRIPT_WAVES).sort((a, b) => a - b)){
  const m = SCRIPT_WAVES[key], units = m.u || [], evs = m.ev || [];
  const tag = 'M' + String(key).padStart(3, '0');
  const ids = new Map();
  const bad = [];
  missions++;

  for(const u of units){
    if(!u.id) bad.push('unit without id (' + u.c + ')');
    else if(ids.has(u.id)) bad.push('id used twice: ' + u.id);
    ids.set(u.id, u);
    if(!CAT_FAC[u.c] && !CAT_FIX[u.c])
      bad.push(u.id + ': unknown category "' + u.c + '" - would never spawn');
  }
  for(const u of units){
    if(u.dockTo && !ids.has(u.dockTo)) bad.push(u.id + ': dockTo points at missing id ' + u.dockTo);
    if(u.at && !ids.has(u.at))         bad.push(u.id + ': at points at missing id ' + u.at);
  }

  const warpedIn = new Set();
  let reinfOn = false, reinfOff = false;
  evs.forEach((e, i) => {
    const where = 'event ' + (i + 1) + ' (' + e.t + ' -> ' + e.w + ')';
    const arg = (e.a2 !== undefined) ? e.a2 : e.a;
    if(!TRIGGERS.has(e.t)) bad.push(where + ': unknown trigger "' + e.t + '"');
    if(!EFFECTS.has(e.w))  bad.push(where + ': unknown effect "' + e.w + '"');
    if(TRIGGERS.has(e.t) && !TRIG_NO_ID.has(e.t) && !ids.has(e.a))
      bad.push(where + ': trigger points at missing id ' + e.a);
    if(e.t === 'angedockt' && ids.has(e.a) && !ids.get(e.a).dockTo)
      bad.push(where + ': ' + e.a + ' has no dockTo, it can never dock');
    if(EFFECT_UNIT.has(e.w) && !ids.has(arg))
      bad.push(where + ': effect points at missing id ' + arg);
    if(e.w === 'jagd' && arg && !ids.has(arg))
      bad.push(where + ': hunt target is a missing id ' + arg);
    if(e.w === 'einwarpen'){
      warpedIn.add(arg);
      if(ids.has(arg) && !ids.get(arg).wait)
        bad.push(where + ': ' + arg + ' is not waiting - warping it in does nothing');
    }
    if(e.w === 'nachschub'){ if(arg === 'aus') reinfOff = true; else reinfOn = true; }
    if(e.w === 'ende') reinfOff = true;
  });
  for(const u of units)
    if(u.wait && !warpedIn.has(u.id)) bad.push(u.id + ': waits, but no event ever warps it in');
  if(reinfOn && !reinfOff) bad.push('reinforcements switched on, never switched off');
  if(m.hunt && !ids.has(m.hunt)) bad.push('hunt points at missing id ' + m.hunt);

  if(bad.length){ errors += bad.length; console.log(tag + ' ' + (m.name || '')); bad.forEach(b => console.log('   ' + b)); }
}
console.log('\n' + missions + ' missions checked, ' + errors + ' problems');
console.log('known triggers: ' + [...TRIGGERS].join(' '));
console.log('known effects:  ' + [...EFFECTS].join(' '));
process.exit(errors ? 1 : 0);
