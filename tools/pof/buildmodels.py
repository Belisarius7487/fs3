# All player hulls -> scratchpad/models/<key>/ (v191)
import os, json, glob, sys, time
import webmodel
# MediaVP 4.7.3 root (folders MV_Assets_*, MV_Effects_*); set FS3_MVPS to point elsewhere
M = os.path.join(os.environ.get('FS3_MVPS', '/mnt/user-data/uploads/MVPS-473'), '')
OUT = sys.argv[1] if len(sys.argv) > 1 else '../models'
maps = {}
for f in glob.glob(M + '*/data/maps/*'):
    b = os.path.basename(f); n = b.rsplit('.', 1)[0].lower(); maps[n] = f
HULLS = {
 'fitoth': ('MV_Assets_V', 'Thoth'), 'fihorus': ('MV_Assets_V', 'Horus'), 'boosiris': ('MV_Assets_V', 'Osiris'),
 'fiserapis': ('MV_Assets_V', 'Serapis'), 'fiseth': ('MV_Assets_V', 'Seth'), 'bobakha': ('MV_Assets_V', 'Fighter2V-03'),
 'fitauret': ('MV_Assets_V', 'Tauret'), 'bosekhmet': ('MV_Assets_V', 'Sekhmet'), 'fiptah': ('MV_Assets_V', 'Ptah'),
 'fimyrmidon': ('MV_Assets_T_1', 'Myrmidon'), 'fiperseus': ('MV_Assets_T_1', 'Perseus'), 'fiherc': ('MV_Assets_T_1', 'Hercules'),
 'boartemis': ('MV_Assets_T_1', 'Artemis'), 'fihercmk2': ('MV_Assets_T_1', 'Hercules-2'), 'bomedusa': ('MV_Assets_T_1', 'Medusa'),
 'fierinyes': ('MV_Assets_T_1', 'Erinyes'), 'boursa': ('MV_Assets_T_1', 'Ursa'), 'fiares': ('MV_Assets_T_1', 'Ares'),
 'fipegasus': ('MV_Assets_T_1', 'Pegasus'), 'fiulysses': ('MV_Assets_T_1', 'ulysses'), 'fiapollo': ('MV_Assets_T_1', 'Apollo'),
 'fivalyrie': ('MV_Assets_T_1', 'Valkyrie'), 'boathena': ('MV_Assets_T_1', 'Athena'), 'fimara': ('MV_Assets_S', 'Mara'),
 # support ships (v192)
 'crfenris': ('MV_Assets_T_2', 'Fenris_FS2'), 'crleviathan': ('MV_Assets_T_2', 'Leviathan_FS2'), 'craeolus': ('MV_Assets_T_2', 'Aeolus'),
 'codeimos': ('MV_Assets_T_2', 'Deimos'), 'deorionright': ('MV_Assets_T_2', 'Orion_FS2'), 'dehecate': ('MV_Assets_T_2', 'Hecate'),
 'craten': ('MV_Assets_V', 'Aten'), 'crmentu': ('MV_Assets_V', 'Mentu'), 'cosobek': ('MV_Assets_V', 'Sobek'),
 'detyphon': ('MV_Assets_V', 'Typhon'), 'dehatshepsut': ('MV_Assets_V', 'Capital2V-01'), 'sdcolossus': ('MV_Assets_T_2', 'Colossus'),
 'sgmjolnir': ('MV_Assets_T_1', 'mjolnir'), 'cacharybdis': ('MV_Assets_T_2', 'Charybdis'), 'casetekh': ('MV_Assets_V', 'Setekh'),
 'coiceni': ('MV_Assets_T_2', 'Corvette2R-01'),
 # Shivan capital ships (v197)
 'crcain': ('MV_Assets_S', 'Cain'), 'crlilith': ('MV_Assets_S', 'Lilith'), 'crrakshasa': ('MV_Assets_S', 'Rakshasa'),
 'comoloch': ('MV_Assets_S', 'Moloch'), 'dedemon': ('MV_Assets_S', 'Demon'), 'deravana': ('MV_Assets_S', 'Ravana'),
 'sdlucifer': ('MV_Assets_S', 'Capital02'), 'sdsathanas': ('MV_Assets_S', 'Sathanas')}
