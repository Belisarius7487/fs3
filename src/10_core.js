const SPR_DATA={};

const NEB_DATA={
  'Aldebaran':'@@FS3_ASSET:nebulae/Aldebaran.jpg@@',
  'AlphaCentauri':'@@FS3_ASSET:nebulae/AlphaCentauri.jpg@@',
  'BeAquilae':'@@FS3_ASSET:nebulae/BeAquilae.jpg@@',
  'DSerpentis':'@@FS3_ASSET:nebulae/DSerpentis.jpg@@',
  'Deneb':'@@FS3_ASSET:nebulae/Deneb.jpg@@',
  'R128':'@@FS3_ASSET:nebulae/R128.jpg@@',
  'Sirius':'@@FS3_ASSET:nebulae/Sirius.jpg@@',
  'Vasuda':'@@FS3_ASSET:nebulae/Vasuda.jpg@@',
  'Vega':'@@FS3_ASSET:nebulae/Vega.jpg@@',
};

// LORE: Die SD Hades stammt aus Silent Threat: Reborn und ist kanonisch
// KEIN NTF-Schiff. Sie steht in ntf_super, weil die NTF sonst kein Schiff
// haette, das als Boss taugt - eine bewusste Freiheit des Autors, keine
// Verwechslung. Bitte nicht umsortieren.
// Der Kommentar steht ausserhalb von ROLES, weil referenced_keys() im
// Packer jeden Ausdruck in Anfuehrungszeichen innerhalb des Blocks als
// Schiffsschluessel liest.
const ROLES={"player_fighters": ["fiares", "fierinyes", "fiherc", "fihercmk2", "fimyrmidon", "fipegasus"], "player_bombers": ["boartemis", "boartemisdh", "boboanerges", "bomedusa", "boursa"], "ntf_fighters": ["fiherc", "fihercmk2", "fimyrmidon", "filoki"], "ntf_bombers": ["boartemis", "boboanerges", "bomedusa", "boursa", "bozeus"], "ntf_cruisers": ["ntfcraeolus", "ntfcrleviathan", "ntfcrfenris"], "ntf_corvette": ["ntfcodeimos"], "ntf_destroyers": ["ntfdeorion", "ntfdehecate"], "ntf_super": ["sdhades"], "shivan_fighters": ["fiaeshma", "fiastaroth", "fibasilisk", "fidragon", "fimanticore", "fimara"], "shivan_bombers": ["bonahema", "bonephilim", "boseraphim", "botaurvi"], "shivan_cruisers": ["crcain", "crlilith", "crrakshasa"], "shivan_corvette": ["comoloch"], "shivan_destroyers": ["dedemon", "deravana"], "shivan_super": ["sdlucifer", "sdsathanas"], "ally_ter_fighters": ["fiares", "fierinyes", "fiherc", "fihercmk2", "fimyrmidon", "fipegasus"], "ally_ter_bombers": ["boartemis", "boartemisdh", "boboanerges", "bomedusa", "boursa"], "ally_ter_cruisers": ["craeolus", "crleviathan", "crfenris"], "ally_ter_corvette": ["codeimos"], "ally_ter_destroyers": ["deorionright"], "ally_vas_fighters": ["fihorus", "fiptah", "fiserapis", "fiseth", "fitauret", "fitoth"], "ally_vas_bombers": ["bobakha", "boosiris", "bosekhmet"], "ally_vas_cruisers": ["craten", "crmentu"], "ally_vas_corvette": ["cosobek"], "ally_vas_destroyers": ["detyphon", "dehatshepsut"], "bonus_ally": ["sdcolossus"], "bonus_enemy": ["coiceni"]};

const NEB_NAMES=["Aldebaran", "AlphaCentauri", "BeAquilae", "DSerpentis", "Deneb", "R128", "Sirius", "Vasuda", "Vega"];


const CVS=document.getElementById('c');
const ctx=CVS.getContext('2d');
const W=800,H=500,HUD_H=54;

