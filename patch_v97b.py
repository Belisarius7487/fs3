#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v97 Teil B: Sperrgeschuetze als Strahlenziel, Todesfolge grosser Schiffe."""
import io, os, sys
F="hlp_shooter_v97_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Sperrgeschuetze nehmen Antijaegerstrahlenschaden ───────────────
# isSmallShip() kannte nur Jaeger und Bomber, also war ein Geschuetzturm
# fuer keinen Strahl ein Ziel: fuer den schweren zu klein, fuer den
# leichten kein kleines Schiff. Es ist konsequent, dass ein Strahl, der
# auf Jaeger ausgelegt ist, auch einen Turm trifft.
sub("small-sentry",
"""function isSmallShip(o){ return o.type==='fighter' || o.type==='bomber'; }""",
"""function isSmallShip(o){
  return o.type==='fighter' || o.type==='bomber' || o.type==='sentry';
}""")

# ── Todesfolge grosser Schiffe ─────────────────────────────────────
# Ein Zerstoerer oder eine Station verschwand in einer Explosion. Vorher
# sollten Sekundaerexplosionen ueber den Rumpf laufen: erst reisst es
# auf, dann bricht es.
sub("death-const",
"""const DISABLE_HULL_FLOOR = 0.15;""",
"""const DISABLE_HULL_FLOOR = 0.15;
// Grosse Schiffe brechen nicht in einem Bild. DEATH_ROLL ist die Dauer
// der Sekundaerexplosionen, danach kommt die eigentliche.
const DEATH_ROLL = 110;          // 1,1 s
const DEATH_ROLL_GAP = 11;       // alle 0,11 s ein Treffer irgendwo im Rumpf""")

sub("death-tick",
"""function tickEscapers(){""",
"""// Sekundaerexplosionen auf einem sterbenden Grosskampfschiff. Es steht
// noch, es schiesst nicht mehr, und es reisst Stueck fuer Stueck auf.
function tickDeathRoll(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(e.rollT==null) continue;
    e.rollT--;
    if(e.rollT % DEATH_ROLL_GAP === 0){
      const img = IMGS[e.img];
      const hw = img ? img.width*e.sc*0.42 : 40;
      const hh = img ? img.height*e.sc*0.34 : 16;
      const px = e.x + (Math.random()*2-1)*hw;
      const py = e.y + (Math.random()*2-1)*hh;
      triggerExpl(px, py, 'cruiser', e.faction, null);
      addShake(2, 8);
    }
    if(e.rollT <= 0){
      e.rollT = null;
      e.hp = 0; e.dead = true;
      triggerExpl(e.x, e.y, e.type, e.faction, e);
      spawnShock(e.x, e.y, 150, 2.6, 0.020);
      addShake(7, 26);
      enemies.splice(i,1);
    }
  }
}
function tickEscapers(){""")
sub("death-call",
"""  tickEscapers();""",
"""  tickDeathRoll();
  tickEscapers();""")

# Grosse Schiffe gehen in die Todesfolge statt sofort zu verschwinden.
sub("death-enter",
"""  if(e.invuln) return;      // Station, die nicht fallen soll
  e.hp -= dmg;""",
"""  if(e.invuln) return;      // Station, die nicht fallen soll
  if(e.rollT!=null) return; // bricht schon auseinander
  e.hp -= dmg;
  if(e.hp <= 0 && !e.dead &&
     (e.type==='destroyer'||e.type==='boss'||e.type==='station')){
    // Sie stirbt nicht sofort: erst die Sekundaerexplosionen.
    e.hp = 1; e.rollT = DEATH_ROLL; e.noFire = true;
    return;
  }""")
# Wer auseinanderbricht, feuert nicht mehr.
sub("death-nofire",
"""function capitalFire(e){""",
"""function capitalFire(e){
  if(e.noFire) return;""")
# Und zaehlt nicht mehr als Bedrohung, damit die Welle nicht haengt.
sub("death-threat",
"""  for(const e of enemies) if(!e.scenery && !e.dead) n++;""",
"""  for(const e of enemies) if(!e.scenery && !e.dead && e.rollT==null) n++;""")

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil B geschrieben")
main()