# NTF reskins (v201): their own models and maps from the NTF texture mod
HULLS.update({'ntfcraeolus': ('NTF', 'NTFAeolus'), 'ntfcodeimos': ('NTF', 'NTFDeimos'), 'ntfcrfenris': ('NTF', 'NTFFenris'),
              'ntfcrleviathan': ('NTF', 'NTFLeviathan_FS2'), 'ntfdeorion': ('NTF', 'NTFOrion'), 'ntfdehecate': ('NTF', 'NTFHecate')})
# v202: the remaining large hulls - freighters, transports, installations,
# gas miners, the Hades, Faustus and Hippocrates, the Knossos
HULLS.update({
 'sdhades': ('MV_Assets_T_2', 'Hades'), 'scfaustus': ('MV_Assets_T_2', 'Faustus'), 'mehippocrates': ('MV_Assets_T_2', 'Hippocrates'),
 'frasmodeus': ('MV_Assets_S', 'Asmodeus'), 'frbast': ('MV_Assets_V', 'Bast'), 'frbes': ('MV_Assets_V', 'bes'),
 'frchronos': ('MV_Assets_T_1', 'Chronos'), 'frdis': ('MV_Assets_S', 'Dis'), 'frmaat': ('MV_Assets_V', "Ma'at"),
 'frmephisto': ('MV_Assets_S', 'Mephisto'), 'frposeidon': ('MV_Assets_T_1', 'Poseidon'), 'frsatis': ('MV_Assets_V', 'Satis'),
 'frtriton': ('MV_Assets_T_1', 'Triton'),
 'trargo': ('MV_Assets_T_1', 'Argo'), 'trazrael': ('MV_Assets_S', 'Azrael'), 'trelysium': ('MV_Assets_T_1', 'Elysium'),
 'trisis': ('MV_Assets_V', 'Isis'),
 'inarcadia': ('MV_Assets_T_2', 'Arcadia'), 'inpharos': ('MV_Assets_T_1', 'NavBuoy'), 'incommnode': ('MV_Assets_S', 'CommNode'),
 'inknossos': ('MV_Assets_T_2', 'Knossos'),
 'gmanuket': ('MV_Assets_V', 'Anuket'), 'gmrahu': ('MV_Assets_S', 'Rahu'), 'gmzephyrus': ('MV_Assets_T_2', 'Zephyrus')})
# v203: the small craft - the enemy and allied fighters and bombers that
# are no player hull, sentries, support ships, escape pods and containers
HULLS.update({
 'boamun': ('MV_Assets_V', 'Amun'), 'boartemisdh': ('MV_Assets_T_1', 'artemisDH'), 'boboanerges': ('MV_Assets_T_1', 'Boanerges'),
 'bonahema': ('MV_Assets_S', 'Nahema'), 'bonephilim': ('MV_Assets_S', 'Nephilim'), 'boseraphim': ('MV_Assets_S', 'Seraphim'),
 'boshaitan': ('MV_Assets_S', 'Shaitan'), 'botaurvi': ('MV_Assets_S', 'Taurvi'), 'bozeus': ('MV_Assets_T_1', 'Zeus'),
 'ephermes': ('MV_Assets_T_1', 'Hermes'), 'epra': ('MV_Assets_V', 'ra'),
 'fcmeson': ('MV_Assets_T_1', 'TC-Meson'), 'fcsac3': ('MV_Assets_S', 'SAC3'), 'fcsc5': ('MV_Assets_S', 'SC5'),
 'fctac1': ('MV_Assets_T_1', 'TAC1'), 'fctc2': ('MV_Assets_T_1', 'tc2'), 'fctctri': ('MV_Assets_T_1', 'TC-TRI'),
 'fctsc2': ('MV_Assets_T_1', 'tc2x'), 'fcttc1': ('MV_Assets_T_1', 'ttc1'), 'fcvac4': ('MV_Assets_V', 'vac4'),
 'fcvac5': ('MV_Assets_V', 'vac5'), 'fcvc3': ('MV_Assets_V', 'VC3'),
 'fiaeshma': ('MV_Assets_S', 'Aeshma'), 'fianubis': ('MV_Assets_V', 'Anubis'), 'fiastaroth': ('MV_Assets_S', 'Astaroth'),
 'fibasilisk': ('MV_Assets_S', 'basilisk'), 'fidragon': ('MV_Assets_S', 'Dragon'), 'filoki': ('MV_Assets_T_1', 'Loki'),
 'fimanticore': ('MV_Assets_S', 'Manticore'), 'fiscorpion': ('MV_Assets_S', 'Scorpion'),
 'sgalastor': ('MV_Assets_T_1', 'Alastor'), 'sgankh': ('MV_Assets_V', 'Ankh'), 'sgbelial': ('MV_Assets_S', 'Belial'),
 'sgcerberus': ('MV_Assets_T_1', 'Cerberus'), 'sgtrident': ('MV_Assets_S', 'Trident'), 'sgwatchdog': ('MV_Assets_T_1', 'Watchdog'),
 'sucentaur': ('MV_Assets_T_1', 'centaur'), 'suhygeia': ('MV_Assets_T_1', 'Hygeia'), 'sunephthys': ('MV_Assets_V', 'Nephthys'),
 'suscarab': ('MV_Assets_V', 'Scarab')})
