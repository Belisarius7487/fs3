// GLSL precision test (v286, F102). The 3D hull shader must ask the card
// for 32-bit floats wherever it has them. On a card that gives the shader
// real 16-bit floats - Linux/ANGLE on OpenGL ES does, Windows/ANGLE on
// Direct3D does not - the normal-map maths underflows, the surface normal
// turns into NaN, the two light terms fall to zero and the hull is drawn
// with its ambient term alone, at about a third of its brightness.
// Usage: node glsltest.js hlp_shooter_vNNN_logic.html
const fs = require('fs');
const src = fs.readFileSync(process.argv[2] || '', 'utf8')
  .match(/<script[^>]*>([\s\S]*)<\/script>/)[1];

const fails = [];
const fail = m => fails.push(m);

// 1. full precision is requested, and only mediump is left as the fallback
if(!/#ifdef GL_FRAGMENT_PRECISION_HIGH/.test(src))
  fail('the fragment shader does not test GL_FRAGMENT_PRECISION_HIGH');
if(!/precision highp float/.test(src))
  fail('the fragment shader never declares highp float');
const med = src.match(/precision mediump float/g) || [];
const hi  = src.match(/precision highp float/g) || [];
if(med.length > hi.length)
  fail('mediump is declared ' + med.length + ' times but highp only ' + hi.length);

// 2. no constant below the smallest 16-bit float (about 6e-8) inside a
//    shader: in the mediump fallback such a constant becomes 0 and the
//    guard it is meant to be stops working. Only the shader strings are
//    looked at - in JavaScript such a constant is perfectly fine.
const GLSL = /\b(?:varying|uniform|precision|discard|texture2D|inversesqrt|smoothstep|normalize|vec[234]|mat[234]|gl_[A-Za-z])\b|\bvec[234]\(/;
for(const lit of src.match(/'(?:[^'\\\n]|\\.)*'/g) || []){
  if(!GLSL.test(lit)) continue;
  for(const m of lit.match(/\b\d(?:\.\d+)?e-\d+\b/gi) || []){
    if(parseInt(m.split(/e-/i)[1], 10) >= 8)
      fail('shader constant ' + m + ' is 0 in a 16-bit float');
  }
}

for(const f of fails) console.log('FAIL  ' + f);
console.log(fails.length ? fails.length + ' failed' : 'glsltest ok');
process.exit(fails.length ? 1 : 0);
