#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reads the original FreeSpace mission files and says what is in them.

The mission files of FS1, Silent Threat: Reborn and FS2 live in fs1/, str/
and fs2/ with their campaign file (.fc2). They are the source material for
rebuilding the browser game's missions - NOT something to translate one to
one: a FreeSpace mission runs 20 to 40 minutes over tens of kilometres with
40 to 65 ships, where an FS3 mission has a handful of units and a dozen
events. What is taken from them is what HAPPENS in a mission.

    python3 missions_read.py --klassen      which ship classes they use, and
                                            which FS3 hull each one is

Everything the script prints is German, like the rest of what Silvio reads.
"""
import os, re, sys, collections

ARCS = (('fs1', 'freespace.fc2', 'FreeSpace 1'),
        ('str', 'SilentThreatReborn.fc2', 'Silent Threat: Reborn'),
        ('fs2', 'FreeSpace2.fc2', 'FreeSpace 2'))

def load(path):
    """A mission file, with its DOS line ends taken out."""
    with open(path, encoding='latin-1') as f:
        return f.read().replace('\r\n', '\n').replace('\r', '\n')

def section(text, name):
    """One #Section of a mission file, up to the next one."""
    m = re.search(r'^#' + re.escape(name) + r'[^\n]*\n(.*?)(?=^#)', text, re.M | re.S)
    return m.group(1) if m else ''

def missions(arc):
    """The mission files of an arc, in campaign order, with the ones the
    campaign does not use left out (ST:R ships four -old spares)."""
    d, fc, _ = arc
    order = re.findall(r'\n\$Mission:\s*(\S+)', load(os.path.join(d, fc)))
    have = {f.lower(): f for f in os.listdir(d) if f.lower().endswith('.fs2')}
    return [(n, os.path.join(d, have[n.lower()])) for n in order if n.lower() in have]

# ── SHIP CLASSES ──────────────────────────────────────────────────────────
# What a class is called in FRED against the hull FS3 draws. Mostly the name
# itself, but FS3 abbreviates some (fiherc, fitoth) and carries one typo of
# long standing (fivalyrie for the Valkyrie), so the table is written out
# rather than guessed at. A name may carry a FRED variant behind a '#'
# (GTD Orion#Galatea is an Orion called Galatea); that is cut off first.
HULL = {
  # fighters
  'GTF Apollo':'fiapollo', 'GTF Ares':'fiares', 'GTF Angel':None,
  'GTF Erinyes':'fierinyes', 'GTF Hercules':'fiherc',
  'GTF Hercules Mark II':'fihercmk2', 'GTF Loki':'filoki',
  'GTF Myrmidon':'fimyrmidon', 'GTF Pegasus':'fipegasus',
  'GTF Perseus':'fiperseus', 'GTF Ulysses':'fiulysses',
  'GTF Valkyrie':'fivalyrie',
  'PVF Anubis':'fianubis', 'PVF Horus':'fihorus', 'PVF Seth':'fiseth',
  'PVF Thoth':'fitoth', 'GVF Serapis':'fiserapis', 'GVF Tauret':'fitauret',
  'GVF Thoth':'fitoth', 'GVF Ptah':'fiptah',
  'SF Aeshma':'fiaeshma', 'SF Astaroth':'fiastaroth', 'SF Basilisk':'fibasilisk',
  'SF Dragon':'fidragon', 'SF Manticore':'fimanticore', 'SF Mara':'fimara',
  'SF Scorpion':'fiscorpion',
  # bombers
  'GTB Artemis':'boartemis', 'GTB Athena':'boathena', 'GTB Boanerges':'boboanerges',
  'GTB Medusa':'bomedusa', 'GTB Ursa':'boursa', 'GTB Zeus':'bozeus',
  'PVB Amun':'boamun', 'PVB Osiris':'boosiris', 'GVB Bakha':'bobakha',
  'GVB Sekhmet':'bosekhmet',
  'SB Nahema':'bonahema', 'SB Nephilim':'bonephilim', 'SB Seraphim':'boseraphim',
  'SB Shaitan':'boshaitan', 'SB Taurvi':'botaurvi',
  # escape pods
  'GTEP Hermes':'ephermes', 'PVEP Ra':'epra',
  # cruisers, corvettes, destroyers
  'GTC Aeolus':'craeolus', 'GTC Fenris':'crfenris', 'GTC Leviathan':'crleviathan',
  'PVC Aten':'craten', 'GVC Mentu':'crmentu',
  'SC Cain':'crcain', 'SC Lilith':'crlilith', 'SC Rakshasa':'crrakshasa',
  'GTCv Deimos':'codeimos', 'GVCv Sobek':'cosobek', 'SCv Moloch':'comoloch',
  'NTF Iceni':'coiceni', 'NTF Boadicea':None,
  'GTD Orion':'deorionright', 'GTD Hecate':'dehecate', 'GTD Hades':'sdhades',
  'PVD Typhon':'detyphon', 'GVD Typhon':'detyphon', 'GVD Hatshepsut':'dehatshepsut',
  'SD Demon':'dedemon', 'SD Ravana':'deravana', 'SD Lucifer':'sdlucifer',
  'SJ Sathanas':'sdsathanas', 'SJD Sathanas':'sdsathanas',
  'GTVA Colossus':'sdcolossus',
  # freighters and transports
  'GTFr Chronos':'frchronos', 'GTFr Poseidon':'frposeidon', 'GTFR Poseidon':'frposeidon',
  'GTFR Triton':'frtriton', 'GTFr Triton':'frtriton',
  'PVFr Bast':'frbast', 'PVFr Bes':'frbes', 'PVFr Ma\'at':'frmaat',
  'PVFR Ma\'at':'frmaat', 'PVFr Satis':'frsatis', 'GVFr Satis':'frsatis',
  'SFr Asmodeus':'frasmodeus', 'SFr Dis':'frdis', 'SFr Mephisto':'frmephisto',
  'GTT Argo':'trargo', 'GTT Elysium':'trelysium', 'PVT Isis':'trisis',
  'GVT Isis':'trisis', 'ST Azrael':'trazrael',
  # sentry guns
  'GTSG Alastor':'sgalastor', 'GTSG Cerberus':'sgcerberus',
  'GTSG Mjolnir':'sgmjolnir', 'GTSG Watchdog':'sgwatchdog',
  'PVSG Ankh':'sgankh', 'SSG Belial':'sgbelial', 'SSG Trident':'sgtrident',
  'SSG Rahu':None,
  # support, science, medical, AWACS, gas
  'GTS Centaur':'sucentaur', 'GTS Hygeia':'suhygeia', 'PVS Scarab':'suscarab',
  'PVS Nephthys':'sunephthys', 'GTSC Faustus':'scfaustus',
  'GTM Hippocrates':'mehippocrates', 'GTA Charybdis':'cacharybdis',
  'GVA Setekh':'casetekh', 'GVG Anuket':'gmanuket', 'GTG Zephyrus':'gmzephyrus',
  'PVSC Imhotep':None, 'GTDr Amazon Advanced':None,
  # installations and cargo
  'GTI Arcadia':'inarcadia', 'Knossos':'inknossos45deg',
  'Shivan Comm Node':'incommnode', 'GTNB Pharos':'inpharos',
  'Terran NavBuoy':'inpharos',
  'GTI Polaris Extension':None, 'GTI Polaris Pylon':None,
  'PVI Karnak':None, 'Karnak Reactor':None,
  'Terran Asteroid Base':None, 'Vasudan Asteroid Base':None,
  'TAC 1':'fctac1', 'TC 2':'fctc2', 'TSC 2':'fctsc2', 'TTC 1':'fcttc1',
  'TC-TRI':'fctctri', 'TC-Meson Bomb':'fcmeson', 'SC 5':'fcsc5',
  'SAC 2':None, 'SAC 3':'fcsac3', 'VC 3':'fcvc3', 'VAC 4':'fcvac4',
  'VAC 5':'fcvac5',
}

