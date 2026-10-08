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

// ── TURRETS FROM THE MODELS (v198, v199) ─────────────────────
// Silvio: the guns of a capital ship with a model are the turrets of that
// model - where they sit, how many there are and what they carry. Every
// turret of the POF (TGUN) with the weapon the ship table gives it
// (pof/turrets.py, tur/gen199.py). Per turret: [z, y, x, normal x, y, z,
// weapon] in the model's own space, halved length = 1 (z along the hull,
// bow +), thr: engine glows [z, y, radius]. v199 (Silvio: the real number, FS values): the weapons carry
// FreeSpace's values, measured against one weapon the game already had
// for each kind - Terran Turret for the guns, BGreen and AAAf on the Orion
// for the beams, the Standard Flak for flak, the Piranha for launchers.
// rate/dmg of flak and launchers are factors on the old per-ship values.
const F3D_WPN = {
  "AAAf": {"k":"afbeam","large":false,"type":"slash","dmg":0.4,"chargeT":800,"fireT":120,"coolT":600},
  "BFred": {"k":"beam","large":true,"type":"static","dmg":2.45,"chargeT":846,"fireT":210,"coolT":200},
  "BGreen": {"k":"beam","large":true,"type":"static","dmg":1.4,"chargeT":800,"fireT":120,"coolT":600},
  "BVas": {"k":"beam","large":true,"type":"static","dmg":1.283,"chargeT":800,"fireT":111,"coolT":480},
  "Bgreen": {"k":"beam","large":true,"type":"static","dmg":1.4,"chargeT":800,"fireT":120,"coolT":600},
  "FighterKiller": {"k":"missile","rate":1.6,"dmg":1.0},
  "Fusion Mortar": {"k":"missile","rate":0.2,"dmg":0.8},
  "Heavy Flak": {"k":"flak","rate":10.0,"dmg":1.67},
  "LRED": {"k":"beam","large":true,"type":"static","dmg":0.7,"chargeT":686,"fireT":210,"coolT":200},
  "LRed": {"k":"beam","large":true,"type":"static","dmg":0.7,"chargeT":686,"fireT":210,"coolT":200},
  "Long Range Flak": {"k":"flak","rate":3.33,"dmg":0.67},
  "Lred": {"k":"beam","large":true,"type":"static","dmg":0.7,"chargeT":686,"fireT":210,"coolT":200},
  "MX-52": {"k":"missile","rate":6.0,"dmg":0.25},
  "MjolnirBeam": {"k":"beam","large":true,"type":"static","dmg":0.875,"chargeT":800,"fireT":120,"coolT":140},
  "Piranha": {"k":"missile","rate":1.0,"dmg":1.0},
  "SAAA": {"k":"afbeam","large":false,"type":"slash","dmg":0.257,"chargeT":533,"fireT":168,"coolT":545},
  "SGreen": {"k":"beam","large":true,"type":"static","dmg":0.245,"chargeT":343,"fireT":75,"coolT":900},
  "SRED": {"k":"beam","large":true,"type":"static","dmg":0.233,"chargeT":343,"fireT":114,"coolT":500},
  "SRed": {"k":"beam","large":true,"type":"static","dmg":0.233,"chargeT":343,"fireT":114,"coolT":500},
  "SVas": {"k":"beam","large":true,"type":"static","dmg":0.408,"chargeT":343,"fireT":75,"coolT":400},
  "Shivan Cluster": {"k":"missile","rate":4.0,"dmg":0.6},
  "Shivan Heavy Flak": {"k":"flak","rate":10.0,"dmg":1.67},
  "Shivan Heavy Laser": {"k":"gun","rate":0.5,"spd":7.77,"dmg":3.43,"aspd":12.95,"admg":7.71,"w":7,"h":3,"scat":1,"shiv":1},
  "Shivan Light Laser": {"k":"gun","rate":0.3,"spd":7.36,"dmg":1.83,"aspd":12.27,"admg":4.11,"w":7,"h":3,"scat":1,"shiv":1},
  "Shivan Long Range Flak": {"k":"flak","rate":3.33,"dmg":0.67},
  "Shivan Megafunk Turret": {"k":"gun","rate":3.4,"spd":2.0,"dmg":36,"aspd":3.3,"admg":81,"w":14,"h":14,"scat":1.5,"big":true,"shiv":1},
  "Shivan Standard Flak": {"k":"flak","rate":1.0,"dmg":1.0},
  "Shivan Turret Laser": {"k":"gun","rate":1.2,"spd":4.1,"dmg":11,"aspd":6.8,"admg":25,"w":9,"h":4,"scat":1,"shiv":1},
  "Sred": {"k":"beam","large":true,"type":"static","dmg":0.233,"chargeT":343,"fireT":114,"coolT":500},
  "Standard Flak": {"k":"flak","rate":1.0,"dmg":1.0},
  "Subach HL-7": {"k":"gun","rate":0.2,"spd":7.36,"dmg":3.43,"aspd":12.27,"admg":7.71,"w":7,"h":3,"scat":1,"shiv":0},
  "TerSlash": {"k":"beam","large":true,"type":"slash","dmg":0.408,"chargeT":686,"fireT":60,"coolT":200},
  "Terran Huge Turret": {"k":"gun","rate":3,"spd":2.9,"dmg":23,"aspd":4.8,"admg":52,"w":12,"h":12,"scat":3,"big":true,"shiv":0},
  "Terran Turret": {"k":"gun","rate":1,"spd":4.5,"dmg":8,"aspd":7.5,"admg":18,"w":8,"h":4,"scat":1,"shiv":0},
  "Terran Turret Weak": {"k":"gun","rate":1.0,"spd":4.5,"dmg":8.0,"aspd":7.5,"admg":18.0,"w":8,"h":4,"scat":1,"shiv":0},
  "VSlash": {"k":"beam","large":true,"type":"slash","dmg":0.875,"chargeT":686,"fireT":60,"coolT":200},
  "Vasudan Huge Turret": {"k":"gun","rate":3,"spd":2.9,"dmg":23,"aspd":4.8,"admg":52,"w":12,"h":12,"scat":3,"big":true,"shiv":0},
  "Vasudan Turret": {"k":"gun","rate":1,"spd":4.5,"dmg":8,"aspd":7.5,"admg":18,"w":8,"h":4,"scat":1,"shiv":0},
  "Vasudan Turret Weak": {"k":"gun","rate":1.0,"spd":4.5,"dmg":8.0,"aspd":7.5,"admg":18.0,"w":8,"h":4,"scat":1,"shiv":0}
};
const F3D_GUNS = {
  crcain:{"beams":[[-0.939,0.124,-0.002,0.05,-0.94,0.32,"SAAA"],[0.43,0.413,-0.001,0.02,-1.0,0.0,"SRed"]],"primary":[[0.593,0.256,-0.38,-0.78,0.62,-0.01,"Shivan Light Laser"],[-0.16,-0.173,-0.002,-0.0,0.59,-0.8,"Shivan Light Laser"],[0.587,0.251,0.379,0.83,0.56,-0.05,"Shivan Light Laser"],[0.815,0.371,0.356,0.09,-1.0,0.03,"Shivan Heavy Laser"],[0.819,0.376,-0.357,0.02,-1.0,0.09,"Shivan Heavy Laser"]],"secondary":[[-0.121,0.089,0.189,0.91,0.42,0.02,"FighterKiller"],[-0.122,0.089,-0.191,-0.83,0.56,0.01,"FighterKiller"]],"thr":[[-0.921,-0.013,0.0193],[-0.931,0.029,0.0193],[-0.997,-0.01,0.0329],[-0.993,0.035,0.0354],[-0.931,0.07,0.0193],[-0.993,0.087,0.0354]]},
  crlilith:{"beams":[[-0.939,0.121,-0.002,0.05,-0.94,0.32,"SAAA"],[0.43,0.416,-0.001,0.02,-1.0,0.0,"LRed"]],"primary":[[0.819,0.373,-0.357,0.02,-1.0,0.09,"Shivan Turret Laser"],[0.593,0.252,-0.38,-0.78,0.62,-0.01,"Shivan Turret Laser"],[-0.16,-0.177,-0.002,-0.0,0.59,-0.8,"Shivan Turret Laser"],[0.587,0.248,0.379,0.83,0.56,-0.05,"Shivan Turret Laser"],[0.815,0.367,0.356,0.09,-1.0,0.03,"Shivan Turret Laser"]],"secondary":[[-0.121,0.085,0.189,0.91,0.42,0.02,"Shivan Cluster"],[-0.122,0.085,-0.191,-0.83,0.56,0.01,"Shivan Cluster"]],"thr":[[-0.921,-0.016,0.0193],[-0.931,0.026,0.0193],[-0.997,-0.014,0.0329],[-0.993,0.032,0.0354],[-0.931,0.067,0.0193],[-0.993,0.084,0.0354]]},
  crrakshasa:{"beams":[[0.894,-0.013,-0.21,-0.03,-0.08,1.0,"SRed"],[0.877,-0.223,-0.047,-0.03,-0.08,1.0,"SRed"],[0.877,-0.223,0.047,-0.03,-0.08,1.0,"SRed"],[-0.322,0.127,-0.0,0.01,0.07,1.0,"SAAA"]],"primary":[[0.894,-0.013,0.21,-0.03,-0.08,1.0,"Shivan Turret Laser"],[0.462,-0.1,-0.162,-0.81,0.58,0.01,"Shivan Turret Laser"],[0.462,0.033,-0.098,-0.2,-0.98,0.04,"Shivan Turret Laser"],[-0.694,-0.103,-0.216,-0.9,0.4,-0.19,"Shivan Heavy Laser"],[0.462,-0.1,0.163,0.81,0.58,0.01,"Shivan Heavy Laser"],[-0.526,-0.316,-0.0,0.01,1.0,0.1,"Shivan Turret Laser"],[-0.705,0.133,0.0,0.04,-0.95,-0.3,"Shivan Turret Laser"],[-0.694,-0.103,0.216,0.9,0.4,-0.19,"Shivan Turret Laser"],[-0.857,-0.26,0.0,0.04,-0.73,-0.68,"Shivan Turret Laser"],[0.462,0.033,0.098,0.2,-0.98,0.04,"Shivan Turret Laser"]],"thr":[[-0.904,-0.192,0.0245],[-0.899,-0.097,0.0302]]},
  comoloch:{"beams":[[0.599,0.175,0.0,-0.04,-0.72,0.69,"SRED"],[-0.048,-0.166,-0.0,-0.04,1.0,0.03,"SRED"],[-0.232,0.139,0.0,-0.04,-0.95,0.31,"SRED"]],"primary":[[0.225,-0.217,-0.0,-0.04,1.0,0.03,"Shivan Turret Laser"],[0.359,0.123,0.111,-0.04,-0.28,-0.96,"Shivan Turret Laser"],[-0.514,0.022,-0.059,-0.97,-0.11,-0.24,"Shivan Turret Laser"],[0.823,-0.102,-0.001,-0.04,0.45,0.89,"Shivan Turret Laser"],[-0.835,-0.215,-0.0,-0.04,0.59,-0.81,"Shivan Turret Laser"]],"flak":[[0.11,-0.021,-0.054,-0.63,-0.78,0.04,"Shivan Standard Flak"],[0.11,-0.021,0.054,0.57,-0.82,0.04,"Shivan Standard Flak"],[0.359,0.124,-0.112,-0.04,-0.28,-0.96,"Shivan Standard Flak"],[-0.911,-0.163,-0.0,-0.04,-0.95,-0.31,"Shivan Heavy Flak"]],"secondary":[[-0.513,0.023,0.059,0.97,-0.11,-0.24,"Piranha"],[-0.121,0.049,0.0,-0.04,-0.82,0.57,"MX-52"],[0.843,-0.043,-0.055,-0.04,1.0,0.03,"MX-52"],[0.843,-0.043,0.055,-0.04,1.0,0.03,"Shivan Cluster"]],"thr":[[-0.678,0.057,0.0073],[-0.747,-0.082,0.0138],[-0.719,-0.032,0.0249],[0.374,0.091,0.0184],[0.374,0.196,0.0267]]},
  dedemon:{"beams":[[0.726,0.149,0.159,0.84,0.53,0.1,"LRED"],[0.726,0.149,-0.159,-0.82,0.56,0.1,"LRED"],[0.23,-0.185,0.0,0.0,1.0,0.0,"SRED"],[0.043,0.126,0.421,0.99,-0.06,0.1,"SAAA"],[0.043,0.126,-0.421,-0.99,-0.06,0.1,"SAAA"]],"primary":[[0.033,0.363,0.0,0.0,-1.0,0.0,"Shivan Megafunk Turret"],[-0.125,-0.587,0.0,0.0,1.0,0.0,"Shivan Megafunk Turret"],[0.96,0.146,-0.077,0.03,0.48,0.88,"Shivan Turret Laser"],[-0.429,0.401,0.384,0.91,-0.4,-0.03,"Shivan Turret Laser"],[-0.429,0.401,-0.384,-0.91,-0.4,-0.03,"Shivan Turret Laser"],[-0.662,-0.236,0.0,0.0,1.0,0.0,"Shivan Turret Laser"],[-0.928,-0.092,0.127,0.35,0.86,-0.37,"Shivan Turret Laser"],[-0.928,-0.092,-0.127,-0.35,0.86,-0.37,"Shivan Turret Laser"],[-0.966,-0.034,0.122,0.18,-0.7,-0.69,"Shivan Turret Laser"],[-0.966,-0.034,-0.122,-0.18,-0.7,-0.69,"Shivan Turret Laser"],[-0.203,-0.476,0.088,0.76,0.6,0.26,"Shivan Turret Laser"],[-0.203,-0.476,-0.086,-0.76,0.6,0.26,"Shivan Turret Laser"]],"flak":[[-0.566,0.061,0.452,0.95,0.15,-0.27,"Shivan Standard Flak"],[-0.566,0.061,-0.452,-0.95,0.15,-0.27,"Shivan Standard Flak"],[0.96,0.146,0.077,0.03,0.48,0.88,"Shivan Standard Flak"],[-0.331,0.201,-0.0,0.0,-0.68,-0.74,"Shivan Standard Flak"]],"secondary":[[0.399,0.034,-0.175,-0.71,-0.63,0.32,"FighterKiller"],[0.399,0.034,0.175,0.71,-0.63,0.32,"FighterKiller"],[0.965,0.16,0.0,0.0,0.5,0.87,"FighterKiller"],[-0.268,-0.388,-0.117,0.5,-0.81,0.3,"FighterKiller"],[-0.267,-0.388,0.119,-0.16,-0.8,0.57,"FighterKiller"]],"thr":[[-0.715,-0.087,0.0191],[-0.715,-0.058,0.0143],[-0.715,-0.044,0.0191],[-0.715,-0.015,0.0143],[-0.715,0.012,0.0191],[-0.715,0.051,0.0238],[-0.715,0.081,0.0095],[-0.747,-0.11,0.0191],[-0.747,-0.127,0.0191],[-0.747,-0.143,0.0191],[-0.747,-0.024,0.0191],[-0.747,-0.04,0.0191],[-0.747,-0.008,0.0191],[-0.747,-0.065,0.0191],[-0.747,-0.081,0.0191],[-0.747,0.016,0.0095]]},
  deravana:{"beams":[[1.001,0.109,-0.146,0.0,0.0,1.0,"LRed"],[1.001,0.109,0.006,-0.0,0.0,1.0,"LRed"],[-0.386,-0.545,-0.373,0.0,0.0,1.0,"SRed"],[-0.356,-0.572,0.061,0.0,0.0,1.0,"SRed"],[-0.428,0.269,-0.114,-0.0,0.0,1.0,"SAAA"],[-0.902,-0.386,-0.18,-0.08,0.93,-0.36,"SAAA"]],"primary":[[0.454,-0.074,0.043,1.0,0.02,-0.0,"Shivan Turret Laser"],[0.034,-0.134,-0.006,0.75,0.66,0.0,"Shivan Turret Laser"],[-0.626,-0.218,0.213,0.68,0.73,0.0,"Shivan Turret Laser"],[0.455,-0.073,-0.184,-0.98,-0.02,0.21,"Shivan Turret Laser"],[-0.42,0.033,-0.305,-0.92,-0.17,0.35,"Shivan Turret Laser"],[-0.279,-0.281,-0.187,-0.73,0.39,0.57,"Shivan Turret Laser"],[-0.492,-0.307,-0.297,-0.85,0.52,0.08,"Shivan Turret Laser"],[-0.261,0.264,0.413,0.98,-0.14,0.13,"Shivan Turret Laser"],[0.544,0.027,0.123,0.94,-0.34,0.08,"Shivan Turret Laser"],[0.543,0.028,-0.263,-0.94,-0.34,0.07,"Shivan Turret Laser"],[-0.224,0.176,0.295,-0.83,-0.55,-0.01,"Shivan Turret Laser"],[0.562,0.103,-0.199,-0.16,-0.99,0.01,"Shivan Turret Laser"],[0.562,0.103,0.06,0.09,-1.0,0.01,"Shivan Turret Laser"],[-0.413,-0.143,0.192,0.96,-0.02,0.28,"Shivan Turret Laser"],[-0.738,0.05,-0.307,-0.97,-0.2,-0.16,"Shivan Turret Laser"],[-0.105,-0.157,0.002,0.68,0.68,0.26,"Shivan Turret Laser"],[-0.283,-0.277,0.015,0.62,0.69,0.37,"Shivan Turret Laser"]],"flak":[[-0.248,0.052,0.464,0.92,0.38,0.02,"Shivan Standard Flak"],[-0.907,-0.32,-0.199,0.01,-0.94,-0.35,"Shivan Standard Flak"],[0.034,-0.133,-0.135,-0.8,0.59,0.0,"Shivan Standard Flak"],[-0.378,0.029,-0.086,0.01,-1.0,0.07,"Shivan Standard Flak"],[-0.755,-0.047,-0.256,-0.03,-0.27,-0.96,"Shivan Standard Flak"]],"secondary":[[0.42,-0.206,-0.07,-0.05,0.96,-0.26,"Shivan Cluster"],[-0.63,-0.151,0.287,1.0,-0.0,0.07,"FighterKiller"]],"thr":[[-0.83,-0.101,0.0104],[-0.83,-0.084,0.0104],[-0.83,-0.166,0.0104],[-0.811,-0.127,0.013],[-0.811,-0.142,0.013],[-0.777,-0.12,0.013],[-0.777,-0.093,0.013]]},
  sdlucifer:{"beams":[[0.897,0.154,0.403,-0.0,0.0,1.0,"Sred"],[0.897,0.154,-0.403,-0.0,0.0,1.0,"Sred"]],"primary":[[0.417,-0.1,0.106,0.62,0.78,0.0,"Shivan Turret Laser"],[0.42,-0.097,-0.11,-0.62,0.78,0.0,"Shivan Turret Laser"],[-0.616,-0.032,0.199,0.91,0.0,0.41,"Shivan Turret Laser"],[-0.616,-0.032,-0.199,-0.91,0.0,0.41,"Shivan Turret Laser"],[0.048,0.14,-0.002,-0.0,-1.0,0.0,"Shivan Turret Laser"],[0.094,-0.151,-0.002,-0.0,1.0,0.0,"Shivan Turret Laser"],[-0.598,0.137,-0.002,-0.0,-1.0,0.0,"Shivan Turret Laser"],[-0.834,-0.057,-0.002,-0.0,1.0,0.0,"Shivan Turret Laser"],[-0.977,0.142,-0.002,-0.0,-1.0,0.0,"Shivan Turret Laser"],[-0.047,-0.032,0.21,0.81,0.51,0.3,"Shivan Turret Laser"],[-0.047,-0.032,-0.21,-0.81,0.51,0.3,"Shivan Turret Laser"]],"secondary":[[0.781,-0.117,0.0,-0.0,0.87,0.49,"FighterKiller"],[-0.606,-0.234,-0.0,-0.0,0.65,-0.76,"FighterKiller"],[0.945,0.115,0.001,-0.0,0.0,1.0,"Shivan Cluster"],[0.313,0.312,-0.001,-0.0,0.0,1.0,"Shivan Cluster"]],"thr":[[0.239,0.252,0.0188],[0.234,0.296,0.0188],[0.228,0.339,0.0188],[-0.806,-0.055,0.0255],[-0.848,-0.026,0.0255],[-0.892,0.004,0.0255]]},
  sdsathanas:{"beams":[[0.993,-0.033,-0.264,-0.03,-0.1,0.99,"BFred"],[0.993,-0.033,0.264,-0.15,-0.1,0.98,"BFred"],[0.97,0.232,-0.15,-0.03,-0.1,0.99,"BFred"],[0.971,0.232,0.154,-0.03,-0.1,0.99,"BFred"],[0.102,-0.0,0.186,0.51,0.75,0.42,"SAAA"],[-0.154,0.158,0.108,0.01,-1.0,0.0,"SAAA"],[-0.154,0.158,-0.108,0.01,-1.0,0.0,"SAAA"],[0.103,-0.0,-0.186,0.4,0.8,0.45,"SAAA"],[-0.791,-0.148,-0.373,-0.75,0.66,0.0,"SAAA"],[-0.692,-0.283,-0.152,-0.61,0.79,0.01,"SAAA"],[-0.791,-0.148,0.373,0.53,0.79,-0.32,"SAAA"],[-0.692,-0.284,0.153,0.41,0.91,-0.0,"SAAA"],[-0.664,0.182,-0.001,0.01,-1.0,0.0,"Lred"]],"primary":[[0.192,-0.231,-0.368,0.01,-1.0,0.0,"Shivan Turret Laser"],[0.191,-0.231,0.368,0.01,-1.0,0.01,"Shivan Turret Laser"],[-0.188,-0.195,0.042,1.0,-0.09,-0.0,"Shivan Turret Laser"],[0.117,-0.055,0.044,1.0,-0.09,-0.0,"Shivan Turret Laser"],[-0.102,0.052,-0.269,0.0,-0.95,-0.31,"Shivan Turret Laser"],[-0.541,-0.318,0.05,1.0,-0.09,-0.0,"Shivan Turret Laser"],[-0.397,-0.01,-0.306,0.02,-0.96,-0.27,"Shivan Turret Laser"],[-0.578,-0.037,-0.338,-0.0,-0.92,-0.38,"Shivan Turret Laser"],[-0.777,-0.172,-0.22,0.36,-0.85,-0.38,"Shivan Turret Laser"],[-0.397,-0.009,0.306,-0.02,-0.96,-0.27,"Shivan Turret Laser"],[0.226,0.329,-0.215,0.01,1.0,-0.01,"Shivan Turret Laser"],[-0.099,0.103,-0.252,-1.0,-0.03,0.0,"Shivan Turret Laser"],[-0.777,-0.172,0.22,-0.36,-0.85,-0.38,"Shivan Turret Laser"],[-0.101,0.103,0.253,1.0,-0.03,0.02,"Shivan Turret Laser"],[-0.045,-0.014,-0.249,-1.0,-0.05,0.0,"Shivan Turret Laser"],[-0.286,-0.203,-0.121,-1.0,-0.05,0.0,"Shivan Turret Laser"],[-0.551,-0.147,-0.311,-0.53,0.85,-0.02,"Shivan Turret Laser"],[-0.468,-0.253,-0.137,-1.0,-0.05,0.0,"Shivan Turret Laser"],[-0.044,-0.015,0.25,0.41,0.75,0.52,"Shivan Turret Laser"],[-0.36,-0.107,0.281,0.47,0.84,0.28,"Shivan Turret Laser"],[-0.285,-0.207,0.121,0.53,0.85,0.06,"Shivan Turret Laser"],[-0.476,0.062,-0.189,-1.0,-0.02,-0.01,"Shivan Turret Laser"]],"flak":[[-0.578,-0.037,0.338,0.0,-0.92,-0.38,"Shivan Standard Flak"],[0.226,0.329,0.215,0.01,1.0,-0.01,"Shivan Standard Flak"],[0.117,-0.055,-0.045,-1.0,-0.09,-0.0,"Shivan Standard Flak"],[-0.188,-0.195,-0.043,-1.0,-0.09,-0.0,"Shivan Standard Flak"],[-0.541,-0.318,-0.05,-1.0,-0.09,-0.0,"Shivan Standard Flak"],[0.019,-0.075,-0.115,-1.0,-0.05,0.0,"Shivan Standard Flak"],[-0.195,-0.058,-0.26,-0.62,0.78,-0.0,"Shivan Standard Flak"],[-0.131,-0.139,-0.114,-1.0,-0.05,0.0,"Shivan Standard Flak"],[-0.359,-0.107,-0.28,-0.46,0.84,0.28,"Shivan Standard Flak"],[-0.194,-0.058,0.26,0.52,0.82,0.23,"Shivan Standard Flak"],[0.411,0.014,0.02,0.0,1.0,0.0,"Shivan Long Range Flak"],[0.411,0.014,-0.02,0.0,1.0,0.0,"Shivan Long Range Flak"],[-0.476,0.063,0.189,1.0,-0.03,-0.01,"Shivan Standard Flak"]],"secondary":[[-0.102,0.052,0.269,-0.0,-0.95,-0.31,"Piranha"],[0.023,-0.079,0.116,0.43,0.77,0.47,"Piranha"],[-0.13,-0.143,0.114,0.53,0.85,0.06,"Piranha"],[-0.551,-0.147,0.312,0.51,0.84,-0.16,"Piranha"],[-0.468,-0.256,0.137,0.56,0.83,0.09,"Piranha"]],"thr":[[-0.75,0.098,0.0169],[-0.859,-0.358,0.0271],[0.135,-0.288,0.0237],[0.169,0.368,0.0237]]},
  crfenris:{"primary":[[0.748,-0.288,-0.0,0.0,1.0,-0.03,"Terran Turret"],[0.87,-0.008,-0.0,-0.0,-0.82,0.57,"Terran Turret"],[-0.879,-0.229,-0.173,-0.66,0.75,-0.0,"Terran Turret"],[-0.914,0.049,-0.185,-0.68,-0.74,0.0,"Terran Turret"],[-0.878,-0.23,0.175,0.64,0.77,0.0,"Terran Turret"],[-0.914,0.049,0.185,0.66,-0.75,-0.0,"Terran Turret"],[0.286,-0.093,0.278,1.0,0.0,0.0,"Terran Turret"],[0.286,-0.093,-0.277,-1.0,0.0,0.0,"Terran Turret"]],"secondary":[[-0.054,0.073,-0.0,0.0,-1.0,0.0,"Fusion Mortar"]],"thr":[[-0.965,-0.186,0.012],[-0.964,0.021,0.012],[-0.962,-0.144,0.012],[-0.962,-0.163,0.008],[-0.962,-0.021,0.012],[-0.962,-0.002,0.008],[-0.959,-0.083,0.0223]]},
  crleviathan:{"beams":[[-0.899,-0.251,-0.207,-0.66,0.75,-0.0,"AAAf"],[-0.899,-0.004,-0.207,-0.68,-0.74,0.0,"AAAf"],[-0.899,-0.253,0.207,0.64,0.77,0.0,"AAAf"],[-0.899,-0.004,0.206,0.66,-0.75,-0.0,"AAAf"],[0.896,-0.086,0.0,-0.0,-0.82,0.57,"SGreen"]],"primary":[[0.67,-0.316,-0.0,0.0,1.0,-0.03,"Terran Turret"],[0.309,-0.111,0.277,1.0,0.0,0.0,"Terran Turret"],[0.309,-0.111,-0.277,-1.0,0.0,0.0,"Terran Turret"]],"secondary":[[0.044,0.727,-0.0,0.0,-1.0,0.0,"Fusion Mortar"]],"thr":[[-0.968,-0.231,0.012],[-0.968,-0.024,0.012],[-0.966,-0.189,0.012],[-0.966,-0.208,0.008],[-0.966,-0.065,0.012],[-0.966,-0.047,0.008],[-0.962,-0.128,0.0224]]},
  craeolus:{"beams":[[0.118,0.039,-0.227,-1.0,0.0,0.0,"AAAf"],[-0.06,0.039,0.227,1.0,0.0,0.0,"AAAf"],[0.734,0.017,-0.181,0.01,-0.04,1.0,"SGreen"],[0.737,0.011,0.179,0.01,-0.04,1.0,"SGreen"]],"primary":[[0.171,0.333,0.0,0.0,-1.0,0.0,"Terran Huge Turret"],[0.072,-0.318,-0.002,0.0,1.0,0.0,"Terran Huge Turret"]],"flak":[[-0.885,0.302,-0.002,0.0,-1.0,0.0,"Standard Flak"],[-0.81,-0.333,-0.002,0.0,1.0,0.0,"Standard Flak"],[0.677,-0.27,-0.002,0.0,1.0,0.0,"Standard Flak"],[0.874,0.311,-0.002,0.0,-1.0,0.0,"Standard Flak"],[-0.06,0.039,-0.227,-1.0,0.0,0.0,"Standard Flak"],[0.118,0.039,0.227,1.0,0.0,0.0,"Standard Flak"]],"thr":[[0.331,0.137,0.0217],[0.331,0.173,0.0181],[-0.272,0.091,0.0094],[-0.272,0.114,0.0094],[-0.272,0.136,0.0094],[-0.977,-0.145,0.0217],[-0.985,-0.109,0.0217],[-0.992,-0.073,0.0217],[-0.985,-0.112,0.0181],[-0.977,-0.152,0.0181],[-0.977,0.123,0.0145],[-0.977,0.094,0.0145],[-0.985,0.065,0.0145],[-0.992,0.036,0.0145]]},
  codeimos:{"beams":[[-0.644,0.147,0.106,0.01,-0.87,-0.49,"AAAf"],[-0.644,0.146,-0.106,-0.01,-0.87,-0.49,"AAAf"],[-0.819,-0.153,-0.197,-0.98,0.18,-0.08,"TerSlash"],[-0.819,-0.153,0.197,0.98,0.18,-0.08,"TerSlash"],[0.746,0.032,0.15,1.0,0.0,0.0,"AAAf"],[0.746,0.032,-0.149,-1.0,0.0,0.0,"AAAf"],[0.969,0.015,-0.07,-0.46,-0.16,0.88,"TerSlash"],[0.969,0.015,0.07,0.46,-0.16,0.88,"TerSlash"]],"primary":[[0.277,-0.359,-0.0,0.0,1.0,0.0,"Terran Huge Turret"],[0.657,-0.332,-0.0,0.0,1.0,0.0,"Terran Huge Turret"],[-0.576,-0.429,-0.0,0.0,1.0,0.0,"Terran Huge Turret"],[0.29,0.295,0.0,0.0,-1.0,0.0,"Terran Huge Turret"],[0.369,0.034,0.162,1.0,0.0,0.0,"Terran Turret"],[0.556,0.034,0.162,1.0,0.0,0.0,"Terran Turret"],[0.369,0.034,-0.162,-1.0,0.0,0.0,"Terran Turret"],[0.556,0.034,-0.162,-1.0,0.0,0.0,"Terran Turret"],[0.929,0.247,-0.069,-0.37,-0.47,0.8,"Terran Turret"],[0.929,0.247,0.069,0.37,-0.47,0.8,"Terran Turret"]],"flak":[[-0.017,0.352,-0.059,-0.01,-0.95,0.31,"Standard Flak"],[-0.017,0.352,0.059,0.01,-0.95,0.31,"Standard Flak"],[-0.997,-0.169,0.152,0.0,0.0,-1.0,"Standard Flak"],[-0.997,-0.169,-0.152,0.0,0.0,-1.0,"Standard Flak"],[0.18,0.036,0.149,1.0,0.0,0.0,"Standard Flak"],[0.18,0.036,-0.149,-1.0,0.0,0.0,"Standard Flak"]],"secondary":[[-0.423,-0.156,-0.205,-0.98,0.14,0.12,"Piranha"],[-0.423,-0.156,0.205,0.98,0.14,0.12,"Piranha"]],"thr":[[-0.861,-0.167,0.0338],[-0.861,-0.032,0.0338],[-0.407,0.348,0.0282],[0.719,0.241,0.0197]]},
  deorionright:{"beams":[[0.856,0.096,0.055,0.0,-1.0,0.0,"BGreen"],[0.451,-0.004,0.208,1.0,0.0,0.0,"TerSlash"],[0.524,-0.028,-0.093,-1.0,0.0,0.0,"TerSlash"],[0.388,-0.163,0.05,0.0,1.0,0.0,"AAAf"],[-0.165,-0.039,0.256,1.0,0.0,0.0,"Bgreen"],[-0.06,0.286,0.117,0.0,-1.0,0.0,"AAAf"],[-0.72,0.137,-0.293,-1.0,0.0,0.0,"BGreen"],[-0.799,0.185,0.292,1.0,0.0,0.0,"TerSlash"],[-0.831,0.329,0.104,0.0,-1.0,0.0,"AAAf"]],"primary":[[0.831,-0.205,0.054,0.0,1.0,0.0,"Terran Huge Turret"],[0.6,-0.205,0.114,0.0,1.0,0.0,"Terran Huge Turret"],[-0.182,0.356,0.02,0.0,-1.0,0.0,"Terran Huge Turret"],[-0.759,-0.356,0.099,0.0,1.0,0.0,"Terran Huge Turret"],[-0.198,-0.19,0.055,0.0,1.0,0.0,"Terran Turret"],[-0.198,0.169,-0.243,-1.0,0.0,0.0,"Terran Turret"],[-0.882,-0.165,0.137,0.0,0.39,-0.92,"Terran Turret"]],"thr":[[-1.013,0.017,0.0385],[-1.013,0.065,0.0385],[-1.013,0.155,0.0385],[-1.013,0.208,0.0385]]},
  dehecate:{"beams":[[-0.774,0.042,0.361,0.97,-0.25,0.0,"AAAf"],[-0.774,0.042,-0.361,-0.97,-0.25,0.0,"AAAf"],[0.597,-0.137,-0.325,-0.97,-0.25,0.0,"AAAf"],[0.597,-0.137,0.325,0.97,-0.25,0.0,"AAAf"],[-0.417,-0.222,0.552,0.24,0.97,-0.03,"AAAf"],[0.989,-0.23,-0.0,0.04,0.02,1.0,"BGreen"],[-0.417,-0.222,-0.552,-0.24,0.97,-0.03,"AAAf"],[0.932,-0.002,-0.0,0.04,-0.32,0.95,"TerSlash"],[0.193,-0.064,0.057,0.96,-0.28,-0.07,"TerSlash"],[0.193,-0.064,-0.057,-0.96,-0.28,-0.07,"TerSlash"],[-0.674,-0.198,-0.0,-0.07,-0.78,-0.62,"TerSlash"]],"primary":[[-0.606,0.044,0.362,0.97,-0.25,0.0,"Terran Huge Turret"],[-0.606,0.044,-0.362,-0.97,-0.25,0.0,"Terran Turret"],[0.598,0.169,-0.327,-0.97,-0.25,0.0,"Terran Turret"],[0.598,0.169,0.327,0.97,-0.25,0.0,"Terran Turret"],[-0.377,0.344,-0.043,-0.97,-0.25,0.0,"Terran Turret"],[-0.377,0.344,0.043,0.97,-0.25,0.0,"Terran Turret"]],"flak":[[0.415,-0.438,0.0,0.01,0.99,0.12,"Heavy Flak"],[0.753,-0.422,0.0,0.01,0.99,0.12,"Long Range Flak"],[-0.293,-0.528,0.0,0.01,0.99,0.12,"Heavy Flak"],[-0.735,-0.537,0.0,0.01,0.99,0.12,"Long Range Flak"],[0.228,0.097,0.0,0.0,-1.0,0.0,"Standard Flak"],[0.85,0.139,0.0,0.0,-1.0,0.0,"Standard Flak"],[-0.606,0.045,0.19,-0.97,-0.25,0.0,"Standard Flak"],[-0.606,0.045,-0.19,0.97,-0.25,0.0,"Standard Flak"],[-0.449,-0.165,-0.588,-0.2,-0.98,-0.02,"Standard Flak"],[-0.449,-0.165,0.588,0.2,-0.98,-0.02,"Standard Flak"]],"thr":[[-0.971,-0.236,0.0277],[-0.962,-0.167,0.0277],[-0.954,-0.073,0.0277],[-0.973,-0.003,0.0277],[0.271,-0.164,0.0138],[0.271,-0.192,0.0138],[0.271,-0.219,0.0138],[0.271,-0.182,0.0092],[-0.498,0.177,0.0138],[0.758,0.044,0.0184],[-0.498,0.155,0.0138],[-0.498,0.198,0.0138],[-0.496,0.149,0.0092]]},
  craten:{"beams":[[0.595,0.048,0.317,0.0,1.0,0.0,"AAAf"],[0.595,0.048,-0.317,0.0,1.0,0.0,"AAAf"]],"primary":[[-0.492,-0.297,-0.0,0.0,1.0,0.0,"Subach HL-7"],[0.531,0.294,0.0,0.0,-1.0,0.0,"Subach HL-7"],[-0.727,0.029,-0.234,-0.87,-0.5,0.0,"Vasudan Turret"],[-0.727,0.029,0.234,0.77,-0.64,0.0,"Vasudan Turret"]],"thr":[[-0.92,-0.031,0.0385],[-0.886,0.065,0.0353]]},
  crmentu:{"beams":[[-0.942,0.066,-0.0,0.01,0.0,-1.0,"AAAf"],[0.148,-0.263,-0.191,-0.28,0.96,0.0,"AAAf"],[0.148,-0.263,0.191,0.57,0.82,-0.01,"AAAf"]],"primary":[[0.108,-0.156,-0.308,-0.77,0.63,0.1,"Vasudan Turret"],[0.107,-0.156,0.308,0.91,0.41,-0.0,"Vasudan Turret"],[-0.254,-0.141,-0.199,-0.72,0.69,0.1,"Vasudan Turret"],[-0.255,-0.142,0.198,0.72,0.69,0.1,"Vasudan Turret"],[-0.571,-0.098,-0.188,-0.68,0.72,0.1,"Vasudan Turret"],[-0.572,-0.101,0.19,0.68,0.72,0.1,"Vasudan Turret"],[-0.678,0.344,0.001,0.0,-1.0,0.0,"Vasudan Huge Turret"],[0.435,0.183,-0.192,0.0,-1.0,0.0,"Vasudan Turret"],[0.434,0.182,0.193,0.0,-1.0,0.0,"Subach HL-7"],[-0.368,-0.238,-0.0,0.0,1.0,-0.1,"Vasudan Huge Turret"]],"flak":[[0.502,-0.108,-0.31,-0.79,0.61,-0.06,"Standard Flak"],[0.507,-0.111,0.301,0.81,0.58,-0.0,"Standard Flak"],[-0.804,-0.068,0.0,-0.0,0.89,-0.45,"Standard Flak"]],"thr":[[-0.972,-0.004,0.0125],[-0.969,-0.004,0.0125],[-0.972,0.116,0.0125],[-0.969,0.116,0.0125]]},
  cosobek:{"beams":[[-0.836,0.28,0.348,-0.44,0.32,-0.84,"AAAf"],[0.53,0.154,-0.137,-0.57,0.8,0.19,"AAAf"],[-0.836,0.28,-0.347,0.43,0.32,-0.85,"AAAf"],[0.837,0.216,-0.09,-0.47,0.81,0.34,"VSlash"],[0.53,0.153,0.136,0.56,0.81,0.19,"AAAf"],[0.837,0.216,0.088,0.46,0.82,0.34,"VSlash"]],"primary":[[-0.231,0.122,-0.084,-0.79,0.61,-0.0,"Vasudan Turret"],[-0.048,0.134,-0.112,-0.75,0.66,-0.07,"Vasudan Turret"],[-0.231,0.121,0.084,0.8,0.59,0.0,"Vasudan Turret"],[-0.048,0.134,0.113,0.84,0.54,-0.07,"Vasudan Turret"],[-0.232,0.224,-0.071,-0.68,-0.74,0.0,"Vasudan Turret"],[-0.032,0.231,-0.092,-0.41,-0.91,-0.06,"Vasudan Turret"],[-0.232,0.224,0.071,0.65,-0.76,0.0,"Vasudan Turret"],[-0.032,0.231,0.092,0.41,-0.91,-0.06,"Vasudan Turret"],[0.666,0.392,-0.133,0.0,-1.0,0.0,"Vasudan Huge Turret"],[0.666,0.392,0.133,0.0,-1.0,0.0,"Vasudan Huge Turret"],[0.093,-0.039,-0.0,0.0,1.0,0.0,"Vasudan Huge Turret"]],"flak":[[0.234,0.079,-0.137,-0.54,0.84,-0.0,"Standard Flak"],[0.234,0.079,0.137,0.57,0.82,0.0,"Standard Flak"],[-0.58,0.089,-0.116,-0.93,0.21,0.29,"Standard Flak"],[-0.58,0.086,0.117,0.94,0.2,0.27,"Standard Flak"],[-0.658,0.401,-0.0,0.0,-1.0,0.0,"Standard Flak"]],"thr":[[-0.807,0.251,0.0197],[-0.807,0.143,0.0197],[0.196,0.286,0.0229]]},
  detyphon:{"beams":[[-0.687,-0.103,0.0,0.0,0.42,-0.91,"AAAf"],[-0.673,0.131,0.0,0.0,-0.45,-0.89,"BVas"],[0.766,0.033,0.0,0.0,-0.32,0.95,"AAAf"],[0.775,-0.033,0.0,0.0,0.37,0.93,"BVas"]],"primary":[[0.729,-0.053,0.033,0.0,1.0,0.0,"Vasudan Huge Turret"],[0.729,-0.053,-0.033,0.0,1.0,0.0,"Vasudan Huge Turret"]],"flak":[[0.132,0.079,-0.178,0.0,-1.0,0.0,"Standard Flak"],[0.132,0.079,0.178,0.0,-1.0,0.0,"Standard Flak"],[0.132,-0.151,0.178,0.0,1.0,0.0,"Standard Flak"],[0.132,-0.151,-0.178,0.0,1.0,0.0,"Standard Flak"],[-0.833,-0.008,-0.0,0.0,-0.45,-0.89,"Standard Flak"]],"secondary":[[-0.384,0.209,0.112,1.0,0.0,0.0,"FighterKiller"],[-0.384,0.209,-0.112,-1.0,0.0,0.0,"FighterKiller"],[-0.117,-0.139,0.0,0.0,0.45,-0.89,"FighterKiller"],[-0.026,0.137,0.0,0.0,-0.45,0.89,"FighterKiller"]],"thr":[[-0.78,0.067,0.0074],[-0.799,0.038,0.0139],[-0.799,0.082,0.0167]]},
  dehatshepsut:{"beams":[[-0.126,0.284,-0.0,0.0,-1.0,0.0,"SVas"],[0.824,0.044,-0.0,-0.0,0.85,0.52,"BVas"],[0.013,-0.244,-0.0,-0.0,1.0,-0.02,"BVas"],[-0.96,-0.124,-0.0,-0.0,0.58,-0.81,"BVas"],[0.846,0.138,0.161,0.0,1.0,0.0,"AAAf"],[-0.798,0.083,0.232,0.23,-0.93,0.29,"AAAf"],[-0.798,0.085,-0.232,-0.27,-0.91,0.32,"AAAf"]],"primary":[[0.506,0.194,-0.264,-0.01,1.0,-0.03,"Vasudan Huge Turret"],[-0.368,0.192,-0.225,-0.47,-0.84,-0.27,"Vasudan Huge Turret"],[-0.668,-0.2,-0.0,0.08,0.91,-0.41,"Vasudan Huge Turret"],[0.506,0.194,0.264,0.01,1.0,-0.03,"Vasudan Huge Turret"],[-0.368,0.192,0.225,0.47,-0.84,-0.27,"Vasudan Huge Turret"],[-0.943,-0.076,0.0,0.06,-0.57,-0.82,"Vasudan Huge Turret"]],"flak":[[0.344,-0.083,-0.063,-0.89,0.37,0.28,"Standard Flak"],[0.054,0.058,-0.225,-0.81,-0.37,0.45,"Standard Flak"],[-0.062,-0.159,-0.162,-0.99,0.02,0.14,"Standard Flak"],[-0.247,-0.008,-0.326,-0.6,0.8,0.02,"Standard Flak"],[-0.426,-0.1,-0.145,-0.74,0.12,0.66,"Standard Flak"],[0.34,-0.083,0.058,0.89,0.37,0.28,"Standard Flak"],[0.054,0.058,0.224,0.81,-0.37,0.45,"Standard Flak"],[-0.06,-0.158,0.162,0.99,0.02,0.14,"Standard Flak"],[-0.254,-0.006,0.33,0.6,0.8,0.02,"Standard Flak"],[-0.429,-0.1,0.144,0.74,0.12,0.66,"Standard Flak"]],"secondary":[[-0.291,-0.257,0.0,0.0,1.0,-0.03,"Fusion Mortar"],[0.771,0.276,0.209,0.0,-1.0,0.02,"Fusion Mortar"],[0.771,0.276,-0.208,0.0,-1.0,0.02,"Fusion Mortar"],[-0.799,-0.089,-0.203,0.0,1.0,-0.03,"Fusion Mortar"],[-0.799,-0.088,0.208,0.0,1.0,-0.03,"Fusion Mortar"]],"thr":[[-0.942,0.042,0.0285],[-0.96,0.061,0.019],[-0.95,0.045,0.0238]]},
  sdcolossus:{"beams":[[-0.199,0.052,0.0,0.0,0.0,-1.0,"AAAf"],[-0.201,0.195,0.0,-0.0,0.0,-1.0,"AAAf"],[-0.127,0.108,0.001,0.0,-0.29,0.96,"AAAf"],[0.9,-0.166,-0.063,0.0,1.0,0.0,"AAAf"],[0.9,-0.166,0.063,0.0,1.0,0.0,"AAAf"],[0.227,-0.237,0.094,0.0,0.84,0.54,"AAAf"],[0.227,-0.237,-0.094,0.0,0.84,0.54,"AAAf"],[-0.118,0.281,0.001,-0.0,0.0,1.0,"AAAf"],[-0.973,-0.13,0.151,0.0,1.0,0.0,"AAAf"],[-0.973,-0.13,-0.151,0.0,1.0,0.0,"AAAf"],[-0.759,-0.086,0.195,1.0,-0.0,0.0,"TerSlash"],[-0.908,-0.086,0.195,1.0,-0.0,0.0,"TerSlash"],[-0.294,-0.249,0.093,0.0,1.0,0.0,"BGreen"],[-0.294,-0.249,-0.092,0.0,1.0,-0.0,"BGreen"],[-0.908,-0.088,-0.196,-1.0,0.0,0.0,"TerSlash"],[-0.759,-0.088,-0.196,-1.0,-0.0,0.0,"TerSlash"],[-0.136,0.001,0.092,0.68,-0.74,0.0,"BGreen"],[-0.136,0.001,-0.093,-0.68,-0.73,-0.0,"BGreen"],[0.185,-0.161,0.201,0.96,-0.0,0.29,"BGreen"],[0.186,-0.161,-0.203,-0.96,-0.0,0.29,"BGreen"],[0.689,-0.109,0.074,0.82,-0.57,0.0,"TerSlash"],[0.689,-0.11,-0.076,-0.83,-0.56,0.0,"TerSlash"],[0.811,-0.224,0.0,0.0,0.89,0.45,"TerSlash"]],"primary":[[0.763,0.06,-0.001,0.0,-1.0,0.0,"Terran Huge Turret"],[0.66,-0.268,-0.001,0.0,1.0,0.0,"Terran Huge Turret"],[-0.439,-0.246,0.098,0.0,1.0,0.0,"Terran Huge Turret"],[-0.724,0.005,0.133,0.0,-1.0,0.0,"Terran Huge Turret"],[0.009,-0.333,-0.001,0.0,1.0,0.0,"Terran Huge Turret"],[0.721,0.063,-0.001,0.0,-1.0,0.0,"Terran Huge Turret"],[-0.195,0.334,0.059,0.0,-1.0,0.0,"Terran Huge Turret"],[-0.195,0.333,-0.061,0.0,-1.0,0.0,"Terran Huge Turret"],[-0.439,-0.246,-0.1,0.0,1.0,0.0,"Terran Huge Turret"],[-0.724,0.005,-0.135,0.0,-1.0,0.0,"Terran Huge Turret"],[0.657,-0.157,-0.119,-1.0,0.0,0.0,"Terran Turret"],[-0.881,0.002,-0.134,0.0,-1.0,-0.0,"Terran Turret"],[-0.153,0.212,-0.089,-1.0,0.0,0.0,"Terran Turret"],[-0.153,0.212,0.089,1.0,-0.0,0.0,"Terran Turret"],[-0.142,0.057,0.093,1.0,-0.0,0.0,"Terran Turret"],[-0.881,0.002,0.134,0.0,-1.0,-0.0,"Terran Turret"],[0.657,-0.157,0.118,1.0,-0.0,0.0,"Terran Turret"],[0.752,-0.174,0.123,1.0,-0.0,0.0,"Terran Turret"]],"flak":[[0.601,-0.212,-0.048,0.0,1.0,0.0,"Standard Flak"],[0.133,-0.161,0.207,1.0,0.0,0.0,"Standard Flak"],[0.602,-0.212,0.048,0.0,1.0,0.0,"Standard Flak"],[-0.142,0.057,-0.093,-1.0,-0.0,0.0,"Standard Flak"],[0.07,-0.161,0.206,1.0,0.0,0.0,"Standard Flak"],[0.003,-0.161,0.201,1.0,0.0,0.0,"Standard Flak"],[-0.068,-0.161,0.191,1.0,-0.0,0.0,"Standard Flak"],[0.132,-0.161,-0.207,-1.0,0.0,0.0,"Standard Flak"],[0.07,-0.161,-0.206,-1.0,-0.0,0.0,"Standard Flak"],[0.003,-0.161,-0.202,-1.0,0.0,0.0,"Standard Flak"],[-0.069,-0.161,-0.191,-1.0,-0.0,0.0,"Standard Flak"],[0.752,-0.174,-0.123,-1.0,0.0,0.0,"Standard Flak"]],"secondary":[[-0.545,-0.157,0.144,1.0,0.0,0.0,"Piranha"],[-0.847,-0.122,0.0,0.0,0.93,0.37,"MX-52"],[0.284,-0.093,0.073,-0.0,-0.68,0.74,"MX-52"],[-0.708,-0.082,0.0,-0.0,0.93,0.37,"MX-52"],[-0.731,-0.15,0.144,1.0,0.0,0.0,"MX-52"],[-0.731,-0.151,-0.144,-1.0,0.0,0.0,"MX-52"],[-0.545,-0.158,-0.144,-1.0,0.0,0.0,"Piranha"],[0.69,-0.041,-0.026,1.0,0.0,-0.04,"MX-52"],[0.69,-0.041,0.026,1.0,0.0,0.04,"MX-52"],[0.284,-0.093,-0.073,0.0,-0.68,0.74,"MX-52"]],"thr":[[-0.946,-0.083,0.0196],[-0.967,-0.083,0.0196],[-0.977,-0.083,0.0196],[-0.934,-0.149,0.0131],[-0.947,-0.188,0.0131],[-0.25,0.278,0.0114],[-0.275,0.278,0.0114],[0.652,0.019,0.0082],[0.653,-0.01,0.0082]]},
  sgmjolnir:{"beams":[[0.105,-1.17,0.0,0.0,1.0,0.0,"MjolnirBeam"]]},
  cacharybdis:{"primary":[[-0.593,0.185,0.204,1.0,0.0,0.0,"Terran Turret Weak"],[-0.593,0.185,-0.204,-1.0,0.0,0.0,"Terran Turret Weak"],[-0.404,-0.124,-0.105,-1.0,0.0,0.0,"Terran Turret Weak"],[-0.404,-0.124,0.105,1.0,0.0,0.0,"Subach HL-7"],[-0.706,-0.156,-0.0,0.0,0.32,-0.95,"Terran Turret Weak"],[0.115,-0.103,-0.0,0.0,0.71,0.71,"Terran Turret Weak"]],"thr":[[-0.97,-0.056,0.0152],[-0.995,0.025,0.0223],[-0.995,0.033,0.0223],[-0.995,0.107,0.0223],[-0.995,0.114,0.0223]]},
  casetekh:{"primary":[[-0.234,0.235,0.0,-0.01,-1.0,-0.09,"Vasudan Turret Weak"],[-0.801,-0.299,0.005,0.06,0.99,0.13,"Vasudan Turret Weak"],[0.777,0.064,0.005,0.06,-0.99,-0.1,"Vasudan Turret Weak"]],"thr":[[-0.866,0.082,0.0236],[-0.866,0.092,0.0236]]},
  coiceni:{"beams":[[0.798,-0.01,0.216,1.0,0.0,0.1,"BGreen"],[-0.26,-0.169,0.254,0.93,0.37,0.0,"BGreen"],[0.798,-0.01,-0.223,-1.0,0.0,0.1,"BGreen"]],"primary":[[-0.195,0.51,0.161,0.0,-1.0,0.0,"Terran Huge Turret"],[0.505,0.016,0.142,1.0,0.0,0.0,"Terran Huge Turret"],[-0.166,0.215,-0.0,0.0,-1.0,0.0,"Terran Huge Turret"],[-0.149,0.292,0.219,1.0,0.0,0.0,"Terran Huge Turret"],[0.987,0.023,-0.063,-0.1,0.0,1.0,"Terran Huge Turret"],[0.987,0.023,0.062,0.1,0.0,1.0,"Terran Huge Turret"],[-0.744,0.334,0.0,0.0,-1.0,0.0,"Terran Huge Turret"],[0.505,0.016,-0.148,-1.0,0.0,0.0,"Terran Turret"],[0.14,-0.169,-0.248,-0.93,0.37,0.0,"Terran Turret"],[-0.837,0.194,-0.0,0.0,-0.51,-0.86,"Terran Turret"],[-0.906,-0.048,-0.0,0.0,0.82,-0.57,"Terran Turret"],[-0.689,-0.222,0.0,0.0,1.0,0.0,"Terran Turret"],[-0.343,-0.529,-0.0,0.0,1.0,0.0,"Terran Turret"],[0.004,-0.14,0.001,0.0,1.0,0.0,"Terran Turret"],[0.301,-0.336,0.0,0.0,1.0,0.0,"Terran Turret"],[0.762,0.399,-0.0,0.0,-1.0,0.0,"Terran Turret"]],"flak":[[0.14,-0.169,0.244,0.93,0.37,0.0,"Standard Flak"],[-0.804,-0.031,0.123,0.89,0.45,0.0,"Standard Flak"]],"secondary":[[-0.26,-0.169,-0.259,-0.93,0.37,0.0,"Piranha"],[-0.149,0.292,-0.226,-1.0,0.0,0.0,"MX-52"],[-0.804,-0.031,-0.128,-0.89,0.45,0.0,"Piranha"],[-0.195,0.51,-0.161,0.0,-1.0,0.0,"MX-52"]],"thr":[[-0.382,-0.249,0.0363],[-0.391,-0.241,0.0363],[-0.382,-0.251,0.0363],[-0.317,-0.085,0.0407],[-0.518,0.329,0.0363],[-0.519,0.332,0.0363]]}
};
const F3D_MNT = {};
// The mount lists of a hull, built from her model's turrets. Needs the
// sprite's proportions (the lists are measured against its box); until it
// has loaded the old lists are given. The old ones stay on .raw (the
// Lucifer's reactors sit on her old gun mounts).
const F3D_GUN_SND = {'Shivan Light Laser': 'wpn_shivan_light', 'Shivan Heavy Laser': 'wpn_shivan_heavy',
                     'Subach HL-7': 'wpn_subach', 'Terran Huge Turret': 'wpn_tht', 'Vasudan Huge Turret': 'wpn_tht'};
