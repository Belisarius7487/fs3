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
  'cacharybdis', 'casetekh', 'coiceni',
  // v201: the NTF reskins, with their own models and maps
  'ntfcraeolus', 'ntfcodeimos', 'ntfcrfenris', 'ntfcrleviathan', 'ntfdeorion', 'ntfdehecate',
  // v202: the remaining large hulls - the Hades, Faustus and Hippocrates,
  // freighters, transports, installations, gas miners and the Knossos
  'sdhades', 'scfaustus', 'mehippocrates', 'frasmodeus', 'frbast', 'frbes', 'frchronos', 'frdis', 'frmaat',
  'frmephisto', 'frposeidon', 'frsatis', 'frtriton', 'trargo', 'trazrael', 'trelysium', 'trisis',
  'inarcadia', 'incommnode', 'inknossos', 'gmanuket', 'gmrahu', 'gmzephyrus',
  // v204 (Silvio): the GTNB Pharos is the MediaVPs' nav buoy (navbuoy.pof),
  // a mast with solar panels - the sprite shows her from the side
  'inpharos'];
// v203 (the 2.5D plan, step 2): the small craft as well - fighters and
// bombers of every side, the player's hull, sentries, support ships,
// escape pods and containers. They load their maps at 512 pixels (they are
// small on the field), keep the hit maps of their sprites and turn in 3D:
// where the sprite was mirrored the hull rolls half round her length, and
// she banks into her turns (f3dTurnRoll).
const F3D_SMALL = ['boamun', 'boartemisdh', 'boboanerges', 'bonahema', 'bonephilim', 'boseraphim', 'boshaitan', 'botaurvi', 'bozeus',
  'ephermes', 'epra', 'fcmeson', 'fcsac3', 'fcsc5', 'fctac1', 'fctc2', 'fctctri', 'fctsc2', 'fcttc1', 'fcvac4', 'fcvac5', 'fcvc3',
  'fiaeshma', 'fianubis', 'fiastaroth', 'fibasilisk', 'fidragon', 'filoki', 'fimanticore', 'fiscorpion',
  'sgalastor', 'sgankh', 'sgbelial', 'sgcerberus', 'sgtrident', 'sgwatchdog', 'sucentaur', 'suhygeia', 'sunephthys', 'suscarab',
  // the player's hulls (flown by the AI as well)
  'fitoth', 'fihorus', 'boosiris', 'fiserapis', 'fiseth', 'bobakha', 'fitauret', 'bosekhmet', 'fiptah', 'fimyrmidon',
  'fiperseus', 'fiherc', 'boartemis', 'fihercmk2', 'bomedusa', 'fierinyes', 'boursa', 'fiares', 'fipegasus', 'fiulysses',
  'fiapollo', 'fivalyrie', 'boathena', 'fimara'];
const F3D_SMALLSET = new Set(F3D_SMALL);
for(const k of F3D_SMALL) F3D_KEYS.push(k);
function f3dSmall(key){ return F3D_SMALLSET.has(key); }
const F3D_ALIAS = {deorionleft: 'deorionright', inknossos45deg: 'inknossos', inknossosfront: 'inknossos'};
// v202: hulls not seen from the side - the turn about the vertical from the
// side view (radians). The Knossos sprites show her face on and at 45
// degrees; the Arcadia and the Unknown Device are seen from the front.
const F3D_VIEW = {inknossosfront: Math.PI/2, inknossos45deg: Math.PI/4, inarcadia: Math.PI/2, incommnode: Math.PI/2,
  // v203: small craft whose sprites show another side (silsmall.py): the
  // Meson bomb is drawn stern first, the SC 5 face on
  fcmeson: Math.PI, fcsc5: Math.PI/2};
