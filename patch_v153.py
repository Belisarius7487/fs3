#!/usr/bin/env python3
"""FS3 v153 - FreeSpace warp checked on every ship of every mission.

    A new test, warpsim.js, flies all 60 missions with ?warp=oval and
    watches every jump in and out, tick by tick: hull that pops into view
    at once, speed that jumps or runs backwards, a vortex that closes on
    a hull, a cut that is not where the vortex is. What it found:

    Deimos, Orion, Hecate  the vortex of a ship jumping in at the right
            edge stood 10 points inside the screen. The stern behind it
            only showed once the jump was over, all at once. The vortex
            now stands on the edge at the most; what is behind it is off
            the screen anyway.
    Fighters and bombers  they come out faster than they could before
            and keep their speed afterwards (they slowed down to half and
            then shot off again). Allied wings jump in just outside the
            left edge and the game puts them on the edge after the jump,
            26 points further - the picture now comes out right there.
    Left edge  ships that jump in at the left edge and come out slowly
            (M4, M22, M38, M55) sat in their vortex when it closed after
            three seconds. While the ship moves on, the vortex now waits
            for its stern, twenty seconds at the most (the Iceni in M60
            crawls out).
    Where the vortex stands and which way the nose points are fixed at
            the first tick of the jump.

Needs v152. Edits src/20_render.js and src/40_world.js in place and writes
warpsim.js.
Run assemble.py afterwards.
"""
import base64
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