# v235: the hulls the original FS1/ST:R/FS2 missions need and FS3 did not
# draw yet. Six come from the FSPort MediaVPs (mv_fsport_47x), the Terran
# asteroid base from the FS2 ones. The POF names are read from the
# $POF file: lines of the base ships.tbl of FSPort and of FS2 retail - not
# guessed - and the lengths in HULL_LEN are measured from each model's own
# bounding box. The NTF Boadicea of FS2 SM1-02 is the SAME model as the
# Terran asteroid base (both Base2r-01), so it has no key of its own.
HULLS.update({
 'fiangel': ('mv_fsport_47x', 'Angel'),
 'scimhotep': ('mv_fsport_47x', 'imhotep'),
 'inkarnak': ('mv_fsport_47x', 'karnak'),
 'inpolaris': ('mv_fsport_47x', 'dock01-terran'),
 'inpolarispylon': ('mv_fsport_47x', 'dock02-terran'),
 'incheops': ('mv_fsport_47x', 'cheops'),
 'inastbase': ('MV_Assets_T_2', 'Base2R-01')})
SMALL_NEW = ['boamun', 'boartemisdh', 'boboanerges', 'bonahema', 'bonephilim', 'boseraphim', 'boshaitan', 'botaurvi', 'bozeus',
 'ephermes', 'epra', 'fcmeson', 'fcsac3', 'fcsc5', 'fctac1', 'fctc2', 'fctctri', 'fctsc2', 'fcttc1', 'fcvac4', 'fcvac5', 'fcvc3',
 'fiaeshma', 'fianubis', 'fiastaroth', 'fibasilisk', 'fidragon', 'filoki', 'fimanticore', 'fiscorpion',
 'sgalastor', 'sgankh', 'sgbelial', 'sgcerberus', 'sgtrident', 'sgwatchdog', 'sucentaur', 'suhygeia', 'sunephthys', 'suscarab']
PLAYER = ['fitoth', 'fihorus', 'boosiris', 'fiserapis', 'fiseth', 'bobakha', 'fitauret', 'bosekhmet', 'fiptah', 'fimyrmidon',
 'fiperseus', 'fiherc', 'boartemis', 'fihercmk2', 'bomedusa', 'fierinyes', 'boursa', 'fiares', 'fipegasus', 'fiulysses',
 'fiapollo', 'fivalyrie', 'boathena', 'fimara']
SHIVAN = ('crcain', 'crlilith', 'crrakshasa', 'comoloch', 'dedemon', 'deravana', 'sdlucifer', 'sdsathanas')
import pof
if __name__ == '__main__':
    index = {}
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    for key, (d, name) in HULLS.items():
        if only and key not in only: continue
        t0 = time.time()
        src = M + d + '/data/models/' + name + '.pof'
        m = pof.read_pof(src)
        skin = {}
        for t in m['textures']:
            tl = t.lower()
            if tl in maps and webmodel.kind_of(t) == 'tex':
                skin[tl] = {'c': maps[tl], 'n': maps.get(tl + '-normal'), 'g': maps.get(tl + '-glow')}
        info = webmodel.convert(src, skin, os.path.join(OUT, key), d0parts=(('subsys' if key in SHIVAN else True) if (key[3:] if key.startswith('ntf') else key)[:2] in ('cr', 'co', 'de', 'sd', 'ca', 'sg') and key not in SMALL_NEW else False))
        sz = sum(os.path.getsize(f) for f in glob.glob(os.path.join(OUT, key, '*')))
        info['bytes'] = sz
        index[key] = info
        print(key, name, info['lod'], info['tex'], round(sz / 1024), 'KB', round(time.time() - t0, 1), 's', flush=True)
    json.dump(index, open(os.path.join(OUT, 'index_build.json'), 'w'), indent=1)
