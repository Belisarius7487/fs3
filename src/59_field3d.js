// ── CAPITAL SHIPS IN 3D ON THE FIELD (v196) ──────────────────
// The 2.5D plan, step 1 (Silvio): capital ships that have a converted
// model are drawn from it instead of from their sprite. Everything the game
// does with a ship stays as it was - position, facing, hits, mounts and the
// damage logic all read the sprite as before; only the picture of the hull
// comes from a WebGL canvas the size of the field. That canvas is copied
// into the field once a frame, after the backdrop, beams and wreckage and
// before the small craft, so fighters and shots stay on top of the
// capitals. A perspective camera looks straight at the middle of the
// field: the plane z = 0 lands exactly where the 2D drawing has it, and
// only the hull's own depth shows perspective. Capitals among themselves
// share one depth buffer, so an overlap is a real overlap.
// Without WebGL, until a model has loaded, or for a hull without a model
// (the Shivans and the NTF reskins for now) the sprite is drawn as before.
// v197: the Shivan capital ships as well (first line)
const F3D_KEYS = ['crcain', 'crlilith', 'crrakshasa', 'comoloch', 'dedemon', 'deravana', 'sdlucifer', 'sdsathanas',
  'crfenris', 'crleviathan', 'craeolus', 'codeimos', 'deorionright', 'dehecate',
  'craten', 'crmentu', 'cosobek', 'detyphon', 'dehatshepsut', 'sdcolossus', 'sgmjolnir',
  'cacharybdis', 'casetekh', 'coiceni'];
const F3D_ALIAS = {deorionleft: 'deorionright'};
// v198: animated glow maps, as the MediaVPs have them (Silvio: the Ravana's
// cable bundle pulses). The frames lie in one picture, cols x rows, row by
// row: <tex>_ga512.webp / _ga1024.webp next to the other maps.
const F3D_GANIM = {ravanapulse: {n: 30, fps: 25, cols: 8, rows: 4}};
const F3D_FOV = 30*Math.PI/180;
// key light from the upper left and in front, a weak fill from below
// right - the same as the previews
const F3D_L1 = [-0.45, 0.65, 0.62], F3D_L2 = [0.7, -0.25, 0.4];
const F3D = {ok: null, gl: null, can: null, prog: null, loc: null, models: {}, white: null, black: null, flatN: null,
             // &f3d=0 in the address draws every ship as a sprite, to compare
             off: (typeof location !== 'undefined' && /[?&]f3d=0(&|$)/.test(location.search||''))};

