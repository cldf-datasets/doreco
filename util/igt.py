import re
import decimal

from pyigt.igt import NON_OVERT_ELEMENT
from pyigt.lgrmorphemes import MORPHEME_SEPARATORS, split_morphemes
from pyigt import IGT


# bora: translations in spanish -> raw/languages.csv:Translation
# even1259 : russian! not english, as claimed in languages.csv!
# sout2856: "§ 014-002" prefixes (and infixes) for tx
# apah: tx: "(\<+)(x+)(\>+)", e.g. "<<xxx>>" meaning what?

def fix_text(s, type_, gc):
    s = s.strip()
    for m, repl in {'â\x80\x9d': '”', 'â\x80\x9c': '“', '\u200e\u200e': ''}.items():
        s = s.replace(m, repl)

    if gc == 'bain1259' and type_ == 'ft' and '|' in s:
        # bain1259: "french | english" translations, separated by pipe.
        french, _, s = s.partition('|')
        s = s.strip()

    if (gc == 'bain1259' or gc == 'anal1239' or gc == 'beja1238') and type_ == 'tx':
        # beja1238: tx ends with / or //
        while s.endswith('/'):
            s = s[:-1].strip()

    if type_ == 'ft':
        # movi: leading and trailing "'" for translation
        # pnar: translations in `...'  , ft may be EMPTY
        if s.startswith("'") and s.endswith("'"):
            s = s[1:-1].strip()
        elif s.startswith("`") and s.endswith("'"):
            s = s[1:-1].strip()
        # FIXME:
        # arap1274: leading "“", trailing "”"
        if s == 'EMPTY':
            s = ''

    # Normalize whitespace!
    s = re.sub(r'\s+', ' ', s)
    return s


def harmonize_separators(morphemes, glosses):
    #
    # Combine morphemes and morpheme glosses at the same time, giving explicit morpheme
    # separators precedence. E.g.

    # anē=n
    # DEM1.A-ART

    # should be

    # anē=n
    # DEM1.A=ART
    #
    nms, ngs = [], []
    for morpheme, gloss in zip(morphemes, glosses):
        mparts = split_morphemes(morpheme)
        gparts = split_morphemes(gloss)
        if len(mparts) == len(gparts):
            for i, sep in enumerate(mparts):
                if i % 2 == 1:  # a separator! copy it over to the gloss parts
                    gparts[i] = sep
            morpheme = ''.join(mparts)
            gloss = ''.join(gparts)
        nms.append(morpheme)
        ngs.append(gloss)
    return nms, ngs


def combine_morphemes(morphemes, type_):
    """
    FIXME:
    goro1270
    tsoobu>-kwí>----dir=í
    liquid.honey>---DemM>---place\LF

    \LF or \F to =LF, =F? or just remove the "="?
    What to do with
    "~$A~","","v Attaches to any category"
    """
    innerhyphen = re.compile(r'([^-]+)-([^-]+)')

    def replace_innerhyphen(s, repl):
        while innerhyphen.search(s):
            s = ''.join(innerhyphen.sub(
                lambda m: '{}{}{}'.format(m.groups()[0], repl, m.groups()[1]), s))
        return s

    word = ''
    for morpheme in morphemes:
        if morpheme:
            # replace inner hyphens!
            morpheme = replace_innerhyphen(morpheme, '.' if type_ == 'g' else '–')
            if word and (not word[-1] in MORPHEME_SEPARATORS) and (not morpheme[0] in MORPHEME_SEPARATORS):
                word += '-'
            word += morpheme
    while word and (word[-1] in MORPHEME_SEPARATORS):
        word = word[:-1]
    while word and word[0] in MORPHEME_SEPARATORS:
        word = word[1:]
    return word.replace('--', '-').replace('=-', '=').replace('==', '=')


def igt(rows, tx, ft, eids, fid):
    gc = rows[0]['Glottocode']
    eids[gc] += 1
    eid = '{}-{}'.format(gc, eids[gc])
    # collect morphemes:
    mbs, gls, mbids = [], [], set()
    #
    # No morphemes, glosses:
    # yong1270
    # tsim1256
    # svan1243
    # sout3282 (no morphemes, but word glosses)
    # sadu1234
    # resi1247
    # lowe1385
    # kark1256
    # anal1239
    #
    for row in rows:
        agg, gl = [], []
        for mb, g, mbid in zip(row['mb'].split(), row['gl'].split(), row['mb_ID'].split()):
            if mbid not in mbids:
                mbids.add(mbid)
                agg.append(mb)
                gl.append(g)
        if agg:
            mbs.append(combine_morphemes(agg, 'm'))
        if gl:
            gls.append(combine_morphemes(gl, 'g'))
    if any(mbs):
        if len(mbs) == len(gls):
            mbs, gls = harmonize_separators(mbs, gls)
        igt = IGT(phrase=mbs, gloss=gls)
        #if not igt.is_valid(strict=True):
        #    inv += 1
        #else:
        #    valid += 1
        res = dict(
            ID=eid,
            Language_ID=gc,
            Primary_Text=tx,
            Analyzed_Word=[k if k else NON_OVERT_ELEMENT for k in mbs],
            Gloss=[k if k else NON_OVERT_ELEMENT for k in gls],
            LGR_Conformance=igt.conformance.name,
            Translated_Text=ft,
            start=decimal.Decimal(rows[0]["start"]),
            end=decimal.Decimal(rows[-1]["end"]),
            File_ID=fid,
        )
        res['duration'] = res['end'] - res['start']
        return res
# 'â\x80\x9c': '“'
# aggregate mb vi mb_ID from word in rows!
#
