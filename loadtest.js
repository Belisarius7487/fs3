// Minimaler Browserersatz. Zweck ist NICHT, das Spiel laufen zu lassen,
// sondern jede Anweisung auf oberster Ebene einmal auszufuehren - genau
// dort sitzen Reihenfolgefehler, die node --check nicht sieht.
const noop = () => {};
const grad = {addColorStop:noop};
const ctx = new Proxy({}, {get(t,k){
  if(k==='canvas') return el();
  if(k==='measureText') return ()=>({width:10});
  if(k==='createLinearGradient'||k==='createRadialGradient'||k==='createPattern') return ()=>grad;
  if(k==='getImageData') return (x,y,w,h)=>({width:w||1,height:h||1,data:new Uint8ClampedArray(4*(w||1)*(h||1))});
  if(k==='createImageData') return (w,h)=>({width:w||1,height:h||1,data:new Uint8ClampedArray(4*(w||1)*(h||1))});
  return noop;
}, set:()=>true});
function el(){
  return new Proxy({}, {get(t,k){
    if(k==='getContext') return ()=>ctx;
    if(k==='style') return {};
    if(k==='width'||k==='height') return 800;
    if(k==='classList') return {add:noop,remove:noop,toggle:noop};
    if(k==='getBoundingClientRect') return ()=>({left:0,top:0,width:800,height:500});
    if(k==='appendChild'||k==='addEventListener'||k==='removeEventListener'
       ||k==='setAttribute'||k==='focus'||k==='requestFullscreen') return noop;
    return undefined;
  }, set:()=>true});
}
global.document = {getElementById:el, createElement:el, querySelector:el,
  addEventListener:noop, body:el(), documentElement:el(), fullscreenElement:null,
  exitFullscreen:noop, hidden:false};
global.window = global;
global.navigator = {userAgent:'node', maxTouchPoints:0};
global.location = {search:'', href:'http://x/'};
const store = {};
global.localStorage = {getItem:k=>(k in store?store[k]:null), setItem:(k,v)=>{store[k]=String(v)}, removeItem:k=>{delete store[k]}};
global.Image = function(){ return new Proxy({}, {get:(t,k)=> k==='width'||k==='height'?64:noop, set:()=>true}); };
global.Audio = function(){ return {play:noop, pause:noop}; };
global.requestAnimationFrame = noop;
global.addEventListener = noop;
global.performance = {now:()=>0};

try {
  require('./v82.js');
  console.log('LADEN OK - alle Anweisungen auf oberster Ebene ausgefuehrt');
} catch(e) {
  console.log('FEHLER BEIM LADEN:', e.constructor.name + ':', e.message);
  const line = (e.stack||'').split('\n').find(l=>l.includes('v82.js'));
  if(line) console.log('  ', line.trim());
  process.exit(1);
}