NEW = "// Where ship and vortex are drawn during a FreeSpace style jump, or null\n// for the old look. Picture only: the ship's place in the game is e.x/e.y.\n//   warp in:  vortex opens, the ship comes out nose first and brakes down\n//             to the speed it flies on at, ending with the jump\n//   warp out: the ship keeps its speed and speeds up into the vortex\n// Where the vortex stands and which way the nose points are fixed at the\n// first tick of the jump, so the cut and the vortex stay together.\nfunction fsNose(e){\n  // The way the picture faces, turned by ang, then mirrored. Most\n  // pictures face right, some big hulls face left.\n  const s = (e.flip ? -1 : 1) * (spriteFacing(e.img)==='left' ? -1 : 1), a = e.ang||0;\n  return {x: Math.cos(a)*s, y: Math.sin(a)*s};\n}\nfunction fsSmall(e){ return e.small || e.type==='fighter' || e.type==='bomber'; }\n// Where a ship ends up after the jump. Fighters and bombers are held\n// inside the field once they fly (shipBound); one that jumps in on the\n// edge is put there at once, so its picture comes out to that spot.\nfunction fsLanding(e){\n  if(!fsSmall(e)) return {x: e.x, y: e.y};\n  const b = shipBound(e);\n  return {x: Math.max(b, Math.min(W-b, e.x)), y: Math.max(HUD_H+b, Math.min(H-b, e.y))};\n}\nfunction fsWarp(e){\n  if(!WARP_STYLE || e.portalWarp || e.type==='asteroid') return null;\n  if(!(e.warp>0) && !(e.warpOut>0)) return null;\n  const img = IMGS[e.img]; const mW = e.warpMax||100;\n  if(!img || mW<=1) return null;\n  const out = e.warpOut>0;\n  const t = out ? (mW-e.warpOut)/mW : (mW-e.warp)/mW;\n  let q = e._fsG;\n  if(!q || q.out !== out){\n    const f = fsNose(e), L = img.width*e.sc, G = L*0.6;   // G: vortex to ship centre\n    const sg = out ? 1 : -1;               // ahead when leaving, behind when coming\n    const at = out ? {x: e.x, y: e.y} : fsLanding(e);\n    // On the screen edge at the most: what sticks out beyond it cannot be\n    // seen, so nothing pops into view when the cut goes.\n    const px = Math.max(0, Math.min(W, at.x + sg*f.x*G));\n    e._fsG = q = {out, fx: f.x, fy: f.y, L, G, px, py: at.y + sg*f.y*G,\n                  x0: e.x, y0: e.y, lx: at.x, ly: at.y, e0: out ? mW-e.warpOut : mW-e.warp, v0: null};\n  }\n  const fx = q.fx, fy = q.fy, L = q.L, D = q.G + L/2;   // D: the whole way through\n  const wS = t<0.30 ? 0.05+0.95*t/0.30 : (t<0.75 ? 1 : Math.max(0, 1-(t-0.75)/0.25));\n  // Going out the picture leaves from where the jump began, whatever the\n  // game still does with the ship meanwhile.\n  let u, vis = true, bx = out ? q.x0 : e.x, by = out ? q.y0 : e.y;\n  if(!out){\n    const at = fsLanding(e); bx = at.x; by = at.y;\n    // Speed wanted at the end, less what the game already moves the ship\n    // during the jump - so it carries on without a stop.\n    const el = mW - e.warp, dt = el - q.e0;\n    const drift = dt > 0 ? ((at.x-q.lx)*fx + (at.y-q.ly)*fy)/dt : 0;\n    const v = Math.max(0, fsExitSpeed(e) - drift);\n    // Coming out takes the last three quarters of the jump, or less for a\n    // fast, short ship: it has to leave at least as fast as it goes on.\n    const Dk = Math.min(mW*0.75, v > 0 ? 1.4*D/v : 1e9);\n    const c = Math.min(1.45*D, v*Dk);\n    const k = 1 - (mW - el)/Dk; if(k<=0) vis = false;\n    const w = 1 - Math.min(1, Math.max(0, k));\n    u = -D*w*w*w - c*(w - w*w*w);\n  } else {\n    // Keeps the speed it had and speeds up from there.\n    if(q.v0 == null) q.v0 = fsSmall(e)\n      ? Math.max(0, (e._fvx1||0)*fx + (e._fvy1||0)*fy)\n      : Math.max(0, (e._fvx||0)*fx + (e._fvy||0)*fy);\n    const Dk = Math.min(mW*0.75, q.v0 > 0 ? 1.4*D/q.v0 : 1e9);\n    const c = Math.min(1.45*D, q.v0*Dk);\n    const k = Math.min(1, Math.max(0, (mW - e.warpOut)/Dk)); if(k>=1) vis = false;\n    u = c*k + (D-c)*k*k*k;\n  }\n  return {out, fx, fy, px: q.px, py: q.py, wS, wA: Math.min(1, wS*1.4),\n          dx: bx - e.x + fx*u, dy: by - e.y + fy*u, vis};\n}\n"
WARPSIM = "Ly8gd2FycHNpbS5qcyAtIHdhdGNoZXMgZXZlcnkganVtcCBpbiBhbmQgb3V0IG9mIGV2ZXJ5IHdyaXR0ZW4gbWlzc2lvbiB3aXRoCi8vIHRoZSBGcmVlU3BhY2Ugc3R5bGUgd2FycCAoP3dhcnA9b3ZhbCkgYW5kIHJlcG9ydHMgd2hhdCB3b3VsZCBsb29rIHdyb25nLgovLwovLyAgIG5vZGUgd2FycHNpbS5qcyBobHBfc2hvb3Rlcl92Tk5OX2xvZ2ljLmh0bWwgW21vdW50cy5qc29uXSBbbWlzc2lvbnNdCi8vICAgbWlzc2lvbnM6IGUuZy4gIjEtNjAiIChkZWZhdWx0KSBvciAiNTIiIG9yICI1MC01NSIKLy8KLy8gQ2hlY2tlZCwgdGljayBieSB0aWNrLCBmb3IgZXZlcnkgc2hpcCB0aGF0IGp1bXBzOgovLyAgIHBvcCAgICAgIHBhcnQgb2YgdGhlIGh1bGwgc2hvd3MgdXAgKG9yIHZhbmlzaGVzKSBhdCBvbmNlIGluc3RlYWQgb2YKLy8gICAgICAgICAgICBzbGlkaW5nIG91dCBvZiAoaW50bykgdGhlIHZvcnRleAovLyAgIHN0b3AgICAgIHRoZSBzaGlwJ3Mgc3BlZWQganVtcHMgb3IgaXQgbW92ZXMgYmFja3dhcmRzIGR1cmluZyB0aGUganVtcAovLyAgIGNsb3NlICAgIGEgdm9ydGV4IGNsb3NlcyB3aGlsZSB0aGUgaHVsbCBzdGlsbCBzdGlja3MgaW4gaXQgb24gc2NyZWVuCi8vICAgcGxhbmUgICAgdGhlIGVkZ2UgdGhhdCBjdXRzIHRoZSBodWxsIGlzIG5vdCB3aGVyZSB0aGUgdm9ydGV4IGlzIGRyYXduCi8vIEV4aXQgY29kZSAxIGlmIGFueXRoaW5nIHdhcyBmb3VuZC4KY29uc3QgZnMgPSByZXF1aXJlKCdmcycpLCBwYXRoID0gcmVxdWlyZSgncGF0aCcpLCBvcyA9IHJlcXVpcmUoJ29zJyk7CmNvbnN0IHtleGVjU3luY30gPSByZXF1aXJlKCdjaGlsZF9wcm9jZXNzJyk7CmNvbnN0IHtjaHJvbWl1bX0gPSByZXF1aXJlKHBhdGguam9pbihleGVjU3luYygnbnBtIHJvb3QgLWcnKS50b1N0cmluZygpLnRyaW0oKSwgJ3BsYXl3cmlnaHQnKSk7Cgpjb25zdCBsb2dpYyA9IHByb2Nlc3MuYXJndlsyXTsKY29uc3QgbW91bnRzID0gcHJvY2Vzcy5hcmd2WzNdIHx8ICdobHBfbW91bnRzX2ZpbmFsLmpzb24nOwpjb25zdCByYW5nZSA9IChwcm9jZXNzLmFyZ3ZbNF0gfHwgJzEtNjAnKS5zcGxpdCgnLScpLm1hcChOdW1iZXIpOwpjb25zdCBNMCA9IHJhbmdlWzBdLCBNMSA9IHJhbmdlWzFdIHx8IHJhbmdlWzBdOwoKLy8gQSAxeDEgcGljdHVyZSBzdGFuZHMgaW4gZm9yIHRoZSB2b3J0ZXggYW5kIGdsb3cgc2hlZXRzOiB0aGUgdm9ydGV4IGlzCi8vIG9ubHkgZHJhd24gb25jZSBpdHMgcGljdHVyZSBoYXMgbG9hZGVkLCBhbmQgdGhlIHJlYWwgb25lcyBhcmUgbm90IGluIGdpdC4KY29uc3QgRE9UID0gJ2RhdGE6aW1hZ2UvcG5nO2Jhc2U2NCxpVkJPUncwS0dnb0FBQUFOU1VoRVVnQUFBQUVBQUFBQkNBUUFBQUMxSEF3Q0FBQUFDMGxFUVZSNDJtTmtZQUFBQUFZQUFqQ0IwQzhBQUFBQVNVVk9SSzVDWUlJPSc7CmxldCBodG1sID0gZnMucmVhZEZpbGVTeW5jKGxvZ2ljLCAndXRmOCcpOwpmb3IoY29uc3QgbiBvZiBbJ3dhcnBfaW1nJywgJ3dhcnBfa25vc3NvcycsICd3YXJwX2dsb3cnLCAnd2FycF9nbG93X2tub3Nzb3MnXSkKICBodG1sID0gaHRtbC5zcGxpdCgnQEBGUzNfQVNTRVQ6aW1hZ2VzLycgKyBuICsgJy53ZWJwQEAnKS5qb2luKERPVCk7Cmh0bWwgPSBodG1sLnJlcGxhY2UoLzxzY3JpcHQoW14+XSopPi8sICc8c2NyaXB0JDE+XG5jb25zdCBNT1VOVFM9JyArCiAgSlNPTi5zdHJpbmdpZnkoSlNPTi5wYXJzZShmcy5yZWFkRmlsZVN5bmMobW91bnRzLCAndXRmOCcpKSkgKyAnO1xuJyk7CmNvbnN0IHRtcCA9IHBhdGguam9pbihvcy50bXBkaXIoKSwgJ3dhcnBzaW1fJyArIHByb2Nlc3MucGlkICsgJy5odG1sJyk7CmZzLndyaXRlRmlsZVN5bmModG1wLCBodG1sKTsKCi8vIFJ1bnMgaW5zaWRlIHRoZSBwYWdlLCBvbmUgbWlzc2lvbi4KY29uc3QgQk9EWSA9IGAKICBpZih0eXBlb2YgZnNOb3NlICE9PSAnZnVuY3Rpb24nKSB3aW5kb3cuZnNOb3NlID0gZSA9PiB7IGNvbnN0IHMgPSAoZS5mbGlwPy0xOjEpKihzcHJpdGVGYWNpbmcoZS5pbWcpPT09J2xlZnQnPy0xOjEpLCBhID0gZS5hbmd8fDA7IHJldHVybiB7eDpNYXRoLmNvcyhhKSpzLCB5Ok1hdGguc2luKGEpKnN9OyB9OwogIGZvcihjb25zdCBrIG9mIE9iamVjdC5rZXlzKEhVTExfTEVOKSl7CiAgICBjb25zdCBzbWFsbCA9IC9eKGZpfGJvfHNnfGZjfGVwKS8udGVzdChrKSAmJiBIVUxMX0xFTltrXSA8IDgwOwogICAgY29uc3QgYyA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ2NhbnZhcycpOwogICAgYy53aWR0aCA9IHNtYWxsID8gNjAgOiAzMjA7IGMuaGVpZ2h0ID0gc21hbGwgPyA0MCA6IDkwOwogICAgSU1HU1trXSA9IGM7CiAgfQogIGltZ3NMb2FkZWQgPSBUT1RBTDsgbmVic0xvYWRlZCA9IDA7CiAgbGF1bmNoR2FtZSgpOwogIGNvbnN0IHN0YXJ0V2F2ZSA9IHdhdmU7CiAgY29uc3QgVCA9IG5ldyBNYXAoKTsgICAgICAgICAgLy8gc2hpcCAtPiB0cmFjawogIGNvbnN0IGZvdW5kID0gW107CiAgZnVuY3Rpb24gbm90ZShraW5kLCBlLCB0eHQpewogICAgY29uc3QgaWQgPSBlLmltZyArIChlLnVpZCA/ICcvJyArIGUudWlkIDogJycpOwogICAgaWYoZm91bmQuc29tZShmID0+IGYua2luZD09PWtpbmQgJiYgZi5pZD09PWlkKSkgcmV0dXJuOwogICAgZm91bmQucHVzaCh7a2luZCwgaWQsIHdhdmUsIHR4dH0pOwogIH0KICAvLyBIdWxsIGFsb25nIHRoZSBub3NlOiBjZW50cmUsIGxlbmd0aCwgYW5kIHdoYXQgb2YgaXQgY2FuIGJlIHNlZW4uCiAgZnVuY3Rpb24gbG9vayhlKXsKICAgIGNvbnN0IGltZyA9IElNR1NbZS5pbWddOyBpZighaW1nKSByZXR1cm4gbnVsbDsKICAgIGNvbnN0IEwgPSBpbWcud2lkdGgqZS5zYzsKICAgIGNvbnN0IGcgPSBmc1dhcnAoZSk7CiAgICBsZXQgcCA9IG51bGw7ICAgICAgICAgICAgICAgICAgICAgICAvLyBjdXR0aW5nIHBsYW5lLCBpZiBhbnkKICAgIGlmKGcpeyBpZighZy52aXMpIHJldHVybiB7dmlzOjAsIGcsIEwsIGN4Om51bGx9OyBwID0ge3B4OmcucHgsIHB5OmcucHksIGZ4OmcuZngsIGZ5OmcuZnksIGtlZXBGcm9udDohZy5vdXR9OyB9CiAgICBlbHNlIGlmKHR5cGVvZiBmc1Bvc3RDbGlwID09PSAnZnVuY3Rpb24nKXsgY29uc3QgcSA9IGZzUG9zdENsaXAoZSk7IGlmKHEpIHAgPSBxOyB9CiAgICBjb25zdCBmID0gZyA/IHt4OmcuZngsIHk6Zy5meX0gOiBmc05vc2UoZSk7CiAgICBjb25zdCBjeCA9IGUueCArIChnID8gZy5keCA6IDApLCBjeSA9IGUueSArIChnID8gZy5keSA6IDApOwogICAgLy8gSHVsbCBhcyBhIHNlZ21lbnQgYWxvbmcgdGhlIG5vc2UsIHBhcmFtZXRlciBzIGZyb20gLUwvMiB0byBMLzIuCiAgICBsZXQgYSA9IC1MLzIsIGIgPSBMLzI7CiAgICBpZihwKXsKICAgICAgY29uc3QgZDAgPSAoY3gtcC5weCkqcC5meCArIChjeS1wLnB5KSpwLmZ5OyAgICAgIC8vIGNlbnRyZSBwYXN0IHRoZSBwbGFuZQogICAgICBpZihwLmtlZXBGcm9udCkgYSA9IE1hdGgubWF4KGEsIC1kMCk7IGVsc2UgYiA9IE1hdGgubWluKGIsIC1kMCk7CiAgICB9CiAgICAvLyBPbiBzY3JlZW46IHggYmV0d2VlbiAwIGFuZCBXLgogICAgaWYoTWF0aC5hYnMoZi54KSA+IDFlLTYpewogICAgICBjb25zdCBzMCA9ICgwIC0gY3gpL2YueCwgczEgPSAoVyAtIGN4KS9mLng7CiAgICAgIGEgPSBNYXRoLm1heChhLCBNYXRoLm1pbihzMCwgczEpKTsgYiA9IE1hdGgubWluKGIsIE1hdGgubWF4KHMwLCBzMSkpOwogICAgfQogICAgcmV0dXJuIHt2aXM6IE1hdGgubWF4KDAsIGItYSksIGcsIEwsIGN4LCBjeSwgZiwgcH07CiAgfQogIGNvbnN0IE1BWFQgPSA0MDAwMDsKICBsZXQgdCA9IDAsIGRvbmUgPSAtMTsKICB3aGlsZSh0IDwgTUFYVCl7CiAgICBwbGF5ZXIuaHAgPSBwbGF5ZXIubWF4SHA7IHBsYXllci5zaCA9IHBsYXllci5tYXhTaDsgbGl2ZXMgPSAzOwogICAgaWYodCAlIDIwMCA9PT0gMCl7CiAgICAgIGZvcihjb25zdCBlIG9mIGVuZW1pZXMpewogICAgICAgIGlmKGUud2FycD4wIHx8IGUuaW52dWxuIHx8IGUuc2NlbmVyeSkgY29udGludWU7CiAgICAgICAgaWYoZS5jYXB0dXJlTG9jayl7IGZvcihjb25zdCBzIG9mIChlLnN1YnN8fFtdKSkgaWYocy5pZD09PSdlbmdpbmVzJ3x8cy5pZD09PSd3ZWFwb25zJ3x8cy5pZD09PSduYXZpZ2F0aW9uJyl7IHMuZGVhZD10cnVlOyBzLmhwPTA7IH0gY29udGludWU7IH0KICAgICAgICBpZihlLnNjYW5TdWJzICYmICFlLnNjYW5uZWQpeyBmb3IoY29uc3QgcyBvZiBlLnN1YnMpIHMuc2NhblQgPSAxZTk7IGNvbnRpbnVlOyB9CiAgICAgICAgaWYoZS5zY2FuTG9jayAmJiAhZS5zY2FubmVkKXsgZS5zY2FubmVkID0gdHJ1ZTsgY29udGludWU7IH0KICAgICAgICAvLyBCaWcgc2hpcHMgZ2V0IHRpbWUgdG8gYmUgc2VlbiBiZWZvcmUgdGhleSBnby4KICAgICAgICBpZighZS5zbWFsbCAmJiBlLnR5cGUhPT0nZmlnaHRlcicgJiYgZS50eXBlIT09J2JvbWJlcicgJiYgZS5fYWdlID09IG51bGwpIGUuX2FnZSA9IHQ7CiAgICAgICAgaWYoZS5fYWdlICE9IG51bGwgJiYgdCAtIGUuX2FnZSA8IDE1MDApIGNvbnRpbnVlOwogICAgICAgIGUuaHAgPSAwOwogICAgICB9CiAgICAgIElURU1TLmxlbmd0aCA9IDA7CiAgICB9CiAgICB1cGRhdGUoKTsgZHJhdygpOyB0Kys7CiAgICBmb3IoY29uc3QgZSBvZiBlbmVtaWVzLmNvbmNhdChhbGxpZXMpKXsKICAgICAgaWYoZS50eXBlPT09J2FzdGVyb2lkJyB8fCBlLnBvcnRhbFdhcnApIGNvbnRpbnVlOwogICAgICBjb25zdCBpbkp1bXAgPSBlLndhcnA+MCB8fCBlLndhcnBPdXQ+MDsKICAgICAgbGV0IHRyID0gVC5nZXQoZSk7CiAgICAgIGlmKCF0cil7IGlmKCFpbkp1bXApIGNvbnRpbnVlOyB0ciA9IHtwcmV2Om51bGx9OyBULnNldChlLCB0cik7IH0KICAgICAgY29uc3Qgbm93ID0gbG9vayhlKTsgaWYoIW5vdykgY29udGludWU7CiAgICAgIGNvbnN0IHByID0gdHIucHJldjsgdHIucHJldiA9IG5vdzsKICAgICAgaWYoIXByKSBjb250aW51ZTsKICAgICAgLy8gU3BlZWQgb2YgdGhlIHBpY3R1cmUgYWxvbmcgdGhlIG5vc2UuCiAgICAgIGxldCB2ID0gbnVsbDsKICAgICAgaWYobm93LmN4IT1udWxsICYmIHByLmN4IT1udWxsICYmIG5vdy5mKSB2ID0gKG5vdy5jeC1wci5jeCkqbm93LmYueCArIChub3cuY3ktcHIuY3kpKm5vdy5mLnk7CiAgICAgIGNvbnN0IHZQcmV2ID0gdHIudjsgdHIudiA9IHY7CiAgICAgIC8vIFRoZSB0aWNrIGEgaHVsbCB2YW5pc2hlcyBoYXMgbm8gc3BlZWQgb2YgaXRzIG93bjogdGhlIGxhc3Qgb25lIGNvdW50cy4KICAgICAgY29uc3QgbW92ZSA9IE1hdGguYWJzKHYhPW51bGwgPyB2IDogKHZQcmV2fHwwKSkgKyAxLjU7CiAgICAgIC8vIHBvcDogbW9yZSBodWxsIHR1cm5zIHZpc2libGUgKG9yIGludmlzaWJsZSkgdGhhbiB0aGUgbW90aW9uIGV4cGxhaW5zLgogICAgICAvLyBUaGUgZmlyc3QgdmlzaWJsZSB0aWNrIG9mIGEganVtcCBpbiBpcyB0aGUgbm9zZSBjb21pbmcgdGhyb3VnaC4KICAgICAgY29uc3QgZHZpcyA9IG5vdy52aXMgLSBwci52aXM7CiAgICAgIGlmKE1hdGguYWJzKGR2aXMpID4gbW92ZSArIDIgJiYgIShwci52aXM9PT0wICYmIGUud2FycD4wKSkKICAgICAgICBub3RlKCdwb3AnLCBlLCAoZHZpcz4wPycrJzonJykrZHZpcy50b0ZpeGVkKDApKydweCBvZiBodWxsIGF0IG9uY2UgKCcgKyBwci52aXMudG9GaXhlZCgwKSArICcgLT4gJyArIG5vdy52aXMudG9GaXhlZCgwKSArICcsIHNwZWVkICcgKyAodj09bnVsbD8nLSc6di50b0ZpeGVkKDIpKSArICcpJyArCiAgICAgICAgICAgICAoZS53YXJwPjA/JyAoanVtcCBpbiknOihlLndhcnBPdXQ+MD8nIChqdW1wIG91dCknOicgKGFmdGVyIGp1bXAgaW4pJykpKTsKICAgICAgLy8gc3RvcDogYSBqdW1wIGluIHNwZWVkLCBvciBiYWNrd2FyZHMgZHVyaW5nIGEganVtcC4KICAgICAgLy8gRmlnaHRlcnMgdHVybiBhbmQgc3BlZWQgdXAgb24gdGhlaXIgb3duIHJpZ2h0IGF3YXk7IGZvciB0aGVtIGEKICAgICAgLy8gbGl0dGxlIG1vcmUgaXMgbGV0IHRocm91Z2gsIGFuZCBhZnRlciB0aGUganVtcCB0aGVpciBmbGlnaHQgbW9kZWwKICAgICAgLy8gdGFrZXMgb3ZlciBhdCBvbmNlLCBzbyBvbmx5IHRoZSBqdW1wIGl0c2VsZiBpcyBjaGVja2VkLgogICAgICBpZih2IT1udWxsICYmIHZQcmV2IT1udWxsICYmIE1hdGguYWJzKHYgLSB2UHJldikgPiAoZnNTbWFsbChlKSA/IDAuNiA6IDAuMzUpICYmCiAgICAgICAgIChpbkp1bXAgfHwgKHRyLndhc0p1bXAgJiYgIWZzU21hbGwoZSkpKSkKICAgICAgICBub3RlKCdzdG9wJywgZSwgJ3NwZWVkICcgKyB2UHJldi50b0ZpeGVkKDIpICsgJyAtPiAnICsgdi50b0ZpeGVkKDIpICsgJyBweC90aWNrJyArIChlLndhcnA+MD8nIChqdW1wIGluKSc6KGUud2FycE91dD4wPycgKGp1bXAgb3V0KSc6JyAoYWZ0ZXIganVtcCknKSkpOwogICAgICBpZih2IT1udWxsICYmIHYgPCAtMC4wNSAmJiBpbkp1bXApIG5vdGUoJ3N0b3AnLCBlLCAnYmFja3dhcmRzICcgKyB2LnRvRml4ZWQoMikgKyAnIHB4L3RpY2snKTsKICAgICAgLy8gcGxhbmU6IHRoZSBjdXQgYW5kIHRoZSBkcmF3biB2b3J0ZXggaGF2ZSB0byBhZ3JlZS4KICAgICAgaWYoZS53YXJwPjAgJiYgbm93LmcgJiYgbm93LmcudmlzICYmIGUuX2ZzcCAmJgogICAgICAgICBNYXRoLmh5cG90KG5vdy5nLnB4IC0gZS5fZnNwLnB4LCBub3cuZy5weSAtIGUuX2ZzcC5weSkgPiAyKQogICAgICAgIG5vdGUoJ3BsYW5lJywgZSwgJ2N1dCAnICsgTWF0aC5oeXBvdChub3cuZy5weC1lLl9mc3AucHgsIG5vdy5nLnB5LWUuX2ZzcC5weSkudG9GaXhlZCgwKSArICdweCBmcm9tIHRoZSB2b3J0ZXgnKTsKICAgICAgLy8gVGhlIGhhbmQtb3ZlcjogdGhlIGZldyB0aWNrcyBhZnRlciBhIGp1bXAuIExhdGVyIGNoYW5nZXMgb2Ygc3BlZWQKICAgICAgLy8gYXJlIHRoZSBzaGlwJ3Mgb3duIChhcnJpdmluZyBhdCBpdHMgc3RhdGlvbiwgdHVybmluZykuCiAgICAgIHRyLndhc0p1bXAgPSBpbkp1bXAgfHwgKHRyLndhc0p1bXAgJiYgKyt0ci5hZnRlciA8IDMpOwogICAgICBpZihpbkp1bXApIHRyLmFmdGVyID0gMDsKICAgIH0KICAgIC8vIGNsb3NlOiBhIGNsb3Npbmcgdm9ydGV4IHdpdGggYSBodWxsIHN0aWxsIGFjcm9zcyBpdCwgb24gc2NyZWVuLgogICAgZm9yKGNvbnN0IHAgb2YgRlNfUE9SVEFMUyl7CiAgICAgIGlmKHAuY2xvc2VUIDwgMCB8fCBwLnB4IDwgMCB8fCBwLnB4ID4gVykgY29udGludWU7CiAgICAgIC8vIE9uIHRoZSBzY3JlZW4gZWRnZSwgd2hhdCBpcyBiZWhpbmQgdGhlIHZvcnRleCBpcyBvZmYgdGhlIHNjcmVlbi4gQQogICAgICAvLyBzaGlwIHRoYXQgc3RheXMgdGhlcmUgaGFsZiBvdXQgaXMgbm8gZmF1bHQ7IG9uZSBzdGlsbCBjb21pbmcgb3V0IGlzLgogICAgICBpZigocC5weCA8PSAwIHx8IHAucHggPj0gVykgJiYgIWZzUG9ydGFsTW92aW5nKHApKSBjb250aW51ZTsKICAgICAgY29uc3QgZSA9IHAuZTsgaWYoZW5lbWllcy5pbmRleE9mKGUpPDAgJiYgYWxsaWVzLmluZGV4T2YoZSk8MCkgY29udGludWU7CiAgICAgIGNvbnN0IGltZyA9IElNR1NbZS5pbWddOyBpZighaW1nKSBjb250aW51ZTsKICAgICAgY29uc3QgTCA9IGltZy53aWR0aCplLnNjLCBnID0gZS53YXJwPjAgPyBmc1dhcnAoZSkgOiBudWxsOwogICAgICBjb25zdCBjeCA9IGUueCArIChnP2cuZHg6MCksIGN5ID0gZS55ICsgKGc/Zy5keTowKTsKICAgICAgY29uc3QgZDAgPSAoY3gtcC5weCkqcC5meCArIChjeS1wLnB5KSpwLmZ5OwogICAgICBpZihkMCAtIEwvMiA8IC0xICYmIGQwICsgTC8yID4gMSkgbm90ZSgnY2xvc2UnLCBlLCAndm9ydGV4IGNsb3NlcyBvbiAnICsgKC0oZDAtTC8yKSkudG9GaXhlZCgwKSArICdweCBvZiBodWxsJyk7CiAgICB9CiAgICBpZihkb25lIDwgMCAmJiB3YXZlID4gc3RhcnRXYXZlKSBkb25lID0gdDsKICAgIGlmKGRvbmUgPj0gMCAmJiB0IC0gZG9uZSA+IDIwMCkgYnJlYWs7CiAgfQogIHJldHVybiB7Zm91bmQsIHRpY2tzOiB0LCBlbmRlZDogZG9uZSA+PSAwLCBqdW1wczogVC5zaXplfTsKYDsKCihhc3luYygpPT57CiAgY29uc3QgYnJvd3NlciA9IGF3YWl0IGNocm9taXVtLmxhdW5jaCgpOwogIGxldCBiYWQgPSAwOwogIGZvcihsZXQgbT1NMDsgbTw9TTE7IG0rKyl7CiAgICBjb25zdCBwYWdlID0gYXdhaXQgYnJvd3Nlci5uZXdQYWdlKCk7CiAgICBjb25zdCBlcnJzID0gW107CiAgICBwYWdlLm9uKCdwYWdlZXJyb3InLCBlPT5lcnJzLnB1c2goU3RyaW5nKGUubWVzc2FnZXx8ZSkpKTsKICAgIGF3YWl0IHBhZ2UuZ290bygnZmlsZTovLycgKyB0bXAgKyAnP209JyArIG0gKyAnJndhcnA9b3ZhbCZwcmFjdGljZT0xJyk7CiAgICBhd2FpdCBwYWdlLndhaXRGb3JUaW1lb3V0KDMwMCk7CiAgICBsZXQgciA9IG51bGw7CiAgICB0cnl7IHIgPSBhd2FpdCBwYWdlLmV2YWx1YXRlKCcoZnVuY3Rpb24oKXsnICsgQk9EWSArICd9KSgpJyk7IH0KICAgIGNhdGNoKGUpeyBlcnJzLnB1c2goU3RyaW5nKGUubWVzc2FnZXx8ZSkpOyB9CiAgICBjb25zdCBoZWFkID0gJ00nICsgU3RyaW5nKG0pLnBhZFN0YXJ0KDIsJzAnKTsKICAgIGlmKHIpewogICAgICBjb25zb2xlLmxvZyhoZWFkICsgJyAgJyArIHIuanVtcHMgKyAnIHNoaXBzIGp1bXBlZCcgKyAoci5lbmRlZCA/ICcnIDogJyAgKHdhdmUgZGlkIG5vdCBlbmQpJykgKwogICAgICAgICAgICAgICAgICAoci5mb3VuZC5sZW5ndGggPyAnJyA6ICcgIG9rJykpOwogICAgICBmb3IoY29uc3QgZiBvZiByLmZvdW5kKSBjb25zb2xlLmxvZygnICAgJyArIGYua2luZC5wYWRFbmQoNikgKyBmLmlkLnBhZEVuZCgyMikgKyBmLnR4dCk7CiAgICAgIGJhZCArPSByLmZvdW5kLmxlbmd0aDsKICAgIH0KICAgIGlmKGVycnMubGVuZ3RoKXsgYmFkKys7IGNvbnNvbGUubG9nKGhlYWQgKyAnICBwYWdlIGVycm9yczogJyArIGVycnMuc2xpY2UoMCwzKS5qb2luKCcgfCAnKSk7IH0KICAgIGF3YWl0IHBhZ2UuY2xvc2UoKTsKICB9CiAgYXdhaXQgYnJvd3Nlci5jbG9zZSgpOwogIGZzLnVubGlua1N5bmModG1wKTsKICBjb25zb2xlLmxvZyhiYWQgPyAnXG4nICsgYmFkICsgJyBmaW5kaW5ncycgOiAnXG5hbGwgY2xlYW4nKTsKICBwcm9jZXNzLmV4aXQoYmFkID8gMSA6IDApOwp9KSgpOwo="