// ── TURRETS FROM THE MODELS (v198) ───────────────────────────
// Silvio: on a 3D ship the guns sit where the model has its turrets. For
// every mount of the game (beams, primary guns, launchers - their number
// and weapons stay as they were) the nearest turret of the same kind in the
// POF TGUN chunk was looked up offline (pof/turrets.py), classified by the
// weapon the ship table gives it. Per mount: [z, y, x, normal x, y, z] in
// the model's own space, halved length = 1 (z = along the hull, bow +).
// 0 = no turret left over, the mount keeps its old place. The Lucifer's
// primary mounts carry her reactors and are not moved.
const F3D_TUR = {
  crcain:{"beams":[[0.43,0.413,-0.001,0.02,-1.0,0.0],[-0.939,0.124,-0.002,0.05,-0.94,0.33]],"secondary":[[-0.122,0.089,-0.192,-0.83,0.56,0.01]],"primary":[[-0.16,-0.173,-0.002,-0.0,0.59,-0.8],[0.819,0.376,-0.357,0.02,-1.0,0.09],[0.587,0.251,0.379,0.83,0.56,-0.05]]},
  crlilith:{"beams":[[0.43,0.416,-0.001,0.02,-1.0,0.0],[-0.939,0.121,-0.002,0.05,-0.94,0.33]],"secondary":[[-0.121,0.085,0.189,0.91,0.42,0.02]],"primary":[[0.819,0.373,-0.357,0.02,-1.0,0.09],[-0.16,-0.176,-0.002,-0.0,0.59,-0.8],[0.587,0.248,0.379,0.83,0.56,-0.05]]},
  crrakshasa:{"beams":[[0.877,-0.223,0.047,-0.03,-0.08,1.0],[0.894,-0.013,-0.21,-0.03,-0.08,1.0],[0.877,-0.223,-0.047,-0.03,-0.08,1.0],[-0.857,-0.26,0.0,0.04,-0.73,-0.68],[-0.322,0.127,-0.0,0.01,0.07,1.0]],"primary":[[-0.695,-0.103,-0.216,-0.9,0.4,-0.19],[0.462,0.033,-0.098,-0.2,-0.98,0.04],[0.462,-0.1,-0.162,-0.81,0.58,0.01]]},
  comoloch:{"beams":[[-0.232,0.139,0.0,-0.04,-0.95,0.31],[-0.048,-0.166,-0.0,-0.04,1.0,0.03],[0.599,0.175,0.0,-0.04,-0.72,0.69],[0.11,-0.021,-0.054,-0.63,-0.78,0.04]],"secondary":[[0.843,-0.043,-0.055,-0.04,1.0,0.03]],"primary":[[0.11,-0.021,0.054,0.57,-0.82,0.04],[-0.514,0.022,-0.059,-0.96,-0.11,-0.24],[-0.835,-0.214,-0.0,-0.04,0.59,-0.81],[0.225,-0.217,-0.0,-0.04,1.0,0.03]]},
  dedemon:{"beams":[[0.726,0.149,-0.159,-0.82,0.56,0.1],[0.23,-0.185,0.0,0.0,1.0,0.0],[0.043,0.126,-0.421,-0.99,-0.06,0.1],[0.043,0.126,0.421,0.99,-0.06,0.1],[0.726,0.149,0.159,0.84,0.54,0.1]],"primary":[[0.96,0.146,-0.077,0.03,0.48,0.88],[0.033,0.363,0.0,0.0,-1.0,0.0],[-0.429,0.401,-0.384,-0.91,-0.4,-0.03],[-0.566,0.061,0.452,0.95,0.15,-0.27]]},
  deravana:{"beams":[[1.001,0.109,-0.146,0.0,0.0,1.0],[1.001,0.109,0.006,-0.0,0.0,1.0],[-0.105,-0.157,0.002,0.68,0.68,0.26],[-0.428,0.269,-0.114,-0.0,0.0,1.0],[-0.387,-0.545,-0.373,0.0,0.0,1.0],[-0.356,-0.572,0.061,0.0,0.0,1.0],[-0.902,-0.386,-0.18,-0.08,0.93,-0.36]],"secondary":[[0.42,-0.206,-0.07,-0.06,0.96,-0.26]],"primary":[[-0.261,0.264,0.413,0.98,-0.14,0.13],[-0.283,-0.277,0.015,0.62,0.69,0.36],[0.034,-0.133,-0.135,-0.8,0.59,0.0],[0.456,-0.073,-0.184,-0.98,-0.02,0.21],[0.544,0.027,0.123,0.94,-0.34,0.08]]},
  sdlucifer:{"beams":[[0.897,0.154,0.403,-0.0,0.0,1.0],[0.897,0.154,-0.403,-0.0,0.0,1.0]],"secondary":[[0.945,0.115,0.001,-0.0,0.0,1.0]]},
  sdsathanas:{"beams":[[0.993,-0.033,0.264,-0.15,-0.1,0.98],[0.971,0.232,-0.15,-0.03,-0.1,0.99],[-0.791,-0.148,-0.373,-0.75,0.66,0.0],[0.102,-0.0,0.186,0.51,0.75,0.42],[-0.154,0.158,-0.108,0.01,-1.0,0.0]],"primary":[[0.411,0.014,0.02,0.0,1.0,0.0],[0.019,-0.075,-0.115,-1.0,-0.05,0.0],[-0.286,-0.203,-0.121,-1.0,-0.05,0.0],[-0.476,0.063,0.189,1.0,-0.03,-0.01],[-0.101,0.103,0.253,1.0,-0.03,0.02],[-0.099,0.103,-0.252,-1.0,-0.03,0.0]]},
  crfenris:{"beams":[[0.87,-0.008,-0.0,-0.0,-0.82,0.57],[-0.914,0.049,0.185,0.66,-0.75,-0.0]],"secondary":[[-0.054,0.073,-0.0,0.0,-1.0,0.0]],"primary":[[0.286,-0.093,-0.278,-1.0,0.0,0.0],[-0.914,0.049,-0.185,-0.68,-0.74,0.0],[-0.878,-0.23,0.175,0.64,0.77,0.0]]},
  crleviathan:{"beams":[[0.896,-0.086,0.0,-0.0,-0.82,0.57],[-0.899,-0.251,-0.206,-0.66,0.75,-0.0],[-0.899,-0.004,0.206,0.66,-0.75,-0.0]],"secondary":[[0.044,0.727,-0.0,0.0,-1.0,0.0]],"primary":[[0.309,-0.111,-0.277,-1.0,0.0,0.0],[0.309,-0.111,0.277,1.0,0.0,0.0]]},
  craeolus:{"beams":[[0.737,0.011,0.179,0.01,-0.04,1.0],[-0.06,0.039,0.228,1.0,0.0,0.0],[0.118,0.039,-0.228,-1.0,0.0,0.0]],"primary":[[0.677,-0.27,-0.002,0.0,1.0,0.0],[0.072,-0.318,-0.002,0.0,1.0,0.0],[-0.81,-0.333,-0.002,0.0,1.0,0.0],[-0.885,0.302,-0.002,0.0,-1.0,0.0],[0.171,0.333,0.0,0.0,-1.0,0.0],[0.874,0.311,-0.002,0.0,-1.0,0.0]]},
  codeimos:{"beams":[[-0.819,-0.153,-0.197,-0.98,0.18,-0.08],[0.969,0.015,-0.07,-0.46,-0.16,0.88],[0.746,0.032,0.15,1.0,0.0,0.0]],"secondary":[[-0.423,-0.156,-0.205,-0.98,0.14,0.12]],"primary":[[-0.576,-0.429,-0.0,0.0,1.0,0.0],[0.277,-0.359,-0.0,0.0,1.0,0.0],[0.657,-0.332,-0.0,0.0,1.0,0.0],[0.29,0.295,0.0,0.0,-1.0,0.0]]},
  deorionright:{"beams":[[0.856,0.096,0.055,0.0,-1.0,0.0],[-0.72,0.137,-0.293,-1.0,0.0,0.0],[0.524,-0.028,-0.093,-1.0,0.0,0.0],[-0.799,0.185,0.292,1.0,0.0,0.0],[0.388,-0.163,0.05,0.0,1.0,0.0],[-0.06,0.286,0.117,0.0,-1.0,0.0]],"secondary":[[0.6,-0.205,0.114,0.0,1.0,0.0]],"primary":[[-0.182,0.356,0.02,0.0,-1.0,0.0],[0.831,-0.205,0.054,0.0,1.0,0.0],[-0.198,-0.19,0.056,0.0,1.0,0.0],[-0.759,-0.356,0.099,0.0,1.0,0.0]]},
  dehecate:{"beams":[[0.989,-0.23,-0.0,0.04,0.02,1.0],[0.193,-0.064,0.057,0.96,-0.28,-0.07],[0.932,-0.002,-0.0,0.04,-0.32,0.95],[0.597,-0.137,-0.325,-0.97,-0.25,0.0],[0.597,-0.137,0.325,0.97,-0.25,0.0]],"secondary":[[-0.377,0.344,-0.043,-0.97,-0.25,0.0]],"primary":[[0.753,-0.422,0.0,0.01,0.99,0.12],[0.85,0.139,0.0,0.0,-1.0,0.0],[0.415,-0.438,0.0,0.01,0.99,0.12],[-0.293,-0.528,0.0,0.01,0.99,0.12],[0.228,0.097,0.0,0.0,-1.0,0.0]]},
  craten:{"beams":[[-0.492,-0.297,-0.0,0.0,1.0,0.0],[0.595,0.048,0.317,0.0,1.0,0.0],[0.595,0.048,-0.317,0.0,1.0,0.0]],"primary":[[0.531,0.294,0.0,0.0,-1.0,0.0],0,[-0.727,0.029,-0.234,-0.87,-0.5,0.0],[-0.727,0.029,0.234,0.77,-0.64,0.0]]},
  crmentu:{"beams":[[0.148,-0.263,-0.191,-0.28,0.96,0.0],[0.148,-0.263,0.191,0.57,0.82,-0.01],[-0.942,0.066,-0.0,0.01,0.0,-1.0]],"secondary":[[0.434,0.182,0.193,0.0,-1.0,0.0]],"primary":[[-0.256,-0.142,0.198,0.72,0.69,0.1],[-0.678,0.344,0.001,0.0,-1.0,0.0],[0.108,-0.156,-0.307,-0.77,0.63,0.1]]},
  cosobek:{"beams":[[0.837,0.216,0.088,0.46,0.82,0.34],[-0.836,0.28,-0.347,0.43,0.32,-0.85],[0.53,0.153,0.136,0.56,0.81,0.2],[-0.837,0.28,0.348,-0.44,0.32,-0.84]],"secondary":[[0.666,0.392,-0.133,0.0,-1.0,0.0]],"primary":[[0.666,0.392,0.133,0.0,-1.0,0.0],[0.234,0.079,0.137,0.57,0.82,0.0],[-0.58,0.089,-0.116,-0.93,0.21,0.29]]},
  detyphon:{"beams":[[0.774,-0.033,0.0,0.0,0.37,0.93],[-0.673,0.131,0.0,0.0,-0.45,-0.89],[-0.687,-0.103,0.0,0.0,0.42,-0.91],[0.766,0.033,0.0,0.0,-0.32,0.95],[-0.833,-0.008,-0.0,0.0,-0.45,-0.89]],"secondary":[[-0.026,0.137,0.0,0.0,-0.45,0.89]],"primary":[[0.729,-0.053,-0.033,0.0,1.0,0.0],[0.729,-0.053,0.033,0.0,1.0,0.0],[0.133,0.079,0.178,0.0,-1.0,0.0],[0.132,-0.151,-0.178,0.0,1.0,0.0],[0.133,0.079,-0.178,0.0,-1.0,0.0],[0.132,-0.151,0.178,0.0,1.0,0.0]]},
  dehatshepsut:{"beams":[[0.824,0.044,-0.0,-0.0,0.85,0.52],[0.013,-0.244,-0.0,-0.0,1.0,-0.02],[-0.96,-0.123,-0.0,-0.0,0.58,-0.81],[-0.798,0.085,-0.232,-0.27,-0.91,0.32],[-0.798,0.083,0.232,0.23,-0.93,0.29],[0.846,0.138,0.161,0.0,1.0,0.0]],"secondary":[[0.771,0.276,0.209,0.0,-1.0,0.02]],"primary":[[0.054,0.058,-0.225,-0.81,-0.37,0.45],[-0.254,-0.006,0.33,0.6,0.8,0.02],[-0.943,-0.076,0.0,0.06,-0.57,-0.82],[0.505,0.194,-0.264,-0.01,1.0,-0.03],[-0.368,0.192,0.225,0.47,-0.84,-0.27]]},
  sdcolossus:{"beams":[[-0.759,-0.088,-0.196,-1.0,-0.0,0.0],[-0.908,-0.086,0.195,1.0,-0.0,0.0],[-0.759,-0.086,0.195,1.0,-0.0,0.0],[-0.973,-0.13,0.151,0.0,1.0,0.0],[-0.136,0.001,-0.093,-0.68,-0.73,-0.0],[0.186,-0.161,-0.203,-0.96,-0.0,0.29],[0.689,-0.11,-0.076,-0.83,-0.56,0.0],[0.811,-0.224,0.0,0.0,0.9,0.45],[0.227,-0.237,0.094,0.0,0.84,0.54]],"secondary":[[-0.545,-0.158,-0.144,-1.0,0.0,0.0]],"primary":[[-0.731,-0.151,-0.144,-1.0,0.0,0.0],[-0.724,0.005,0.133,0.0,-1.0,0.0],[-0.439,-0.245,-0.1,0.0,1.0,0.0],[-0.195,0.334,-0.061,0.0,-1.0,0.0],[0.763,0.06,-0.001,0.0,-1.0,0.0],[0.721,0.063,-0.001,0.0,-1.0,0.0],[0.66,-0.268,-0.001,0.0,1.0,0.0]]},
  sgmjolnir:{"beams":[[0.105,-1.17,0.0,0.0,1.0,0.0]]},
  cacharybdis:{"beams":[[-0.404,-0.123,-0.105,-1.0,0.0,0.0]],"secondary":[[0.115,-0.103,-0.0,0.0,0.71,0.71]],"primary":[[-0.593,0.185,0.204,1.0,0.0,0.0]]},
  casetekh:{"primary":[[-0.234,0.235,0.0,-0.01,-1.0,-0.09],[-0.8,-0.299,0.005,0.06,0.99,0.13]]},
  coiceni:{"beams":[[0.797,-0.009,0.215,0.99,0.0,0.1],[0.987,0.023,0.062,0.1,0.0,0.99],[0.797,-0.009,-0.223,-0.99,0.0,0.1],[0.14,-0.169,-0.248,-0.93,0.37,0.0],[-0.26,-0.169,0.254,0.93,0.37,0.0],[-0.149,0.291,-0.226,-1.0,0.0,0.0],[-0.804,-0.032,-0.128,-0.89,0.45,0.0],[-0.837,0.194,-0.0,0.0,-0.51,-0.86],[-0.906,-0.048,-0.0,0.0,0.82,-0.57]],"secondary":[[-0.195,0.51,-0.161,0.0,-1.0,0.0]],"primary":[[0.14,-0.169,0.244,0.93,0.37,0.0],[-0.343,-0.529,-0.0,0.0,1.0,0.0],[0.301,-0.336,0.0,0.0,1.0,0.0],[-0.744,0.334,0.0,0.0,-1.0,0.0],[-0.689,-0.222,0.0,0.0,1.0,0.0]]}
};
const F3D_MNT = {};
// The mount lists of a hull with its turrets moved onto the model. Needs the
// sprite's proportions (the old lists are measured against its box); until
// it has loaded the old lists are given.
function f3dMounts(key, m){
  if(!m || !key) return m;
  const t = F3D_TUR[key]; if(!t) return m;
  const c0 = F3D_MNT[key]; if(c0) return c0;
  const img = (typeof IMGS !== 'undefined') ? IMGS[key] : null;
  if(!img || !img.width || !img.height) return m;
  const asp = img.width/img.height, sg = m.facing === 'left' ? -1 : 1;
  const c = Object.assign({}, m);
  for(const kind in t){
    if(!m[kind]) continue;
    c[kind] = m[kind].map(function(p, i){
      const q = t[kind][i]; if(!q) return p;
      return Object.assign({}, p, {dx: sg*q[0], dy: q[1]*asp, mx: q[2], n3: [q[3], q[4], q[5]]});
    });
  }
  return (F3D_MNT[key] = c);
}
// Is the ship drawn from her model right now?
function f3dOn(e){ return !!e && e._f3fc != null && typeof fc !== 'undefined' && fc - e._f3fc <= 2; }
// Which way the bow points on the screen: +1 right, -1 left.
function f3dBow(e){ return ((spriteFacing(e.img) === 'right') !== !!e.flip) ? 1 : -1; }
// A turret on the flank turned away from the player (Weg 3): it fires, but
// what it fires comes out from behind the hull.
function mountHid(e, b){
  if(!b || !b.n3 || !f3dOn(e)) return false;
  const bw = f3dBow(e);
  const toCam = -bw*b.n3[0], depth = -bw*(b.mx||0);
  return toCam < -0.5 || (depth < -0.15 && toCam < 0.3);
}
// A turret only covers the half of space its face looks into (FreeSpace
// FOV 180): one on the back cannot fire down through the hull. Turrets on
// the flanks look out of the picture and reach everything in the plane.
const F3D_FOV_SLACK = 0.20;
function mountCanAim(e, b, x, y, tx, ty){
  if(!b || !b.n3) return true;
  const ny = b.n3[1], nz = b.n3[2], l = Math.hypot(ny, nz);
  if(l < 0.45) return true;
  const bw = f3dBow(e), a = e.ang || 0, ca = Math.cos(a), sa = Math.sin(a);
  const sx = bw*nz/l, sy = -ny/l;
  const ux = sx*ca - sy*sa, uy = sx*sa + sy*ca;
  const dx = tx - x, dy = ty - y, d = Math.hypot(dx, dy);
  if(d < 1) return true;
  return (ux*dx + uy*dy)/d >= -F3D_FOV_SLACK;
}
function f3dKey(e){
  if(!e || !e.img || e.type === 'asteroid') return null;
  const k = F3D_ALIAS[e.img] || e.img;
  return F3D_KEYS.indexOf(k) >= 0 ? k : null;
}
function f3dInit(){
  if(F3D.ok !== null) return F3D.ok;
  F3D.ok = false;
  try{
    if(typeof document === 'undefined' || !document.createElement) return false;
    const can = document.createElement('canvas');
    const gl = can.getContext('webgl', {alpha: true, premultipliedAlpha: true, antialias: true,
                                        preserveDrawingBuffer: true, depth: true});
    if(!gl) return false;
    const deriv = !!gl.getExtension('OES_standard_derivatives');
    gl.getExtension('OES_element_index_uint');
    const vs = 'attribute vec3 aP; attribute vec3 aN; attribute vec2 aT;'
      + 'uniform mat4 uM; uniform mat4 uVP; varying vec3 vW; varying vec3 vN; varying vec2 vT;'
      + 'void main(){ vec4 w = uM*vec4(aP,1.0); vW = w.xyz; vN = mat3(uM)*aN; vT = aT*3.99994-1.0; gl_Position = uVP*w; }';
    const fs = (deriv ? '#extension GL_OES_standard_derivatives : enable\n#define DERIV 1\n' : '')
      + 'precision mediump float; varying vec3 vW; varying vec3 vN; varying vec2 vT;'
      + 'uniform sampler2D tC; uniform sampler2D tN; uniform sampler2D tG;'
      + 'uniform float uHasN; uniform float uKind; uniform vec3 uCam; uniform vec3 uL1; uniform vec3 uL2;'
      + 'uniform vec3 uClip; uniform float uA; uniform vec3 uGA; uniform vec3 uGF;'
      + 'void main(){'
      + ' if(dot(uClip.xy, vW.xy) + uClip.z < 0.0) discard;'
      + ' vec3 N = normalize(vN);'
      + '\n#ifdef DERIV\n'
      + ' if(uHasN > 0.5){ vec3 d1 = dFdx(vW), d2 = dFdy(vW); vec2 t1 = dFdx(vT), t2 = dFdy(vT);'
      + '  vec3 c2 = cross(d2, N), c1 = cross(N, d1); vec3 T = c2*t1.x + c1*t2.x; vec3 B = c2*t1.y + c1*t2.y;'
      + '  float im = inversesqrt(max(max(dot(T,T), dot(B,B)), 1e-20));'
      + '  vec2 nm = texture2D(tN, vT).rg*2.0-1.0; vec3 tn = vec3(nm, sqrt(max(0.0, 1.0-dot(nm,nm))));'
      + '  N = normalize(T*im*tn.x - B*im*tn.y + N*tn.z); }\n'
      + '\n#endif\n'
      + ' vec3 base = uKind < 0.5 ? texture2D(tC, vT).rgb : (uKind > 1.5 ? vec3(0.05,0.07,0.10) : vec3(0.30,0.30,0.32));'
      + ' vec3 V = normalize(uCam - vW);'
      + ' float d = max(dot(N, uL1), 0.0)*0.95 + max(dot(N, uL2), 0.0)*0.30;'
      + ' float s = pow(max(dot(N, normalize(uL1+V)), 0.0), uKind > 1.5 ? 60.0 : 24.0)*(uKind > 1.5 ? 0.9 : 0.35);'
      + ' vec3 col = base*(0.30 + d*1.15)*1.15 + vec3(s);'
      + ' if(uKind < 0.5){ vec2 gt = vT;'
      + '  if(uGF.z > 0.5) gt = (uGF.xy + clamp(fract(vT), vec2(uGA.z), vec2(1.0-uGA.z)))/uGA.xy;'
      + '  col += texture2D(tG, gt).rgb; }'
      + ' gl_FragColor = vec4(col*uA, uA); }';
    const sh = function(t, src){ const s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
      if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr, gl.LINK_STATUS)) return false;
    const loc = {};
    for(const a of ['aP', 'aN', 'aT']) loc[a] = gl.getAttribLocation(pr, a);
    for(const u of ['uM', 'uVP', 'tC', 'tN', 'tG', 'uHasN', 'uKind', 'uCam', 'uL1', 'uL2', 'uClip', 'uA', 'uGA', 'uGF']) loc[u] = gl.getUniformLocation(pr, u);
    const px = function(r, g, b){ const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([r, g, b, 255])); return t; };
    F3D.white = px(160, 160, 160); F3D.black = px(0, 0, 0); F3D.flatN = px(128, 128, 255);
    // a lost context takes every buffer with it: start over, sprites meanwhile
    can.addEventListener('webglcontextlost', function(ev){
      ev.preventDefault(); F3D.models = {}; F3D.gl = null; F3D.ok = null;
    }, false);
    F3D.gl = gl; F3D.can = can; F3D.prog = pr; F3D.loc = loc;
    F3D.ok = true;
  }catch(e){ F3D.ok = false; F3D.err = String(e && e.message || e); }
  return F3D.ok;
}
// One level of a model into this context: the same files the previews use.
function f3dLevel(key, tag, size){
  const gl = F3D.gl, rev = (typeof M3D_REV !== 'undefined') ? M3D_REV : 0;
  const L = {state: 'loading', parts: [], tex: {}};
  fetch(M3D_BASE + key + '/' + tag + '.bin?r=' + rev).then(function(r){
    if(!r.ok) throw new Error('missing'); return r.arrayBuffer();
  }).then(function(buf){
    if(gl !== F3D.gl) throw new Error('lost');
    const hl = new DataView(buf).getUint32(0, true);
    const head = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 4, hl)));
    const data = buf.slice(4 + hl);
    L.head = head;
    const want = {};
    for(const p of head.parts){
      const mk = function(target, from, bytes){ const b = gl.createBuffer(); gl.bindBuffer(target, b);
        gl.bufferData(target, new Uint8Array(data, from, bytes), gl.STATIC_DRAW); return b; };
      L.parts.push({kind: p.kind, tex: (p.tex||'').toLowerCase(), n: p.ni, big: p.big,
        pos: mk(gl.ARRAY_BUFFER, p.pos, p.nv*6), nrm: mk(gl.ARRAY_BUFFER, p.nrm, p.nv*4),
        uv: mk(gl.ARRAY_BUFFER, p.uv, p.nv*4), idx: mk(gl.ELEMENT_ARRAY_BUFFER, p.idx, p.ni*(p.big?4:2))});
      if(p.kind === 'tex') want[(p.tex||'').toLowerCase()] = true;
    }
    const jobs = [];
    for(const t in want){
      L.tex[t] = {};
      for(const k of (F3D_GANIM[t] ? ['c', 'n', 'g', 'ga'] : ['c', 'n', 'g'])){
        jobs.push(new Promise(function(res){
          const im = new Image();
          im.onload = function(){
            if(gl !== F3D.gl) return res();
            const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
            if(k === 'ga'){
              // frames side by side: no mipmaps, they would bleed into each other
              gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
              gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
              gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
              L.tex[t].gaw = im.width;
            } else {
              gl.generateMipmap(gl.TEXTURE_2D);
              gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
            }
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
            L.tex[t][k] = tx; res();
          };
          im.onerror = function(){ res(); };       // no glow map is normal
          im.src = M3D_BASE + key + '/' + t + '_' + k + size + '.webp?r=' + rev;
        }));
      }
    }
    return Promise.all(jobs);
  }).then(function(){ L.state = 'ready'; }, function(){ L.state = 'failed'; });
  return L;
}
// The coarse level comes first so the ship shows soon; the full one (every
// part of the finest level, v196) follows and takes over once it is in.
function f3dModel(key){
  let m = F3D.models[key];
  if(!m){
    m = F3D.models[key] = {lo: f3dLevel(key, 'lo', 512), full: null};
  }
  if(!m.full && m.lo.state !== 'loading') m.full = f3dLevel(key, 'full', 1024);
  return m;
}
function f3dReadyLevel(key){
  if(F3D.off || !f3dInit()) return null;
  const m = f3dModel(key);
  if(m.full && m.full.state === 'ready') return m.full;
  return m.lo.state === 'ready' ? m.lo : null;
}
function f3dMat(e, x, y, L){
  const right = (spriteFacing(e.img) === 'right') !== !!e.flip;
  const yaw = right ? Math.PI/2 : -Math.PI/2;
  const img = IMGS[e.img], w = img ? img.width*e.sc : 100;
  const s = w/Math.max(0.01, L.head.size[2]/L.head.ext);
  const a = -(e.ang||0), ca = Math.cos(a), sa = Math.sin(a), cy = Math.cos(yaw), sy = Math.sin(yaw);
  // translate * rotZ(a) * rotY(yaw) * scale, column-major
  return new Float32Array([
    s*ca*cy, s*sa*cy, -s*sy, 0,
    -s*sa,   s*ca,    0,     0,
    s*ca*sy, s*sa*sy, s*cy,  0,
    x,       -y,      0,     1]);
}
function f3dVP(){
  const D = (H/2)/Math.tan(F3D_FOV/2), asp = W/H, f = 1/Math.tan(F3D_FOV/2);
  const near = D*0.3, far = D*3, nf = 1/(near - far);
  const P = [f/asp,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0];
  const ex = W/2, ey = -H/2;
  // camera at (ex, ey, D) looking down -z: the view only moves the world
  const Vw = [1,0,0,0, 0,1,0,0, 0,0,1,0, -ex,-ey,-D,1];
  const o = new Float32Array(16);
  for(let c = 0; c < 4; c++) for(let r = 0; r < 4; r++){
    let s = 0; for(let k = 0; k < 4; k++) s += P[k*4+r]*Vw[c*4+k]; o[c*4+r] = s;
  }
  return {vp: o, eye: [ex, ey, D]};
}
// Draws the given ships into the field canvas and copies it into the
// field. items: {e, L, x, y, a (alpha), clip (screen half-plane or null)}.
function f3dRender(items){
  const gl = F3D.gl, can = F3D.can, loc = F3D.loc;
  const pw = (typeof CVS !== 'undefined' && CVS.width) || Math.round(W), ph = (typeof CVS !== 'undefined' && CVS.height) || Math.round(H);
  if(can.width !== pw || can.height !== ph){ can.width = pw; can.height = ph; }
  gl.viewport(0, 0, pw, ph);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST); gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
  gl.useProgram(F3D.prog);
  const cam = f3dVP();
  gl.uniformMatrix4fv(loc.uVP, false, cam.vp);
  gl.uniform3fv(loc.uCam, cam.eye);
  gl.uniform3fv(loc.uL1, f3dNorm(F3D_L1)); gl.uniform3fv(loc.uL2, f3dNorm(F3D_L2));
  gl.uniform1i(loc.tC, 0); gl.uniform1i(loc.tN, 1); gl.uniform1i(loc.tG, 2);
  const now = ((typeof performance !== 'undefined') ? performance.now() : Date.now())/1000;
  for(const it of items){
    const L = it.L;
    gl.uniformMatrix4fv(loc.uM, false, f3dMat(it.e, it.x, it.y, L));
    gl.uniform1f(loc.uA, it.a);
    // the clip of a ship sliding through her vortex (fsWarpClip), in the
    // field's own units with y turned up
    if(it.clip){ const c = it.clip; gl.uniform3f(loc.uClip, c.sg*c.fx, -c.sg*c.fy, -c.sg*(c.px*c.fx + c.py*c.fy)); }
    else gl.uniform3f(loc.uClip, 0, 0, 1);
    if(it.a < 1){ gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); } else gl.disable(gl.BLEND);
    for(const p of L.parts){
      const tx = L.tex[p.tex] || {};
      const kind = p.kind === 'tex' && tx.c ? 0 : (p.kind === 'glass' ? 2 : 1);
      gl.uniform1f(loc.uKind, kind);
      gl.uniform1f(loc.uHasN, kind === 0 && tx.n ? 1 : 0);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tx.c || F3D.white);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tx.n || F3D.flatN);
      const ga = tx.ga && F3D_GANIM[p.tex];
      if(ga){
        const f = Math.floor(now*ga.fps) % ga.n, cell = (tx.gaw || 2048)/ga.cols;
        gl.uniform3f(loc.uGA, ga.cols, ga.rows, 0.5/cell);
        gl.uniform3f(loc.uGF, f % ga.cols, Math.floor(f/ga.cols), 1);
      } else gl.uniform3f(loc.uGF, 0, 0, 0);
      gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, ga ? tx.ga : (tx.g || F3D.black));
      gl.bindBuffer(gl.ARRAY_BUFFER, p.pos); gl.enableVertexAttribArray(loc.aP);
      gl.vertexAttribPointer(loc.aP, 3, gl.SHORT, true, 6, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, p.nrm); gl.enableVertexAttribArray(loc.aN);
      gl.vertexAttribPointer(loc.aN, 3, gl.BYTE, true, 4, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, p.uv); gl.enableVertexAttribArray(loc.aT);
      gl.vertexAttribPointer(loc.aT, 2, gl.UNSIGNED_SHORT, true, 4, 0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, p.idx);
      gl.drawElements(gl.TRIANGLES, p.n, p.big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT, 0);
    }
  }
  gl.disable(gl.BLEND);
  ctx.drawImage(can, 0, 0, W, H);
}
function f3dNorm(v){ const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0]/l, v[1]/l, v[2]/l]; }
// Whether a ship is drawn here this frame, and how: the same decisions the
// ship loop in draw() makes for a sprite (vortex, fade in and out).
function f3dVis(e){
  fsTrack(e);
  const g = fsWarp(e);
  if(g){
    if(!g.vis) return null;
    const out = !!g.out;
    return {x: (e.x|0) + g.dx, y: (e.y|0) + g.dy, a: 1, g: g,
            clip: {sg: out ? -1 : 1, fx: g.fx, fy: g.fy, px: g.px, py: g.py}};
  }
  let a = 1;
  if(e.warp > 0){
    const m = e.warpMax||100, el = m - e.warp;
    if(el < m*0.40) return null;
    if(el < m*0.60) a = (el - m*0.40)/(m*0.20);
  } else if(e.warpOut > 0){
    const m = e.warpMax||100, el = m - e.warpOut;
    if(el > m*0.60) return null;
    if(el > m*0.40) a = 1 - (el - m*0.40)/(m*0.20);
  }
  return {x: e.x|0, y: e.y|0, a: a, g: null, clip: null};
}
// Called by draw() before the ship loop. Draws the vortex and thrusters of
// every 3D ship (they lie under the hull), then all the 3D hulls at once,
// and returns the set of ships the loop must not draw a sprite hull for.
function f3dFieldPass(list){
  const done = new Set();
  if(F3D.off || typeof document === 'undefined') return done;
  const items = [];
  for(const e of list){
    const key = f3dKey(e); if(!key) continue;
    const L = f3dReadyLevel(key); if(!L) continue;
    done.add(e);
    e._f3fc = (typeof fc !== 'undefined') ? fc : 0;
    try{ drawVortexOf(e); }catch(ev){ ctx.restore(); }
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    const v = f3dVis(e); e._f3v = v;
    if(!v) continue;
    try{
      ctx.save();
      if(v.g){ fsWarpClip(v.g); ctx.translate(v.g.dx, v.g.dy); }
      else ctx.globalAlpha = v.a;
      drawThrusters(e.img, e.x|0, e.y|0, e.sc, e.flip, e.faction, v.g ? (v.g.out ? 1 : 0.6) : (e.warp > 0 ? 0.35 : 1), e.ang||0, e);
      ctx.restore();
    }catch(et){ ctx.restore(); }
    ctx.globalAlpha = 1;
    items.push({e: e, L: L, x: v.x, y: v.y, a: v.a, clip: v.clip});
  }
  if(items.length){
    try{ f3dRender(items); }catch(er){ F3D.err = String(er && er.message || er); }
  }
  return done;
}
// After the 3D hulls, in the ship loop's order: what she has taken (the
// damage marks alone, 20_render.js), then marks, bar, shields and beams.
function f3dShipTop(e){
  const v = e._f3v; if(!v) return;
  if(v.g){
    // in her vortex: the hull only, cut like the sprite would be
    ctx.save(); fsWarpClip(v.g); ctx.translate(v.g.dx, v.g.dy);
    f3dDamage(e);
    ctx.restore();
    warpBeamOrbs(e, v.g);
    return;
  }
  ctx.globalAlpha = v.a;
  f3dDamage(e);
  drawShipTop(e);
  ctx.globalAlpha = 1;
}
function f3dDamage(e){
  e._gl3 = true;
  try{ drawShipE(e, e.x|0, e.y|0, e.sc, e.flip, e.ang||0); }
  finally{ e._gl3 = false; }
}
