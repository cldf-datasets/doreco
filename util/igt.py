import re

from pyigt.lgrmorphemes import MORPHEME_SEPARATORS, split_morphemes
from pyigt import IGT


def harmonize_separators(morphemes, glosses):
    #
    # Combine morphemes and morpheme glosses at the same time, giving explicit morpheme
    # saparators precedence. E.g.

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


def igt(rows, tx, ft, eids):
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
        return dict(
            ID=eid,
            Language_ID=gc,
            Primary_Text=tx,
            Analyzed_Word=mbs,
            Gloss=gls,
            Translated_Text=ft,
        )
# 'â\x80\x9c': '“'
# aggregate mb vi mb_ID from word in rows!
#