rd = open("src/20_render.js", encoding="utf-8").read()

START = "// Where ship and vortex are drawn during a FreeSpace style jump, or null\n"
END = "  return {out, fx, fy, px, py, wS, wA: Math.min(1, wS*1.4), dx: fx*u, dy: fy*u, vis};\n}\n"
if rd.count(START) != 1 or rd.count(END) != 1:
    sys.exit("Abbruch (fsWarp): Funktion nicht wie erwartet gefunden.")
a = rd.index(START)
b = rd.index(END) + len(END)
rd = rd[:a] + NEW + rd[b:]
rd = replace_once(rd, "  e._fsE0 = null; e._fsV = null;\n", "  e._fsG = null;\n", "reset")

rd = replace_once(
    rd,
    "  if(e.small || e.type==='fighter' || e.type==='bomber') return e.spd || 1.5;\n",
    "  // A fighter flies along its heading, which the picture only follows\n"
    "  // roughly: what counts is the part along the nose.\n"
    "  if(fsSmall(e)){ const f = fsNose(e), h = e.head||0;\n"
    "    return (e.spd || 1.5)*Math.max(0, Math.cos(h)*f.x + Math.sin(h)*f.y); }\n",
    "exit speed small")

# A ship that stops half off the screen at the left edge sat in its
# vortex when it closed after three seconds. While the ship moves on the
# vortex now waits for its stern, up to twenty seconds (the Iceni crawls).
rd = replace_once(
    rd,
    "    if(p.closeT < 0 && age >= p.mW*0.75 &&\n"
    "       (fsPortalCleared(p) || age > p.mW + FS_PORTAL_LINGER*TICK_HZ)) p.closeT = fc;\n",
    "    if(p.closeT < 0 && age >= p.mW*0.75 && (fsPortalCleared(p) ||\n"
    "       (age > p.mW + FS_PORTAL_LINGER*TICK_HZ && !fsPortalMoving(p)) ||\n"
    "       age > p.mW + FS_PORTAL_MAX*TICK_HZ)) p.closeT = fc;\n",
    "linger")
