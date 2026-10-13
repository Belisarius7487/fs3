# FS3 – POF converter

Turns FreeSpace POF models (MediaVP) into the compact web format the game
loads from `models/<key>/`. Python 3 with Pillow (`pip install pillow`).

## Files

| File | What it does |
|---|---|
| `pof.py` | Reads a POF (version 2301, BSP2): submodels, triangles, textures, special points (subsystems, turrets, docks, thrusters), debris. |
| `poflite.py` | Header-only reader (bbox, submodels, special points) – fast on big models. |
| `webmodel.py` | Converts one POF into `lo.bin` / `hi.bin` (or `full.bin.gz`) plus `c/n/g512` and `c/n/g1024.webp` textures. |
| `buildmodels.py` | Batch: every hull in `HULLS` (game key → MediaVP folder and POF name) into `<out>/<key>/`. |
| `buildfull201.py` | Capital ships with moving parts kept apart (turrets, dishes), gzipped `full.bin.gz`. |
| `builddebtex.py` | Maps of the debris pieces (dead, damage, debris textures). |
| `mkthrusters.py` | Thruster points of all hulls → `thrusters.json`. |
| `mkwarp.py` | The warp disc from MediaVP `Warp.pof` → JSON. |
| `mkfxsheets.py` | MediaVP explosion/smoke/trail animations (`.dds` frames) → sprite sheets (v216). |

## Usage

MediaVP 4.7.3 unpacked (folders `MV_Assets_S`, `MV_Assets_T_1`, … each with
`data/models` and `data/maps`). Point `FS3_MVPS` at it:

```
export FS3_MVPS=/path/to/MVPS-473
cd tools/pof
python3 -I buildmodels.py ../../models                  # all hulls
python3 -I buildmodels.py ../../models fimyrmidon,codeimos   # only these
python3 -I buildfull201.py ../../models codeimos,deravana
python3 -I builddebtex.py ../../models codeimos,deravana
python3 -I webmodel.py <file.pof> '<skin json>' <out dir>   # one model by hand
python3 -I mkwarp.py . <Warp.pof> warp.json
python3 -I mkfxsheets.py <MV_Effects_1/data/effects> <out dir>
```

A new hull: add a line to `HULLS` in `buildmodels.py` (`'key': ('MV_Assets_T_1', 'PofName')`)
and run it for that key. Models go to the server as a ZIP with paths `models/<key>/…`.

## Coordinates

FreeSpace is left-handed. The converter mirrors x and reverses the winding,
so WebGL gets a right-handed model with +z forward (bow) and +y up.
