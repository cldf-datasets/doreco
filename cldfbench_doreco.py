"""
Filled pause: <<fp>>
False start: <<fs>>
Prolongation: <<pr>>
Foreign material: <<fm>>
Singing: <<sg>>
Backchannel: <<bc>>
Ideophone: <<id>>
Onomatopoeic: <<on>>
Word-internal pause: <<wip>>
Unidentifiable: <<ui>>
Silent pause: <p:>

Labels consist of two opening brackets, the label proper, a closing bracket, the content (optional),
and another closing bracket, e.g. <<ui>word>. Labels may also appear on their own if the content is
not known, e.g. <<ui>>. Silent pauses are marked by a special symbol, <p:>. The location of silent
pauses is manually checked by the DoReCo team, while the symbol itself is inserted by the WebMAUS
service. Unlike the other labels, the <p:> symbol has only one of each bracket, and no other
content may be included in it.
"""
import collections
import re
import decimal
import pathlib
import itertools
import urllib.parse

import requests
from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec
import pybtex.database
from pyigt.lgrmorphemes import MORPHEME_SEPARATORS, split_morphemes
from pyigt import IGT

NAKALA_API = 'https://api.nakala.fr/'

# bora: translations in spanish -> raw/languages.csv:Translation
# even1259 : russian! not english, as claimed in languages.csv!
# sout2856: "§ 014-002" prefixes (and infixes) for tx
# apah: tx: "(\<+)(x+)(\>+)", e.g. "<<xxx>>" meaning what?

