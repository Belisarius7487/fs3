// endsim.js - can every written mission still END?
//
//   node endsim.js hlp_shooter_vNNN_logic.html
//
// A mission ends when nothing holds the wave open any more (60_effects.js):
// no queue, no live threat, nothing crossing, no event pending, no escort
// pending, no mission clock running, nothing left to scan. Three of those
// can be nailed shut by the DATA of a mission rather than by what the
// player does, and then the mission runs for ever:
//
//   1  a holding event (einwarpen / seite) whose trigger names a unit the
//      mission never puts in the field. evPending() only lets such an event
//      go when the unit HAS been seen and is gone (evSeen && byId empty);
//      a unit that never existed was never seen, so the event stays pending
//      for ever. One mistyped id is enough.
//   2  reinforcements switched on and never switched off. They are not an
//      event - evReinf keeps queueing wings - so liveThreatCount() never
//      reaches zero. This is F13: in M68 a lostMax guard sat on all three
//      events that switch them off and the mission had no end at all.
//   3  a mission clock started and never stopped. missionTimerLeft() gives
//      0 once it has run out, and the wave end asks for < 0, so an expired
//      clock holds the wave just as a running one does.
//
// Everything is read out of the logic file: SCRIPT_WAVES, the trigger list
// with the triggers that work on an id, the effect list, and
// EV_LOST_GUARDS. Nothing here is a copy of the game's logic, so the stage
// cannot drift away from it. No browser - 100 missions in a second.
const fs = require('fs');
const html = fs.readFileSync(process.argv[2] || 'hlp_shooter_v235_logic.html', 'utf8');
const src = html.match(/<script[^>]*>([\s\S]*)<\/script>/)[1];

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
const SCRIPT_WAVES = eval('(' + body('const SCRIPT_WAVES =').replace(/^const SCRIPT_WAVES =\s*/, '') + ')');
const EV_LOST_GUARDS = eval('(' + body('const EV_LOST_GUARDS =').replace(/^const EV_LOST_GUARDS =\s*/, '') + ')');

// Which triggers work on a unit's id? Taken from evTrig itself: a case that
// asks byId() or evSeen() is about a unit, one that does not is not. Read
// rather than listed, so a new trigger is classified without touching this
// file.
const trigBody = body('function evTrig(');
const ID_TRIG = new Set(), ALL_TRIG = new Set();
{
  const parts = trigBody.split(/case\s+'(\w+)'\s*:/);
  for(let i = 1; i < parts.length; i += 2){
    const name = parts[i], code = parts[i+1] || '';
    ALL_TRIG.add(name);
    if(/\bbyId\(|\bevSeen\(/.test(code)) ID_TRIG.add(name);
  }
}
// The effects that hold the wave open while they are pending, straight out
// of evPending(): it walks EV and only keeps going for these.
const pendBody = body('function evPending(');
const HOLDING = new Set();
for(const m of pendBody.matchAll(/e\.w\s*!==\s*'(\w+)'/g)) HOLDING.add(m[1]);
// Which effects switch the reinforcements off, and which clear the clock?
// Read out of evFire's own case bodies, not listed here. The first cut of
// this stage listed them by hand, forgot 'ende' - which does
// evReinf = false just as 'abzug' does - and reported M35, M45 and M50 as
// endless when all three end on 'ende'. A list written by hand is a list
// that goes stale.
const fireBody = body('function evFire(');
const REINF_OFF = new Set(), TIMER_OFF = new Set(), REINF_ANY = new Set();
{
  const parts = fireBody.split(/case\s+'(\w+)'\s*:/);
  for(let i = 1; i < parts.length; i += 2){
    const name = parts[i], code = (parts[i+1] || '').split(/case\s+'/)[0];
    if(/evReinf\s*=/.test(code)) REINF_ANY.add(name);
    if(/evReinf\s*=\s*false/.test(code)) REINF_OFF.add(name);
    if(/missionTimer\s*=\s*\{\s*end\s*:\s*0/.test(code)) TIMER_OFF.add(name);
  }
}
// 'nachschub' is the one that does both: evReinf = (arg !== 'aus').
const switchesReinfOff = (e) => REINF_OFF.has(e.w) ||
                                (REINF_ANY.has(e.w) && e.a2 === 'aus');
const RELEASING = [...new Set([...REINF_OFF, ...TIMER_OFF])];

const evIds = a => String(a == null ? '' : a).split('+');
let bad = 0, checked = 0;
const say = (m, txt) => { bad++; console.log('  M' + String(m).padStart(2, '0') + '  ' + txt); };

console.log('endsim: ' + (process.argv[2] || '') +
            '\n  triggers that work on an id: ' + [...ID_TRIG].sort().join(', ') +
            '\n  holds the wave open: ' + [...HOLDING].sort().join(', ') +
            '\n  the lostMax guard applies to: ' + Object.keys(EV_LOST_GUARDS).sort().join(', ') +
            '\n  switches reinforcements off: ' + [...REINF_OFF].sort().join(', ') +
            '\n  clears the clock: ' + [...TIMER_OFF].sort().join(', ') + '\n');

// R0, at the source: a lostMax guard may never sit on an effect that lets
// the wave go. That is exactly what F13 was.
for(const w of RELEASING)
  if(EV_LOST_GUARDS[w])
    { bad++; console.log("  SOURCE  EV_LOST_GUARDS holds '" + w + "' - a lostMax guard can then shut a mission's end for good (F13)"); }

for(const key of Object.keys(SCRIPT_WAVES).sort((a, b) => a - b)){
  const m = SCRIPT_WAVES[key], units = m.u || [], evs = m.ev || [];
  checked++;
  const ids = new Set(units.map(u => u.id).filter(Boolean));
  // Can this event ever fire, as far as the data can tell?
  const reachable = (e) => {
    if(!ID_TRIG.has(e.t)) return true;              // time, clock, counters
    return evIds(e.a).every(id => ids.has(id));
  };
  // 1  a holding event that can never fire
  for(const e of evs){
    if(!HOLDING.has(e.w)) continue;
    if(reachable(e)) continue;
    const miss = evIds(e.a).filter(id => !ids.has(id));
    say(key, "pending for ever: '" + e.w + "' waits for " + e.t + " of " +
             miss.join('+') + ", and no unit of the mission carries that id");
  }
  // 2  reinforcements on and never off
  const on  = evs.some(e => REINF_ANY.has(e.w) && e.a2 !== 'aus' && !REINF_OFF.has(e.w));
  if(on){
    const offs = evs.filter(switchesReinfOff);
    const good = offs.filter(e => reachable(e) && !EV_LOST_GUARDS[e.w]);
    if(!offs.length)
      say(key, 'switches reinforcements on and never off - the stream of enemies never ends');
    else if(!good.length)
      say(key, 'switches reinforcements on, and every event that switches them off cannot fire: ' +
               offs.map(e => e.w + '/' + e.t + ' ' + (e.a == null ? '' : e.a)).join(', '));
  }
  // 3  a clock started and never stopped
  if(evs.some(e => e.w === 'timer')){
    const stop = evs.filter(e => TIMER_OFF.has(e.w) && reachable(e) && !EV_LOST_GUARDS[e.w]);
    if(!stop.length)
      say(key, 'starts a clock and never stops it - an expired clock holds the wave just as a running one does');
  }
}
console.log('\n' + checked + ' missions checked, ' + (bad ? bad + ' findings' : 'every one can end'));
process.exit(bad ? 1 : 0);