def base(name):
    """The class without its FRED variant and without a note in brackets."""
    return name.split('#')[0].split('(')[0].strip()

def hull_of(name):
    """The FS3 hull for a class, '' where FS3 has none, None where the class
    is not in the table at all (then the table is incomplete)."""
    b = base(name)
    if b in HULL:
        return HULL[b] or ''
    return None

def ship_classes():
    """Every class in every mission, counted."""
    out = collections.Counter()
    for arc in ARCS:
        for name, path in missions(arc):
            objs = section(load(path), 'Objects')
            for c in re.findall(r'^\$Class:\s*(.+?)\s*$', objs, re.M):
                out[c] += 1
    return out

def report_classes():
    keys = set(re.findall(r'([a-z0-9]+):[0-9.]+',
               re.search(r'const HULL_LEN = \{(.*?)\};', load('src/40_world.js'), re.S).group(1)))
    cls = ship_classes()
    known = unknown = nohull = 0
    missing_table, missing_hull = collections.Counter(), collections.Counter()
    bad = []
    for c, n in cls.items():
        h = hull_of(c)
        if h is None:
            unknown += n; missing_table[base(c)] += n
        elif h == '':
            nohull += n; missing_hull[base(c)] += n
        else:
            known += n
            if h not in keys: bad.append((c, h))
    tot = known + unknown + nohull
    print('%d Missionen, %d verschiedene Schiffsklassen, %d Schiffe insgesamt'
          % (sum(len(missions(a)) for a in ARCS), len(cls), tot))
    print('  %4d Schiffe (%d %%) haben einen Rumpf, den FS3 schon zeichnet'
          % (known, round(known*100/tot)))
    print('  %4d Schiffe (%d %%) haben keinen' % (nohull, round(nohull*100/tot)))
    print('  %4d Schiffe stehen nicht in der Tabelle' % unknown)
    if bad:
        print('\nFEHLER in der Tabelle - diese Rumpfnamen kennt FS3 nicht:')
        for c, h in bad: print('  %-28s -> %s' % (c, h))
    if missing_table:
        print('\nNicht in der Tabelle (die Tabelle ist unvollstaendig):')
        for c, n in missing_table.most_common(): print('  %-28s %3d' % (c, n))
    if missing_hull:
        print('\nFS3 hat dafuer keinen Rumpf - Silvio entscheidet, was dafuer einsteht:')
        for c, n in missing_hull.most_common(): print('  %-28s %3d' % (c, n))
    return 1 if (bad or missing_table) else 0

if __name__ == '__main__':
    if '--klassen' in sys.argv:
        sys.exit(report_classes())
    print(__doc__)