// The canvas holds a fixed 800x500 coordinate space, but CSS stretches it
// across the whole viewport. Without a matching backing store every pixel
// gets upscaled, which is why text used to look smeared. We size the
// backing store to real device pixels and scale the context instead, so
// all game code keeps working in the original 800x500 units.
// ECO: vier einzeln schaltbare Posten gegen die Ueberhitzung des
// Testgeraets. Bewusst KEIN Sammelschalter - ein Sammelschalter sagt
// hinterher nur, dass es besser wurde, nicht welcher Posten es war.
//   res    Zeichenflaeche. Auf einem 1280x800-Tablet mit
//          Geraetepixelverhaeltnis 2 ergibt 3 eine Flaeche von 2400x1500,
//          also 3,6 Millionen Bildpunkte je Bild. 1.5 sind 0,9 Millionen.
//   blur   shadowBlur im Strahlenzeichner, je Strahl je Bild.
//   rim    drawRimLight, 640er Puffer mit drei Kompositdurchgaengen je
//          Grosskampfschiff je Bild.
//   glint  gebackene Glanzkarten und Schildhaeute. Wachsen mit jedem neuen
//          Rumpftyp, den man zu Gesicht bekommt - passt zum Muster
//          "erst in spaeteren Wellen".
// Der Stand wird gemerkt, damit nach einem Schwarzwerden nicht alles neu
// gestellt werden muss. Uebungsmodus und Anzeigen bewusst nicht.
const ECO_RES_STEPS = [3, 2, 1.5];
// Voreinstellung sparsam. Auf einem 1280x800-Tablet mit
// Geraetepixelverhaeltnis 2 kostet res 3 eine Flaeche von 3,6 Millionen
// Bildpunkten je Bild und macht das Geraet nach laengeren Sitzungen heiss;
// bei 1.5 sind es 0,9 Millionen. true heisst hier AUS.
// Wer schon einmal gespielt hat, behaelt seine eigene Wahl - der
// gespeicherte Stand ueberschreibt diese Zeile weiter unten.
let ECO = {res:1.5, blur:true, rim:true, glint:true, scheme:'fire'};
try{
  const _es = localStorage.getItem('fs3_eco');
  if(_es){
    const _eo = JSON.parse(_es);
    if(_eo && typeof _eo === 'object'){
      if(ECO_RES_STEPS.indexOf(_eo.res) >= 0) ECO.res = _eo.res;
      ECO.blur = !!_eo.blur; ECO.rim = !!_eo.rim; ECO.glint = !!_eo.glint;
      if(_eo.scheme==='fire' || _eo.scheme==='void') ECO.scheme = _eo.scheme;
    }
  }
}catch(ex){}
function ecoSave(){
  try{ localStorage.setItem('fs3_eco', JSON.stringify(ECO)); }catch(ex){}
}