def fix_text(s, type_, gc):
    s = s.strip()
    for m, repl in {
        'â\x80\x9d': '”',
        'â\x80\x9c': '“',
        #<200e><200e>
        '\u200e\u200e': '',
    }.items():
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


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "doreco"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(
                dir=self.cldf_dir, 
                module='Generic'
                )

    def cmd_download(self, args):
        self.raw_dir.download(
            'https://sharedocs.huma-num.fr/wl/?id=s947TcfRfDZR643QURdyncdku4EmeKyb&fmode=download',
            'languages.csv')
        self.raw_dir.download(
            'https://sharedocs.huma-num.fr/wl/?id=xqkUR3WoFOKB8cRb0MdHYJxIDEXEXlVG&fmode=download',
            'sources.bib')

        for row in self.raw_dir.read_csv('languages.csv', dicts=True):
            if 'ND' not in row['Annotation license']:
                print(row['Glottocode'], row['DOI'])
                cid = urllib.parse.quote(row['DOI'], safe='')
                for f in requests.get("{}datas/{}?metadata-format=dc".format(NAKALA_API, cid)).json()['files']:
                    for s in ['_wd.csv', '_ph.csv', '_metadata.csv', '_gloss-abbreviations.csv']:
                        if f['name'].endswith(s):
                            print(f['name'], f['sha1'])
                            self.raw_dir.download('{}data/{}/{}'.format(NAKALA_API, cid, f['sha1']), '{}{}'.format(row['Glottocode'], s))
                            break

    def iter_rows(self, pattern):
        for p in sorted(self.raw_dir.glob(pattern), key=lambda pp: pp.name):
            for row in self.raw_dir.read_csv(p.name, dicts=True):
                row.setdefault('Glottocode', p.name.partition('_')[0])
                if '_wd' in pattern or ('_ph' in pattern):
                    # doreco-mb-algn and mc-zero col missing in some files of _ph
                    row.setdefault('doreco-mb-algn', '')
                    row.setdefault('mc-zero', '')
                for k in ['ft', 'tx']:
                    if k in row:
                        row[k] = fix_text(row[k], k, row['Glottocode'])
                yield row

    def cmd_makecldf(self, args):
        self.create_schema(args.writer.cldf)

        args.writer.cldf.add_sources(pybtex.database.parse_string(
            self.raw_dir.joinpath('sources.bib').read_text(encoding='utf8'),
            bib_format='bibtex',
        ))
        args.log.info("added sources")
        inv, valid = 0, 0

        for row in self.raw_dir.read_csv('languages.csv', dicts=True):
            args.writer.objects["LanguageTable"].append({
                "ID": row["Glottocode"],
                "Name": row["Language"],
                "Glottocode": row["Glottocode"],
                "Latitude": row["Latitude"],
                "Longitude": row["Longitude"],
                "Macroarea": row["Area"],
                "Source": "doreco-" + row["Glottocode"],
                "Translation": row["Translation"],
                "Gloss": row["Gloss"],
                "ExtendedSpeakers": row["Extended speakers"],
                "ExtendedWordTokens": row["Extended word tokens"],
                "ExtendedTexts": row["Extended texts"],
                "CoreSpeakers": row["Core speakers"],
                # inconsistent caps in core/Core in original file
                "CoreWordTokens": row["core word tokens"],
                "CoreTexts": row["Core texts"],
                "YearsOfRecordingsInCoreSet": row["Years of recordings in core set"]
            })

            args.writer.objects["ContributionTable"].append({
                "ID": row["Glottocode"],
                "Name": row["Language"],
                "Contributor": row["Creator"],
                "Archive": row["Archive"],
                "Archive_link": row["Archive_link"],
                "AnnotationLicense": row["Annotation license"],
                "AudioLicense": row["Audio license"],
                "DOI": row["DOI"]
            })
        args.log.info("added languages and contributions")

        for i, row in enumerate(self.iter_rows('*_metadata.csv'), start=1):
            args.writer.objects["metadata.csv"].append({
                "ID": row["Glottocode"] + "_" + row["id"],
                "Filename": "doreco_" + row["Glottocode"] + "_" + row["name"],
                "spk_code": row["spk_code"],
                "spk_age": row["spk_age"],
                "spk_age_c": row["spk_age_c"],
                "spk_sex": row["spk_sex"],
                "rec_date": row["rec_date"],
                "rec_date_c": row["rec_date_c"],
                "genre": row["genre"],
                "genre_stim": row["genre_stim"],
                "gloss": row["gloss"],
                "transl": row["transl"],
                "sound_quality": row["sound_quality"],
                "background_noise": row["background_noise"],
                "word_tokens": row["word_tokens"],
                "extended": row["extended"],
                "Glottocode": row["Glottocode"]
            })

        for i, row in enumerate(self.iter_rows('*_gloss-abbreviations.csv'), start=1):
            args.writer.objects["glosses.csv"].append({
                "ID": row['Glottocode'] + str(i),
                "Gloss": row["Gloss"],
                "LGR": row["LGR"],
                "Meaning": row["Meaning"],
                "Glottocode": row["Glottocode"]
            })

        wd_intervals = {}
        eids = collections.defaultdict(int)
        for (f, tx, ft), rows in itertools.groupby(self.iter_rows('*_wd.csv'), lambda r: (r['file'], r['tx'], r['ft'])):
            rows = list(rows)
            gc = rows[0]['Glottocode']
            eid = None
            # Create an entry in ExampleTable if tx not in ['', None, '****', '<p:>']
            if tx and (ft not in ['', None, '****', '<p:>']):
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
                    if not igt.is_valid(strict=True):
                        inv += 1
                        print(gc)
                        print(tx)
                        print('\t'.join(mbs))
                        print('\t'.join(gls))
                        print(ft)
                    else:
                        valid += 1
                if eids[gc] <= 10:
                    args.writer.objects['ExampleTable'].append(dict(
                        ID=eid,
                    Language_ID=gc,
                    Primary_Text=tx,
                    Analyzed_Word=mbs,
                    Gloss=gls,
                    Translated_Text=ft,
                    ))
                else:
                    eid = None
            #'â\x80\x9c': '“'
            # aggregate mb vi mb_ID from word in rows!
            #

            for row in rows:
                args.writer.objects["words.csv"].append({
                "Language_ID": row["lang"],
                "Filename": row["file"],
                # "core_extended": row["core_extended"],
                "speaker": row["speaker"],
                "Example_ID": eid,
                "wd_ID": row["lang"] + "_" + row["wd_ID"],
                "wd": row["wd"],
                "start": decimal.Decimal(row["start"]),
                "end": decimal.Decimal(row["end"]),
                "ref": row["ref"],
                "tx": row["tx"],
                "ft": row["ft"],
                # FIXME: mb_ID is a whitespace-separated list of IDs
                #"mb_ID": row["lang"] + "_" + row["mb_ID"],
                #"mb": row["mb"],
                #"doreco-mb-algn": row["doreco-mb-algn"],
                # FIXME: add ps and gl to ExampleTable!
                #"ps": row["ps"],
                #"gl": row["gl"],
                "ph_ID": row["lang"] + "_" + row["ph_ID"],
                "ph": row["ph"]
                })
                wd_intervals[row["lang"] + "_" + row["wd_ID"]] = (decimal.Decimal(row["start"]), decimal.Decimal(row["end"]))

        misaligned_start, max_misalignment = [], decimal.Decimal('0')
        for wid, rows in itertools.groupby(self.iter_rows('*_ph.csv'), lambda r: r['wd_ID']):
            rows = list(rows)
            for i, row in enumerate(rows):
                if i == 0:
                    try:
                        ps = decimal.Decimal(row["start"])
                        ws = wd_intervals[row['Glottocode'] + '_' + wid][0]
                        assert ps >= ws
                        if ps > ws:
                            misaligned_start.append((row['Glottocode'], ps - ws, row['wd'], [r['ph'] for r in rows]))
                            if ps - ws > max_misalignment:
                                max_misalignment = ps - ws
                    except:
                        print(decimal.Decimal(row["start"]), wd_intervals[row['Glottocode'] + '_' + wid][0])
                        raise
                if i == len(rows) - 1:
                    pe = decimal.Decimal(row["end"])
                    we = wd_intervals[row['Glottocode'] + '_' + wid][1]
                    assert pe <= we
                    #if pe < we:
                    #    misaligned_start.append((row['Glottocode'], row['wd']))
                if 0 < i < len(rows):
                    try:
                        assert decimal.Decimal(row["start"]) >= args.writer.objects["phones.csv"][-1]['end']
                    except:
                        if row['ph'] != '****':
                            print(row['Glottocode'], wid, args.writer.objects["phones.csv"][-1]['ph_ID'], row['ph_ID'])
                            print(args.writer.objects["phones.csv"][-1]['end'], decimal.Decimal(row["start"]))
                        continue

                args.writer.objects["phones.csv"].append({
                "Language_ID": row["lang"],
                "Filename": row["file"],
                # "core_extended": row["core_extended"],
                "speaker": row["lang"] + "_" + row["speaker"],
                "ph_ID": row["lang"] + "_" + row["ph_ID"],
                "ph": row["ph"],
                "start": decimal.Decimal(row["start"]),
                "end": decimal.Decimal(row["end"]),
                #"duration": int(re.sub(r"\.", "", row["end"])) - int(re.sub(r"\.", "", row["start"])),
                # "ref": row["ref"],
                # "tx": row["tx"],
                # "ft": row["ft"],
                "wd_ID": row["lang"] + "_" + row["wd_ID"],
                # "wd": row["wd"],
                # "mb_ID": row["mb_ID"],
                # "mb": row["mb"],
                # "doreco-mb-algn": row["doreco-mb-algn"],
                # "ps": row["ps"],
                # "gl": row["gl"]
                })
        #for cid, forms in itertools.groupby(misaligned_start, lambda i: i[0]):
        #    forms = list(forms)
        #    print(cid, len(forms))
        #    for f in forms[:10]:
        #        print(f[1:])
        #print(len(misaligned_start))
        #print(max_misalignment)

        print(inv, valid)

    def create_schema(self, cldf):
        cldf.add_component('ExampleTable')
        cldf['ExampleTable', 'Analyzed_Word'].separator = '\t'
        cldf['ExampleTable', 'Gloss'].separator = '\t'
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Source',
                'datatype': 'string',
            },
            {
                'name': 'Translation',
                'datatype': 'string',
            },
            {
                'name': 'Gloss',
                'datatype': 'string',
            },
            {
                'name': 'ExtendedSpeakers',
                'datatype': 'int',
            },
            {
                'name': 'ExtendedWordTokens',
                'datatype': 'int',
            },
            {
                'name': 'ExtendedTexts',
                'datatype': 'int',
            },
            {
                'name': 'CoreSpeakers',
                'datatype': 'int',
            },
            {
                'name': 'CoreWordTokens',
                'datatype': 'int',
            },
            {
                'name': 'CoreTexts',
                'datatype': 'int',
            },
            {
                'name': 'YearsOfRecordingInCoreSet',
                'datatype': 'string',
            })

        cldf.add_component(
            'ContributionTable',
            {
                'name': 'Archive',
                'datatype': 'string',
            },
            {
                'name': 'Archive_link',
                'datatype': 'string',
            },
            {
                'name': 'AnnotationLicense',
                'datatype': 'string',
            },
            {
                'name': 'AudioLicense',
                'datatype': 'string',
            },
            {
                'name': 'DOI',
                'datatype': 'string',
            },
        )

        cldf.add_table(
            'phones.csv',
            {
                'name': 'Language_ID',
                'datatype': 'string',
            },
            {
                'name': 'Filename',
                'datatype': 'string',
            },
            {
                'name': 'speaker',
                'datatype': 'string',
            },
            {
                'name': 'ph_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'ph',
                'datatype': 'string',
            },
            {
                'name': 'start',
                'datatype': 'decimal',
            },
            {
                'name': 'end',
                'datatype': 'decimal',
            },
            #{
            #    'name': 'duration',
            #    'datatype': 'string',
            #},
            # {
            #     'name': 'ref',
            #     'datatype': 'str',
            # },
            # {
            #     'name': 'tx',
            #     'datatype': 'str',
            # },
            # {
            #     'name': 'ft',
            #     'datatype': 'str',
            # },
            {
                'name': 'wd_ID',
                'datatype': 'string',
            },
            # {
            #     'name': 'wd',
            #     'datatype': 'str',
            # },
            # {
            #     'name': 'mb_ID',
            #     'datatype': 'str',
            # },
            # {
            #     'name': 'mb',
            #     'datatype': 'str',
            # },
            # {
            #     'name': 'doreco-mb-algn',
            #     'datatype': 'str',
            # },
            # {
            #     'name': 'ps',
            #     'datatype': 'str',
            # },
            # {
            #     'name': 'gl',
            #     'datatype': 'str',
            # },
        )

        cldf.add_table(
            'words.csv',
            {
                'name': 'Language_ID',
                'datatype': 'string',
            },
            {
                'name': 'Filename',
                'datatype': 'string',
            },
            {
                'name': 'Speaker_ID',
                'datatype': 'string',
            },
            {
                'name': 'start',
                'datatype': 'decimal',
            },
            {
                'name': 'end',
                'datatype': 'decimal',
            },
            {
                'name': 'ref',
                'datatype': 'string',
            },
            {
                'name': 'Example_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#exampleReference',
            },
            {
                'name': 'wd_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'wd',
                'datatype': 'string',
            },
            {
                'name': 'mb_ID',
                'datatype': 'string',
            },
            {
                'name': 'mb',
                'datatype': 'string',
            },
            {
                'name': 'doreco-mb-algn',
                'datatype': 'string',
            },
            {
                'name': 'ps',
                'datatype': 'string',
            },
            {
                'name': 'gl',
                'datatype': 'string',
            },
            {
                'name': 'ph_id',
                'datatype': 'string',
            },
            {
                'name': 'ph',
                'datatype': 'string',
            },
        )

        T = cldf.add_table(
            'metadata.csv',
            {
                'name': 'ID',
            },
            {
                'name': 'Filename',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'spk_code',
                'datatype': 'string',
            },
            {
                'name': 'spk_age',
                'datatype': 'string',
            },
            {
                'name': 'spk_age_c',
                'datatype': 'string',
            },
            {
                'name': 'spk_sex',
                'datatype': 'string',
            },
            {
                'name': 'rec_date',
                'datatype': 'string',
            },
            {
                'name': 'rec_date_c',
                'datatype': 'string',
            },
            {
                'name': 'genre',
                'datatype': 'string',
            },
            {
                'name': 'genre_stim',
                'datatype': 'string',
            },
            {
                'name': 'gloss',
                'datatype': 'string',
            },
            {
                'name': 'transl',
                'datatype': 'string',
            },
            {
                'name': 'sound_quality',
                'datatype': 'string',
            },
            {
                'name': 'background_noise',
                'datatype': 'string',
            },
            {
                'name': 'word_tokens',
                'datatype': 'int',
            },
            {
                'name': 'extended',
                'datatype': 'string',
            },
            {
                'name': 'Glottocode',
                'datatype': 'string',
            }
            )

        cldf.add_table(
            'glosses.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'Gloss',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
            },
            {
                'name': 'LGR',
                'datatype': 'string',
            },
            {
                'name': 'Meaning',
                'datatype': 'string',
            },
            {
                'name': 'Glottocode',
                'datatype': 'string',
            }
            )

        cldf.add_foreign_key('metadata.csv', 'Glottocode', 'LanguageTable', 'ID')
        cldf.add_foreign_key('glosses.csv', 'Glottocode', 'LanguageTable', 'ID')
        cldf.add_foreign_key('ContributionTable', 'ID', 'LanguageTable', 'ID')
        cldf.add_foreign_key('phones.csv', 'wd_ID', 'words.csv', 'wd_ID')
        cldf.add_foreign_key('phones.csv', 'Language_ID', 'LanguageTable', 'ID')
        cldf.add_foreign_key('phones.csv', 'Filename', 'metadata.csv', 'Filename')
        cldf.add_foreign_key('words.csv', 'Language_ID', 'LanguageTable', 'ID')
        cldf.add_foreign_key('words.csv', 'Filename', 'metadata.csv', 'Filename')
