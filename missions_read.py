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
# Silvio has been through the twelve classes FS3 had no hull for (v233) and
# settled every one. Three of them need no model at all:
#
#   SAC 2                a cargo container; the SAC 3 stands in for it
#   SSG Rahu             "Das ist die SG Rahu. Volition hat hierbei einen
#                        Klassifizierungsfehler begangen und nie behoben. Das
#                        hab ich fuer FS3 gemacht, weil es ein Gasminer ist
#                        und keine Sentry Gun." -> gmrahu
#   GTDr Amazon Advanced "Ist das gleiche Modell wie die GTFr Chronos."
#
# One is not needed: the Karnak Reactor sits INSIDE the PVI Karnak, and the
# game cannot fly into a station - the mission it is in (str16) gets
# redesigned instead.
#
# The remaining eight are hulls FS3 does not have yet. They are marked
# WANTED below with the mission that needs them, and the list is in
# OFFENE_FEHLER.md. Until a hull is there, '' keeps the table honest: the
# check counts the class as having no hull rather than guessing a stand-in.
  # fighters
  'GTF Apollo':'fiapollo', 'GTF Ares':'fiares',
  'GTF Angel':'fiangel',                # v235: Angel.pof, FSPort MediaVPs
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
  'NTF Iceni':'coiceni',
  # WANTED, FS2 SM1-02: the asteroid the Iceni hides in. Silvio: "Das Modell
  # heisst Boadicea, wobei der Name ingame nie faellt." Model from the FS2 files.
  'NTF Boadicea':'inastbase',   # v235: Base2r-01.pof - the SAME model as the
                                # Terran asteroid base, so no key of her own
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
  # Volition filed the Rahu as a sentry gun and never corrected it; it is a
  # gas miner, and FS3 has it as one (Silvio).
  'SSG Rahu':'gmrahu',
  # support, science, medical, AWACS, gas
  'GTS Centaur':'sucentaur', 'GTS Hygeia':'suhygeia', 'PVS Scarab':'suscarab',
  'PVS Nephthys':'sunephthys', 'GTSC Faustus':'scfaustus',
  'GTM Hippocrates':'mehippocrates', 'GTA Charybdis':'cacharybdis',
  'GVA Setekh':'casetekh', 'GVG Anuket':'gmanuket', 'GTG Zephyrus':'gmzephyrus',
  'PVSC Imhotep':'scimhotep',           # v235: imhotep.pof, FSPort MediaVPs
  'GTDr Amazon Advanced':'frchronos',   # the same model as the Chronos
  # installations and cargo
  'GTI Arcadia':'inarcadia', 'Knossos':'inknossos45deg',
  'Shivan Comm Node':'incommnode', 'GTNB Pharos':'inpharos',
  'Terran NavBuoy':'inpharos',
  'GTI Polaris Extension':'inpolaris',  # v235: dock01-terran.pof, FSPort MediaVPs
  'GTI Polaris Pylon':'inpolarispylon', # v235: dock02-terran.pof, FSPort MediaVPs
  'PVI Karnak':'inkarnak',              # v235: karnak.pof, FSPort MediaVPs
  # Inside the Karnak, and the game cannot fly into a station: str16 gets
  # redesigned rather than this hull built (Silvio).
  'Karnak Reactor':'',
  'Terran Asteroid Base':'inastbase',   # v235: Base2R-01.pof, FS2 MediaVPs
  'Vasudan Asteroid Base':'incheops',   # v235: cheops.pof, FSPort MediaVPs
  'TAC 1':'fctac1', 'TC 2':'fctc2', 'TSC 2':'fctsc2', 'TTC 1':'fcttc1',
  'TC-TRI':'fctctri', 'TC-Meson Bomb':'fcmeson', 'SC 5':'fcsc5',
  'SAC 2':'fcsac3',                     # the SAC 3 stands in (Silvio)
  'SAC 3':'fcsac3', 'VC 3':'fcvc3', 'VAC 4':'fcvac4',
  'VAC 5':'fcvac5',
}

def base(name):
    """The class without its FRED variant and without a note in brackets."""
    return name.split('#')[0].split('(')[0].strip()

# The eight hulls FS3 is still missing, and what needs them. A class whose
# entry is None is one of these: the table says "wanted", not "unknown".
# Which mission needs a hull that is still missing. v235: empty - all eight
# that stood here are built, and every one of the 3844 ships in the 83
# missions now has a hull. The dict stays, because the next hull that turns
# up belongs in it rather than in a comment.
WANTED = {}

def hull_of(name):
    """The FS3 hull for a class. '' where none is needed or wanted, None
    where the hull is still missing, and the class is not in the table at all
    only if it raises a KeyError - which report() reports."""
    b = base(name)
    if b not in HULL:
        raise KeyError(b)
    return HULL[b]

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
        try:
            h = hull_of(c)
        except KeyError:
            unknown += n; missing_table[base(c)] += n; continue
        if h is None:
            nohull += n; missing_hull[base(c)] += n
        elif h == '':
            known += n          # nothing to draw, and nothing wanted
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
        print('\nRuempfe, die FS3 noch fehlen (Silvio zieht die Modelle, v233):')
        for c, n in missing_hull.most_common():
            print('  %-24s %3d Schiffe   fuer %s' % (c, n, WANTED.get(c, '?')))
    return 1 if (bad or missing_table) else 0

if __name__ == '__main__':
    if '--klassen' in sys.argv:
        sys.exit(report_classes())
    print(__doc__)