function f3dMounts(key, m){
  if(!m || !key) return m;
  const t = F3D_GUNS[key]; if(!t) return m;
  const c0 = F3D_MNT[key]; if(c0) return c0;
  const img = (typeof IMGS !== 'undefined') ? IMGS[key] : null;
  if(!img || !img.width || !img.height) return m;
  const asp = img.width/img.height, sg = m.facing === 'left' ? -1 : 1;
  const pos = function(q){ return {dx: sg*q[0], dy: q[1]*asp, mx: q[2], n3: [q[3], q[4], q[5]], wpn: q[6]}; };
  const c = Object.assign({}, m, {beams: [], primary: [], flak: [], secondary: [], raw: m});
  for(const q of (t.beams || [])){
    const w = F3D_WPN[q[6]];
    c.beams.push(Object.assign(pos(q), {large: w.large, type: w.type, dmg: w.dmg,
      chargeT: w.chargeT, fireT: w.fireT, coolT: w.coolT}));
  }
  for(const q of (t.primary || [])){
    const w = F3D_WPN[q[6]];
    const g = {rate: w.rate, spd: w.spd, dmg: w.dmg, aspd: w.aspd, admg: w.admg, w: w.w, h: w.h,
               scat: w.scat, big: !!w.big,
               snd: F3D_GUN_SND[q[6]] || (w.shiv ? 'wpn_shivan_turret' : (w.big ? 'wpn_tht' : 'wpn_terran_turret'))};
    c.primary.push(Object.assign(pos(q), {g: g}));
  }
  for(const q of (t.flak || [])){ const w = F3D_WPN[q[6]]; c.flak.push(Object.assign(pos(q), {fk: {rate: w.rate, dmg: w.dmg}})); }
  for(const q of (t.secondary || [])){ const w = F3D_WPN[q[6]]; c.secondary.push(Object.assign(pos(q), {sec: {rate: w.rate, dmg: w.dmg}})); }
  // the engine glows of the model (FUEL), aft, sized by their glow radius
  if(t.thr && t.thr.length) c.thrusters = t.thr.map(function(q){
    return {dx: sg*q[0], dy: q[1]*asp, w: Math.min(0.6, 2*q[2]*asp), len: Math.max(0.12, Math.min(0.5, 10*q[2])), dir: -sg};
  });
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
      // v199: the coarse level keeps its shape for the hit map (f3dMask)
      if(tag === 'lo' && p.kind !== 'skip'){
        (L.cpu = L.cpu || []).push({pos: new Int16Array(data.slice(p.pos, p.pos + p.nv*6)),
          idx: p.big ? new Uint32Array(data.slice(p.idx, p.idx + p.ni*4)) : new Uint16Array(data.slice(p.idx, p.idx + p.ni*2))});
      }
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
          // v200: decoded by the browser off the game's thread, then handed
          // to the graphics card in the upload queue - one at a time between
          // frames instead of all in one (Silvio: hitches when a big ship
          // warped in, the Moloch in M77).
          const up = function(){
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
          im.onload = function(){
            const go = function(){ f3dUpload(up); };
            if(im.decode) im.decode().then(go, go); else go();
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
// ── UPLOADS AND LOADING UP FRONT (v200) ──────────────────────
// Handing a texture to the graphics card blocks the game while it runs
// (measured in M77: the Moloch's fine level, eight uploads one after the
// other). The queue does them between frames, a few milliseconds at a time.
const F3D_UPQ = [];
let F3D_PUMP = false;
const F3D_UP_MS = 6;
function f3dNow(){ return (typeof performance !== 'undefined') ? performance.now() : Date.now(); }
function f3dUpload(job){
  F3D_UPQ.push(job);
  if(!F3D_PUMP){ F3D_PUMP = true; setTimeout(f3dPump, 0); }
}
function f3dPump(){
  const t0 = f3dNow();
  // at least one job per turn, more while there is time
  do { const j = F3D_UPQ.shift(); try{ j(); }catch(e){ F3D.err = String(e && e.message || e); } }
  while(F3D_UPQ.length && f3dNow() - t0 < F3D_UP_MS);
  if(F3D_UPQ.length) setTimeout(f3dPump, 4); else F3D_PUMP = false;
}
// Silvio: load every 3D capital ship before the game starts, not when she
// warps in. Starts as soon as the title shows; the title shows how far it
// is. A ship not ready by the time she appears loads as before.
const F3D_PRE = {on: false, done: false, n: 0, of: 0};
function f3dPreload(){
  if(F3D_PRE.on || F3D.off || typeof document === 'undefined' || !f3dInit()) return;
  F3D_PRE.on = true; F3D_PRE.of = F3D_KEYS.length;
  const tick = function(){
    if(!F3D.gl){ F3D_PRE.done = true; return; }      // context lost: as before
    let n = 0;
    for(const k of F3D_KEYS){ const m = f3dModel(k); if(m.full && m.full.state !== 'loading') n++; }
    F3D_PRE.n = n;
    if(n < F3D_KEYS.length) setTimeout(tick, 250);
    else { F3D_PRE.done = true; f3dWarm(); }
  };
  tick();
}
// Every loaded ship drawn once, out of sight: the graphics driver sets a
// texture up for good only the first time it is used (in sight: what lies
// outside the picture is never drawn), and that first time
// cost a frame of 0.4 s at the start of a mission (measured).
function f3dWarm(){
  const gl = F3D.gl; if(!gl) return;
  const ks = F3D_KEYS.slice();
  const one = function(){
    const k = ks.shift(); if(!k || gl !== F3D.gl) return;
    try{
      const L = f3dReadyLevel(k);
      if(L && typeof IMGS !== 'undefined' && IMGS[k]){
        const e = {img: k, sc: 64/Math.max(1, IMGS[k].width), flip: false, ang: 0};
        f3dRender([{e: e, L: L, x: W/2, y: H/2, a: 1, clip: null}], true);
      }
    }catch(er){}
    setTimeout(one, 30);
  };
  one();
}
// The bar on the title screen while the ships load.
function f3dPreloadBar(){
  if(!F3D_PRE.on) f3dPreload();
  if(!F3D_PRE.on || F3D_PRE.done) return;
  const w = 220, h = 4, x = W/2 - w/2, y = H - 34;
  ctx.save();
  ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = (typeof TH === 'function') ? TH('glow') : '#7cf';
  ctx.fillRect(x, y, w*F3D_PRE.n/Math.max(1, F3D_PRE.of), h);
  ctx.fillStyle = (typeof TH === 'function') ? TH('text') : '#ccc';
  ctx.font = (typeof thValue === 'function') ? thValue(11, false) : '11px sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
  ctx.fillText('LOADING 3D SHIPS ' + F3D_PRE.n + '/' + F3D_PRE.of, W/2, y - 4);
  ctx.restore();
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
function f3dRender(items, warm){
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
  if(!warm) ctx.drawImage(can, 0, 0, W, H);
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
// v199 (Silvio: model and the old data do not always line up): a ship
// drawn from her model is hit where her model is. The hit map of the sprite
// (buildMask, 20_render.js) is replaced by the model's side view, drawn from
// the coarse level into the same box - once per hull, when it has loaded.
// What of the model sticks out of the sprite's box (the Sathanas' claws)
// is not in the map yet.
const F3D_MASKED = {};
function f3dMask(skey, mkey){
  if(F3D_MASKED[skey] || typeof MASKS === 'undefined' || typeof document === 'undefined') return;
  const m = F3D.models[mkey], L = m && m.lo;
  const img = IMGS[skey];
  if(!L || L.state !== 'ready' || !L.cpu || !img || !img.width) return;
  F3D_MASKED[skey] = true;
  try{
    const f = Math.min(1, MASK_MAX/Math.max(img.width, img.height));
    const mw = Math.max(1, Math.round(img.width*f)), mh = Math.max(1, Math.round(img.height*f));
    const hd = L.head, e = hd.ext/32767, s = mw/hd.size[2];
    const sg = spriteFacing(skey) === 'left' ? -1 : 1;
    // v199b (Silvio: a few seconds of still picture at the start): filled
    // here pixel by pixel instead of as one canvas path - a path of 90,000
    // triangles held the Sathanas up for seconds. Each triangle sets the
    // map cells whose centre it covers, at most a few dozen cells apiece.
    const bits = new Uint8Array(mw*mh);
    for(const pt of L.cpu){
      const P = pt.pos, I = pt.idx;
      for(let i = 0; i + 2 < I.length; i += 3){
        const a = I[i]*3, b = I[i+1]*3, c3 = I[i+2]*3;
        const ax = mw/2 + sg*P[a+2]*e*s, ay = mh/2 - P[a+1]*e*s;
        const bx = mw/2 + sg*P[b+2]*e*s, by = mh/2 - P[b+1]*e*s;
        const cx = mw/2 + sg*P[c3+2]*e*s, cy = mh/2 - P[c3+1]*e*s;
        const ar = (bx-ax)*(cy-ay) - (by-ay)*(cx-ax);
        const x0 = Math.max(0, Math.floor(Math.min(ax, bx, cx))), x1 = Math.min(mw-1, Math.ceil(Math.max(ax, bx, cx)));
        const y0 = Math.max(0, Math.floor(Math.min(ay, by, cy))), y1 = Math.min(mh-1, Math.ceil(Math.max(ay, by, cy)));
        if(x1 < x0 || y1 < y0) continue;
        if(Math.abs(ar) < 1e-6){
          // edge-on: a sliver still counts where it lies (thin spines)
          bits[(Math.min(mh-1, Math.max(0, Math.round(ay))))*mw + Math.min(mw-1, Math.max(0, Math.round(ax)))] = 1;
          continue;
        }
        const sgn = ar > 0 ? 1 : -1;
        for(let y = y0; y <= y1; y++){
          const py = y + 0.5;
          for(let x = x0; x <= x1; x++){
            const px = x + 0.5;
            const w0 = ((bx-ax)*(py-ay) - (by-ay)*(px-ax))*sgn;
            const w1 = ((cx-bx)*(py-by) - (cy-by)*(px-bx))*sgn;
            const w2 = ((ax-cx)*(py-cy) - (ay-cy)*(px-cx))*sgn;
            if(w0 >= 0 && w1 >= 0 && w2 >= 0) bits[y*mw + x] = 1;
          }
        }
        // a triangle smaller than a cell still marks the cell it sits in
        if(x1 - x0 <= 1 && y1 - y0 <= 1){
          const mx = Math.min(mw-1, Math.max(0, Math.floor((ax+bx+cx)/3))), my = Math.min(mh-1, Math.max(0, Math.floor((ay+by+cy)/3)));
          bits[my*mw + mx] = 1;
        }
      }
    }
    MASKS[skey] = {w: mw, h: mh, bits: bits, model: true};
    // the hull's box is read off the map again (40_world.js)
    if(typeof SPR_BOX !== 'undefined') delete SPR_BOX[skey];
  }catch(err){ F3D.err = String(err && err.message || err); }
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
    if(!F3D_MASKED[e.img]) f3dMask(e.img, key);
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
