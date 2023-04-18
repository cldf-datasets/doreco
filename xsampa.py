"""
https://en.wikipedia.org/wiki/X-SAMPA
http://clarin.phonetik.uni-muenchen.de/BASWebServices/services/runMAUSGetInventar?LANGUAGE=sampa

Notes:

- The IPA symbols that are ordinary lower case letters have the same value in X-SAMPA as they do in
  the IPA.
- X-SAMPA uses backslashes as modifying suffixes to create new symbols. For example, O is a distinct
  sound from O\, to which it bears no relation. Such use of the backslash character can be a
  problem, since many programs interpret it as an escape character for the character following it.
  For example, such X-SAMPA symbols do not work in EMU, so backslashes must be replaced with some
  other symbol (e.g., an asterisk: '*') when adding phonemic transcription to an EMU speech
  database. The backslash has no fixed meaning.
- X-SAMPA diacritics follow the symbols they modify. Except for
  - ~ for nasalization,
  - = for syllabicity, and
  - ` for retroflexion and rhotacization,
  diacritics are joined to the character with the underscore character _.
- The underscore character is also used to encode the IPA tiebar: k_p codes for /k͡p/.
- The numbers _1 to _6 are reserved diacritics as shorthand for language-specific tone numbers.
"""
import collections

SYMBOLS = {
    "a": "a",  # Xsampa-a.png 	open front unrounded vowel 	French dame [dam]
    "b": "b",  # Xsampa-b.png 	voiced bilabial plosive 	English bed [bEd], French bon [bO~]
    "b_<": "ɓ",  # Xsampa-b lessthan.png 	voiced bilabial implosive 	Sindhi ɓarʊ [b_<arU]
    "c": "c",  # Xsampa-c.png 	voiceless palatal plosive 	Hungarian latyak ["lQcQk]
    "d": "d",  # Xsampa-d.png 	voiced alveolar plosive 	English dig [dIg], French doigt [dwa]
    "d`": "ɖ",  # Xsampa-d'.png 	voiced retroflex plosive 	Swedish hord [hu:d`]
    "d_<": "ɗ",  # Xsampa-d lessthan.png 	voiced alveolar implosive 	Sindhi ɗarʊ [d_<arU]
    "e": "e",  # Xsampa-e.png 	close-mid front unrounded vowel 	French blé [ble]
    "f": "f",  # Xsampa-f2.png 	voiceless labiodental fricative 	English five [faIv], French femme [fam]
    "g": "ɡ",  # Xsampa-g.png 	voiced velar plosive 	English game [geIm], French longue [lO~g]
    "g_<": "ɠ",  # Xsampa-g lessthan.png 	voiced velar implosive 	Sindhi ɠəro [g_<@ro]
    "h": "h",  # Xsampa-h.png 	voiceless glottal fricative 	English house [haUs]
    "h\\": "ɦ",  # Xsampa-hslash.png 	voiced glottal fricative 	Czech hrad [h\rat]
    "i": "i",  # Xsampa-i.png 	close front unrounded vowel 	English be [bi:], French oui [wi], Spanish si [si]
    "j": "j",  # Xsampa-j2.png 	palatal approximant 	English yes [jEs], French yeux [j2]
    "j\\": "ʝ",  # Xsampa-jslash2.png 	voiced palatal fricative 	Greek γειά [j\a]
    "k": "k",  # Xsampa-k.png 	voiceless velar plosive 	English scat [sk{t], Spanish carro ["karo]
    "l": "l",  # Xsampa-l.png 	alveolar lateral approximant 	English lay [leI], French mal [mal]
    "l`": "ɭ",  # Xsampa-l'.png 	retroflex lateral approximant 	Svealand Swedish sorl [so:l`]
    "l\\": "ɺ",  # Xsampa-lslash.png 	alveolar lateral flap 	Wayuu püülükü [pM:l\MkM]
    "m": "m",  # Xsampa-m.png 	bilabial nasal 	English mouse [maUs], French homme [Om]
    "n": "n",  # Xsampa-n.png 	alveolar nasal 	English nap [n{p], French non [nO~]
    "n`": "ɳ",  # Xsampa-n'.png 	retroflex nasal 	Swedish hörn [h2:n`]
    "o": "o",  # Xsampa-o.png 	close-mid back rounded vowel 	French veau [vo]
    "p": "p",  # Xsampa-p.png 	voiceless bilabial plosive 	English speak [spik], French pose [poz], Spanish perro ["pero]
    "p\\": "ɸ",  # Xsampa-pslash.png 	voiceless bilabial fricative 	Japanese fuku [p\M_0kM]
    "q": "q",  # Xsampa-q.png 	voiceless uvular plosive 	Arabic qasbah ["qQs_Gba]
    "r": "r",  # Xsampa-r.png 	alveolar trill 	Spanish perro ["pero]
    "r`": "ɽ",  # Xsampa-r'.png 	retroflex flap 	Bengali gari [gar`i:]
    "r\\": "ɹ",  # Xsampa-rslash2.png 	alveolar approximant 	English red [r\Ed]
    "r\`": "ɻ",  # Xsampa-rslash'.png 	retroflex approximant 	Malayalam വഴി ["v@r\`i]
    "s": "s",  # Xsampa-s.png 	voiceless alveolar fricative 	English seem [si:m], French session [sE"sjO~]
    "s`": "ʂ",  # Xsampa-s'.png 	voiceless retroflex fricative 	Swedish mars [mas`]
    "s\\": "ɕ",  # Xsampa-sslash.png 	voiceless alveolo-palatal fricative 	Polish świerszcz [s\v'ers`ts`]
    "t": "t",  # Xsampa-t.png 	voiceless alveolar plosive 	English stew [stju:], French raté [Ra"te]
    "t`": "ʈ",  # Xsampa-t'.png 	voiceless retroflex plosive 	Swedish mört [m2t`]
    "u": "u",  # Xsampa-u.png 	close back rounded vowel 	English boom [bu:m], Spanish su [su]
    "v": "v",  # Xsampa-v.png 	voiced labiodental fricative 	English vest [vEst], French voix [vwa]
    "v\\": "ʋ",  # Xsampa-Porvslash.png 	labiodental approximant 	Dutch west [v\Est]/[PEst]
    "w": "w",  # Xsampa-w2.png 	labial-velar approximant 	English west [wEst], French oui [wi]
    "x": "x",  # Xsampa-x.png 	voiceless velar fricative 	Scots loch [lOx] or [5Ox]; German Buch, Dach; Spanish caja, gestión
    "x\\": "ɧ",  # Xsampa-xslash2.png 	voiceless palatal-velar fricative 	Swedish sjal [x\A:l]
    "y": "y",  # Xsampa-y.png 	close front rounded vowel 	French tu [ty] German über ["y:b6]
    "z": "z",  # Xsampa-z.png 	voiced alveolar fricative 	English zoo [zu:], French azote [a"zOt]
    "z`": "ʐ",  # Xsampa-z'.png 	voiced retroflex fricative 	Mandarin Chinese rang [z`aN]
    "z\\": "ʑ",  # Xsampa-zslash.png 	voiced alveolo-palatal fricative 	Polish źrebak ["z\rEbak]


    "A": "ɑ",  # Xsampa-A2.png 	open back unrounded vowel 	English father ["fA:D@(r\)] (RP and Gen.Am.)
    "B": "β",  # Xsampa-B2.png 	voiced bilabial fricative 	Spanish lavar [la"Ba4]
    "B\\": "ʙ",  # Xsampa-Bslash.png 	bilabial trill 	Reminiscent of shivering ("brrr")
    "C": "ç",  # Xsampa-C2.png 	voiceless palatal fricative 	German ich [IC], English human ["Cjum@n] (broad transcription uses [hj-])
    "D": "ð",  # Xsampa-D2.png 	voiced dental fricative 	English then [DEn]
    "E": "ɛ",  # Xsampa-E2.png 	open-mid front unrounded vowel 	French même [mE:m], English met [mEt] (RP and Gen.Am.)
    "F": "ɱ",  # Xsampa-F.png 	labiodental nasal 	English emphasis ["EFf@sIs] (spoken quickly, otherwise uses [Emf-])
    "G": "ɣ",  # Xsampa-G2.png 	voiced velar fricative 	Greek γωνία [Go"nia]
    "G\\": "ɢ",  # Xsampa-Gslash.png 	voiced uvular plosive 	Inuktitut nirivvik [niG\ivvik]
    "G\\_<": "ʛ",  # Xsampa-Gslash lessthan.png 	voiced uvular implosive 	Mam ʛa [G\_<a]
    "H": "ɥ",  # Xsampa-H.png 	labial-palatal approximant 	French huit [Hit]
    "H\\": "ʜ",  # Xsampa-Hslash.png 	voiceless epiglottal fricative 	Agul мехӀ [mEH\]
    "I": "ɪ",  # Xsampa-I2.png 	near-close front unrounded vowel 	English kit [kIt]
    "I\\": "ᵻ",  # Xsampa-Islash.png 	near-close central unrounded vowel (non-IPA) 	Polish ryba [rI\bA]
    "J": "ɲ",  # Xsampa-J.png 	palatal nasal 	Spanish año ["aJo], English canyon ["k{J@n] (broad transcription uses [-nj-])
    "J\\": "ɟ",  # Xsampa-Jslash.png 	voiced palatal plosive 	Hungarian egy [EJ\]
    "J\\_<": "ʄ",  # Xsampa-Jslash lessthan.png 	voiced palatal implosive 	Sindhi ʄaro [J\_<aro]
    "K": "ɬ",  # Xsampa-K2.png 	voiceless alveolar lateral fricative 	Welsh llaw [KaU]
    "K\\": "ɮ",  # Xsampa-Kslash.png 	voiced alveolar lateral fricative 	Mongolian долоо [tOK\O:]
    "L": "ʎ",  # Xsampa-L2.png 	palatal lateral approximant 	Italian famiglia [fa"miLLa], Castilian llamar [La"mar]
    "L\\": "ʟ",  # Xsampa-Lslash.png 	velar lateral approximant 	Korean 달구지 [t6L\gudz\i]
    "M": "ɯ",  # Xsampa-M.png 	close back unrounded vowel 	Korean 음식 [M:ms\_hik_}]
    "M\\": "ɰ",  # Xsampa-Mslash.png 	velar approximant 	Spanish fuego ["fweM\o]
    "N": "ŋ",  # Xsampa-N2.png 	velar nasal 	English thing [TIN]
    "N\\": "ɴ",  # Xsampa-Nslash.png 	uvular nasal 	Japanese san [saN\]
    "O": "ɔ",  # Xsampa-O2.png 	open-mid back rounded vowel 	American English off [O:f]
    "O\\": "ʘ",  # Xsampa-Oslash.png 	bilabial click
    "P": "ʋ",  # Xsampa-Porvslash.png 	labiodental approximant 	Dutch west [v\Est]/[PEst]
    "Q": "ɒ",  # Xsampa-Q.png 	open back rounded vowel 	RP lot [lQt]
    "R": "ʁ",  # Xsampa-R2.png 	voiced uvular fricative 	German rein [RaIn]
    "R\\": "ʀ",  # Xsampa-Rslash.png 	uvular trill 	French roi [R\wa]
    "S": "ʃ",  # Xsampa-S2.png 	voiceless postalveolar fricative 	English ship [SIp]
    "T": "θ",  # Xsampa-T2.png 	voiceless dental fricative 	English thin [TIn]
    "U": "ʊ",  # Xsampa-U2.png 	near-close back rounded vowel 	English foot [fUt]
    "U\\": "ᵿ",  # Xsampa-Uslash.png 	near-close central rounded vowel (non-IPA) 	English euphoria [jU\"fO@r\i@]
    "V": "ʌ",  # Xsampa-V.png 	open-mid back unrounded vowel 	Scottish English strut [str\Vt]
    "W": "ʍ",  # Xsampa-X.png 	voiceless labial-velar fricative 	Scots when [WEn]
    "X": "χ",  # Xsampa-x2.png 	voiceless uvular fricative 	Klallam sχaʔqʷaʔ [sXa?q_wa?]
    "X\\": "ħ",  # Xsampa-Xslash.png 	voiceless pharyngeal fricative 	Arabic <ح>ha’ [X\A:]
    "Y": "ʏ",  # Xsampa-Y2.png 	near-close front rounded vowel 	German hübsch [hYpS]
    "Z": "ʒ",  # Xsampa-Z2.png 	voiced postalveolar fricative 	English vision ["vIZ@n]
    "ts": "ts",
    "ts\\": "tsʲ",  # FIXME: check!
    "tS": "tʃ",
    "dZ": "dz",  # FIXME: check!
    "n_p": "ⁿpʲ",  # FIXME: check!
    "tK": "tɬ",  # voiceless alveolar lateral affricate
    "t:S": "tʃː",
    "t:s": "tsː",


    # other symbols:

    ".": ".",  # Xsampa-fullstop.png 	syllable break
    "\"": "ˈ",  # Xsampa-doublequotes.png 	primary stress
    "%": "ˌ",  # Xsampa-percentage.png 	secondary stress 	American English pronunciation [pr\@%nVn.si."eI.S@n]
    "' (or     _j)": "ʲ",  # Xsampa-'or
    ":\\": "ˑ",  # Xsampa-colonslash.png 	half long 	Estonian differentiates three vowel lengths
#- 		  	separator 	Polish trzy [t-S1] vs. czy [tS1] (affricate)
    "@": "ə",  # Xsampa-at.png 	schwa  English arena [@"r\i:n@]
    "@\\": "ɘ",  # Xsampa-atslash.png 	close-mid central unrounded vowel 	Paicĩ kɘ̄ɾɘ [k@\_M4@\_M]
    "@`": "ɚ",  # Xsampa-at'.png 	r-coloured schwa 	American English color ["kVl@`]
    "{": "æ",  # Xsampa-leftcurly.png 	near-open front unrounded vowel 	English trap [tr\{p]
    "}": "ʉ",  # Xsampa-rightcurly.png 	close central rounded vowel 	Swedish sju [x\}:]; AuE/NZE boot [b}:t]
    "1": "ɨ",  # Xsampa-1.png 	close central unrounded vowel 	Welsh tu [t1], American English rose's ["r\oUz1z]
    "2": "ø",  # Xsampa-2.png 	close-mid front rounded vowel 	Danish købe ["k2:b@], French deux [d2]
    "3": "ɜ",  # Xsampa-3.png 	open-mid central unrounded vowel 	English nurse [n3:s] (RP) or [n3`s] (Gen.Am.)
    "3\\": "ɞ",  # Xsampa-3slash.png 	open-mid central rounded vowel 	Irish tomhail [t3\:l']
    "4": "ɾ",  # Xsampa-4.png 	alveolar flap 	Spanish pero ["pe4o], American English better ["bE4@`]
    "5": "ɫ",  # Xsampa-l eor5.png 	velarized alveolar lateral approximant; also see _e 	English milk [mI5k], Portuguese livro ["5iv4u]
    "6": "ɐ",  # Xsampa-6.png 	near-open central vowel 	German besser ["bEs6], Australian English mud [m6d]
    "7": "ɤ",  # Xsampa-7.png 	close-mid back unrounded vowel 	Estonian kõik [k7ik], Vietnamese mơ [m7_M]
    "8": "ɵ",  # Xsampa-8.png 	close-mid central rounded vowel 	Swedish buss [b8s]
    "9": "œ",  # Xsampa-9.png 	open-mid front rounded vowel 	French neuf [n9f], Danish drømme [dR9m@]
    "&": "ɶ",  # Xsampa-amper.png 	open front rounded vowel 	Swedish skörd [x\&d`]
    "?": "ʔ",  # Xsampa-questionmark.png 	glottal stop 	Cockney English bottle ["bQ?o]
    "?\\": "ʕ",  # Xsampa-qmarkslash.png 	voiced pharyngeal fricative 	Arabic ع (`ayn) [?\Ajn]
#* 		  	undefined escape character, SAMPA's "conjunctor"
#/ 		  	(a) French vowel archiphonemes or indeterminacies
#(b) delimiter of phonemic transcriptions 	maison /mE/zO~/
#< 		  	begin nonsegmental notation, e.g., SAMPROSA[3]
    r"<\\": "ʢ",  # Xsampa-lessthanslash.png 	voiced epiglottal fricative 	Siwi arˤbˤəʢa (four) [ar_?\b_?\@<\a]
#> 		  	end nonsegmental notation
    ">\\": "ʡ",  # Xsampa-greaterthanslash.png 	epiglottal plosive 	Archi гӀарз (complaint) [>\arz]
    "^": "ꜛ",  # Xsampa-hat.png 	upstep
    "!": "ꜜ",  # Xsampa-exclamation.png 	downstep
    "!\\": "ǃ",  # Xsampa-exclamationslash.png 	postalveolar click 	Zulu iqaqa (polecat) [i:!\a:!\a]
    "|": "|",  # Xsampa-bar.png 	minor (foot) group
    "|\\": "ǀ",  # Xsampa-barslash.png 	dental click 	Zulu icici (earring) [i:|\i:|\i]
    "||": "‖",  # Xsampa-doublebar.png 	major (intonation) group
    "|\\|\\": "ǁ",  # Xsampa-doublebarslash.png 	alveolar lateral click 	Zulu xoxa (to converse) [|\|\O:|\|\a]
    "=\\": "ǂ",  # Xsampa-equalsslash.png 	palatal click
    "-\\": "‿",  # Xsampa-dashslash.png 	linking mark
}
DIACRITICS = {
    ":": "ː",  # Xsampa-colon.png 	long
    '~': '̃ ',  # nasalization
    "_h": "ʰ",  # Xsampa- h.png 	aspirated
    "_j": "ʲ",  # Xsampa-'or j.png 	palatalized
    "'": "ʲ",  # Xsampa-'or j.png 	palatalized
    "_r": "̝",  # Xsampa- r.png 	raised
    "_w": "ʷ",  # Xsampa- w.png 	labialized
    "_>": "ʼ",  # Xsampa- greaterthan.png 	ejective
    "=": "̩",  # Xsampa-equalsor equals.png 	syllabic
    "_=": "̩",  # Xsampa-equalsor equals.png 	syllabic
    "_d": "̪",  # Xsampa- d.png 	dental
    "_o": "̞",  # Xsampa- o.png 	lowered
    "_0": "̥",  # Xsampa- 0.png 	voiceless
    "_?\\": "ˤ",  # Xsampa- questionslash.png 	pharyngealized
    "`": "˞",  # Xsampa-'rhino.png rhotacization in vowels, retroflexion in consonants
    # (IPA uses separate symbols for consonants, see t` for an example)
    "_t": "̤",  # Xsampa- t.png 	breathy voice
    "_+": "̟",  # Xsampa- plus.png 	advanced
}
"""
# diacritics:

_" 	  ̈ 	Xsampa- doublequotes.png 	centralized
_- 	  ̠ 	Xsampa- minus.png 	retracted
_/ 	  ̌ 	Xsampa- slash.png 	rising tone
_< 		  	implosive (IPA uses separate symbols for implosives)
_\ 	  ̂ 	  	falling tone
_^ 	  ̯ 	Xsampa- hat.png 	non-syllabic
_} 	  ̚ 	Xsampa- rightcurly.png 	no audible release
~ (or _~) 	  ̃ 	Xsampa-tildor tild.png 	nasalization
_A 	  ̘ 	Xsampa- A.png 	advanced tongue root
_a 	  ̺ 	Xsampa- a2.png 	apical
_B 	  ̏ 	Xsampa- B.png 	extra low tone
_B_L 	 ᷅ 	Xsampa- B L.png 	low rising tone
_c 	  ̜ 	Xsampa- c.png 	less rounded
_e 	  ̴ 	Xsampa- e.png 	velarized or pharyngealized; also see 5
    r"<F>": "↘",  # Xsampa-ltFgt.png 	global fall
_F 	  ̂ 	Xsampa- F.png 	falling tone
    r"_G": "ˠ",  # Xsampa- G.png 	velarized
_H 	  ́ 	Xsampa- H.png 	high tone
_H_T 	 ᷄ 	Xsampa- H T.png 	high rising tone
_k 	  ̰ 	Xsampa- k.png 	creaky voice
_L 	  ̀ 	Xsampa- L.png 	low tone
    r"_l": "ˡ",  # Xsampa- l.png 	lateral release
_M 	  ̄ 	Xsampa- M.png 	mid tone
_m 	  ̻ 	Xsampa- m.png 	laminal
_N 	  ̼ 	Xsampa- N.png 	linguolabial
    r"_n": "ⁿ",  # Xsampa- n2.png 	nasal release
_O 	  ̹ 	Xsampa O.png 	more rounded
_q 	  ̙ 	Xsampa- q.png 	retracted tongue root
    r"<R>": "↗",  # Xsampa-ltRgt.png 	global rise
_R 	  ̌ 	Xsampa- R.png 	rising tone
_R_F 	 ᷈ 	Xsampa- R F.png 	rising falling tone
_T 	  ̋ 	Xsampa- T.png 	extra high tone
_v 	  ̬ 	Xsampa- v.png 	voiced
_X 	  ̆ 	Xsampa- X.png 	extra-short
_x 	  ̽ 	Xsampa- x.png 	mid-centralized
"""


if __name__ == '__main__':
    from csvw.dsv import reader

    SYMBOLS = collections.OrderedDict(sorted(SYMBOLS.items(), key=lambda i: -len(i[0])))

    def to_ipa(s):
        if s in SYMBOLS:
            return SYMBOLS[s]
        res = ''
        for x, ipa in SYMBOLS.items():
            if s.startswith(x):
                res += ipa
                s = s[len(x):]
                break
        if s in SYMBOLS:
            return res + SYMBOLS[s]
        while any(s.endswith(d) for d in DIACRITICS):
            for d in DIACRITICS:
                if s.endswith(d):
                    res += DIACRITICS[d]
                    s = s[:-len(d)]
                    break
        if not s:
            return res

    for row in reader('etc/orthography.tsv', delimiter='\t', dicts=True):
        ipa = to_ipa(row['Grapheme'])
        if ipa is None:
            pass
            #print(row)
            #break
        print('{}\t{}\t{}'.format(row['Grapheme'], ipa or '', row['Frequency']))