rd = replace_once(
    rd,
    "function drawFsPortals(){\n",
    "const FS_PORTAL_MAX = 20;      // seconds after the jump, for a ship still moving out\n"
    "// The ship still moving on along its nose (measured by fsTrack).\n"
    "function fsPortalMoving(p){\n"
    "  const e = p.e;\n"
    "  return ((e._fvx||0)*p.fx + (e._fvy||0)*p.fy) > 0.05;\n"
    "}\n"
    "function drawFsPortals(){\n",
    "moving")

# A fighter changes course all the time: the speed it jumps out with is
# the one of its last tick, not the smoothed one of a capital ship.
rd = replace_once(
    rd,
    "    e._fvy = (e._fvy||0)*0.8 + 0.2*(e.y - e._ly)/n;\n",
    "    e._fvy = (e._fvy||0)*0.8 + 0.2*(e.y - e._ly)/n;\n"
    "    e._fvx1 = (e.x - e._lx)/n; e._fvy1 = (e.y - e._ly)/n;\n",
    "last speed")

# Allied wings jump in just outside the left edge. The flight model only
# puts them inside the field one tick after the jump, so they jumped 26
# points on their first tick out - in the old look as well.
wo = open("src/40_world.js", encoding="utf-8").read()
wo = replace_once(
    wo,
    "    if(a.warp>0){\n"
    "      a.warp--;\n",
    "    if(a.warp>0){\n"
    "      a.warp--;\n"
    "      // Out of the vortex inside the field, where the flight model keeps it.\n"
    "      if(a.warp<=0 && a.small){ const b = shipBound(a);\n"
    "        a.x = Math.max(b, Math.min(W-b, a.x)); a.y = Math.max(HUD_H+b, Math.min(H-b, a.y)); }\n",
    "ally lands inside")
open("src/40_world.js", "w", encoding="utf-8").write(wo)

open("src/20_render.js", "w", encoding="utf-8").write(rd)
open("warpsim.js", "w", encoding="utf-8").write(base64.b64decode(WARPSIM).decode("utf-8"))