// HLP THEME TOKENS
// The two colour schemes of the HLP forum theme, copied from the theme's own
// CSS: index.css :root for Fire, void.css html.hlp-void for Void. The names
// are the roles the forum gives them, not the places the game draws, so a
// colour is looked up here instead of being typed at a draw call.
const THEMES = {
  fire: {
    back:'rgb(19,19,19)',         // body_bg
    panelBack:'rgb(37,18,18)',    // window_bg_2
    panelFront:'rgb(43,22,23)',   // window_bg_1
    raised:'rgb(52,26,26)',       // main_bg
    barTop:'rgb(72,36,36)',       // between main_bg and top_section
    edgeLight:'rgb(75,35,35)',    // main_border_cool_light
    edgeDark:'rgb(12,5,5)',       // main_border_cool_dark
    glow:'160,58,35',             // glow-rgb
    text:'rgb(185,170,153)',      // body_text
    textBright:'rgb(225,205,182)',// white
    textDim:'rgb(122,101,88)',
    accent:'rgb(156,214,255)',    // link
    // The colour of the board links on the forum index, not link_hover:
    // that one is pale and turns to ochre on a dark surface.
    // PROVISIONAL - measured off a screenshot, to be replaced with the
    // exact value from the theme's index.css.
    accentWarm:'rgb(208,128,66)'
  },
  void: {
    back:'rgb(14,10,24)',
    panelBack:'rgb(22,10,44)',
    panelFront:'rgb(28,13,54)',
    raised:'rgb(32,14,62)',
    barTop:'rgb(46,20,86)',
    edgeLight:'rgb(72,28,112)',
    edgeDark:'rgb(8,3,18)',
    glow:'155,48,225',
    text:'rgb(185,170,220)',
    textBright:'rgb(225,205,255)',
    textDim:'rgb(120,104,150)',
    accent:'rgb(180,145,255)',
    accentWarm:'rgb(195,95,255)'
  }
};
function TH(role){ return (THEMES[ECO.scheme] || THEMES.fire)[role]; }
// Type follows the forum as well: Tahoma for labels and headings, Segoe UI
// for values and running text. Both are system faces, so nothing has to
// finish loading before the first frame can be drawn.
function thLabel(px){ return 'bold '+px+'px Tahoma, "Segoe UI", sans-serif'; }
function thValue(px, bold){ return (bold?'bold ':'')+px+'px "Segoe UI", Tahoma, sans-serif'; }
// The resting edge. Once a bevel in the forum's manner, now the kit's
// outline: chamfered, one dark line all round, one bright line on top.
// Kept under its old name because the bar still calls it for the gauges,
// and it disappears when the bar is rebuilt.
function thBevel(x, y, w, h){
  ctx.lineWidth = 1;
  ctx.strokeStyle = TH('edgeDark');
  thChamferPath(x+0.5, y+0.5, w-1, h-1, 4);
  ctx.stroke();
  ctx.strokeStyle = TH('edgeLight');
  ctx.beginPath();
  ctx.moveTo(x+4.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);
  ctx.stroke();
  thCutGlint(x, y, w, h, 4);
}
// What the forum emphasises with: a 1 px ring plus two blurred ones at
// falling opacity. Canvas has no box-shadow, so the blur comes from
// shadowBlur on a stroke. k scales the whole ring down for a weaker state.
function thGlow(x, y, w, h, k){
  const g = TH('glow'), s = (k===undefined) ? 1 : k;
  ctx.save();
  ctx.lineWidth = 1;
  ctx.shadowColor = 'rgba('+g+','+(0.40*s)+')'; ctx.shadowBlur = 6;
  ctx.strokeStyle = 'rgba('+g+','+(0.65*s)+')';
  ctx.strokeRect(x+0.5, y+0.5, w-1, h-1);
  ctx.shadowColor = 'rgba('+g+','+(0.20*s)+')'; ctx.shadowBlur = 14;
  ctx.strokeRect(x+0.5, y+0.5, w-1, h-1);
  ctx.restore();
}
// Every surface in the theme carries a vertical gradient, lighter at the top.
function thPanel(x, y, w, h, top, bottom){
  const gr = ctx.createLinearGradient(0, y, 0, y+h);
  gr.addColorStop(0, top); gr.addColorStop(1, bottom);
  ctx.fillStyle = gr; ctx.fillRect(x, y, w, h);
}
// A hairline divider, bevelled like everything else.
function thDivider(x, y0, y1){
  ctx.lineWidth = 1;
  ctx.strokeStyle = TH('edgeDark');
  ctx.beginPath(); ctx.moveTo(x+0.5, y0); ctx.lineTo(x+0.5, y1); ctx.stroke();
  ctx.strokeStyle = TH('edgeLight');
  ctx.beginPath(); ctx.moveTo(x+1.5, y0); ctx.lineTo(x+1.5, y1); ctx.stroke();
}
// One button, drawn the theme's way: quiet at rest, ringed when it wants
// attention. The caller owns whatever goes inside it.
// There is one look now. These four are what is left of the switch that
// used to choose between two: callers still pass a trailing CLASSIC
// argument, which is ignored here and disappears from each screen as that
// screen is rebuilt.
function UI(role){ return TH(role); }
function uiHLP(){ return true; }
function uiLabel(px){ return thLabel(px); }
function uiValue(px, bold){ return thValue(px, bold); }
// A cell or a row. state: 'on' for the active one, 'ready' for available,
// 'off' for locked or unaffordable.
function uiCell(x, y, w, h, o){
  o = o || {};
  thPlate(x, y, w, h,
          o.state==='on'  ? TH('raised') :
          o.state==='off' ? TH('back')   : TH('panelFront'));
  // Emphasis belongs to one thing at a time: the ring and the angles are
  // the active state only. What is merely available is the normal case and
  // gets nothing.
  if(o.state==='on'){
    thGlowPath(x, y, w, h, 6, 1);
    thBrackets(x, y, w, h, TH('accentWarm'));
  }
}
// A panel over the playfield. One frame for all of them now, so the call
// menu, the settings panel and the pause panel are the same object as the
// hangar. Their contents have not moved; only what they are drawn on has.
function uiDialog(x, y, w, h){
  thFrame(x, y, w, h, 0);
}
function thButton(x, y, w, h, state){
  thPlate(x, y, w, h, TH('raised'), 4);
  if(state==='on')           thGlowPath(x, y, w, h, 4, 1);
  else if(state==='ready')   thGlowPath(x, y, w, h, 4, 0.5);
}