// and the turn about her own length (radians), should a picture need it
const F3D_ROLL = {};
// v198: animated glow maps, as the MediaVPs have them (Silvio: the Ravana's
// cable bundle pulses). The frames lie in one picture, cols x rows, row by
// row: <tex>_ga512.webp / _ga1024.webp next to the other maps.
const F3D_GANIM = {ravanapulse: {n: 30, fps: 25, cols: 8, rows: 4}};
// v208: a long lens. With real sizes a destroyer is thousands of units long;
// at 30 degrees she reached through the camera. 1.2 degrees keeps every hull
// in front of it and looks nearly flat, as the drafts did (Silvio).
// v209: a real perspective like the 2.5D demo (Silvio). The camera still
// looks straight down; f3dVP puts the eye so that the play plane z = 0
// lies on the screen exactly as the 2D field does, so shots, effects, the
// HUD and the pointer are not distorted. What sticks out of the plane
// (above it: nearer) is drawn larger, what lies under it smaller.
const F3D_FOV = 40*Math.PI/180;
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
// weapon, turret index (v201)] in the model's own space, halved length = 1 (z along the hull,
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
  "LTerSlash": {"k":"beam","large":true,"type":"slash","dmg":0.175,"chargeT":686,"fireT":66,"coolT":200},
  "Long Range Flak": {"k":"flak","rate":3.33,"dmg":0.67},
  "Lred": {"k":"beam","large":true,"type":"static","dmg":0.7,"chargeT":686,"fireT":210,"coolT":200},
  "MX-52": {"k":"missile","rate":6.0,"dmg":0.25},
  "Mekhu HL-7": {"k":"gun","rate":0.15,"spd":7.94,"dmg":2.74,"aspd":13.23,"admg":6.17,"w":7,"h":3,"scat":1,"shiv":0},
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
  crcain:{"beams":[[-0.939,0.124,-0.002,0.05,-0.94,0.32,"SAAA",0],[0.43,0.413,-0.001,0.02,-1.0,0.0,"SRed",6]],"primary":[[0.593,0.256,-0.38,-0.78,0.62,-0.01,"Shivan Light Laser",1],[-0.16,-0.173,-0.002,-0.0,0.59,-0.8,"Shivan Light Laser",2],[0.587,0.251,0.379,0.83,0.56,-0.05,"Shivan Light Laser",3],[0.815,0.371,0.356,0.09,-1.0,0.03,"Shivan Heavy Laser",4],[0.819,0.376,-0.357,0.02,-1.0,0.09,"Shivan Heavy Laser",5]],"secondary":[[-0.121,0.089,0.189,0.91,0.42,0.02,"FighterKiller",7],[-0.122,0.089,-0.191,-0.83,0.56,0.01,"FighterKiller",8]],"thr":[[-0.921,-0.013,0.0193],[-0.931,0.029,0.0193],[-0.997,-0.01,0.0329],[-0.993,0.035,0.0354],[-0.931,0.07,0.0193],[-0.993,0.087,0.0354]]},
  crlilith:{"beams":[[-0.939,0.121,-0.002,0.05,-0.94,0.32,"SAAA",1],[0.43,0.416,-0.001,0.02,-1.0,0.0,"LRed",6]],"primary":[[0.819,0.373,-0.357,0.02,-1.0,0.09,"Shivan Turret Laser",0],[0.593,0.252,-0.38,-0.78,0.62,-0.01,"Shivan Turret Laser",2],[-0.16,-0.177,-0.002,-0.0,0.59,-0.8,"Shivan Turret Laser",3],[0.587,0.248,0.379,0.83,0.56,-0.05,"Shivan Turret Laser",4],[0.815,0.367,0.356,0.09,-1.0,0.03,"Shivan Turret Laser",5]],"secondary":[[-0.121,0.085,0.189,0.91,0.42,0.02,"Shivan Cluster",7],[-0.122,0.085,-0.191,-0.83,0.56,0.01,"Shivan Cluster",8]],"thr":[[-0.921,-0.016,0.0193],[-0.931,0.026,0.0193],[-0.997,-0.014,0.0329],[-0.993,0.032,0.0354],[-0.931,0.067,0.0193],[-0.993,0.084,0.0354]]},
  crrakshasa:{"beams":[[0.894,-0.013,-0.21,-0.03,-0.08,1.0,"SRed",0],[0.877,-0.223,-0.047,-0.03,-0.08,1.0,"SRed",1],[0.877,-0.223,0.047,-0.03,-0.08,1.0,"SRed",2],[-0.322,0.127,-0.0,0.01,0.07,1.0,"SAAA",8]],"primary":[[0.894,-0.013,0.21,-0.03,-0.08,1.0,"Shivan Turret Laser",3],[0.462,-0.1,-0.162,-0.81,0.58,0.01,"Shivan Turret Laser",4],[0.462,0.033,-0.098,-0.2,-0.98,0.04,"Shivan Turret Laser",5],[-0.694,-0.103,-0.216,-0.9,0.4,-0.19,"Shivan Heavy Laser",6],[0.462,-0.1,0.163,0.81,0.58,0.01,"Shivan Heavy Laser",7],[-0.526,-0.316,-0.0,0.01,1.0,0.1,"Shivan Turret Laser",9],[-0.705,0.133,0.0,0.04,-0.95,-0.3,"Shivan Turret Laser",10],[-0.694,-0.103,0.216,0.9,0.4,-0.19,"Shivan Turret Laser",11],[-0.857,-0.26,0.0,0.04,-0.73,-0.68,"Shivan Turret Laser",12],[0.462,0.033,0.098,0.2,-0.98,0.04,"Shivan Turret Laser",13]],"thr":[[-0.904,-0.192,0.0245],[-0.899,-0.097,0.0302]]},
  comoloch:{"beams":[[0.599,0.175,0.0,-0.04,-0.72,0.69,"SRED",0],[-0.048,-0.166,-0.0,-0.04,1.0,0.03,"SRED",1],[-0.232,0.139,0.0,-0.04,-0.95,0.31,"SRED",2]],"primary":[[0.225,-0.217,-0.0,-0.04,1.0,0.03,"Shivan Turret Laser",6],[0.359,0.123,0.111,-0.04,-0.28,-0.96,"Shivan Turret Laser",7],[-0.514,0.022,-0.059,-0.97,-0.11,-0.24,"Shivan Turret Laser",9],[0.823,-0.102,-0.001,-0.04,0.45,0.89,"Shivan Turret Laser",12],[-0.835,-0.215,-0.0,-0.04,0.59,-0.81,"Shivan Turret Laser",13]],"flak":[[0.11,-0.021,-0.054,-0.63,-0.78,0.04,"Shivan Standard Flak",3],[0.11,-0.021,0.054,0.57,-0.82,0.04,"Shivan Standard Flak",4],[0.359,0.124,-0.112,-0.04,-0.28,-0.96,"Shivan Standard Flak",5],[-0.911,-0.163,-0.0,-0.04,-0.95,-0.31,"Shivan Heavy Flak",10]],"secondary":[[-0.513,0.023,0.059,0.97,-0.11,-0.24,"Piranha",8],[-0.121,0.049,0.0,-0.04,-0.82,0.57,"MX-52",11],[0.843,-0.043,-0.055,-0.04,1.0,0.03,"MX-52",14],[0.843,-0.043,0.055,-0.04,1.0,0.03,"Shivan Cluster",15]],"thr":[[-0.678,0.057,0.0073],[-0.747,-0.082,0.0138],[-0.719,-0.032,0.0249],[0.374,0.091,0.0184],[0.374,0.196,0.0267]]},
  dedemon:{"beams":[[0.726,0.149,0.159,0.84,0.53,0.1,"LRED",0],[0.726,0.149,-0.159,-0.82,0.56,0.1,"LRED",1],[0.23,-0.185,0.0,0.0,1.0,0.0,"SRED",2],[0.043,0.126,0.421,0.99,-0.06,0.1,"SAAA",3],[0.043,0.126,-0.421,-0.99,-0.06,0.1,"SAAA",4]],"primary":[[0.033,0.363,0.0,0.0,-1.0,0.0,"Shivan Megafunk Turret",5],[-0.125,-0.587,0.0,0.0,1.0,0.0,"Shivan Megafunk Turret",6],[0.96,0.146,-0.077,0.03,0.48,0.88,"Shivan Turret Laser",9],[-0.429,0.401,0.384,0.91,-0.4,-0.03,"Shivan Turret Laser",12],[-0.429,0.401,-0.384,-0.91,-0.4,-0.03,"Shivan Turret Laser",13],[-0.662,-0.236,0.0,0.0,1.0,0.0,"Shivan Turret Laser",14],[-0.928,-0.092,0.127,0.35,0.86,-0.37,"Shivan Turret Laser",15],[-0.928,-0.092,-0.127,-0.35,0.86,-0.37,"Shivan Turret Laser",16],[-0.966,-0.034,0.122,0.18,-0.7,-0.69,"Shivan Turret Laser",17],[-0.966,-0.034,-0.122,-0.18,-0.7,-0.69,"Shivan Turret Laser",18],[-0.203,-0.476,0.088,0.76,0.6,0.26,"Shivan Turret Laser",19],[-0.203,-0.476,-0.086,-0.76,0.6,0.26,"Shivan Turret Laser",20]],"flak":[[-0.566,0.061,0.452,0.95,0.15,-0.27,"Shivan Standard Flak",7],[-0.566,0.061,-0.452,-0.95,0.15,-0.27,"Shivan Standard Flak",8],[0.96,0.146,0.077,0.03,0.48,0.88,"Shivan Standard Flak",10],[-0.331,0.201,-0.0,0.0,-0.68,-0.74,"Shivan Standard Flak",11]],"secondary":[[0.399,0.034,-0.175,-0.71,-0.63,0.32,"FighterKiller",21],[0.399,0.034,0.175,0.71,-0.63,0.32,"FighterKiller",22],[0.965,0.16,0.0,0.0,0.5,0.87,"FighterKiller",23],[-0.268,-0.388,-0.117,0.5,-0.81,0.3,"FighterKiller",24],[-0.267,-0.388,0.119,-0.16,-0.8,0.57,"FighterKiller",25]],"thr":[[-0.715,-0.087,0.0191],[-0.715,-0.058,0.0143],[-0.715,-0.044,0.0191],[-0.715,-0.015,0.0143],[-0.715,0.012,0.0191],[-0.715,0.051,0.0238],[-0.715,0.081,0.0095],[-0.747,-0.11,0.0191],[-0.747,-0.127,0.0191],[-0.747,-0.143,0.0191],[-0.747,-0.024,0.0191],[-0.747,-0.04,0.0191],[-0.747,-0.008,0.0191],[-0.747,-0.065,0.0191],[-0.747,-0.081,0.0191],[-0.747,0.016,0.0095]]},
  deravana:{"beams":[[1.001,0.109,-0.146,0.0,0.0,1.0,"LRed",0],[1.001,0.109,0.006,-0.0,0.0,1.0,"LRed",1],[-0.386,-0.545,-0.373,0.0,0.0,1.0,"SRed",2],[-0.356,-0.572,0.061,0.0,0.0,1.0,"SRed",3],[-0.428,0.269,-0.114,-0.0,0.0,1.0,"SAAA",4],[-0.902,-0.386,-0.18,-0.08,0.93,-0.36,"SAAA",9]],"primary":[[0.454,-0.074,0.043,1.0,0.02,-0.0,"Shivan Turret Laser",5],[0.034,-0.134,-0.006,0.75,0.66,0.0,"Shivan Turret Laser",6],[-0.626,-0.218,0.213,0.68,0.73,0.0,"Shivan Turret Laser",7],[0.455,-0.073,-0.184,-0.98,-0.02,0.21,"Shivan Turret Laser",12],[-0.42,0.033,-0.305,-0.92,-0.17,0.35,"Shivan Turret Laser",14],[-0.279,-0.281,-0.187,-0.73,0.39,0.57,"Shivan Turret Laser",16],[-0.492,-0.307,-0.297,-0.85,0.52,0.08,"Shivan Turret Laser",17],[-0.261,0.264,0.413,0.98,-0.14,0.13,"Shivan Turret Laser",19],[0.544,0.027,0.123,0.94,-0.34,0.08,"Shivan Turret Laser",20],[0.543,0.028,-0.263,-0.94,-0.34,0.07,"Shivan Turret Laser",21],[-0.224,0.176,0.295,-0.83,-0.55,-0.01,"Shivan Turret Laser",22],[0.562,0.103,-0.199,-0.16,-0.99,0.01,"Shivan Turret Laser",23],[0.562,0.103,0.06,0.09,-1.0,0.01,"Shivan Turret Laser",24],[-0.413,-0.143,0.192,0.96,-0.02,0.28,"Shivan Turret Laser",26],[-0.738,0.05,-0.307,-0.97,-0.2,-0.16,"Shivan Turret Laser",27],[-0.105,-0.157,0.002,0.68,0.68,0.26,"Shivan Turret Laser",28],[-0.283,-0.277,0.015,0.62,0.69,0.37,"Shivan Turret Laser",29]],"flak":[[-0.248,0.052,0.464,0.92,0.38,0.02,"Shivan Standard Flak",8],[-0.907,-0.32,-0.199,0.01,-0.94,-0.35,"Shivan Standard Flak",10],[0.034,-0.133,-0.135,-0.8,0.59,0.0,"Shivan Standard Flak",11],[-0.378,0.029,-0.086,0.01,-1.0,0.07,"Shivan Standard Flak",13],[-0.755,-0.047,-0.256,-0.03,-0.27,-0.96,"Shivan Standard Flak",15]],"secondary":[[0.42,-0.206,-0.07,-0.05,0.96,-0.26,"Shivan Cluster",18],[-0.63,-0.151,0.287,1.0,-0.0,0.07,"FighterKiller",25]],"thr":[[-0.83,-0.101,0.0104],[-0.83,-0.084,0.0104],[-0.83,-0.166,0.0104],[-0.811,-0.127,0.013],[-0.811,-0.142,0.013],[-0.777,-0.12,0.013],[-0.777,-0.093,0.013]]},
  sdlucifer:{"beams":[[0.897,0.154,0.403,-0.0,0.0,1.0,"Sred",0],[0.897,0.154,-0.403,-0.0,0.0,1.0,"Sred",1]],"primary":[[0.417,-0.1,0.106,0.62,0.78,0.0,"Shivan Turret Laser",2],[0.42,-0.097,-0.11,-0.62,0.78,0.0,"Shivan Turret Laser",3],[-0.616,-0.032,0.199,0.91,0.0,0.41,"Shivan Turret Laser",4],[-0.616,-0.032,-0.199,-0.91,0.0,0.41,"Shivan Turret Laser",5],[0.048,0.14,-0.002,-0.0,-1.0,0.0,"Shivan Turret Laser",6],[0.094,-0.151,-0.002,-0.0,1.0,0.0,"Shivan Turret Laser",7],[-0.598,0.137,-0.002,-0.0,-1.0,0.0,"Shivan Turret Laser",8],[-0.834,-0.057,-0.002,-0.0,1.0,0.0,"Shivan Turret Laser",9],[-0.977,0.142,-0.002,-0.0,-1.0,0.0,"Shivan Turret Laser",10],[-0.047,-0.032,0.21,0.81,0.51,0.3,"Shivan Turret Laser",11],[-0.047,-0.032,-0.21,-0.81,0.51,0.3,"Shivan Turret Laser",12]],"secondary":[[0.781,-0.117,0.0,-0.0,0.87,0.49,"FighterKiller",15],[-0.606,-0.234,-0.0,-0.0,0.65,-0.76,"FighterKiller",16],[0.945,0.115,0.001,-0.0,0.0,1.0,"Shivan Cluster",17],[0.313,0.312,-0.001,-0.0,0.0,1.0,"Shivan Cluster",18]],"thr":[[0.239,0.252,0.0188],[0.234,0.296,0.0188],[0.228,0.339,0.0188],[-0.806,-0.055,0.0255],[-0.848,-0.026,0.0255],[-0.892,0.004,0.0255]]},
  sdsathanas:{"beams":[[0.993,-0.033,-0.264,-0.03,-0.1,0.99,"BFred",0],[0.993,-0.033,0.264,-0.15,-0.1,0.98,"BFred",1],[0.97,0.232,-0.15,-0.03,-0.1,0.99,"BFred",2],[0.971,0.232,0.154,-0.03,-0.1,0.99,"BFred",3],[0.102,-0.0,0.186,0.51,0.75,0.42,"SAAA",13],[-0.154,0.158,0.108,0.01,-1.0,0.0,"SAAA",18],[-0.154,0.158,-0.108,0.01,-1.0,0.0,"SAAA",19],[0.103,-0.0,-0.186,0.4,0.8,0.45,"SAAA",26],[-0.791,-0.148,-0.373,-0.75,0.66,0.0,"SAAA",35],[-0.692,-0.283,-0.152,-0.61,0.79,0.01,"SAAA",36],[-0.791,-0.148,0.373,0.53,0.79,-0.32,"SAAA",46],[-0.692,-0.284,0.153,0.41,0.91,-0.0,"SAAA",47],[-0.664,0.182,-0.001,0.01,-1.0,0.0,"Lred",50]],"primary":[[0.192,-0.231,-0.368,0.01,-1.0,0.0,"Shivan Turret Laser",4],[0.191,-0.231,0.368,0.01,-1.0,0.01,"Shivan Turret Laser",5],[-0.188,-0.195,0.042,1.0,-0.09,-0.0,"Shivan Turret Laser",6],[0.117,-0.055,0.044,1.0,-0.09,-0.0,"Shivan Turret Laser",7],[-0.102,0.052,-0.269,0.0,-0.95,-0.31,"Shivan Turret Laser",8],[-0.541,-0.318,0.05,1.0,-0.09,-0.0,"Shivan Turret Laser",9],[-0.397,-0.01,-0.306,0.02,-0.96,-0.27,"Shivan Turret Laser",10],[-0.578,-0.037,-0.338,-0.0,-0.92,-0.38,"Shivan Turret Laser",11],[-0.777,-0.172,-0.22,0.36,-0.85,-0.38,"Shivan Turret Laser",12],[-0.397,-0.009,0.306,-0.02,-0.96,-0.27,"Shivan Turret Laser",14],[0.226,0.329,-0.215,0.01,1.0,-0.01,"Shivan Turret Laser",16],[-0.099,0.103,-0.252,-1.0,-0.03,0.0,"Shivan Turret Laser",20],[-0.777,-0.172,0.22,-0.36,-0.85,-0.38,"Shivan Turret Laser",23],[-0.101,0.103,0.253,1.0,-0.03,0.02,"Shivan Turret Laser",25],[-0.045,-0.014,-0.249,-1.0,-0.05,0.0,"Shivan Turret Laser",27],[-0.286,-0.203,-0.121,-1.0,-0.05,0.0,"Shivan Turret Laser",32],[-0.551,-0.147,-0.311,-0.53,0.85,-0.02,"Shivan Turret Laser",33],[-0.468,-0.253,-0.137,-1.0,-0.05,0.0,"Shivan Turret Laser",34],[-0.044,-0.015,0.25,0.41,0.75,0.52,"Shivan Turret Laser",38],[-0.36,-0.107,0.281,0.47,0.84,0.28,"Shivan Turret Laser",42],[-0.285,-0.207,0.121,0.53,0.85,0.06,"Shivan Turret Laser",43],[-0.476,0.062,-0.189,-1.0,-0.02,-0.01,"Shivan Turret Laser",51]],"flak":[[-0.578,-0.037,0.338,0.0,-0.92,-0.38,"Shivan Standard Flak",15],[0.226,0.329,0.215,0.01,1.0,-0.01,"Shivan Standard Flak",17],[0.117,-0.055,-0.045,-1.0,-0.09,-0.0,"Shivan Standard Flak",21],[-0.188,-0.195,-0.043,-1.0,-0.09,-0.0,"Shivan Standard Flak",22],[-0.541,-0.318,-0.05,-1.0,-0.09,-0.0,"Shivan Standard Flak",24],[0.019,-0.075,-0.115,-1.0,-0.05,0.0,"Shivan Standard Flak",28],[-0.195,-0.058,-0.26,-0.62,0.78,-0.0,"Shivan Standard Flak",29],[-0.131,-0.139,-0.114,-1.0,-0.05,0.0,"Shivan Standard Flak",30],[-0.359,-0.107,-0.28,-0.46,0.84,0.28,"Shivan Standard Flak",31],[-0.194,-0.058,0.26,0.52,0.82,0.23,"Shivan Standard Flak",40],[0.411,0.014,0.02,0.0,1.0,0.0,"Shivan Long Range Flak",48],[0.411,0.014,-0.02,0.0,1.0,0.0,"Shivan Long Range Flak",49],[-0.476,0.063,0.189,1.0,-0.03,-0.01,"Shivan Standard Flak",52]],"secondary":[[-0.102,0.052,0.269,-0.0,-0.95,-0.31,"Piranha",37],[0.023,-0.079,0.116,0.43,0.77,0.47,"Piranha",39],[-0.13,-0.143,0.114,0.53,0.85,0.06,"Piranha",41],[-0.551,-0.147,0.312,0.51,0.84,-0.16,"Piranha",44],[-0.468,-0.256,0.137,0.56,0.83,0.09,"Piranha",45]],"thr":[[-0.75,0.098,0.0169],[-0.859,-0.358,0.0271],[0.135,-0.288,0.0237],[0.169,0.368,0.0237]]},
  crfenris:{"beams":[[0.87,-0.008,-0.0,-0.0,-0.82,0.57,"LTerSlash",1],[-0.914,0.049,-0.185,-0.68,-0.74,0.0,"AAAf",3],[-0.914,0.049,0.185,0.66,-0.75,-0.0,"AAAf",5]],"primary":[[0.748,-0.288,-0.0,0.0,1.0,-0.03,"Terran Turret",0],[-0.879,-0.229,-0.173,-0.66,0.75,-0.0,"Terran Turret",2],[-0.878,-0.23,0.175,0.64,0.77,0.0,"Terran Turret",4],[0.286,-0.093,0.278,1.0,0.0,0.0,"Terran Turret",6],[0.286,-0.093,-0.277,-1.0,0.0,0.0,"Terran Turret",7]],"secondary":[[-0.054,0.073,-0.0,0.0,-1.0,0.0,"Fusion Mortar",8]],"thr":[[-0.965,-0.186,0.012],[-0.964,0.021,0.012],[-0.962,-0.144,0.012],[-0.962,-0.163,0.008],[-0.962,-0.021,0.012],[-0.962,-0.002,0.008],[-0.959,-0.083,0.0223]]},
  crleviathan:{"beams":[[-0.899,-0.251,-0.207,-0.66,0.75,-0.0,"AAAf",0],[-0.899,-0.004,-0.207,-0.68,-0.74,0.0,"AAAf",1],[-0.899,-0.253,0.207,0.64,0.77,0.0,"AAAf",2],[-0.899,-0.004,0.206,0.66,-0.75,-0.0,"AAAf",3],[0.896,-0.086,0.0,-0.0,-0.82,0.57,"SGreen",5]],"primary":[[0.67,-0.316,-0.0,0.0,1.0,-0.03,"Terran Turret",4],[0.309,-0.111,0.277,1.0,0.0,0.0,"Terran Turret",6],[0.309,-0.111,-0.277,-1.0,0.0,0.0,"Terran Turret",7]],"secondary":[[0.044,0.727,-0.0,0.0,-1.0,0.0,"Fusion Mortar",8]],"thr":[[-0.968,-0.231,0.012],[-0.968,-0.024,0.012],[-0.966,-0.189,0.012],[-0.966,-0.208,0.008],[-0.966,-0.065,0.012],[-0.966,-0.047,0.008],[-0.962,-0.128,0.0224]]},
  craeolus:{"beams":[[0.118,0.039,-0.227,-1.0,0.0,0.0,"AAAf",6],[-0.06,0.039,0.227,1.0,0.0,0.0,"AAAf",8],[0.734,0.017,-0.181,0.01,-0.04,1.0,"SGreen",10],[0.737,0.011,0.179,0.01,-0.04,1.0,"SGreen",11]],"primary":[[0.171,0.333,0.0,0.0,-1.0,0.0,"Terran Huge Turret",0],[0.072,-0.318,-0.002,0.0,1.0,0.0,"Terran Huge Turret",3]],"flak":[[-0.885,0.302,-0.002,0.0,-1.0,0.0,"Standard Flak",1],[-0.81,-0.333,-0.002,0.0,1.0,0.0,"Standard Flak",2],[0.677,-0.27,-0.002,0.0,1.0,0.0,"Standard Flak",4],[0.874,0.311,-0.002,0.0,-1.0,0.0,"Standard Flak",5],[-0.06,0.039,-0.227,-1.0,0.0,0.0,"Standard Flak",7],[0.118,0.039,0.227,1.0,0.0,0.0,"Standard Flak",9]],"thr":[[0.331,0.137,0.0217],[0.331,0.173,0.0181],[-0.272,0.091,0.0094],[-0.272,0.114,0.0094],[-0.272,0.136,0.0094],[-0.977,-0.145,0.0217],[-0.985,-0.109,0.0217],[-0.992,-0.073,0.0217],[-0.985,-0.112,0.0181],[-0.977,-0.152,0.0181],[-0.977,0.123,0.0145],[-0.977,0.094,0.0145],[-0.985,0.065,0.0145],[-0.992,0.036,0.0145]]},
  codeimos:{"beams":[[-0.644,0.147,0.106,0.01,-0.87,-0.49,"AAAf",6],[-0.644,0.146,-0.106,-0.01,-0.87,-0.49,"AAAf",7],[-0.819,-0.153,-0.197,-0.98,0.18,-0.08,"TerSlash",10],[-0.819,-0.153,0.197,0.98,0.18,-0.08,"TerSlash",11],[0.746,0.032,0.15,1.0,0.0,0.0,"AAAf",15],[0.746,0.032,-0.149,-1.0,0.0,0.0,"AAAf",19],[0.969,0.015,-0.07,-0.46,-0.16,0.88,"TerSlash",22],[0.969,0.015,0.07,0.46,-0.16,0.88,"TerSlash",23]],"primary":[[0.277,-0.359,-0.0,0.0,1.0,0.0,"Terran Huge Turret",0],[0.657,-0.332,-0.0,0.0,1.0,0.0,"Terran Huge Turret",1],[-0.576,-0.429,-0.0,0.0,1.0,0.0,"Terran Huge Turret",2],[0.29,0.295,0.0,0.0,-1.0,0.0,"Terran Huge Turret",3],[0.369,0.034,0.162,1.0,0.0,0.0,"Terran Turret",13],[0.556,0.034,0.162,1.0,0.0,0.0,"Terran Turret",14],[0.369,0.034,-0.162,-1.0,0.0,0.0,"Terran Turret",17],[0.556,0.034,-0.162,-1.0,0.0,0.0,"Terran Turret",18],[0.929,0.247,-0.069,-0.37,-0.47,0.8,"Terran Turret",20],[0.929,0.247,0.069,0.37,-0.47,0.8,"Terran Turret",21]],"flak":[[-0.017,0.352,-0.059,-0.01,-0.95,0.31,"Standard Flak",4],[-0.017,0.352,0.059,0.01,-0.95,0.31,"Standard Flak",5],[-0.997,-0.169,0.152,0.0,0.0,-1.0,"Standard Flak",8],[-0.997,-0.169,-0.152,0.0,0.0,-1.0,"Standard Flak",9],[0.18,0.036,0.149,1.0,0.0,0.0,"Standard Flak",12],[0.18,0.036,-0.149,-1.0,0.0,0.0,"Standard Flak",16]],"secondary":[[-0.423,-0.156,-0.205,-0.98,0.14,0.12,"Piranha",24],[-0.423,-0.156,0.205,0.98,0.14,0.12,"Piranha",25]],"thr":[[-0.861,-0.167,0.0338],[-0.861,-0.032,0.0338],[-0.407,0.348,0.0282],[0.719,0.241,0.0197]]},
  deorionright:{"beams":[[0.856,0.096,0.055,0.0,-1.0,0.0,"BGreen",0],[0.451,-0.004,0.208,1.0,0.0,0.0,"TerSlash",5],[0.524,-0.028,-0.093,-1.0,0.0,0.0,"TerSlash",6],[0.388,-0.163,0.05,0.0,1.0,0.0,"AAAf",7],[-0.165,-0.039,0.256,1.0,0.0,0.0,"Bgreen",8],[-0.06,0.286,0.117,0.0,-1.0,0.0,"AAAf",9],[-0.72,0.137,-0.293,-1.0,0.0,0.0,"BGreen",10],[-0.799,0.185,0.292,1.0,0.0,0.0,"TerSlash",13],[-0.831,0.329,0.104,0.0,-1.0,0.0,"AAAf",15]],"primary":[[0.831,-0.205,0.054,0.0,1.0,0.0,"Terran Huge Turret",1],[0.6,-0.205,0.114,0.0,1.0,0.0,"Terran Huge Turret",2],[-0.182,0.356,0.02,0.0,-1.0,0.0,"Terran Huge Turret",3],[-0.759,-0.356,0.099,0.0,1.0,0.0,"Terran Huge Turret",4],[-0.198,-0.19,0.055,0.0,1.0,0.0,"Terran Turret",11],[-0.198,0.169,-0.243,-1.0,0.0,0.0,"Terran Turret",12],[-0.882,-0.165,0.137,0.0,0.39,-0.92,"Terran Turret",14]],"thr":[[-1.013,0.017,0.0385],[-1.013,0.065,0.0385],[-1.013,0.155,0.0385],[-1.013,0.208,0.0385]]},
  dehecate:{"beams":[[-0.774,0.042,0.361,0.97,-0.25,0.0,"AAAf",1],[-0.774,0.042,-0.361,-0.97,-0.25,0.0,"AAAf",8],[0.597,-0.137,-0.325,-0.97,-0.25,0.0,"AAAf",11],[0.597,-0.137,0.325,0.97,-0.25,0.0,"AAAf",12],[-0.417,-0.222,0.552,0.24,0.97,-0.03,"AAAf",18],[0.989,-0.23,-0.0,0.04,0.02,1.0,"BGreen",19],[-0.417,-0.222,-0.552,-0.24,0.97,-0.03,"AAAf",20],[0.932,-0.002,-0.0,0.04,-0.32,0.95,"TerSlash",21],[0.193,-0.064,0.057,0.96,-0.28,-0.07,"TerSlash",24],[0.193,-0.064,-0.057,-0.96,-0.28,-0.07,"TerSlash",25],[-0.674,-0.198,-0.0,-0.07,-0.78,-0.62,"TerSlash",26]],"primary":[[-0.606,0.044,0.362,0.97,-0.25,0.0,"Terran Huge Turret",2],[-0.606,0.044,-0.362,-0.97,-0.25,0.0,"Terran Turret",9],[0.598,0.169,-0.327,-0.97,-0.25,0.0,"Terran Turret",10],[0.598,0.169,0.327,0.97,-0.25,0.0,"Terran Turret",13],[-0.377,0.344,-0.043,-0.97,-0.25,0.0,"Terran Turret",14],[-0.377,0.344,0.043,0.97,-0.25,0.0,"Terran Turret",15]],"flak":[[0.415,-0.438,0.0,0.01,0.99,0.12,"Heavy Flak",0],[0.753,-0.422,0.0,0.01,0.99,0.12,"Long Range Flak",3],[-0.293,-0.528,0.0,0.01,0.99,0.12,"Heavy Flak",4],[-0.735,-0.537,0.0,0.01,0.99,0.12,"Long Range Flak",5],[0.228,0.097,0.0,0.0,-1.0,0.0,"Standard Flak",6],[0.85,0.139,0.0,0.0,-1.0,0.0,"Standard Flak",7],[-0.606,0.045,0.19,-0.97,-0.25,0.0,"Standard Flak",16],[-0.606,0.045,-0.19,0.97,-0.25,0.0,"Standard Flak",17],[-0.449,-0.165,-0.588,-0.2,-0.98,-0.02,"Standard Flak",22],[-0.449,-0.165,0.588,0.2,-0.98,-0.02,"Standard Flak",23]],"thr":[[-0.971,-0.236,0.0277],[-0.962,-0.167,0.0277],[-0.954,-0.073,0.0277],[-0.973,-0.003,0.0277],[0.271,-0.164,0.0138],[0.271,-0.192,0.0138],[0.271,-0.219,0.0138],[0.271,-0.182,0.0092],[-0.498,0.177,0.0138],[0.758,0.044,0.0184],[-0.498,0.155,0.0138],[-0.498,0.198,0.0138],[-0.496,0.149,0.0092]]},
  craten:{"beams":[[0.595,0.048,0.317,0.0,1.0,0.0,"AAAf",2],[0.595,0.048,-0.317,0.0,1.0,0.0,"AAAf",3]],"primary":[[-0.492,-0.297,-0.0,0.0,1.0,0.0,"Subach HL-7",0],[0.531,0.294,0.0,0.0,-1.0,0.0,"Subach HL-7",1],[-0.727,0.029,-0.234,-0.87,-0.5,0.0,"Vasudan Turret",4],[-0.727,0.029,0.234,0.77,-0.64,0.0,"Vasudan Turret",5]],"thr":[[-0.92,-0.031,0.0385],[-0.886,0.065,0.0353]]},
  crmentu:{"beams":[[-0.942,0.066,-0.0,0.01,0.0,-1.0,"AAAf",0],[0.148,-0.263,-0.191,-0.28,0.96,0.0,"AAAf",1],[0.148,-0.263,0.191,0.57,0.82,-0.01,"AAAf",2]],"primary":[[0.108,-0.156,-0.308,-0.77,0.63,0.1,"Vasudan Turret",5],[0.107,-0.156,0.308,0.91,0.41,-0.0,"Vasudan Turret",6],[-0.254,-0.141,-0.199,-0.72,0.69,0.1,"Vasudan Turret",7],[-0.255,-0.142,0.198,0.72,0.69,0.1,"Vasudan Turret",8],[-0.571,-0.098,-0.188,-0.68,0.72,0.1,"Vasudan Turret",9],[-0.572,-0.101,0.19,0.68,0.72,0.1,"Vasudan Turret",10],[-0.678,0.344,0.001,0.0,-1.0,0.0,"Vasudan Huge Turret",12],[0.435,0.183,-0.192,0.0,-1.0,0.0,"Vasudan Turret",13],[0.434,0.182,0.193,0.0,-1.0,0.0,"Subach HL-7",14],[-0.368,-0.238,-0.0,0.0,1.0,-0.1,"Vasudan Huge Turret",15]],"flak":[[0.502,-0.108,-0.31,-0.79,0.61,-0.06,"Standard Flak",3],[0.507,-0.111,0.301,0.81,0.58,-0.0,"Standard Flak",4],[-0.804,-0.068,0.0,-0.0,0.89,-0.45,"Standard Flak",11]],"thr":[[-0.972,-0.004,0.0125],[-0.969,-0.004,0.0125],[-0.972,0.116,0.0125],[-0.969,0.116,0.0125]]},
  cosobek:{"beams":[[-0.836,0.28,0.348,-0.44,0.32,-0.84,"AAAf",1],[0.53,0.154,-0.137,-0.57,0.8,0.19,"AAAf",2],[-0.836,0.28,-0.347,0.43,0.32,-0.85,"AAAf",3],[0.837,0.216,-0.09,-0.47,0.81,0.34,"VSlash",4],[0.53,0.153,0.136,0.56,0.81,0.19,"AAAf",7],[0.837,0.216,0.088,0.46,0.82,0.34,"VSlash",9]],"primary":[[-0.231,0.122,-0.084,-0.79,0.61,-0.0,"Vasudan Turret",10],[-0.048,0.134,-0.112,-0.75,0.66,-0.07,"Vasudan Turret",11],[-0.231,0.121,0.084,0.8,0.59,0.0,"Vasudan Turret",12],[-0.048,0.134,0.113,0.84,0.54,-0.07,"Vasudan Turret",13],[-0.232,0.224,-0.071,-0.68,-0.74,0.0,"Vasudan Turret",14],[-0.032,0.231,-0.092,-0.41,-0.91,-0.06,"Vasudan Turret",15],[-0.232,0.224,0.071,0.65,-0.76,0.0,"Vasudan Turret",16],[-0.032,0.231,0.092,0.41,-0.91,-0.06,"Vasudan Turret",17],[0.666,0.392,-0.133,0.0,-1.0,0.0,"Vasudan Huge Turret",18],[0.666,0.392,0.133,0.0,-1.0,0.0,"Vasudan Huge Turret",19],[0.093,-0.039,-0.0,0.0,1.0,0.0,"Vasudan Huge Turret",20]],"flak":[[0.234,0.079,-0.137,-0.54,0.84,-0.0,"Standard Flak",0],[0.234,0.079,0.137,0.57,0.82,0.0,"Standard Flak",5],[-0.58,0.089,-0.116,-0.93,0.21,0.29,"Standard Flak",6],[-0.58,0.086,0.117,0.94,0.2,0.27,"Standard Flak",8],[-0.658,0.401,-0.0,0.0,-1.0,0.0,"Standard Flak",21]],"thr":[[-0.807,0.251,0.0197],[-0.807,0.143,0.0197],[0.196,0.286,0.0229]]},
  detyphon:{"beams":[[-0.687,-0.103,0.0,0.0,0.42,-0.91,"AAAf",9],[-0.673,0.131,0.0,0.0,-0.45,-0.89,"BVas",10],[0.766,0.033,0.0,0.0,-0.32,0.95,"AAAf",12],[0.775,-0.033,0.0,0.0,0.37,0.93,"BVas",13]],"primary":[[0.729,-0.053,0.033,0.0,1.0,0.0,"Vasudan Huge Turret",0],[0.729,-0.053,-0.033,0.0,1.0,0.0,"Vasudan Huge Turret",1]],"flak":[[0.132,0.079,-0.178,0.0,-1.0,0.0,"Standard Flak",2],[0.132,0.079,0.178,0.0,-1.0,0.0,"Standard Flak",3],[0.132,-0.151,0.178,0.0,1.0,0.0,"Standard Flak",4],[0.132,-0.151,-0.178,0.0,1.0,0.0,"Standard Flak",5],[-0.833,-0.008,-0.0,0.0,-0.45,-0.89,"Standard Flak",14]],"secondary":[[-0.384,0.209,0.112,1.0,0.0,0.0,"FighterKiller",6],[-0.384,0.209,-0.112,-1.0,0.0,0.0,"FighterKiller",7],[-0.117,-0.139,0.0,0.0,0.45,-0.89,"FighterKiller",8],[-0.026,0.137,0.0,0.0,-0.45,0.89,"FighterKiller",11]],"thr":[[-0.78,0.067,0.0074],[-0.799,0.038,0.0139],[-0.799,0.082,0.0167]]},
  dehatshepsut:{"beams":[[-0.126,0.284,-0.0,0.0,-1.0,0.0,"SVas",0],[0.824,0.044,-0.0,-0.0,0.85,0.52,"BVas",1],[0.013,-0.244,-0.0,-0.0,1.0,-0.02,"BVas",2],[-0.96,-0.124,-0.0,-0.0,0.58,-0.81,"BVas",3],[0.846,0.138,0.161,0.0,1.0,0.0,"AAAf",10],[-0.798,0.083,0.232,0.23,-0.93,0.29,"AAAf",16],[-0.798,0.085,-0.232,-0.27,-0.91,0.32,"AAAf",26]],"primary":[[0.506,0.194,-0.264,-0.01,1.0,-0.03,"Vasudan Huge Turret",23],[-0.368,0.192,-0.225,-0.47,-0.84,-0.27,"Vasudan Huge Turret",24],[-0.668,-0.2,-0.0,0.08,0.91,-0.41,"Vasudan Huge Turret",25],[0.506,0.194,0.264,0.01,1.0,-0.03,"Vasudan Huge Turret",27],[-0.368,0.192,0.225,0.47,-0.84,-0.27,"Vasudan Huge Turret",28],[-0.943,-0.076,0.0,0.06,-0.57,-0.82,"Vasudan Huge Turret",29]],"flak":[[0.344,-0.083,-0.063,-0.89,0.37,0.28,"Standard Flak",5],[0.054,0.058,-0.225,-0.81,-0.37,0.45,"Standard Flak",6],[-0.062,-0.159,-0.162,-0.99,0.02,0.14,"Standard Flak",7],[-0.247,-0.008,-0.326,-0.6,0.8,0.02,"Standard Flak",8],[-0.426,-0.1,-0.145,-0.74,0.12,0.66,"Standard Flak",9],[0.34,-0.083,0.058,0.89,0.37,0.28,"Standard Flak",11],[0.054,0.058,0.224,0.81,-0.37,0.45,"Standard Flak",12],[-0.06,-0.158,0.162,0.99,0.02,0.14,"Standard Flak",13],[-0.254,-0.006,0.33,0.6,0.8,0.02,"Standard Flak",14],[-0.429,-0.1,0.144,0.74,0.12,0.66,"Standard Flak",15]],"secondary":[[-0.291,-0.257,0.0,0.0,1.0,-0.03,"Fusion Mortar",17],[0.771,0.276,0.209,0.0,-1.0,0.02,"Fusion Mortar",18],[0.771,0.276,-0.208,0.0,-1.0,0.02,"Fusion Mortar",19],[-0.799,-0.089,-0.203,0.0,1.0,-0.03,"Fusion Mortar",20],[-0.799,-0.088,0.208,0.0,1.0,-0.03,"Fusion Mortar",21]],"thr":[[-0.942,0.042,0.0285],[-0.96,0.061,0.019],[-0.95,0.045,0.0238]]},
  sdcolossus:{"beams":[[-0.199,0.052,0.0,0.0,0.0,-1.0,"AAAf",30],[-0.201,0.195,0.0,-0.0,0.0,-1.0,"AAAf",31],[-0.127,0.108,0.001,0.0,-0.29,0.96,"AAAf",32],[0.9,-0.166,-0.063,0.0,1.0,0.0,"AAAf",33],[0.9,-0.166,0.063,0.0,1.0,0.0,"AAAf",34],[0.227,-0.237,0.094,0.0,0.84,0.54,"AAAf",35],[0.227,-0.237,-0.094,0.0,0.84,0.54,"AAAf",36],[-0.118,0.281,0.001,-0.0,0.0,1.0,"AAAf",39],[-0.973,-0.13,0.151,0.0,1.0,0.0,"AAAf",40],[-0.973,-0.13,-0.151,0.0,1.0,0.0,"AAAf",42],[-0.759,-0.086,0.195,1.0,-0.0,0.0,"TerSlash",50],[-0.908,-0.086,0.195,1.0,-0.0,0.0,"TerSlash",51],[-0.294,-0.249,0.093,0.0,1.0,0.0,"BGreen",52],[-0.294,-0.249,-0.092,0.0,1.0,-0.0,"BGreen",53],[-0.908,-0.088,-0.196,-1.0,0.0,0.0,"TerSlash",54],[-0.759,-0.088,-0.196,-1.0,-0.0,0.0,"TerSlash",55],[-0.136,0.001,0.092,0.68,-0.74,0.0,"BGreen",56],[-0.136,0.001,-0.093,-0.68,-0.73,-0.0,"BGreen",57],[0.185,-0.161,0.201,0.96,-0.0,0.29,"BGreen",58],[0.186,-0.161,-0.203,-0.96,-0.0,0.29,"BGreen",59],[0.689,-0.109,0.074,0.82,-0.57,0.0,"TerSlash",60],[0.689,-0.11,-0.076,-0.83,-0.56,0.0,"TerSlash",61],[0.811,-0.224,0.0,0.0,0.89,0.45,"TerSlash",62]],"primary":[[0.763,0.06,-0.001,0.0,-1.0,0.0,"Terran Huge Turret",0],[0.66,-0.268,-0.001,0.0,1.0,0.0,"Terran Huge Turret",1],[-0.439,-0.246,0.098,0.0,1.0,0.0,"Terran Huge Turret",2],[-0.724,0.005,0.133,0.0,-1.0,0.0,"Terran Huge Turret",3],[0.009,-0.333,-0.001,0.0,1.0,0.0,"Terran Huge Turret",4],[0.721,0.063,-0.001,0.0,-1.0,0.0,"Terran Huge Turret",5],[-0.195,0.334,0.059,0.0,-1.0,0.0,"Terran Huge Turret",6],[-0.195,0.333,-0.061,0.0,-1.0,0.0,"Terran Huge Turret",7],[-0.439,-0.246,-0.1,0.0,1.0,0.0,"Terran Huge Turret",8],[-0.724,0.005,-0.135,0.0,-1.0,0.0,"Terran Huge Turret",9],[0.657,-0.157,-0.119,-1.0,0.0,0.0,"Terran Turret",12],[-0.881,0.002,-0.134,0.0,-1.0,-0.0,"Terran Turret",14],[-0.153,0.212,-0.089,-1.0,0.0,0.0,"Terran Turret",16],[-0.153,0.212,0.089,1.0,-0.0,0.0,"Terran Turret",18],[-0.142,0.057,0.093,1.0,-0.0,0.0,"Terran Turret",20],[-0.881,0.002,0.134,0.0,-1.0,-0.0,"Terran Turret",23],[0.657,-0.157,0.118,1.0,-0.0,0.0,"Terran Turret",25],[0.752,-0.174,0.123,1.0,-0.0,0.0,"Terran Turret",27]],"flak":[[0.601,-0.212,-0.048,0.0,1.0,0.0,"Standard Flak",10],[0.133,-0.161,0.207,1.0,0.0,0.0,"Standard Flak",11],[0.602,-0.212,0.048,0.0,1.0,0.0,"Standard Flak",13],[-0.142,0.057,-0.093,-1.0,-0.0,0.0,"Standard Flak",15],[0.07,-0.161,0.206,1.0,0.0,0.0,"Standard Flak",17],[0.003,-0.161,0.201,1.0,0.0,0.0,"Standard Flak",19],[-0.068,-0.161,0.191,1.0,-0.0,0.0,"Standard Flak",21],[0.132,-0.161,-0.207,-1.0,0.0,0.0,"Standard Flak",22],[0.07,-0.161,-0.206,-1.0,-0.0,0.0,"Standard Flak",24],[0.003,-0.161,-0.202,-1.0,0.0,0.0,"Standard Flak",26],[-0.069,-0.161,-0.191,-1.0,-0.0,0.0,"Standard Flak",28],[0.752,-0.174,-0.123,-1.0,0.0,0.0,"Standard Flak",29]],"secondary":[[-0.545,-0.157,0.144,1.0,0.0,0.0,"Piranha",37],[-0.847,-0.122,0.0,0.0,0.93,0.37,"MX-52",38],[0.284,-0.093,0.073,-0.0,-0.68,0.74,"MX-52",41],[-0.708,-0.082,0.0,-0.0,0.93,0.37,"MX-52",43],[-0.731,-0.15,0.144,1.0,0.0,0.0,"MX-52",44],[-0.731,-0.151,-0.144,-1.0,0.0,0.0,"MX-52",45],[-0.545,-0.158,-0.144,-1.0,0.0,0.0,"Piranha",46],[0.69,-0.041,-0.026,1.0,0.0,-0.04,"MX-52",47],[0.69,-0.041,0.026,1.0,0.0,0.04,"MX-52",48],[0.284,-0.093,-0.073,0.0,-0.68,0.74,"MX-52",49]],"thr":[[-0.946,-0.083,0.0196],[-0.967,-0.083,0.0196],[-0.977,-0.083,0.0196],[-0.934,-0.149,0.0131],[-0.947,-0.188,0.0131],[-0.25,0.278,0.0114],[-0.275,0.278,0.0114],[0.652,0.019,0.0082],[0.653,-0.01,0.0082]]},
  sgmjolnir:{"beams":[[0.808,0.072,0.0,0.0,-0.0,1.0,"MjolnirBeam",0]]},
  cacharybdis:{"primary":[[-0.593,0.185,0.204,1.0,0.0,0.0,"Terran Turret Weak",0],[-0.593,0.185,-0.204,-1.0,0.0,0.0,"Terran Turret Weak",1],[-0.404,-0.124,-0.105,-1.0,0.0,0.0,"Terran Turret Weak",2],[-0.404,-0.124,0.105,1.0,0.0,0.0,"Subach HL-7",3],[-0.706,-0.156,-0.0,0.0,0.32,-0.95,"Terran Turret Weak",4],[0.115,-0.103,-0.0,0.0,0.71,0.71,"Terran Turret Weak",5]],"thr":[[-0.97,-0.056,0.0152],[-0.995,0.025,0.0223],[-0.995,0.033,0.0223],[-0.995,0.107,0.0223],[-0.995,0.114,0.0223]]},
  casetekh:{"primary":[[-0.234,0.235,0.0,-0.01,-1.0,-0.09,"Vasudan Turret Weak",0],[-0.801,-0.299,0.005,0.06,0.99,0.13,"Vasudan Turret Weak",1],[0.777,0.064,0.005,0.06,-0.99,-0.1,"Vasudan Turret Weak",2]],"thr":[[-0.866,0.082,0.0236],[-0.866,0.092,0.0236]]},
  coiceni:{"beams":[[0.798,-0.01,0.216,1.0,0.0,0.1,"BGreen",1],[-0.26,-0.169,0.254,0.93,0.37,0.0,"BGreen",7],[0.798,-0.01,-0.223,-1.0,0.0,0.1,"BGreen",11]],"primary":[[-0.195,0.51,0.161,0.0,-1.0,0.0,"Terran Huge Turret",0],[0.505,0.016,0.142,1.0,0.0,0.0,"Terran Huge Turret",2],[-0.166,0.215,-0.0,0.0,-1.0,0.0,"Terran Huge Turret",3],[-0.149,0.292,0.219,1.0,0.0,0.0,"Terran Huge Turret",4],[0.987,0.023,-0.063,-0.1,0.0,1.0,"Terran Huge Turret",6],[0.987,0.023,0.062,0.1,0.0,1.0,"Terran Huge Turret",8],[-0.744,0.334,0.0,0.0,-1.0,0.0,"Terran Huge Turret",10],[0.505,0.016,-0.148,-1.0,0.0,0.0,"Terran Turret",12],[0.14,-0.169,-0.248,-0.93,0.37,0.0,"Terran Turret",13],[-0.837,0.194,-0.0,0.0,-0.51,-0.86,"Terran Turret",14],[-0.906,-0.048,-0.0,0.0,0.82,-0.57,"Terran Turret",16],[-0.689,-0.222,0.0,0.0,1.0,0.0,"Terran Turret",18],[-0.343,-0.529,-0.0,0.0,1.0,0.0,"Terran Turret",20],[0.004,-0.14,0.001,0.0,1.0,0.0,"Terran Turret",21],[0.301,-0.336,0.0,0.0,1.0,0.0,"Terran Turret",22],[0.762,0.399,-0.0,0.0,-1.0,0.0,"Terran Turret",23]],"flak":[[0.14,-0.169,0.244,0.93,0.37,0.0,"Standard Flak",5],[-0.804,-0.031,0.123,0.89,0.45,0.0,"Standard Flak",9]],"secondary":[[-0.26,-0.169,-0.259,-0.93,0.37,0.0,"Piranha",15],[-0.149,0.292,-0.226,-1.0,0.0,0.0,"MX-52",17],[-0.804,-0.031,-0.128,-0.89,0.45,0.0,"Piranha",19],[-0.195,0.51,-0.161,0.0,-1.0,0.0,"MX-52",24]],"thr":[[-0.382,-0.249,0.0363],[-0.391,-0.241,0.0363],[-0.382,-0.251,0.0363],[-0.317,-0.085,0.0407],[-0.518,0.329,0.0363],[-0.519,0.332,0.0363]]},
  ntfcraeolus:{"beams":[[0.118,0.039,-0.227,-1.0,0.0,0.0,"AAAf",6],[-0.06,0.039,0.227,1.0,0.0,0.0,"AAAf",8],[0.734,0.017,-0.181,0.01,-0.04,1.0,"SGreen",10],[0.737,0.011,0.179,0.01,-0.04,1.0,"SGreen",11]],"primary":[[0.171,0.333,0.0,0.0,-1.0,0.0,"Terran Huge Turret",0],[0.072,-0.318,-0.002,0.0,1.0,0.0,"Terran Huge Turret",3]],"flak":[[-0.885,0.302,-0.002,0.0,-1.0,0.0,"Standard Flak",1],[-0.81,-0.333,-0.002,0.0,1.0,0.0,"Standard Flak",2],[0.677,-0.27,-0.002,0.0,1.0,0.0,"Standard Flak",4],[0.874,0.311,-0.002,0.0,-1.0,0.0,"Standard Flak",5],[-0.06,0.039,-0.227,-1.0,0.0,0.0,"Standard Flak",7],[0.118,0.039,0.227,1.0,0.0,0.0,"Standard Flak",9]],"thr":[[0.331,0.137,0.0217],[0.331,0.173,0.0181],[-0.272,0.091,0.0094],[-0.272,0.114,0.0094],[-0.272,0.136,0.0094],[-0.977,-0.145,0.0217],[-0.985,-0.109,0.0217],[-0.992,-0.073,0.0217],[-0.985,-0.112,0.0181],[-0.977,-0.152,0.0181],[-0.977,0.123,0.0145],[-0.977,0.094,0.0145],[-0.985,0.065,0.0145],[-0.992,0.036,0.0145]]},
  ntfcodeimos:{"beams":[[-0.644,0.147,0.106,0.01,-0.87,-0.49,"AAAf",6],[-0.644,0.146,-0.106,-0.01,-0.87,-0.49,"AAAf",7],[-0.819,-0.153,-0.197,-0.98,0.18,-0.08,"TerSlash",10],[-0.819,-0.153,0.197,0.98,0.18,-0.08,"TerSlash",11],[0.746,0.032,0.15,1.0,0.0,0.0,"AAAf",15],[0.746,0.032,-0.149,-1.0,0.0,0.0,"AAAf",19],[0.969,0.015,-0.07,-0.46,-0.16,0.88,"TerSlash",22],[0.969,0.015,0.07,0.46,-0.16,0.88,"TerSlash",23]],"primary":[[0.277,-0.359,-0.0,0.0,1.0,0.0,"Terran Huge Turret",0],[0.657,-0.332,-0.0,0.0,1.0,0.0,"Terran Huge Turret",1],[-0.576,-0.429,-0.0,0.0,1.0,0.0,"Terran Huge Turret",2],[0.29,0.295,0.0,0.0,-1.0,0.0,"Terran Huge Turret",3],[0.369,0.034,0.162,1.0,0.0,0.0,"Terran Turret",13],[0.556,0.034,0.162,1.0,0.0,0.0,"Terran Turret",14],[0.369,0.034,-0.162,-1.0,0.0,0.0,"Terran Turret",17],[0.556,0.034,-0.162,-1.0,0.0,0.0,"Terran Turret",18],[0.929,0.247,-0.069,-0.37,-0.47,0.8,"Terran Turret",20],[0.929,0.247,0.069,0.37,-0.47,0.8,"Terran Turret",21]],"flak":[[-0.017,0.352,-0.059,-0.01,-0.95,0.31,"Standard Flak",4],[-0.017,0.352,0.059,0.01,-0.95,0.31,"Standard Flak",5],[-0.997,-0.169,0.152,0.0,0.0,-1.0,"Standard Flak",8],[-0.997,-0.169,-0.152,0.0,0.0,-1.0,"Standard Flak",9],[0.18,0.036,0.149,1.0,0.0,0.0,"Standard Flak",12],[0.18,0.036,-0.149,-1.0,0.0,0.0,"Standard Flak",16]],"secondary":[[-0.423,-0.156,-0.205,-0.98,0.14,0.12,"Piranha",24],[-0.423,-0.156,0.205,0.98,0.14,0.12,"Piranha",25]],"thr":[[-0.861,-0.167,0.0338],[-0.861,-0.032,0.0338],[-0.407,0.348,0.0282],[0.719,0.241,0.0197]]},
  ntfcrfenris:{"beams":[[0.87,-0.008,-0.0,-0.0,-0.82,0.57,"LTerSlash",1],[-0.914,0.049,-0.185,-0.68,-0.74,0.0,"AAAf",3],[-0.914,0.049,0.185,0.66,-0.75,-0.0,"AAAf",5]],"primary":[[0.748,-0.288,-0.0,0.0,1.0,-0.03,"Terran Turret",0],[-0.879,-0.229,-0.173,-0.66,0.75,-0.0,"Terran Turret",2],[-0.878,-0.23,0.175,0.64,0.77,0.0,"Terran Turret",4],[0.286,-0.093,0.278,1.0,0.0,0.0,"Terran Turret",6],[0.286,-0.093,-0.277,-1.0,0.0,0.0,"Terran Turret",7]],"secondary":[[-0.054,0.073,-0.0,0.0,-1.0,0.0,"Fusion Mortar",8]],"thr":[[-0.965,-0.186,0.012],[-0.964,0.021,0.012],[-0.962,-0.144,0.012],[-0.962,-0.163,0.008],[-0.962,-0.021,0.012],[-0.962,-0.002,0.008],[-0.959,-0.083,0.0223]]},
  ntfcrleviathan:{"beams":[[-0.899,-0.251,-0.207,-0.66,0.75,-0.0,"AAAf",0],[-0.899,-0.004,-0.207,-0.68,-0.74,0.0,"AAAf",1],[-0.899,-0.253,0.207,0.64,0.77,0.0,"AAAf",2],[-0.899,-0.004,0.206,0.66,-0.75,-0.0,"AAAf",3],[0.896,-0.086,0.0,-0.0,-0.82,0.57,"SGreen",5]],"primary":[[0.67,-0.316,-0.0,0.0,1.0,-0.03,"Terran Turret",4],[0.309,-0.111,0.277,1.0,0.0,0.0,"Terran Turret",6],[0.309,-0.111,-0.277,-1.0,0.0,0.0,"Terran Turret",7]],"secondary":[[0.044,0.727,-0.0,0.0,-1.0,0.0,"Fusion Mortar",8]],"thr":[[-0.968,-0.231,0.012],[-0.968,-0.024,0.012],[-0.966,-0.189,0.012],[-0.966,-0.208,0.008],[-0.966,-0.065,0.012],[-0.966,-0.047,0.008],[-0.962,-0.128,0.0224]]},
  ntfdeorion:{"beams":[[0.856,0.096,0.055,0.0,-1.0,0.0,"BGreen",0],[0.451,-0.004,0.208,1.0,0.0,0.0,"TerSlash",5],[0.524,-0.028,-0.093,-1.0,0.0,0.0,"TerSlash",6],[0.388,-0.163,0.05,0.0,1.0,0.0,"AAAf",7],[-0.165,-0.039,0.256,1.0,0.0,0.0,"Bgreen",8],[-0.06,0.286,0.117,0.0,-1.0,0.0,"AAAf",9],[-0.72,0.137,-0.293,-1.0,0.0,0.0,"BGreen",10],[-0.799,0.185,0.292,1.0,0.0,0.0,"TerSlash",13],[-0.831,0.329,0.104,0.0,-1.0,0.0,"AAAf",15]],"primary":[[0.831,-0.205,0.054,0.0,1.0,0.0,"Terran Huge Turret",1],[0.6,-0.205,0.114,0.0,1.0,0.0,"Terran Huge Turret",2],[-0.182,0.356,0.02,0.0,-1.0,0.0,"Terran Huge Turret",3],[-0.759,-0.356,0.099,0.0,1.0,0.0,"Terran Huge Turret",4],[-0.198,-0.19,0.055,0.0,1.0,0.0,"Terran Turret",11],[-0.198,0.169,-0.243,-1.0,0.0,0.0,"Terran Turret",12],[-0.882,-0.165,0.137,0.0,0.39,-0.92,"Terran Turret",14]],"thr":[[-1.013,0.017,0.0385],[-1.013,0.065,0.0385],[-1.013,0.155,0.0385],[-1.013,0.208,0.0385]]},
  ntfdehecate:{"beams":[[-0.774,0.042,0.361,0.97,-0.25,0.0,"AAAf",1],[-0.774,0.042,-0.361,-0.97,-0.25,0.0,"AAAf",8],[0.597,-0.137,-0.325,-0.97,-0.25,0.0,"AAAf",11],[0.597,-0.137,0.325,0.97,-0.25,0.0,"AAAf",12],[-0.417,-0.222,0.552,0.24,0.97,-0.03,"AAAf",18],[0.989,-0.23,-0.0,0.04,0.02,1.0,"BGreen",19],[-0.417,-0.222,-0.552,-0.24,0.97,-0.03,"AAAf",20],[0.932,-0.002,-0.0,0.04,-0.32,0.95,"TerSlash",21],[0.193,-0.064,0.057,0.96,-0.28,-0.07,"TerSlash",24],[0.193,-0.064,-0.057,-0.96,-0.28,-0.07,"TerSlash",25],[-0.674,-0.198,-0.0,-0.07,-0.78,-0.62,"TerSlash",26]],"primary":[[-0.606,0.044,0.362,0.97,-0.25,0.0,"Terran Huge Turret",2],[-0.606,0.044,-0.362,-0.97,-0.25,0.0,"Terran Turret",9],[0.598,0.169,-0.327,-0.97,-0.25,0.0,"Terran Turret",10],[0.598,0.169,0.327,0.97,-0.25,0.0,"Terran Turret",13],[-0.377,0.344,-0.043,-0.97,-0.25,0.0,"Terran Turret",14],[-0.377,0.344,0.043,0.97,-0.25,0.0,"Terran Turret",15]],"flak":[[0.415,-0.438,0.0,0.01,0.99,0.12,"Heavy Flak",0],[0.753,-0.422,0.0,0.01,0.99,0.12,"Long Range Flak",3],[-0.293,-0.528,0.0,0.01,0.99,0.12,"Heavy Flak",4],[-0.735,-0.537,0.0,0.01,0.99,0.12,"Long Range Flak",5],[0.228,0.097,0.0,0.0,-1.0,0.0,"Standard Flak",6],[0.85,0.139,0.0,0.0,-1.0,0.0,"Standard Flak",7],[-0.606,0.045,0.19,-0.97,-0.25,0.0,"Standard Flak",16],[-0.606,0.045,-0.19,0.97,-0.25,0.0,"Standard Flak",17],[-0.449,-0.165,-0.588,-0.2,-0.98,-0.02,"Standard Flak",22],[-0.449,-0.165,0.588,0.2,-0.98,-0.02,"Standard Flak",23]],"thr":[[-0.971,-0.236,0.0277],[-0.962,-0.167,0.0277],[-0.954,-0.073,0.0277],[-0.973,-0.003,0.0277],[0.271,-0.164,0.0138],[0.271,-0.192,0.0138],[0.271,-0.219,0.0138],[0.271,-0.182,0.0092],[-0.498,0.177,0.0138],[0.758,0.044,0.0184],[-0.498,0.155,0.0138],[-0.498,0.198,0.0138],[-0.496,0.149,0.0092]]},
  sdhades:{"beams":[[0.769,-0.142,0.0,0.0,1.0,0.0,"BGreen",0],[-0.133,-0.523,0.0,0.0,1.0,0.0,"BGreen",1]],"primary":[[-0.948,-0.252,0.271,0.0,1.0,0.0,"Shivan Turret Laser",2],[-0.948,-0.252,-0.271,0.0,1.0,0.0,"Shivan Turret Laser",3],[-0.95,0.433,0.271,0.0,-1.0,0.0,"Shivan Turret Laser",5],[0.883,0.426,0.0,0.0,-1.0,0.0,"Shivan Turret Laser",6],[0.25,0.193,0.075,0.0,-1.0,0.0,"Shivan Turret Laser",10],[0.25,0.193,-0.075,0.0,-1.0,0.0,"Shivan Turret Laser",11],[0.82,0.087,-0.133,-1.0,0.0,0.0,"Shivan Turret Laser",12],[0.82,0.087,0.133,1.0,0.0,0.0,"Shivan Turret Laser",13],[-0.547,0.477,0.301,1.0,0.0,0.0,"Shivan Turret Laser",14],[-0.547,0.477,-0.301,-1.0,0.0,0.0,"Shivan Turret Laser",15],[-0.394,0.042,-0.194,0.0,1.0,0.0,"Shivan Turret Laser",16],[-0.394,0.042,0.194,0.0,1.0,0.0,"Shivan Turret Laser",17],[0.249,0.088,0.165,1.0,0.0,0.0,"Shivan Turret Laser",18],[0.249,0.088,-0.165,-1.0,0.0,0.0,"Shivan Turret Laser",19],[-0.082,-0.428,-0.126,-0.5,0.87,0.0,"Shivan Turret Laser",20],[-0.082,-0.428,0.126,0.5,0.87,0.0,"Shivan Turret Laser",21]],"secondary":[[-0.95,0.433,-0.271,0.0,-1.0,0.0,"FighterKiller",4],[0.644,-0.061,-0.0,0.0,1.0,0.0,"FighterKiller",7],[0.933,0.009,-0.0,0.0,0.87,0.5,"Shivan Cluster",8],[0.899,0.283,-0.0,0.0,-0.26,0.97,"Shivan Cluster",9]],"thr":[[-0.963,-0.134,0.0322],[-0.834,0.091,0.0263],[-0.963,0.314,0.0322]]},
  scfaustus:{"primary":[[0.633,-0.341,0.0,0.0,1.0,0.0,"Terran Turret Weak",0],[0.614,0.24,0.0,0.0,-1.0,0.0,"Terran Turret Weak",1],[-0.659,-0.248,0.148,0.0,1.0,0.0,"Terran Turret Weak",2],[-0.659,-0.248,-0.149,0.0,1.0,0.0,"Subach HL-7",3],[-0.659,0.248,0.147,0.0,-1.0,0.0,"Subach HL-7",4],[-0.659,0.248,-0.147,0.0,-1.0,0.0,"Subach HL-7",5]],"thr":[[-0.794,-0.122,0.0515],[-0.794,0.122,0.0515]]},
  mehippocrates:{"beams":[[-0.604,-0.353,0.0,0.0,1.0,0.0,"LTerSlash",1],[-0.519,0.188,-0.04,-0.96,-0.29,0.0,"AAAf",3]],"primary":[[0.756,-0.335,0.076,0.0,1.0,0.0,"Terran Turret",0],[0.662,0.282,0.02,0.0,-1.0,0.0,"Terran Turret",2],[-0.519,0.188,0.121,0.96,-0.29,0.0,"Terran Turret",4]],"thr":[[-0.887,-0.173,0.0109],[-0.923,-0.042,0.0109],[-0.691,0.164,0.0109]]},
  frasmodeus:{"primary":[[0.737,-0.481,0.0,-0.0,0.97,0.25,"Shivan Light Laser",0],[-0.077,-0.179,0.47,0.96,-0.27,0.07,"Shivan Light Laser",2],[-0.077,-0.179,-0.47,-0.96,-0.27,0.07,"Shivan Heavy Laser",3]],"flak":[[-0.945,-0.483,-0.0,0.0,0.88,-0.47,"Shivan Standard Flak",1]],"thr":[[-0.798,-0.149,0.1652]]},
  frbast:{"thr":[[-0.959,-0.165,0.1069],[-0.966,0.061,0.1032]]},
  frbes:{"primary":[[0.281,-0.298,-0.0,0.0,1.0,0.0,"Vasudan Turret",0],[-0.846,-0.326,-0.0,0.0,1.0,0.0,"Vasudan Turret",1]],"thr":[[-0.696,0.027,0.0746],[-0.719,0.22,0.0562]]},
  frchronos:{"primary":[[0.683,-0.376,-0.0,0.0,1.0,0.0,"Subach HL-7",0]],"thr":[[-0.932,-0.125,0.0331],[-0.947,-0.051,0.0331]]},
  frdis:{"primary":[[0.199,-0.092,-0.0,0.0,1.0,0.0,"Shivan Light Laser",0],[0.199,0.001,-0.0,0.0,-1.0,0.0,"Shivan Light Laser",1],[-0.137,-0.308,-0.0,0.0,1.0,0.0,"Shivan Light Laser",2],[-0.346,0.233,0.0,0.0,-1.0,0.0,"Shivan Light Laser",3]],"thr":[[-0.788,-0.046,0.0678],[-0.788,-0.061,0.0678]]},
  frmaat:{"primary":[[0.77,0.045,-0.139,0.0,-0.2,0.98,"Vasudan Turret",0],[-0.872,-0.039,-0.046,0.0,0.0,-1.0,"Mekhu HL-7",1],[0.524,0.389,-0.123,0.0,-1.0,0.0,"Vasudan Turret",2]],"thr":[[-0.694,0.084,0.0442],[-0.708,0.093,0.0506]]},
  frmephisto:{"primary":[[0.797,-0.04,0.0,0.0,1.0,0.0,"Shivan Light Laser",0],[0.895,0.25,0.001,0.0,-1.0,0.0,"Shivan Light Laser",1],[-0.788,-0.068,0.0,-0.0,0.74,-0.67,"Shivan Light Laser",2],[-0.788,0.214,0.0,-0.0,-0.74,-0.67,"Shivan Light Laser",3]],"thr":[[-0.61,0.072,0.0367]]},
  frposeidon:{"primary":[[0.642,-0.598,-0.0,0.0,1.0,0.0,"Subach HL-7",0],[-0.893,-0.447,-0.0,0.0,1.0,0.0,"Subach HL-7",1],[-0.299,0.146,-0.512,-1.0,0.0,0.0,"Subach HL-7",2],[-0.299,0.146,0.512,1.0,0.0,0.0,"Subach HL-7",3]],"thr":[[-0.582,-0.629,0.0678],[-0.521,-0.303,0.0798],[-0.987,-0.259,0.0718],[-0.521,-0.534,0.0798],[-0.477,-0.422,0.0279],[-0.967,-0.325,0.0558],[-0.947,-0.172,0.0359]]},
  frsatis:{"primary":[[0.18,0.063,-0.0,-0.0,-1.0,0.0,"Vasudan Turret",0],[0.896,-0.309,0.0,0.0,1.0,-0.0,"Vasudan Turret",1],[-0.238,-0.08,0.359,1.0,-0.09,-0.0,"Vasudan Turret",2],[-0.238,-0.08,-0.359,-1.0,-0.09,-0.0,"Vasudan Turret",3],[-0.698,-0.128,0.0,0.0,0.02,-1.0,"Vasudan Turret",4]],"thr":[[-0.797,-0.061,0.0674]]},
  frtriton:{"primary":[[0.044,0.489,0.0,0.0,-1.0,0.0,"Subach HL-7",1]],"flak":[[-0.118,-0.489,-0.0,0.0,1.0,0.0,"Standard Flak",0]],"thr":[[-0.329,-0.366,0.0277],[-0.339,-0.364,0.0277],[-0.295,-0.364,0.0277],[-0.252,-0.192,0.0487],[-0.193,0.305,0.0487],[-1.0,-0.323,0.0562],[-0.969,-0.198,0.0562],[-0.945,-0.083,0.0562]]},
  trargo:{"primary":[[0.49,-0.434,0.138,0.0,1.0,0.0,"Terran Turret",0],[-0.423,0.403,0.147,0.0,-1.0,0.0,"Terran Turret",1]],"thr":[[-0.974,0.001,0.058],[-0.974,0.121,0.058]]},
  trazrael:{"primary":[[-0.197,-0.367,-0.241,-0.5,0.86,-0.0,"Shivan Light Laser",0],[-0.198,-0.366,0.242,0.5,0.87,0.0,"Shivan Light Laser",1],[-0.672,0.273,0.033,0.0,-0.98,-0.22,"Shivan Light Laser",2]],"thr":[[-0.544,-0.088,0.0668]]},
  trelysium:{"primary":[[0.019,-0.14,0.067,0.0,1.0,0.0,"Subach HL-7",0]],"thr":[[-0.987,-1.012,0.0952],[-0.987,-0.75,0.0952],[-0.987,1.14,0.0952],[-0.987,0.883,0.0952],[-0.796,-1.055,0.0952],[-0.796,-0.812,0.0952],[-0.796,-0.555,0.0952],[-0.796,-0.312,0.0952],[-0.796,1.178,0.0952],[-0.796,0.93,0.0952],[-0.796,0.683,0.0952],[-0.796,0.435,0.0952]]},
  trisis:{"primary":[[0.038,-0.157,0.002,0.0,1.0,0.0,"Mekhu HL-7",0],[0.573,0.384,0.002,0.0,-1.0,0.0,"Mekhu HL-7",1]],"thr":[[-0.96,-0.108,0.0239]]},
  inarcadia:{"primary":[[0.05,-0.394,-0.724,0.0,1.0,0.0,"Terran Turret",0],[-0.434,-0.371,-0.685,0.0,0.88,-0.48,"Terran Turret",1],[0.057,0.262,-0.61,-0.09,-1.0,0.0,"Terran Turret",2],[-0.366,0.255,-0.657,-0.09,-1.0,-0.0,"Terran Turret",3],[-0.56,-0.354,0.047,-0.0,0.0,-1.0,"Terran Turret",4],[0.271,-0.335,0.047,0.0,0.0,1.0,"Terran Turret",5],[0.19,-1.046,0.018,0.0,1.0,0.0,"Terran Turret",6],[-0.238,0.582,0.14,0.0,-0.71,-0.71,"Terran Turret",7],[0.175,1.046,0.135,0.0,-1.0,-0.0,"Terran Turret",8],[-0.271,0.026,1.398,0.0,1.0,0.0,"Terran Turret",9],[-0.271,0.172,1.403,0.0,-1.0,-0.0,"Terran Turret",10],[-0.934,0.026,0.423,0.0,1.0,0.0,"Terran Turret",11],[0.793,-0.027,1.079,0.0,1.0,0.0,"Terran Turret",12],[0.792,0.176,1.079,0.0,-1.0,-0.0,"Terran Turret",13],[-0.935,0.177,0.421,0.0,-1.0,-0.0,"Terran Turret",14],[0.318,-0.017,-0.636,0.0,-0.04,1.0,"Terran Turret",15],[-0.541,-0.156,-0.588,-0.03,-0.04,-1.0,"Terran Turret",16],[-0.386,-0.063,-1.406,-1.0,-0.04,-0.0,"Terran Turret",17],[0.079,-0.063,-1.429,-1.0,-0.04,-0.0,"Terran Turret",18]],"secondary":[[0.243,-0.526,0.043,-0.0,0.17,0.98,"FighterKiller",19],[-0.259,-0.503,0.091,0.0,0.87,-0.5,"FighterKiller",20],[0.073,-0.229,-1.254,-0.5,0.87,-0.0,"FighterKiller",21],[-0.35,0.103,-1.246,-0.6,-0.8,0.01,"FighterKiller",22],[-0.269,0.105,1.463,1.0,-0.0,0.0,"FighterKiller",23]]},
  gmanuket:{"primary":[[-0.352,0.152,-0.0,0.0,-1.0,0.0,"Vasudan Turret Weak",0],[-0.4,0.012,0.083,0.72,0.56,-0.42,"Vasudan Turret Weak",2],[0.135,0.014,-0.09,-0.81,0.35,-0.48,"Subach HL-7",3],[0.135,0.014,0.09,0.81,0.35,-0.48,"Subach HL-7",4]],"flak":[[-0.4,0.012,-0.083,-0.72,0.56,-0.42,"Standard Flak",1]],"thr":[[-0.738,0.065,0.0057],[-0.74,0.08,0.0068]]},
  gmrahu:{"primary":[[0.315,0.023,-0.205,-0.8,0.0,0.6,"Shivan Heavy Laser",0],[0.315,0.023,0.205,0.8,0.0,0.6,"Shivan Heavy Laser",1],[0.753,0.164,0.0,0.0,-0.45,0.89,"Shivan Heavy Laser",2]],"thr":[[-0.815,-0.001,0.1431]]},
  gmzephyrus:{"primary":[[0.608,-0.229,-0.0,0.0,1.0,0.0,"Terran Turret Weak",0],[-0.592,-0.101,-0.188,-0.98,0.21,0.01,"Terran Turret Weak",2],[0.536,0.129,0.0,0.0,-1.0,0.0,"Subach HL-7",3],[-0.559,-0.148,0.0,0.0,0.0,-1.0,"Subach HL-7",4]],"flak":[[-0.592,-0.101,0.188,0.98,0.21,0.01,"Standard Flak",1]],"thr":[[-0.777,-0.139,0.019],[-0.773,-0.022,0.0159],[-0.758,-0.199,0.0072]]}
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
  // v202: a hull turned about her length (F3D_ROLL) carries her turrets
  // round; one seen from another side (F3D_VIEW) as well, and the picture's
  // width is then another span of her
  const rl = F3D_ROLL[key] || 0, cr = Math.cos(rl), sr = Math.sin(rl);
  const vw = F3D_VIEW[key] || 0, cv = Math.cos(vw), sv = Math.sin(vw);
  const hs = vw && F3D.models[f3dKey({img: key})] && F3D.models[f3dKey({img: key})].full && F3D.models[f3dKey({img: key})].full.head;
  if(vw && !hs) return m;                 // her model's size first (not cached)
  const kv = vw ? hs.size[2]/(hs.size[2]*Math.abs(cv) + hs.size[0]*Math.abs(sv)) : 1;
  const pos = (!rl && !vw) ? function(q){ return {dx: sg*q[0], dy: q[1]*asp, mx: q[2], n3: [q[3], q[4], q[5]], wpn: q[6], ti: q[7]}; }
    : function(q){
        const z0 = q[0], y0 = q[1]*cr - q[2]*sr, x0 = q[2]*cr + q[1]*sr;
        const n0 = q[3]*cr - q[4]*sr, n1 = q[3]*sr + q[4]*cr, n2 = q[5];
        return {dx: sg*(z0*cv + x0*sv)*kv, dy: y0*kv*asp, mx: (x0*cv - z0*sv)*kv,
                n3: [n0*cv - n2*sv, n1, n2*cv + n0*sv], wpn: q[6], ti: q[7]}; };
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
      + 'uniform mat4 uM; uniform mat4 uVP; varying vec3 vW; varying vec3 vN; varying vec2 vT; varying vec3 vP; varying vec3 vMN;'
      + 'void main(){ vec4 w = uM*vec4(aP,1.0); vW = w.xyz; vN = mat3(uM)*aN; vT = aT*3.99994-1.0; vP = aP; vMN = aN; gl_Position = uVP*w; }';
    const fs = (deriv ? '#extension GL_OES_standard_derivatives : enable\n#define DERIV 1\n' : '')
      + 'precision mediump float; varying vec3 vW; varying vec3 vN; varying vec2 vT; varying vec3 vP; varying vec3 vMN;'
      + 'uniform sampler2D tC; uniform sampler2D tN; uniform sampler2D tG; uniform sampler2D tD; uniform sampler2D tF;'
      + 'uniform vec4 uDP; uniform vec3 uDD; uniform vec4 uFR; uniform float uFon;'
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
      // v204: what she has taken, on her hull - the damage picture of her
      // side view (20_render.js) laid onto the model across her flanks,
      // faded where the plating turns away from the side
      + ' if(uDP.w > 0.5){ vec2 su = vec2(0.5 + uDP.x*vP.z + uDP.y*vP.x, 0.5 + uDP.z*vP.y);'
      + '  float fw = smoothstep(0.12, 0.45, abs(dot(normalize(vMN), uDD)));'
      + '  if(su.x > 0.0 && su.x < 1.0 && su.y > 0.0 && su.y < 1.0){ vec4 m = texture2D(tD, su); col = mix(col, m.rgb, m.a*fw);'
      + '   if(uFon > 0.5){ vec2 fu = (su - uFR.xy)/uFR.zw;'
      + '    if(fu.x > 0.0 && fu.x < 1.0 && fu.y > 0.0 && fu.y < 1.0){ vec4 f = texture2D(tF, fu); col = mix(col, f.rgb, f.a*fw); } } } }'
      + ' gl_FragColor = vec4(col*uA, uA); }';
    const sh = function(t, src){ const s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
      if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr, gl.LINK_STATUS)) return false;
    const loc = {};
    for(const a of ['aP', 'aN', 'aT']) loc[a] = gl.getAttribLocation(pr, a);
    for(const u of ['uM', 'uVP', 'tC', 'tN', 'tG', 'uHasN', 'uKind', 'uCam', 'uL1', 'uL2', 'uClip', 'uA', 'uGA', 'uGF',
                    'tD', 'tF', 'uDP', 'uDD', 'uFR', 'uFon']) loc[u] = gl.getUniformLocation(pr, u);
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
// v201: a model file, from what the loading page already fetched
// (window.FS3_MODELS, by path) or from the server. .gz files are unpacked
// here (the full level is shipped gzipped, half the size).
function f3dFile(path){
  const rev = (typeof M3D_REV !== 'undefined') ? M3D_REV : 0;
  const pre = (typeof window !== 'undefined' && window.FS3_MODELS) ? window.FS3_MODELS[path] : null;
  if(pre && typeof window !== 'undefined') delete window.FS3_MODELS[path];
  return pre ? Promise.resolve(pre) : fetch(path + '?r=' + rev).then(function(r){
    if(!r.ok) throw new Error('missing'); return r.blob();
  });
}
function f3dFetchBin(path){
  return f3dFile(path).then(function(blob){
    if(/\.gz$/.test(path)){
      if(typeof DecompressionStream === 'undefined') throw new Error('no gzip');
      return new Response(blob.stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    }
    return blob.arrayBuffer();
  });
}
function f3dLevel(key, tag, size){
  const gl = F3D.gl, rev = (typeof M3D_REV !== 'undefined') ? M3D_REV : 0;
  const L = {state: 'loading', parts: [], tex: {}};
  f3dFetchBin(M3D_BASE + key + '/' + (tag === 'full' ? 'full.bin.gz' : tag + '.bin')).then(function(buf){
    if(gl !== F3D.gl) throw new Error('lost');
    const hl = new DataView(buf).getUint32(0, true);
    const head = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 4, hl)));
    const data = buf.slice(4 + hl);
    L.head = head;
    const want = {};
    for(const p of head.parts){
      const mk = function(target, from, bytes){ const b = gl.createBuffer(); gl.bindBuffer(target, b);
        gl.bufferData(target, new Uint8Array(data, from, bytes), gl.STATIC_DRAW); return b; };
      // v199: the level keeps its shape for the hit map (f3dMask); v201 the
      // full one, the only one the field loads now
      const pnd = head.nodes && p.node ? head.nodes[p.node] : null;
      if(tag === 'full' && p.kind !== 'skip' && !(pnd && pnd.k === 'deb')){
        (L.cpu = L.cpu || []).push({pos: new Int16Array(data.slice(p.pos, p.pos + p.nv*6)),
          idx: p.big ? new Uint32Array(data.slice(p.idx, p.idx + p.ni*4)) : new Uint16Array(data.slice(p.idx, p.idx + p.ni*2))});
      }
      L.parts.push({kind: p.kind, tex: (p.tex||'').toLowerCase(), n: p.ni, big: p.big, node: p.node || 0,
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
          const ip = M3D_BASE + key + '/' + t + '_' + k + size + '.webp';
          const pb = (typeof window !== 'undefined' && window.FS3_MODELS) ? window.FS3_MODELS[ip] : null;
          if(pb){ delete window.FS3_MODELS[ip]; im.src = URL.createObjectURL(pb); }
          else im.src = ip + '?r=' + rev;
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
    f3dLoadBoxShow();
    if(n < F3D_KEYS.length) setTimeout(tick, 100);
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
      if(L){
        const e = {img: k, sc: 1, flip: false, ang: 0};
        f3dRender([{e: e, L: L, x: W/2, y: H/2, a: 1, clip: null}], true);
      }
    }catch(er){}
    if(ks.length) setTimeout(one, 15); else { F3D_PRE.warm = true; f3dLoadBoxShow(); }
  };
  one();
}
// ── ONE LOADING BAR (v201) ───────────────────────────────────
// Silvio: one bar from start to finish. The loading page fetches the game
// and the models and hands over its box (window.FS3_LOADBOX); the game
// shows that same box again over everything while it puts the models on
// the graphics card, carries the bar on from where the page left it, and
// takes it away when the ships are ready. Its style lives in a shadow root,
// so none of it touches the game's page.
let F3D_BOX = null;
function f3dLoadBoxShow(){
  if(typeof window === 'undefined' || typeof document === 'undefined' || !document.body) return;
  const lb = window.FS3_LOADBOX;
  if(!lb) return;
  const ready = F3D.off || F3D.ok === false || (F3D_PRE.done && F3D_PRE.warm) || f3dNow() - (lb.t0 || (lb.t0 = f3dNow())) > 30000;
  if(ready){
    if(F3D_BOX && F3D_BOX.parentNode) F3D_BOX.parentNode.removeChild(F3D_BOX);
    F3D_BOX = null; window.FS3_LOADBOX = null;
    return;
  }
  if(!F3D_BOX){
    const host = document.createElement('div');
    host.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;z-index:50;background:#000;' +
      'display:flex;align-items:center;justify-content:center;font-family:Tahoma,"Segoe UI",sans-serif';
    if(lb.cls) host.className = lb.cls;
    const root = host.attachShadow ? host.attachShadow({mode: 'open'}) : host;
    const css = String(lb.css || '').replace(/:root/g, ':host').replace(/html\.void/g, ':host(.void)');
    root.innerHTML = '<style>' + css + '</style>' + lb.html;
    document.body.appendChild(host);
    F3D_BOX = host;
  }
  const root = F3D_BOX.shadowRoot || F3D_BOX;
  const n = F3D_PRE.of ? F3D_PRE.n/F3D_PRE.of : 0;
  const p = Math.min(1, (lb.p || 0) + (1 - (lb.p || 0))*(n*0.9 + (F3D_PRE.warm ? 0.1 : 0)));
  const segs = root.querySelectorAll('.seg'), N = segs.length, full = Math.floor(p*N);
  for(let i = 0; i < N; i++){
    segs[i].className = 'seg' + (i < full ? ' on' : (i === full && p < 1 ? ' now' : ''));
    if(segs[i].firstChild) segs[i].firstChild.style.width = (i === full ? Math.round((p*N - full)*100) : 0) + '%';
  }
  const st = root.querySelector('#status');
  if(st) st.innerHTML = 'PREPARING SHIPS <b>' + Math.round(p*100) + ' %</b>';
}
if(typeof window !== 'undefined' && typeof setTimeout !== 'undefined') setTimeout(function(){
  // straight away, not on the first title frame: the box is there at once
  if(window.FS3_LOADBOX){ f3dLoadBoxShow(); try{ f3dPreload(); }catch(e){} if(!F3D_PRE.on) f3dLoadBoxShow(); }
}, 0);
// The bar on the title screen while the ships load.
function f3dPreloadBar(){
  if(!F3D_PRE.on) f3dPreload();
  // v201: no bar of its own on the title any more (Silvio: it covered the
  // title's text) - the loading page's bar carries it, see f3dLoadBoxShow
  return;
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
// v201: the field loads the full level only (it is loaded up front now);
// lo stays as a name for it.
function f3dModel(key){
  let m = F3D.models[key];
  if(!m){
    const L = f3dLevel(key, 'full', f3dSmall(key) ? 512 : 1024);
    m = F3D.models[key] = {lo: L, full: L};
  }
  return m;
}
function f3dReadyLevel(key){
  if(F3D.off || !f3dInit()) return null;
  const m = f3dModel(key);
  return (m.full && m.full.state === 'ready') ? m.full : null;
}
function f3dMat(e, x, y, L){
  const right = (spriteFacing(e.img) === 'right') !== !!e.flip;
  const vw = F3D_VIEW[e.img] || 0;
  const yaw = (right ? Math.PI/2 : -Math.PI/2) - (right ? vw : -vw);
  const img = IMGS[e.img], w = img ? img.width*e.sc : 100;
  // the hull's width across the picture: her length from the side, her
  // beam face on (F3D_VIEW)
  const sz = L.head.size, span = sz[2]*Math.abs(Math.cos(vw)) + sz[0]*Math.abs(Math.sin(vw));
  const s = w/Math.max(0.01, span/L.head.ext);
  const a = -(e.ang||0), ca = Math.cos(a), sa = Math.sin(a), cy = Math.cos(yaw), sy = Math.sin(yaw);
  const rl = (F3D_ROLL[e.img] || 0) + (f3dSmall(F3D_ALIAS[e.img] || e.img) ? f3dTurnRoll(e) : 0);
  if(rl){
    // translate * rotZ(a) * rotY(yaw) * roll about the bow * scale (v202)
    const A = f3dMulA(f3dMulA([ca, sa, 0, -sa, ca, 0, 0, 0, 1], [cy, 0, -sy, 0, 1, 0, sy, 0, cy]),
                      [Math.cos(rl), Math.sin(rl), 0, -Math.sin(rl), Math.cos(rl), 0, 0, 0, 1]);
    return new Float32Array([s*A[0], s*A[1], s*A[2], 0, s*A[3], s*A[4], s*A[5], 0,
                             s*A[6], s*A[7], s*A[8], 0, x, -y, 0, 1]);
  }
  // v209: a capital ship is sunk below the play plane by half her
  // thickness, so the side facing the camera lies in the plane - fighters
  // fly over her, and her drawn hull is never larger than her 2D outline
  // (Silvio). f3dMidZ() gives the same depth to the 2D overlays.
  const tz = f3dSmall(F3D_ALIAS[e.img] || e.img) ? 0 : -s*(sz[0]*Math.abs(Math.cos(vw)) + sz[2]*Math.abs(Math.sin(vw)))/2/L.head.ext;
  // translate * rotZ(a) * rotY(yaw) * scale, column-major
  return new Float32Array([
    s*ca*cy, s*sa*cy, -s*sy, 0,
    -s*sa,   s*ca,    0,     0,
    s*ca*sy, s*sa*sy, s*cy,  0,
    x,       -y,      tz,    1]);
}
// v203: how far a small craft is rolled about her length. The sprite was
// mirrored when her nose came round past the vertical (poseFor, KEEP_UPRIGHT);
// a mirrored side view is the hull rolled half round her length, so the
// model rolls through that half turn instead (about a third of a second),
// the way her heading turns. And she banks while she turns, a little,
// so her back or her belly shows.
const F3D_ROLL_RATE = Math.PI/0.32;                       // rad/s
const F3D_BANK_K = 0.30, F3D_BANK_MAX = 0.65, F3D_BANK_TAU = 0.12;
function f3dTurnRoll(e){
  const now = f3dNow()/1000, fl = !!e.flip, h = (e.ang || 0) + (fl ? Math.PI : 0);
  let s = e._f3r;
  if(!s){ s = e._f3r = {fl: fl, h: h, t: now, r: 0, b: 0}; return 0; }
  const dt = Math.max(0, Math.min(0.1, now - s.t)); s.t = now;
  let dh = h - s.h; s.h = h;
  while(dh > Math.PI) dh -= 2*Math.PI; while(dh < -Math.PI) dh += 2*Math.PI;
  if(fl !== s.fl){
    s.fl = fl;
    // the picture is the same hull rolled by pi: start from there and roll
    // back, the way she is turning
    let r = s.r + Math.PI;
    while(r > Math.PI) r -= 2*Math.PI; while(r < -Math.PI) r += 2*Math.PI;
    if(Math.abs(Math.abs(r) - Math.PI) < 0.3) r = (dh >= 0 ? 1 : -1)*Math.abs(r);
    s.r = r;
  }
  if(s.r){
    const st = F3D_ROLL_RATE*dt;
    s.r = Math.abs(s.r) <= st ? 0 : s.r - Math.sign(s.r)*st;
  }
  if(dt > 0){
    const bw = f3dBow(e);
    const want = Math.max(-F3D_BANK_MAX, Math.min(F3D_BANK_MAX, F3D_BANK_K*bw*dh/dt));
    s.b += (want - s.b)*(1 - Math.exp(-dt/F3D_BANK_TAU));
  }
  return s.r + s.b;
}
// The player's hull, drawn from her model (70_ui.js): one object that keeps
// her roll and is handed to the break-up when she dies. False: draw the
// sprite.
const F3D_PL = {img: null, sc: 1, flip: false, ang: 0, x: 0, y: 0, faction: 'terran', player: true};
function f3dPlayer(key, x, y, sc, flip, ang, a){
  if(F3D.off || typeof document === 'undefined') return false;
  const k = f3dKey({img: key}); if(!k) return false;
  const L = f3dReadyLevel(k); if(!L) return false;
  const P = F3D_PL;
  if(P.img !== key){ P.img = key; P._f3r = null; P._f3n = null; P._shq = null;
    P.faction = (typeof shipStats === 'function' && shipStats(key).fac) || 'terran'; }
  P.sc = sc; P.flip = !!flip; P.ang = ang || 0; P.x = x; P.y = y;
  if(typeof player !== 'undefined'){ P.rvx = player.vx || 0; P.rvy = player.vy || 0; }
  P._f3fc = (typeof fc !== 'undefined') ? fc : 0;
  const ga = ctx.globalAlpha;
  ctx.globalAlpha = 1;
  try{ f3dRender([{e: P, L: L, x: x, y: y, a: ga, clip: null}]); }
  catch(er){ F3D.err = String(er && er.message || er); ctx.globalAlpha = ga; return false; }
  ctx.globalAlpha = ga;
  return true;
}
// v209: the eye's height over the play plane, in world units (f3dVP)
function f3dEyeD(){
  const z = (typeof CAM !== 'undefined' && CAM.z) || 1;
  return (H/2)/Math.tan(F3D_FOV/2)/z;
}
// v209: a world point at height z over the play plane (negative: under
// it) moved to where the camera shows it in the plane - the same rays as
// the 3D picture (f3dVP), so a 2D overlay drawn there sits on the drawn
// model. Logic and hits stay in the plane; this is only for drawing.
function f3dPersp(x, y, z){
  if(!z || F3D_FOV < 0.1) return {x: x, y: y};
  const D = f3dEyeD(), k = D/Math.max(D*0.05, D - z);
  const ex = (typeof CAM !== 'undefined') ? s2wX(W/2) : W/2, ey = (typeof CAM !== 'undefined') ? s2wY(H/2) : H/2;
  return {x: ex + (x - ex)*k, y: ey + (y - ey)*k};
}
// v209: how deep under the play plane the middle of a hull drawn from her
// model lies (f3dMat sinks a capital ship by half her thickness). 0 for
// small craft, sprites and the sprite mode.
function f3dMidZ(e){
  if(!f3dOn(e) || e.type === 'asteroid') return 0;
  if(f3dSmall(F3D_ALIAS[e.img] || e.img)) return 0;
  const k = f3dKey(e), L = k ? f3dReadyLevel(k) : null;
  if(!L || !L.head || !L.head.size) return 0;
  const vw = F3D_VIEW[e.img] || 0, sz = L.head.size, img = IMGS[e.img];
  const span = sz[2]*Math.abs(Math.cos(vw)) + sz[0]*Math.abs(Math.sin(vw));
  const s = (img ? img.width*e.sc : 100)/Math.max(0.01, span/L.head.ext);
  return -s*(sz[0]*Math.abs(Math.cos(vw)) + sz[2]*Math.abs(Math.sin(vw)))/2/L.head.ext;
}
// v209: a point on a hull (in the plane, as the game has it) moved to
// where her model is drawn: at the depth of her middle, d higher (towards
// the camera; a turret's own depth, mountDepth). Safe for every ship: a
// sprite or a small craft gets the point back as it is.
function hullPt(e, x, y, d){
  const z = f3dMidZ(e);
  if(!z) return {x: x, y: y};
  return f3dPersp(x, y, Math.min(0, z + (d || 0)));
}
function f3dVP(){
  // v208: through the camera (10_core.js). The canvas covers the whole
  // screen; its middle is the world point s2w(W/2, H/2), and the zoom moves
  // the eye back.
  const D = f3dEyeD(), asp = W/H, f = 1/Math.tan(F3D_FOV/2);
  // v209: checked for 40 degrees - a sunk Colossus reaches ~D+1200 deep,
  // the overview D ~5900; a debris piece standing up comes nearer than
  // the plane, so the near plane sits closer than before (0.3)
  const near = D*0.15, far = D*3, nf = 1/(near - far);
  const P = [f/asp,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0];
  const ex = (typeof CAM !== 'undefined') ? s2wX(W/2) : W/2, ey = -((typeof CAM !== 'undefined') ? s2wY(H/2) : H/2);
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
  gl.uniform1i(loc.tC, 0); gl.uniform1i(loc.tN, 1); gl.uniform1i(loc.tG, 2); gl.uniform1i(loc.tD, 3); gl.uniform1i(loc.tF, 4);
  const now = ((typeof performance !== 'undefined') ? performance.now() : Date.now())/1000;
  for(const it of items){
    const L = it.L;
    // v203: every ship on her own depth - drawn in the field's order (the
    // big ones first), each lies wholly in front of the ones before it, as
    // the sprites did; two hulls never cut into each other (Silvio: M11,
    // M38, M54, M78)
    gl.clear(gl.DEPTH_BUFFER_BIT);
    const M0 = it.M || f3dMat(it.e, it.x, it.y, L);
    // v201: moving parts - one matrix per node (turret bases, barrels,
    // spinning dishes), the hull's own for node 0
    const NM = (it.deb != null) ? null : ((L.head && L.head.nodes && !warm) ? f3dNodeMats(it.e, L, M0, it.x, it.y, now) : null);
    let curNode = -1;
    gl.uniformMatrix4fv(loc.uM, false, M0);
    gl.uniform1f(loc.uA, it.a);
    f3dDmgBind(it.deb != null ? null : it.e, L);
    // the clip of a ship sliding through her vortex (fsWarpClip), in the
    // field's own units with y turned up
    if(it.clip){ const c = it.clip; gl.uniform3f(loc.uClip, c.sg*c.fx, -c.sg*c.fy, -c.sg*(c.px*c.fx + c.py*c.fy)); }
    else gl.uniform3f(loc.uClip, 0, 0, 1);
    if(it.a < 1){ gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); } else gl.disable(gl.BLEND);
    const DN = L.head && L.head.nodes;
    for(const p of L.parts){
      // v202: debris pieces only fly when she breaks up (it.deb: that piece)
      if(it.deb != null){ if(p.node !== it.deb) continue; }
      else if(p.node && DN && DN[p.node] && DN[p.node].k === 'deb') continue;
      if(NM && p.node !== curNode){ curNode = p.node; gl.uniformMatrix4fv(loc.uM, false, p.node ? NM[p.node] : M0); }
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
    // v208: her engine flames (FUEL), then v205: her shield where it was
    // hit, over her hull
    if(!warm){ try{ f3dThDraw(it, M0, cam); }catch(et){ F3D.err = String(et && et.message || et); } }
    if(!warm) f3dShDraw(it, M0, cam);
  }
  gl.disable(gl.BLEND);
  // v208: the picture is the screen's, whatever transform the field has
  if(!warm){
    ctx.save();
    if(typeof camScreen === 'function') camScreen();
    ctx.drawImage(can, 0, 0, W, H);
    ctx.restore();
  }
}
// ── DAMAGE ON THE MODEL (v204) ───────────────────────────────
// Silvio (M38): the damage of a ship drawn from her model lies on her
// model, under whatever is in front of her. The damage picture is still
// made as before (dmgBuild: scoring, tears, craters, in the sprite's side
// view; dmgFx: hot edges, fire, arcs), but handed to the graphics card and
// laid onto the hull across her flanks: it turns with her and is hidden
// by any hull in front.
function f3dDmgTex(old, src){
  const gl = F3D.gl;
  const t = (old && old.gl === gl) ? old : {gl: gl, t: gl.createTexture(), w: 0, h: 0};
  // uploaded on a unit of its own: the units 0-4 hold what is being drawn
  gl.activeTexture(gl.TEXTURE5);
  gl.bindTexture(gl.TEXTURE_2D, t.t);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return t;
}
function f3dDmgBind(e, L){
  const gl = F3D.gl, loc = F3D.loc;
  const D = e && e.dm, img = e && IMGS[e.img];
  if(!D || !D.can || !D.gl3 || !img || !img.width || !L.head || F3D_ROLL[e.img]){
    gl.uniform4f(loc.uDP, 0, 0, 0, 0); return;
  }
  // the marks: uploaded again when they were drawn again
  if(!D.t3 || D.t3.gl !== gl || D.t3b !== D.built){ D.t3 = f3dDmgTex(D.t3, D.can); D.t3b = D.built; }
  // model (normalised) -> the sprite's box, as f3dMat and f3dMounts place her
  const vw = F3D_VIEW[e.img] || 0, cv = Math.cos(vw), sv = Math.sin(vw);
  const sz = L.head.size, ext = L.head.ext;
  const span = sz[2]*Math.abs(cv) + sz[0]*Math.abs(sv);
  const sg = spriteFacing(e.img) === 'left' ? -1 : 1;
  gl.uniform4f(loc.uDP, sg*cv*ext/span, sg*sv*ext/span, -ext*img.width/(span*img.height), 1);
  gl.uniform3f(loc.uDD, cv, 0, -sv);
  gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, D.t3.t);
  const R = D.fxR;
  if(D.fxL && R && R.w > 0){
    if(!D.t4 || D.t4.gl !== gl || D.t4b !== D.fxT){ D.t4 = f3dDmgTex(D.t4, D.fxL); D.t4b = D.fxT; }
    gl.uniform4f(loc.uFR, R.x0/R.w, R.y0/R.h, R.fw/R.w, R.fh/R.h);
    gl.uniform1f(loc.uFon, 1);
    gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, D.t4.t);
  } else gl.uniform1f(loc.uFon, 0);
}
// ── MOVING PARTS (v201) ──────────────────────────────────────
// Turrets turn to what they shoot at, as in FreeSpace: the base about its
// own axis, the barrel up and down; after a while without a target they
// go back to rest. Spinning parts ($rotate: radar dishes, the Mjolnir's
// rings) turn at their FreeSpace rate. Only the picture moves - where a
// turret can fire is still decided by its face (mountCanAim).
const F3D_TURN_BASE = 1.6, F3D_TURN_GUN = 1.2;     // rad/s
const F3D_AIM_HOLD = 300;                           // steps a target is kept
function f3dM4(a, b){
  const o = new Float32Array(16);
  for(let c = 0; c < 4; c++) for(let r = 0; r < 4; r++)
    o[c*4+r] = a[r]*b[c*4] + a[4+r]*b[c*4+1] + a[8+r]*b[c*4+2] + a[12+r]*b[c*4+3];
  return o;
}
// turn by a about axis u through point p (column-major)
function f3dRotAbout(p, u, a){
  const c = Math.cos(a), s = Math.sin(a), t = 1 - c, x = u[0], y = u[1], z = u[2];
  const R = [t*x*x + c, t*x*y + s*z, t*x*z - s*y,
             t*x*y - s*z, t*y*y + c, t*y*z + s*x,
             t*x*z + s*y, t*y*z - s*x, t*z*z + c];
  const tx = p[0] - (R[0]*p[0] + R[3]*p[1] + R[6]*p[2]);
  const ty = p[1] - (R[1]*p[0] + R[4]*p[1] + R[7]*p[2]);
  const tz = p[2] - (R[2]*p[0] + R[5]*p[1] + R[8]*p[2]);
  return new Float32Array([R[0], R[1], R[2], 0, R[3], R[4], R[5], 0, R[6], R[7], R[8], 0, tx, ty, tz, 1]);
}
function f3dDot(a, b){ return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
function f3dCross(a, b){ return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]; }
// Where each turret of the ship wants to point: the target of the beam on
// it, or the last shot of the gun on it (f3dAim, from 50_combat.js).
// the base's rest heading: the bow (+z) across the turret's normal, or up
// for a turret that itself faces the bow
function f3dRestFw(ax){
  let f = [0, 0, 1];
  if(Math.abs(ax[2]) > 0.9) f = [0, 1, 0];
  const k = f3dDot(f, ax), v = [f[0] - k*ax[0], f[1] - k*ax[1], f[2] - k*ax[2]];
  const l = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0]/l, v[1]/l, v[2]/l];
}
function f3dAimPoints(e){
  const out = {};
  if(e.beams) for(const b of e.beams){
    if(b.ti == null) continue;
    if(b.state === 'firing'){
      const mp = mountPos(e, b), a = b.type === 'slash' ? b.curAngle : b.angle;
      out[b.ti] = {x: mp.x + Math.cos(a)*600, y: mp.y + Math.sin(a)*600};
    } else if(b.state === 'charging' && b.tgt) out[b.ti] = {x: b.tgt.x, y: b.tgt.y};
  }
  const A = e._aimT;
  if(A) for(const ti in A){
    const q = A[ti];
    if(typeof fc !== 'undefined' && fc - q.fc > F3D_AIM_HOLD){ delete A[ti]; continue; }
    if(!out[ti]) out[ti] = q;
  }
  return out;
}
function f3dAim(e, ti, x, y){
  if(ti == null) return;
  (e._aimT || (e._aimT = {}))[ti] = {x: x, y: y, fc: (typeof fc !== 'undefined') ? fc : 0};
}
function f3dNodeMats(e, L, M0, x, y, now){
  const N = L.head.nodes, n = N.length;
  let st = e._f3n;
  if(!st || st.n !== n) st = e._f3n = {n: n, a: new Float32Array(n), t: now};
  const dt = Math.max(0, Math.min(0.1, now - st.t)); st.t = now;
  const aims = f3dAimPoints(e);
  // the model's turn and size: model directions from field directions
  const sc = Math.hypot(M0[0], M0[1], M0[2]) || 1;
  const toModel = function(w){ return [(M0[0]*w[0] + M0[1]*w[1] + M0[2]*w[2])/sc,
                                       (M0[4]*w[0] + M0[5]*w[1] + M0[6]*w[2])/sc,
                                       (M0[8]*w[0] + M0[9]*w[1] + M0[10]*w[2])/sc]; };
  const out = new Array(n); out[0] = M0;
  const ease = function(j, want, rate, wrap){
    let d = want - st.a[j];
    if(wrap){ while(d > Math.PI) d -= 2*Math.PI; while(d < -Math.PI) d += 2*Math.PI; }
    const mx = rate*dt;
    st.a[j] += Math.max(-mx, Math.min(mx, d));
  };
  for(let j = 1; j < n; j++){
    const nd = N[j]; if(!nd){ out[j] = M0; continue; }
    const par = (nd.par && out[nd.par]) ? out[nd.par] : M0;
    let ang = 0;
    if(nd.k === 'rot'){
      ang = (2*Math.PI*now/(nd.t || 20)) % (2*Math.PI);
    } else {
      const tgt = aims[nd.ti];
      let want = 0;
      if(tgt){
        // the turret's place in the field, and the way to the target in
        // the model's own space
        const pv = nd.pv;
        const wx = M0[0]*pv[0] + M0[4]*pv[1] + M0[8]*pv[2] + M0[12];
        const wy = M0[1]*pv[0] + M0[5]*pv[1] + M0[9]*pv[2] + M0[13];
        const wz = M0[2]*pv[0] + M0[6]*pv[1] + M0[10]*pv[2] + M0[14];
        let d = toModel([tgt.x - wx, -tgt.y - wy, -wz]);
        const dl = Math.hypot(d[0], d[1], d[2]) || 1; d = [d[0]/dl, d[1]/dl, d[2]/dl];
        const ax = nd.ax, up = f3dDot(d, ax);
        if(nd.k === 'base'){
          // FreeSpace: the base faces the model's bow at rest
          const f0 = f3dRestFw(ax);
          const dp = [d[0] - up*ax[0], d[1] - up*ax[1], d[2] - up*ax[2]];
          if(Math.hypot(dp[0], dp[1], dp[2]) > 1e-4)
            want = Math.atan2(f3dDot(f3dCross(f0, dp), ax), f3dDot(f0, dp));
        } else {
          // FreeSpace: a barrel rests pointing along the turret's normal and
          // tips over towards the bow side its base faces, down to just
          // past level
          want = Math.max(0, Math.min(Math.PI/2 + 0.12, Math.acos(Math.max(-1, Math.min(1, up)))));
        }
      }
      ease(j, want, nd.k === 'base' ? F3D_TURN_BASE : F3D_TURN_GUN, nd.k === 'base');
      ang = st.a[j];
    }
    let axis = nd.ax;
    if(nd.k === 'gun'){
      // tips the normal towards the base's rest bow side; the base's own
      // turn is in the parent matrix
      const r = f3dCross(nd.ax, f3dRestFw(nd.ax)), rl = Math.hypot(r[0], r[1], r[2]) || 1;
      axis = [r[0]/rl, r[1]/rl, r[2]/rl];
    }
    out[j] = f3dM4(par, f3dRotAbout(nd.pv, axis, ang));
  }
  return out;
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
// The model's side view as a hit map, in the sprite's box (as wide as the
// sprite, as tall as the model is): sg the sprite's facing, rl the turn
// about her length.
function f3dBuildMask(L, img, sg, rl){
  const hd = L.head;
  // a hull turned about her length (F3D_ROLL) shows another height
  const cr = Math.cos(rl), sr = Math.sin(rl);
  const hy = Math.abs(cr)*hd.size[1] + Math.abs(sr)*hd.size[0];
  const ky = Math.max(1, hy/hd.size[2]*img.width/img.height*1.02);
  const f = Math.min(1, MASK_MAX/Math.max(img.width, img.height*ky));
  const mw = Math.max(1, Math.round(img.width*f)), mh = Math.max(1, Math.round(img.height*ky*f));
  const e = hd.ext/32767, s = mw/hd.size[2];
  // v199b (Silvio: a few seconds of still picture at the start): filled
  // here pixel by pixel instead of as one canvas path - a path of 90,000
  // triangles held the Sathanas up for seconds. Each triangle sets the
  // map cells whose centre it covers, at most a few dozen cells apiece.
  const bits = new Uint8Array(mw*mh);
  for(const pt of L.cpu){
    const P = pt.pos, I = pt.idx;
    for(let i = 0; i + 2 < I.length; i += 3){
      const a = I[i]*3, b = I[i+1]*3, c3 = I[i+2]*3;
      const ax = mw/2 + sg*P[a+2]*e*s, ay = mh/2 - (P[a+1]*cr + P[a]*sr)*e*s;
      const bx = mw/2 + sg*P[b+2]*e*s, by = mh/2 - (P[b+1]*cr + P[b]*sr)*e*s;
      const cx = mw/2 + sg*P[c3+2]*e*s, cy = mh/2 - (P[c3+1]*cr + P[c3]*sr)*e*s;
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
  return {w: mw, h: mh, bits: bits, ky: ky, model: true};
}
// v204 (Silvio: a hull that turns is hit where she is): the small craft are
// hit on their model's outline as it is drawn - one map per stage of her
// roll, built when first asked for. Only while she is drawn from her model
// (the sprite's map otherwise).
const F3D_RSTEPS = 16;
const F3D_RMASK = {};
function f3dRollMask(key, o){
  if(!o || F3D.off || o._f3fc == null || typeof fc === 'undefined' || fc - o._f3fc > 2) return null;
  const k = F3D_ALIAS[key] || key;
  if(!f3dSmall(k) || F3D_VIEW[key]) return null;
  const m = F3D.models[k], L = m && m.lo;
  const img = IMGS[key];
  if(!L || L.state !== 'ready' || !L.cpu || !img || !img.width) return null;
  const s = o._f3r, tw = 2*Math.PI;
  let r = (s ? s.r + s.b : 0) + (F3D_ROLL[key] || 0);
  r = ((r % tw) + tw) % tw;
  const i = Math.round(r/tw*F3D_RSTEPS) % F3D_RSTEPS;
  const A = F3D_RMASK[key] || (F3D_RMASK[key] = []);
  if(A[i] === undefined){
    try{ A[i] = f3dBuildMask(L, img, spriteFacing(key) === 'left' ? -1 : 1, i*tw/F3D_RSTEPS); }
    catch(err){ A[i] = null; }
  }
  return A[i];
}
// v199 (Silvio: model and the old data do not always line up): a ship
// drawn from her model is hit where her model is. The hit map of the sprite
// (buildMask, 20_render.js) is replaced by the model's side view, drawn from
// the coarse level into the same box - once per hull, when it has loaded.
// What of the model sticks out of the sprite's box (the Sathanas' claws)
// is not in the map yet.
// v201: a map of its own (MASKS3D), as tall as the model is: what sticks
// out of the sprite's box (the Sathanas' claws) is hit too. The sprite's
// map (MASKS) stays for subsystem placing and wreckage.
const F3D_MASKED = {};
const MASKS3D = {};
function f3dMask(skey, mkey){
  if(F3D_MASKED[skey] || typeof MASKS === 'undefined' || typeof document === 'undefined') return;
  const m = F3D.models[mkey], L = m && m.lo;
  const img = IMGS[skey];
  if(!L || L.state !== 'ready' || !L.cpu || !img || !img.width) return;
  F3D_MASKED[skey] = true;
  if(F3D_VIEW[skey]) return;            // scenery seen face on keeps its sprite map (v202)
  try{
    MASKS3D[skey] = f3dBuildMask(L, img, spriteFacing(skey) === 'left' ? -1 : 1, F3D_ROLL[skey] || 0);
    // the hull's box is read off the map again (40_world.js)
    if(typeof SPR_BOX !== 'undefined') delete SPR_BOX[skey];
  }catch(err){ F3D.err = String(err && err.message || err); }
}
// Called by draw() before the ship loop. Draws the vortex and thrusters of
// every 3D ship (they lie under the hull), then all the 3D hulls at once,
// and returns the set of ships the loop must not draw a sprite hull for.
// v202: the field pass in two halves. f3dFieldPrep() picks the ships drawn
// from a model (key, level loaded) without drawing anything; f3dFlush()
// draws one batch of them - vortex and thrusters, the hulls in one render,
// then damage, marks and bars - at its place in the ship loop.
function f3dFieldPrep(list){
  const done = new Map();
  if(F3D.off || typeof document === 'undefined') return done;
  for(const e of list){
    const key = f3dKey(e); if(!key) continue;
    const L = f3dReadyLevel(key); if(!L) continue;
    if(!F3D_MASKED[e.img] && !f3dSmall(key)) f3dMask(e.img, key);
    e._f3fc = (typeof fc !== 'undefined') ? fc : 0;
    done.set(e, {e: e, L: L});
  }
  return done;
}
function f3dFlush(seg){
  const items = [];
  for(const s of seg){
    if(s.hulk){ const hi = f3dHulkItem(s.hulk); if(hi) items.push(hi); continue; }
    const e = s.e;
    try{ drawVortexOf(e); }catch(ev){ ctx.restore(); }
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    const v = f3dVis(e); e._f3v = v;
    if(!v) continue;
    try{
      ctx.save();
      if(v.g){ fsWarpClip(v.g); ctx.translate(v.g.dx, v.g.dy); }
      else ctx.globalAlpha = v.a;
      // v208: her flames are drawn in her 3D pass (f3dThDraw)
      ctx.restore();
    }catch(et){ ctx.restore(); }
    ctx.globalAlpha = 1;
    items.push({e: e, L: s.L, x: v.x, y: v.y, a: v.a, clip: v.clip});
  }
  if(items.length){
    try{ f3dRender(items); }catch(er){ F3D.err = String(er && er.message || er); }
  }
  for(const s of seg){
    if(s.hulk) continue;
    try{ f3dShipTop(s.e); }catch(et){ ctx.restore(); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; }
  }
}
// All at once (tests and older callers): the ships drawn from a model.
function f3dFieldPass(list){
  const m = f3dFieldPrep(list);
  const done = new Set(m.keys());
  if(m.size) f3dFlush(Array.from(m.values()));
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
  e._gl3 = 2;            // v204: the marks go onto the model (f3dDmgBind)
  try{ drawShipE(e, e.x|0, e.y|0, e.sc, e.flip, e.ang||0); }
  finally{ e._gl3 = false; }
}

// ── BREAKING UP IN 3D (v202) ─────────────────────────────────
// A ship drawn from her model breaks into the debris pieces her model
// carries (the POF's debris objects), not into cut-outs of her sprite:
// each piece starts where it sits in her hull, keeps her drift, takes the
// push of the blast and tumbles about an axis of its own. As with the
// sections of v183 nothing fades: a piece flies off the field or blows
// apart in a later explosion, leaving the usual small wreckage.
let F3D_HULKS = [];
function f3dM3(M){ return [M[0], M[1], M[2], M[4], M[5], M[6], M[8], M[9], M[10]]; }
// x' = A * x, A 3x3 column-major
function f3dMulV(A, v){ return [A[0]*v[0] + A[3]*v[1] + A[6]*v[2], A[1]*v[0] + A[4]*v[1] + A[7]*v[2], A[2]*v[0] + A[5]*v[1] + A[8]*v[2]]; }
function f3dMulA(A, B){
  const o = new Array(9);
  for(let c = 0; c < 3; c++) for(let r = 0; r < 3; r++)
    o[c*3+r] = A[r]*B[c*3] + A[3+r]*B[c*3+1] + A[6+r]*B[c*3+2];
  return o;
}
// rotation about unit axis u by a, 3x3 column-major
function f3dAxisRot(u, a){
  const c = Math.cos(a), s = Math.sin(a), t = 1 - c, x = u[0], y = u[1], z = u[2];
  return [t*x*x + c, t*x*y + s*z, t*x*z - s*y,
          t*x*y - s*z, t*y*y + c, t*y*z + s*x,
          t*x*z + s*y, t*y*z - s*x, t*z*z + c];
}
// She breaks into her debris. False when she has no model on the field or
// her model no pieces: the sprite sections take over (dmgBreakup).
function f3dBreakup(e){
  // drawn from her model: a key and a loaded model (not f3dOn - the game
  // may run steps between two pictures)
  if(e && e.player && !e.ang && F3D_PL.img === e.img) e = F3D_PL;   // the player (60_effects.js)
  if(!e || e._f3fc == null) return false;
  const key = f3dKey(e), L = key ? f3dReadyLevel(key) : null;
  const N = L && L.head && L.head.nodes;
  if(!N) return false;
  const M0 = f3dMat(e, e.x, e.y, L), A0 = f3dM3(M0);
  const img = IMGS[e.img], span = img ? img.width*e.sc : 100;
  // her place in the field's order (the footprint the ship loop sorts by):
  // her pieces stay in her layer (v204, Silvio: M11)
  const fp = img ? img.width*e.sc*img.height*e.sc : 0;
  const svx = (e.rvx != null ? e.rvx : (e._vx||0)), svy = (e.rvy != null ? e.rvy : (e._vy||0));
  let made = 0;
  for(let j = 1; j < N.length; j++){
    const n = N[j]; if(!n || n.k !== 'deb' || n.empty) continue;
    const c = f3dMulV(A0, n.pv);
    // v209: from her depth (a capital ship is sunk, f3dMat)
    const x = M0[12] + c[0], y = -(M0[13] + c[1]), z = M0[14] + c[2];
    const dx = x - e.x, dy = y - e.y, dl = Math.hypot(dx, dy) || 1;
    const rr = (n.r || 0.2)*span/2;
    const mass = Math.min(1, rr/80);
    const push = (0.12 + 0.26*Math.random())*(1 - 0.5*mass);
    let ax = [Math.random()-0.5, Math.random()-0.5, Math.random()-0.5];
    const al = Math.hypot(ax[0], ax[1], ax[2]) || 1; ax = [ax[0]/al, ax[1]/al, ax[2]/al];
    F3D_HULKS.push({L: L, j: j, pv: n.pv, A0: A0, x: x, y: y, z: z, r: rr, fp: fp,
      vx: svx + dx/dl*push, vy: svy + dy/dl*push + (Math.random()-0.5)*0.05,
      ax: ax, w: (0.002 + Math.random()*0.006)*(1 - 0.6*mass)*(Math.random()<0.5 ? -1 : 1), a: 0,
      heat: 1, fac: e.faction,
      // a small craft's pieces burn out sooner (v203)
      next: fc + Math.round(TICK_HZ*(f3dSmall(key) ? 0.8 + Math.random()*2.2 : 2 + Math.random()*4.5))});
    made++;
  }
  return made > 0;
}
function f3dTickHulks(){
  for(let i = F3D_HULKS.length - 1; i >= 0; i--){
    const P = F3D_HULKS[i];
    P.x += P.vx; P.y += P.vy; P.a += P.w;
    if(P.heat > 0) P.heat = Math.max(0, P.heat - 1/(TICK_HZ*9));
    if(P.x < WX0-P.r-60 || P.x > WX1+P.r+60 || P.y < WY0-HUD_H-P.r-60 || P.y > WY1+P.r+60){ F3D_HULKS.splice(i, 1); continue; }
    // what still burns in it smokes
    if(P.heat > 0.15 && fc % 6 === i % 6){
      const a = Math.random()*Math.PI*2, sp = 0.08 + Math.random()*0.2, hot = Math.random() < P.heat*0.6;
      PARTS.push({type: hot ? 'dfl' : 'dsmk', free: true, x: P.x + (Math.random()-0.5)*P.r, y: P.y + (Math.random()-0.5)*P.r,
                  vx: P.vx + Math.cos(a)*sp, vy: P.vy + Math.sin(a)*sp,
                  life: hot ? 20 : 110, ml: hot ? 20 : 110, r0: hot ? 2 : 2.5, r1: hot ? 7 : 9, al: 0.22});
    }
    // a later explosion takes it apart
    if(fc >= P.next){
      spawnFireball(P.x, P.y, P.r*0.9 + 8, 22);
      spawnDebris(P.x, P.y, 8 + Math.min(12, (P.r/6)|0), 255,220,170, 200,110,50, false);
      sndDeath(P.x, 0.35, P.y);
      F3D_HULKS.splice(i, 1);
    }
  }
}
// v204: the pieces as items of the ship loop's batches, each at the place of
// the ship she came from (70_ui.js): in front of what lay behind her, behind
// what lay in front.
function f3dHulkItem(P){
  if(!P.L || P.L.state !== 'ready') return null;
  // T(pos) * R(tumble) * A0 * T(-pv)
  const A = f3dMulA(f3dAxisRot(P.ax, P.a), P.A0);
  const q = f3dMulV(A, P.pv);
  const M = new Float32Array([A[0], A[1], A[2], 0, A[3], A[4], A[5], 0, A[6], A[7], A[8], 0,
                              P.x - q[0], -P.y - q[1], P.z - q[2], 1]);
  return {e: null, L: P.L, deb: P.j, M: M, a: 1, clip: null};
}
function f3dHulksOn(){ return F3D_HULKS.length > 0 && !F3D.off && f3dInit(); }
// all of them at once (tests, older callers)
function f3dDrawHulks(){
  if(!f3dHulksOn()) return;
  const items = [];
  for(const P of F3D_HULKS){ const it = f3dHulkItem(P); if(it) items.push(it); }
  if(items.length){ try{ f3dRender(items); }catch(er){ F3D.err = String(er && er.message || er); } }
}
// ── SHIELDS AS IN FREESPACE (v205) ───────────────────────────
// Silvio: the shield is not shown all the time. A hit lights up a piece of
// the ship's shield mesh (the POF's SHLD chunk, a coarse hull around her)
// round the place it struck, painted with the MediaVPs' animated shield
// texture (ShieldHit01a) in the colour of her side, fading in about half a
// second. Display only: one shield, no quadrants. A hull without a shield
// mesh shows no shield, as in FreeSpace. v206 (Silvio): the Lucifer's mesh
// comes from The Scroll of Atankharzim's capital02.pof (the MediaVPs' model
// has none); her hits look like those of every other Shivan.
// Data: models/shields.json.gz (mkshields.py), models/shieldhit.webp (the
// 13 frames in a 4x4 grid, grey; tinted here).
const F3D_SH_DUR = 0.55;            // seconds a hit is seen
const F3D_SH_FRAMES = 13;
// v208: the hit of each species as the MediaVPs 5.0.2 give it
// (mv_effects-sdf.tbm): ShieldHit01a Terran (the v205 sheet, 13 frames 4x4),
// ShieldHit02a Vasudan (45 frames, 7x7), ShieldHit03a Shivan (22, 5x5);
// grey, tinted in the colour of her side as before. A sheet that did not
// load falls back to the Terran one.
const F3D_SH_SP = {terran: {f: 'shieldhit.webp', n: 13, g: 4},
                   vasudan: {f: 'shieldhit02.webp', n: 45, g: 7},
                   shivan: {f: 'shieldhit03.webp', n: 22, g: 5}};
const F3D_SH_MAX = 4;               // hits seen at once on one ship
const F3D_SH = {state: null, data: null, tex: null, prog: null, loc: null, mesh: {}};
function f3dShLoad(){
  if(F3D_SH.state) return F3D_SH.state === 'ready';
  F3D_SH.state = 'loading';
  const gl = F3D.gl;
  try{
    const vs = 'attribute vec3 aP; attribute vec3 aN; uniform mat4 uM; uniform mat4 uVP;'
      + 'uniform vec3 uH; uniform vec3 uT; uniform vec3 uB; uniform vec3 uHN; uniform float uR;'
      + 'varying vec2 vU; varying float vF; varying float vZ; varying vec3 vNw; varying vec3 vWp;'
      + 'void main(){ vec3 d = aP - uH; vU = vec2(dot(d, uT), dot(d, uB))/(2.0*uR) + 0.5; vZ = dot(d, uHN)/uR;'
      + ' vF = dot(normalize(aN), uHN); vec4 w = uM*vec4(aP, 1.0); vWp = w.xyz; vNw = mat3(uM)*aN; gl_Position = uVP*w; }';
    const fs = 'precision mediump float; varying vec2 vU; varying float vF; varying float vZ; varying vec3 vNw; varying vec3 vWp;'
      + 'uniform sampler2D tS; uniform vec2 uFr; uniform vec3 uCol; uniform float uA; uniform float uMode; uniform vec3 uCam; uniform float uGrid;'
      + 'void main(){ vec3 c;'
      + ' if(uMode < 0.5){'
      + '  if(vU.x < 0.0 || vU.x > 1.0 || vU.y < 0.0 || vU.y > 1.0) discard;'
      + '  vec2 st = (uFr + clamp(vU, vec2(0.004), vec2(0.996)))/uGrid;'
      + '  float t = texture2D(tS, st).r*smoothstep(-0.15, 0.35, vF)*(1.0 - smoothstep(0.35, 0.9, abs(vZ)));'
      // the side's colour, going white where the texture is brightest
      + '  c = (uCol*t + vec3(t*t*t*0.55))*uA;'
      + ' } else { c = vec3(0.0); }'
      + ' gl_FragColor = vec4(c, max(c.r, max(c.g, c.b))); }';
    const sh = function(t, src){ const s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
      if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error('link');
    const loc = {};
    for(const a of ['aP', 'aN']) loc[a] = gl.getAttribLocation(pr, a);
    for(const u of ['uM', 'uVP', 'uH', 'uT', 'uB', 'uHN', 'uR', 'tS', 'uFr', 'uCol', 'uA', 'uMode', 'uCam', 'uGrid'])
      loc[u] = gl.getUniformLocation(pr, u);
    F3D_SH.prog = pr; F3D_SH.loc = loc; F3D_SH.gl = gl;
  }catch(er){ F3D_SH.state = 'failed'; F3D.err = String(er && er.message || er); return false; }
  const rev = (typeof M3D_REV !== 'undefined') ? M3D_REV : 0;
  F3D_SH.texs = {};
  const loadTex = function(sp){ return new Promise(function(res){
    const im = new Image();
    im.onload = function(){
      if(gl !== F3D.gl) return res();
      const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      F3D_SH.texs[sp] = tx; if(sp === 'terran') F3D_SH.tex = tx; res();
    };
    im.onerror = function(){ res(); };
    const ip = M3D_BASE + F3D_SH_SP[sp].f;
    const pb = (typeof window !== 'undefined' && window.FS3_MODELS) ? window.FS3_MODELS[ip] : null;
    if(pb){ delete window.FS3_MODELS[ip]; im.src = URL.createObjectURL(pb); }
    else im.src = ip + '?r=' + rev;
  }); };
  const pTex = Promise.all(Object.keys(F3D_SH_SP).map(loadTex));
  const pData = f3dFetchBin(M3D_BASE + 'shields.json.gz').then(function(buf){
    F3D_SH.data = JSON.parse(new TextDecoder().decode(new Uint8Array(buf)));
  }, function(){ F3D_SH.data = {}; });
  Promise.all([pTex, pData]).then(function(){ F3D_SH.state = F3D_SH.tex ? 'ready' : 'failed'; });
  return false;
}
// The shield mesh of one hull in the model's own space (as its level is
// drawn), with a normal at every corner. Null: she has none.
function f3dShMesh(key, L){
  let S = F3D_SH.mesh[key];
  if(S === null || (S && S.gl === F3D.gl)) return S;
  const gl = F3D.gl, hd = L.head;
  const raw = F3D_SH.data && F3D_SH.data[key];
  if(!raw){ F3D_SH.mesh[key] = null; return null; }
  const v = new Float32Array(raw.v.length), f = raw.f;
  for(let i = 0; i < raw.v.length; i += 3) for(let a = 0; a < 3; a++) v[i+a] = (raw.v[i+a] - hd.centre[a])/hd.ext;
  const n = new Float32Array(v.length);
  for(let i = 0; i < f.length; i += 3){
    const a = f[i]*3, b = f[i+1]*3, c = f[i+2]*3;
    const u = [v[b]-v[a], v[b+1]-v[a+1], v[b+2]-v[a+2]], w = [v[c]-v[a], v[c+1]-v[a+1], v[c+2]-v[a+2]];
    const x = f3dCross(u, w);
    for(const j of [a, b, c]){ n[j] += x[0]; n[j+1] += x[1]; n[j+2] += x[2]; }
  }
  // outward, whichever way the corners run
  let out = 0;
  for(let i = 0; i < v.length; i += 3) out += v[i]*n[i] + v[i+1]*n[i+1] + v[i+2]*n[i+2];
  if(out < 0) for(let i = 0; i < n.length; i++) n[i] = -n[i];
  const mk = function(target, arr){ const b = gl.createBuffer(); gl.bindBuffer(target, b);
    gl.bufferData(target, arr, gl.STATIC_DRAW); return b; };
  S = F3D_SH.mesh[key] = {gl: gl, v: v, f: f, n: f.length, flip: out < 0,
    pos: mk(gl.ARRAY_BUFFER, v), nrm: mk(gl.ARRAY_BUFFER, n),
    idx: mk(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(f))};
  return S;
}
// A hit on the shield, at (x, y) on the field (null: somewhere on it).
// v205: the player's hull is drawn from her model this frame
function f3dPlayerOn(){
  return F3D_PL._f3fc != null && typeof fc !== 'undefined' && fc - F3D_PL._f3fc <= 2
      && typeof player !== 'undefined' && F3D_PL.img === player.ship;
}
function f3dShieldHit(e, x, y){
  if(!e || F3D.off) return;
  const q = e._shq || (e._shq = []);
  if(q.length >= F3D_SH_MAX) q.shift();
  q.push({wx: x == null ? null : x - e.x, wy: x == null ? null : y - e.y, t: f3dNow()/1000, p: null});
}
// Where a hit lies on the mesh (v206): the part of the shield the viewer
// sees at the point it struck - a ray from the camera's side through that
// point, first crossing with the mesh. Where it misses (a hit just outside
// her outline) the line from her middle out towards the hit, leaning
// towards the viewer, to where it leaves the shield.
function f3dShRay(S, O, D, near){
  const v = S.v, f = S.f;
  let best = near ? Infinity : -1, bi = -1;
  for(let i = 0; i < f.length; i += 3){
    const a = f[i]*3, b = f[i+1]*3, c = f[i+2]*3;
    const e1 = [v[b]-v[a], v[b+1]-v[a+1], v[b+2]-v[a+2]], e2 = [v[c]-v[a], v[c+1]-v[a+1], v[c+2]-v[a+2]];
    const p = f3dCross(D, e2), det = f3dDot(e1, p);
    if(Math.abs(det) < 1e-12) continue;
    const sv = [O[0]-v[a], O[1]-v[a+1], O[2]-v[a+2]], u = f3dDot(sv, p)/det;
    if(u < 0 || u > 1) continue;
    const qv = f3dCross(sv, e1), w = f3dDot(D, qv)/det;
    if(w < 0 || u + w > 1) continue;
    const t = f3dDot(e2, qv)/det;
    if(t > 0 && (near ? t < best : t > best)){ best = t; bi = i; }
  }
  return bi < 0 ? null : {t: best, i: bi};
}
function f3dShPlace(h, S, M0){
  const s2 = M0[0]*M0[0] + M0[1]*M0[1] + M0[2]*M0[2];
  // world -> model: the transpose of the turn, over the scale
  const toM = function(w){ return [0, 4, 8].map(function(o){ return (M0[o]*w[0] + M0[o+1]*w[1] + M0[o+2]*w[2])/s2; }); };
  let P = null, D = null;
  if(h.wx != null){
    // v209: the ray comes from the real eye (f3dVP) through the point in
    // the plane where the hit was, both relative to her middle (M0)
    const E = f3dVP().eye, ox = M0[12], oy = M0[13], oz = M0[14];
    const O = toM([E[0] - ox, E[1] - oy, E[2] - oz]);
    const V = f3dNorm(toM([ox + h.wx - E[0], oy - h.wy - E[1], -E[2]]));
    const r = f3dShRay(S, O, V, true);
    if(r){ P = [O[0] + V[0]*r.t, O[1] + V[1]*r.t, O[2] + V[2]*r.t]; D = [-V[0], -V[1], -V[2]]; }
  }
  if(!P){
    let dx, dy;
    if(h.wx == null || (Math.abs(h.wx) + Math.abs(h.wy)) < 0.5){ const a = Math.random()*Math.PI*2; dx = Math.cos(a); dy = Math.sin(a); }
    else { const l = Math.hypot(h.wx, h.wy); dx = h.wx/l; dy = h.wy/l; }
    D = f3dNorm(toM([dx, -dy, 0.55]));
    const r = f3dShRay(S, [0, 0, 0], D, false);
    let t = r ? r.t : -1;
    if(t <= 0){ const v = S.v; for(let i = 0; i < v.length; i += 3) t = Math.max(t, v[i]*D[0] + v[i+1]*D[1] + v[i+2]*D[2]); }
    P = [D[0]*t, D[1]*t, D[2]*t];
  }
  const T = f3dNorm(Math.abs(D[1]) > 0.9 ? f3dCross(D, [1, 0, 0]) : f3dCross(D, [0, 1, 0]));
  h.p = P; h.n = D; h.tg = T; h.bt = f3dCross(D, T);
}
// The shield of one ship, right after her hull (f3dRender): her hull is in
// the depth buffer, so what of the shield lies behind her is hidden.
function f3dShDraw(it, M0, cam){
  const e = it.e;
  if(!e || it.deb != null || it.clip || !it.L.head) return;
  if(!(e._shq && e._shq.length)) return;
  if(!f3dShLoad()) return;
  const gl = F3D.gl, sl = F3D_SH.loc, now = f3dNow()/1000;
  for(const a of ['aP', 'aN', 'aT']) if(F3D.loc[a] >= 0) gl.disableVertexAttribArray(F3D.loc[a]);
  const key = F3D_ALIAS[e.img] || e.img;
  const S = f3dShMesh(key, it.L);
  if(!S){ e._shq.length = 0; return; }
  const s = Math.hypot(M0[0], M0[1], M0[2]) || 1;
  const fac = e.player ? (e.faction || 'terran') : e.faction;
  const hc = hullShieldCol(fac), col = [0, 2, 4].map(function(i){ return parseInt(hc.glow.substr(1 + i, 2), 16)/255; });
  gl.useProgram(F3D_SH.prog);
  gl.uniformMatrix4fv(sl.uM, false, M0); gl.uniformMatrix4fv(sl.uVP, false, cam.vp);
  gl.uniform3fv(sl.uCam, cam.eye); gl.uniform3fv(sl.uCol, col); gl.uniform1i(sl.tS, 0);
  // v208: her species' hit (F3D_SH_SP)
  let spk = (typeof raceOf === 'function') ? raceOf(fac || 'terran') : 'terran';
  if(!F3D_SH.texs || !F3D_SH.texs[spk]) spk = 'terran';
  const SP = F3D_SH_SP[spk];
  gl.uniform1f(sl.uGrid, SP.g);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, (F3D_SH.texs && F3D_SH.texs[spk]) || F3D_SH.tex);
  gl.bindBuffer(gl.ARRAY_BUFFER, S.pos); gl.enableVertexAttribArray(sl.aP); gl.vertexAttribPointer(sl.aP, 3, gl.FLOAT, false, 12, 0);
  gl.bindBuffer(gl.ARRAY_BUFFER, S.nrm); gl.enableVertexAttribArray(sl.aN); gl.vertexAttribPointer(sl.aN, 3, gl.FLOAT, false, 12, 0);
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, S.idx);
  gl.enable(gl.BLEND); gl.blendFuncSeparate(gl.ONE, gl.ONE, gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  gl.depthMask(false);
  gl.disable(gl.CULL_FACE);
  gl.uniform1f(sl.uMode, 0);
  const q = e._shq || [];
  const frac = e.player ? (typeof player !== 'undefined' && player.maxSh ? player.sh/player.maxSh : 1)
                        : (e.bShield > 0 ? 1 : (e.maxSh ? e.sh/e.maxSh : 1));
  // a hit is as wide on the screen as a fighter's flank, a little less on
  // a big hull
  const len = s*2, rpx = Math.max(16, Math.min(80, 0.36*len));
  for(let i = q.length - 1; i >= 0; i--){
    const h = q[i], a = (now - h.t)/F3D_SH_DUR;
    if(a >= 1 || a < 0){ q.splice(i, 1); continue; }
    if(!h.p) f3dShPlace(h, S, M0);
    const fr = Math.min(SP.n - 1, Math.floor(a*SP.n*1.15));
    gl.uniform2f(sl.uFr, fr % SP.g, Math.floor(fr/SP.g));
    gl.uniform3fv(sl.uH, h.p); gl.uniform3fv(sl.uHN, h.n); gl.uniform3fv(sl.uT, h.tg); gl.uniform3fv(sl.uB, h.bt);
    gl.uniform1f(sl.uR, rpx/s);
    const fade = a < 0.7 ? 1 : (1 - a)/0.3;
    gl.uniform1f(sl.uA, 1.6*fade*(0.55 + 0.45*Math.max(0, frac))*it.a);
    gl.drawElements(gl.TRIANGLES, S.n, gl.UNSIGNED_SHORT, 0);
  }
  gl.depthMask(true); gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); gl.disable(gl.BLEND);
  gl.disableVertexAttribArray(sl.aP); gl.disableVertexAttribArray(sl.aN);
  gl.useProgram(F3D.prog);
}
// ── ENGINE FLAMES AND WARP IN 3D (v208) ──────────────────────
// One small program for the effects of the MediaVPs (5.0.2) laid into the
// 3D pass: textured quads in world space, added to what is drawn (the
// flames), or laid over it with their own alpha (the warp). uClip cuts
// them like the hull of a ship sliding through her vortex.
const F3D_FX = {prog: null, loc: null, buf: null, ok: null};
function f3dFxProg(){
  if(F3D_FX.ok !== null && F3D_FX.gl === F3D.gl) return F3D_FX.ok;
  const gl = F3D.gl; F3D_FX.gl = gl; F3D_FX.ok = false;
  try{
    const vs = 'attribute vec3 aP; attribute vec3 aT; uniform mat4 uVP; uniform mat4 uM;'
      + 'varying vec3 vT; varying vec3 vW;'
      + 'void main(){ vec4 w = uM*vec4(aP, 1.0); vW = w.xyz; vT = aT; gl_Position = uVP*w; }';
    const fs = 'precision mediump float; varying vec3 vT; varying vec3 vW;'
      + 'uniform sampler2D tS; uniform vec3 uClip; uniform float uA; uniform vec4 uUV; uniform float uPre;'
      + 'void main(){ if(dot(uClip.xy, vW.xy) + uClip.z < 0.0) discard;'
      + ' vec4 c = texture2D(tS, uUV.xy + clamp(vT.xy, vec2(0.002), vec2(0.998))*uUV.zw); float a = vT.z*uA;'
      + ' if(uPre > 0.5) gl_FragColor = vec4(c.rgb*c.a*a, c.a*a);'
      + ' else { vec3 k = c.rgb*a; gl_FragColor = vec4(k, max(k.r, max(k.g, k.b))); } }';
    const sh = function(t, src){ const s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
      if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error('fx link');
    const loc = {};
    for(const a of ['aP', 'aT']) loc[a] = gl.getAttribLocation(pr, a);
    for(const u of ['uVP', 'uM', 'tS', 'uClip', 'uA', 'uUV', 'uPre']) loc[u] = gl.getUniformLocation(pr, u);
    F3D_FX.prog = pr; F3D_FX.loc = loc; F3D_FX.buf = gl.createBuffer(); F3D_FX.ok = true;
  }catch(er){ F3D.err = String(er && er.message || er); }
  return F3D_FX.ok;
}
const F3D_ID = new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
// A picture of the effects (models/fx/ or images/) as a texture of this
// context, null until it has loaded.
const F3D_FXTEX = {};
function f3dFxTex(path, img){
  let T = F3D_FXTEX[path];
  if(T && T.gl === F3D.gl) return T.t;
  if(T && T.loading) return null;
  const gl = F3D.gl;
  const up = function(im){
    const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    F3D_FXTEX[path] = {gl: gl, t: t};
  };
  // a picture already in the page (the warp sheets, images/)
  if(img){ if(!(img.complete && img.naturalWidth > 0)) return null; up(img); return F3D_FXTEX[path].t; }
  F3D_FXTEX[path] = {loading: true};
  const im = new Image();
  im.onload = function(){ if(gl === F3D.gl) up(im); else delete F3D_FXTEX[path]; };
  im.onerror = function(){ F3D_FXTEX[path] = {gl: gl, t: null}; };
  const pb = (typeof window !== 'undefined' && window.FS3_MODELS) ? window.FS3_MODELS[path] : null;
  if(pb){ delete window.FS3_MODELS[path]; im.src = URL.createObjectURL(pb); }
  else im.src = path + '?r=' + ((typeof M3D_REV !== 'undefined') ? M3D_REV : 0);
  return null;
}
// Draws quads (6 corners each: x, y, z, u, v, alpha) with the fx program.
function f3dFxDraw(arr, n, tex, M, cam, clip, A, pre, uv){
  const gl = F3D.gl, l = F3D_FX.loc;
  gl.useProgram(F3D_FX.prog);
  gl.uniformMatrix4fv(l.uVP, false, cam.vp); gl.uniformMatrix4fv(l.uM, false, M || F3D_ID);
  gl.uniform1i(l.tS, 0); gl.uniform1f(l.uA, A); gl.uniform1f(l.uPre, pre ? 1 : 0);
  const u = uv || [0, 0, 1, 1]; gl.uniform4f(l.uUV, u[0], u[1], u[2], u[3]);
  if(clip) gl.uniform3f(l.uClip, clip.sg*clip.fx, -clip.sg*clip.fy, -clip.sg*(clip.px*clip.fx + clip.py*clip.fy));
  else gl.uniform3f(l.uClip, 0, 0, 1);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.bindBuffer(gl.ARRAY_BUFFER, F3D_FX.buf);
  gl.bufferData(gl.ARRAY_BUFFER, arr.subarray(0, n*6), gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(l.aP); gl.vertexAttribPointer(l.aP, 3, gl.FLOAT, false, 24, 0);
  gl.enableVertexAttribArray(l.aT); gl.vertexAttribPointer(l.aT, 3, gl.FLOAT, false, 24, 12);
  gl.drawArrays(gl.TRIANGLES, 0, n);
  gl.disableVertexAttribArray(l.aP); gl.disableVertexAttribArray(l.aT);
}
// One quad into arr at corner k: centre c, half axes a and b (world), the
// atlas rect r (u0, v0, du, dv) and its alpha.
function f3dQuad(arr, k, c, a, b, r, al){
  const P = [[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]];
  for(let i = 0; i < 6; i++){
    const s = P[i][0], t = P[i][1], o = (k+i)*6;
    arr[o] = c[0] + a[0]*s + b[0]*t; arr[o+1] = c[1] + a[1]*s + b[1]*t; arr[o+2] = c[2] + a[2]*s + b[2]*t;
    arr[o+3] = r[0] + r[2]*(s+1)/2; arr[o+4] = r[1] + r[3]*(t+1)/2; arr[o+5] = al;
  }
  return k + 6;
}

// Engine flames as in FreeSpace: at every glow point of the POF (FUEL:
// position, direction, radius) the glow (thrusterglow0N), the flame
// stretched out behind along the direction (thruster02-0N) and a flare at
// the nozzle (thruster03-0N) - N by species as the MediaVPs' species table
// gives them (mv_effects-sdf.tbm): 1 Terran, 2 Vasudan, 3 Shivan. Drawn in
// her 3D pass, so they roll, turn and bank with her and her hull hides
// what is behind it. They replace the old flames (drawThrusters), which
// stay for the ships drawn as sprites (&f3d=0).
// Data: models/fx/thrusters.json.gz (mkthrusters.py), models/fx/thrusters.webp
// (3 columns by species; rows: glow, flare, flame).
const F3D_TH = {state: null, data: null};
const F3D_TH_SP = {terran: 0, vasudan: 1, shivan: 2};
const F3D_TH_GLOW = 2.3, F3D_TH_FLARE = 1.5;       // half sizes, in thruster radii
const F3D_TH_LEN = [4.0, 10.0], F3D_TH_WID = 1.0;  // flame: length idle..full, half width
let F3D_TH_ARR = new Float32Array(6*6*3*16);
function f3dThLoad(){
  if(F3D_TH.state) return F3D_TH.state === 'ready';
  F3D_TH.state = 'loading';
  f3dFetchBin(M3D_BASE + 'fx/thrusters.json.gz').then(function(buf){
    F3D_TH.data = JSON.parse(new TextDecoder().decode(new Uint8Array(buf))); F3D_TH.state = 'ready';
  }, function(){ F3D_TH.data = {}; F3D_TH.state = 'failed'; });
  return false;
}
// Drawn from her model this frame, flames and all (drawThrusters leaves
// her alone then).
function f3dDrawsThr(key){
  if(F3D.off || typeof document === 'undefined' || !F3D.ok) return false;
  const k = f3dKey({img: key}); if(!k) return false;
  return !!f3dReadyLevel(k);
}
// How hard her engines run, 0..1 and a little over for the player's burn.
function f3dThMag(e){
  if(e.player) return (typeof playerThrust === 'function') ? Math.min(1.2, playerThrust()) : 0.8;
  let m;
  if(e.small || e.type === 'fighter' || e.type === 'bomber') m = 0.35 + 0.65*Math.min(1, Math.abs(e.cs || 0)/(e.spd || 2));
  else m = 0.45 + Math.min(0.55, Math.hypot(e._fvx || 0, e._fvy || 0)*1.5);
  if(e.warp > 0) m *= 0.6;
  // engines shot out: a sputter (v180's damaged flames)
  if(typeof hasSubsystems === 'function' && hasSubsystems(e) && typeof subOK === 'function' && !subOK(e, 'engines'))
    m *= (Math.random() < 0.3) ? 0.6 : 0.08;
  return m;
}
function f3dThDraw(it, M0, cam){
  const e = it.e;
  if(!e || it.deb != null || !it.L.head) return;
  if(!f3dThLoad() || !F3D_TH.data) return;
  const key = F3D_ALIAS[e.img] || e.img, G = F3D_TH.data[key];
  if(!G || !G.length) return;
  const tex = f3dFxTex(M3D_BASE + 'fx/thrusters.webp'); if(!tex) return;
  if(!f3dFxProg()) return;
  const hd = it.L.head, ext = hd.ext, cn = hd.centre;
  const sp = F3D_TH_SP[(typeof raceOf === 'function') ? raceOf(e.faction || 'terran') : 'terran'] || 0;
  const s = Math.hypot(M0[0], M0[1], M0[2]);          // world units per model unit (normalised)
  const mag = f3dThMag(e), al = it.a*(0.85 + 0.15*Math.random());
  const need = G.length*18*6;
  if(F3D_TH_ARR.length < need) F3D_TH_ARR = new Float32Array(need);
  const A = F3D_TH_ARR, cu = sp/3;
  let k = 0;
  for(const g of G){
    const p = [(g[0]-cn[0])/ext, (g[1]-cn[1])/ext, (g[2]-cn[2])/ext];
    const c = [M0[0]*p[0] + M0[4]*p[1] + M0[8]*p[2] + M0[12], M0[1]*p[0] + M0[5]*p[1] + M0[9]*p[2] + M0[13],
               M0[2]*p[0] + M0[6]*p[1] + M0[10]*p[2] + M0[14]];
    const n = f3dNorm([M0[0]*g[3] + M0[4]*g[4] + M0[8]*g[5], M0[1]*g[3] + M0[5]*g[4] + M0[9]*g[5], M0[2]*g[3] + M0[6]*g[4] + M0[10]*g[5]]);
    const r = g[6]/ext*s;
    if(!(r > 0.05)) continue;
    // the glow and the flare face the camera; seen from her stern they
    // are brighter, from the side as FS shows them, a little less
    const face = 0.75 + 0.25*Math.abs(n[2]);
    const hg = r*F3D_TH_GLOW*(0.85 + 0.25*mag), hf = r*F3D_TH_FLARE*(0.7 + 0.4*mag);
    k = f3dQuad(A, k, c, [hg, 0, 0], [0, hg, 0], [cu, 0, 1/3, 256/576], al*face*Math.min(1, 0.55 + 0.5*mag));
    k = f3dQuad(A, k, [c[0] + n[0]*r*0.3, c[1] + n[1]*r*0.3, c[2] + n[2]*r*0.3], [hf, 0, 0], [0, hf, 0], [cu, 256/576, 1/3, 256/576], al*face*0.8);
    // the flame, from the nozzle out along her direction, turned about its
    // own axis to face the camera (a beam, as FS draws it)
    const ax = Math.hypot(n[0], n[1]);
    if(ax > 0.08){
      const len = r*(F3D_TH_LEN[0] + (F3D_TH_LEN[1] - F3D_TH_LEN[0])*Math.min(1.2, mag))*ax;
      const d = [n[0]/ax, n[1]/ax, 0], w = [-d[1]*r*F3D_TH_WID, d[0]*r*F3D_TH_WID, 0];
      const hl = len/2, cc = [c[0] + d[0]*hl, c[1] + d[1]*hl, c[2]];
      // the texture's hot end is its left edge: u runs out from the nozzle
      k = f3dQuad(A, k, cc, [d[0]*hl, d[1]*hl, 0], w, [cu, 512/576, 1/3, 64/576], al*Math.min(1, 0.5 + 0.6*mag));
    }
  }
  if(!k) return;
  const gl = F3D.gl;
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); gl.depthMask(false); gl.disable(gl.CULL_FACE);
  try{ f3dFxDraw(A, k, tex, null, cam, it.clip, 1, false); }
  finally{
    gl.depthMask(true); gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); gl.disable(gl.BLEND);
    gl.useProgram(F3D.prog);
  }
}

// The warp as in the MediaVPs 5.0.2, style "cinematic" (mv_effects-fbl.tbm):
// the model Warp.pof (its finest disc, warp01a) painted with the animation
// WarpMap01 (75 frames, 25 a second), the glow WarpGlow01 over it; the
// Knossos' own WarpMap02 / WarpGlow02. The disc stands across the flight
// path as in FS, leaned towards the camera (WARP_OVAL), so it shows as the
// oval of before - now from the model, with depth. Drawn where the old
// vortex was drawn (drawWarpFrame), in its own small pass.
// Data: models/fx/warp.json.gz (mkwarp.py); the frame sheets are the
// page's images/warp_img.webp etc., as for the sprite fallback.
const F3D_WP = {state: null, n: 0, arr: null};
function f3dWarpLoad(){
  if(F3D_WP.state) return F3D_WP.state === 'ready';
  F3D_WP.state = 'loading';
  f3dFetchBin(M3D_BASE + 'fx/warp.json.gz').then(function(buf){
    const w = JSON.parse(new TextDecoder().decode(new Uint8Array(buf)));
    const n = w.i.length, a = new Float32Array(n*6);
    for(let j = 0; j < n; j++){
      const v = w.i[j];
      a[j*6] = w.p[v*3]; a[j*6+1] = w.p[v*3+1]; a[j*6+2] = w.p[v*3+2];
      a[j*6+3] = w.t[v*2]; a[j*6+4] = w.t[v*2+1]; a[j*6+5] = 1;
    }
    F3D_WP.arr = a; F3D_WP.n = n; F3D_WP.state = 'ready';
  }, function(){ F3D_WP.state = 'failed'; });
  return false;
}
const F3D_WP_GLOW = new Float32Array(36);
// px, py: where the vortex stands; fx, fy: the way through it; WS: its
// size across; wS: how far open (0..1); alpha; seed: its own start frame.
// False: not drawn (no 3D) - the caller draws the old picture.
function f3dWarp(px, py, fx, fy, WS, wS, alpha, seed, knossos){
  if(F3D.off || typeof document === 'undefined' || !F3D.ok || !F3D.gl) return false;
  if(!f3dWarpLoad() || !f3dFxProg()) return false;
  const sheetImg = (knossos && imgReady(KNOSSOS_WARP_IMG)) ? KNOSSOS_WARP_IMG : WARP_IMG;
  const glowImg = (knossos && imgReady(KNOSSOS_GLOW_IMG)) ? KNOSSOS_GLOW_IMG : WARP_GLOW_IMG;
  const ts = f3dFxTex(knossos ? 'warp_knossos' : 'warp', sheetImg);
  if(!ts) return false;
  const tg = imgReady(glowImg) ? f3dFxTex(knossos ? 'glow_knossos' : 'glow', glowImg) : null;
  const gl = F3D.gl, can = F3D.can;
  const pw = (typeof CVS !== 'undefined' && CVS.width) || Math.round(W), ph = (typeof CVS !== 'undefined' && CVS.height) || Math.round(H);
  if(can.width !== pw || can.height !== ph){ can.width = pw; can.height = ph; }
  gl.viewport(0, 0, pw, ph);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.disable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE); gl.enable(gl.BLEND);
  const cam = f3dVP();
  // the disc: its axis along the way through, leaned towards the camera
  const c = WARP_OVAL, s = Math.sqrt(1 - c*c);
  const nl = Math.hypot(fx, fy) || 1;
  const n = [fx/nl*s, -fy/nl*s, c], u = f3dNorm([n[1], -n[0], 0]), v = f3dCross(n, u);
  const th = fc*WARP_SPIN/TICK_HZ + (seed || 0), ct = Math.cos(th), st = Math.sin(th);
  const X = [u[0]*ct + v[0]*st, u[1]*ct + v[1]*st, u[2]*ct + v[2]*st];
  const Y = [-u[0]*st + v[0]*ct, -u[1]*st + v[1]*ct, -u[2]*st + v[2]*ct];
  const R = WS/2*wS, C = [px, -py, 0];
  const M = new Float32Array([X[0]*R, X[1]*R, X[2]*R, 0, Y[0]*R, Y[1]*R, Y[2]*R, 0, n[0]*R, n[1]*R, n[2]*R, 0, C[0], C[1], C[2], 1]);
  const wF = Math.floor(fc*WARP_FPS/TICK_HZ + (seed || 0)) % WARP_FRAMES;
  const cs = 1/WARP_COLS;
  // the glow first, added; then the disc with its own alpha
  if(tg){
    const G = WS*wS*WARP_GLOW_SIZE*0.5;
    f3dQuad(F3D_WP_GLOW, 0, C, [u[0]*G, u[1]*G, 0], [-u[1]*G*0.6, u[0]*G*0.6, 0], [0, 0, 1, 1], 1);
    gl.blendFunc(gl.ONE, gl.ONE);
    f3dFxDraw(F3D_WP_GLOW, 6, tg, null, cam, null, alpha, false);
  }
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  f3dFxDraw(F3D_WP.arr, F3D_WP.n, ts, M, cam, null, alpha, true, [(wF % WARP_COLS)*cs, Math.floor(wF/WARP_COLS)*cs, cs, cs]);
  gl.disable(gl.BLEND); gl.enable(gl.DEPTH_TEST); gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
  gl.useProgram(F3D.prog);
  ctx.save();
  if(typeof camScreen === 'function') camScreen();
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.drawImage(can, 0, 0, W, H);
  ctx.restore();
  return true;
}
