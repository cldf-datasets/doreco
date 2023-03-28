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
import re
import decimal
import pathlib
import itertools
import collections
import urllib.error
import urllib.parse
import urllib.request

from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec
from clldutils.clilib import confirm
import pybtex.database

from util import nakala
from util import igt

SILENT_PAUSE = '<p:>'


# bora: translations in spanish -> raw/languages.csv:Translation
# even1259 : russian! not english, as claimed in languages.csv!
# sout2856: "§ 014-002" prefixes (and infixes) for tx
# apah: tx: "(\<+)(x+)(\>+)", e.g. "<<xxx>>" meaning what?

def fix_text(s, type_, gc):
    s = s.strip()
    for m, repl in {
        'â\x80\x9d': '”',
        'â\x80\x9c': '“',
        # <200e><200e>
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


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "doreco"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(
            dir=self.cldf_dir,
            module='Generic',
            zipped={'phones.csv', 'words.csv'},
        )

    def cmd_download(self, args):
        self.raw_dir.download(
            #'https://sharedocs.huma-num.fr/wl/?id=s947TcfRfDZR643QURdyncdku4EmeKyb&fmode=download',  # v1.1
            "https://sharedocs.huma-num.fr/wl/?id=3LuEgKRrEUrdkAeDVskK46eNFqes5s6F&fmode=download",  # v1.2
            'languages.csv')
        self.raw_dir.download(
            #'https://sharedocs.huma-num.fr/wl/?id=xqkUR3WoFOKB8cRb0MdHYJxIDEXEXlVG&fmode=download',  # v1.1
            "https://sharedocs.huma-num.fr/wl/?id=6OkBYGXrPkLEuHchF4kOXpsJf7MOKcLv&fmode=download",  # v1.2
            'sources.bib')

        with_nd_data = confirm('Include ND data?', default=False)
        with_audio_data = confirm('Include audio files?', default=False)
        for row in self.raw_dir.read_csv('languages.csv', dicts=True):
            if with_nd_data or ('ND' not in row['Annotation license']):
                print(row['Glottocode'], row['DOI'])

                dep = nakala.Deposit(row['DOI'])
                for f in dep.files:
                    for s in ['_wd.csv', '_ph.csv', '_metadata.csv', '_gloss-abbreviations.csv']:
                        if f.name.endswith(s):
                            print(f.name, f.sha1)
                            self.raw_dir.download(f.url, '{}{}'.format(row['Glottocode'], s))
                            break
                if with_audio_data:
                    for supp in dep.supplements:
                        for f in supp.files:
                            if f.mime_type == 'audio/x-wav':
                                target = self.dir / 'audio' / row['Glottocode'] / f.name
                                target.parent.mkdir(parents=True, exist_ok=True)
                                if not target.exists():
                                    try:
                                        urllib.request.urlretrieve(f.url, target)
                                    except urllib.error.HTTPError as e:
                                        if int(e.code) == 401:
                                            pass


    def iter_rows(self, pattern):
        mismatch = set()
        for p in sorted(self.raw_dir.glob(pattern), key=lambda pp: pp.name):
            # What to do if there are tab-delimited files? Sniff!
            delimiter = ','
            with p.open(encoding='utf8') as f:
                if '\t' in f.readline():  # Even gloss abbreviations come in a tab-delimited file.
                    assert 'even' in p.stem
                    delimiter = '\t'
            for row in self.raw_dir.read_csv(p.name, dicts=True, delimiter=delimiter):
                # Catch the Beja issue in v1.2, where the file for a different language was
                # packaged in the deposit for Beja:
                if row.get('lang') and row.get('lang') != p.name.partition('_')[0]:
                    if p.name.partition('_')[0] not in mismatch:
                        print('Glottocode mismatch: {}'.format(p))
                        mismatch.add(p.name.partition('_')[0])
                    #raise ValueError(p)
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
        from pyclts import CLTS
        clts = CLTS('../../cldf-clts/clts-data')
        xsampa_to_bipa = collections.OrderedDict()
        for row in self.etc_dir.read_csv('orthography.tsv', dicts=True, delimiter='\t'):
            bipa = clts.bipa[row['IPA']] if row['IPA'] else None
            if bipa and bipa.type != 'unknownsound':
                xsampa_to_bipa[row['Grapheme']] = bipa

        self.create_schema(args.writer.cldf)

        args.writer.cldf.add_sources(pybtex.database.parse_string(
            self.raw_dir.joinpath('sources.bib').read_text(encoding='utf8'),
            bib_format='bibtex',
        ))

        for i, (xsampa, bipa) in enumerate(list(xsampa_to_bipa.items()), start=1):
            args.writer.objects['ParameterTable'].append(dict(
                ID=str(i),
                Name=bipa.s,
                CLTS_ID=bipa.name,
            ))
            xsampa_to_bipa[xsampa] = str(i)

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
            eid = None
            # Create an entry in ExampleTable if tx not in ['', None, '****', '<p:>']
            if tx and (ft not in ['', None, '****', SILENT_PAUSE]):
                ex = igt.igt(rows, tx, ft, eids)
                if ex:
                    args.writer.objects['ExampleTable'].append(ex)
                    eid = ex['ID']

            for row in rows:
                args.writer.objects["words.csv"].append({
                    "Language_ID": row["Glottocode"],
                    "Filename": row["file"],
                    # "core_extended": row["core_extended"],
                    "speaker": row["speaker"],
                    "Example_ID": eid,
                    "wd_ID": row["Glottocode"] + "_" + row["wd_ID"],
                    "wd": row["wd"],
                    "start": decimal.Decimal(row["start"]),
                    "end": decimal.Decimal(row["end"]),
                    "duration": decimal.Decimal(row["end"]) - decimal.Decimal(row["start"]),
                    "ref": row["ref"],
                    "tx": row["tx"],
                    "ft": row["ft"],
                    # FIXME: mb_ID is a whitespace-separated list of IDs
                    # "mb_ID": row["lang"] + "_" + row["mb_ID"],
                    # "mb": row["mb"],
                    # "doreco-mb-algn": row["doreco-mb-algn"],
                    # FIXME: add ps and gl to ExampleTable!
                    "ps": row["ps"],
                    "gl": row["gl"],
                    "ph_ID": row["Glottocode"] + "_" + row["ph_ID"],
                    "ph": row["ph"]
                })
                wd_intervals[row["Glottocode"] + "_" + row["wd_ID"]] = (
                    decimal.Decimal(row["start"]), decimal.Decimal(row["end"]))

        misaligned_start, max_misalignment = [], decimal.Decimal('0')
        uid = 0
        for wid, rows in itertools.groupby(self.iter_rows('*_ph.csv'), lambda r: r['wd_ID']):
            wido = wid
            wid = wid.split()[0]
            rows = list(rows)
            for i, row in enumerate(rows):
                if row['Glottocode'] + '_' + wido not in wd_intervals:
                    assert row['Glottocode'] == 'even1259' and ' ' in wido, '{} - {}'.format(row['Glottocode'], wido)
                    print('dropping phone with wid {}'.format(wid))
                    continue
                if row['ph'] == SILENT_PAUSE:  # Silent pauses delimit utterances.
                    uid += 1
                if i == 0:
                    ps = decimal.Decimal(row["start"])
                    ws = wd_intervals[row['Glottocode'] + '_' + wid][0]
                    assert ps >= ws
                    if ps > ws:
                        misaligned_start.append((row['Glottocode'], ps - ws, row['wd'], [r['ph'] for r in rows]))
                        if ps - ws > max_misalignment:
                            max_misalignment = ps - ws
                if i == len(rows) - 1:
                    pe = decimal.Decimal(row["end"])
                    we = wd_intervals[row['Glottocode'] + '_' + wid][1]
                    assert pe <= we
                    if pe < we:
                        misaligned_start.append((row['Glottocode'], row['wd']))
                if 0 < i < len(rows):
                    assert decimal.Decimal(row["start"]) >= args.writer.objects["phones.csv"][-1]['end']

                args.writer.objects["phones.csv"].append({
                    "Language_ID": row["Glottocode"],
                    "Filename": row["file"],
                    # "core_extended": row["core_extended"],
                    "speaker": row["Glottocode"] + "_" + row["speaker"],
                    "ph_ID": row["Glottocode"] + "_" + row["ph_ID"],
                    "ph": row["ph"],
                    "IPA": xsampa_to_bipa[row['ph']] if row['ph'] in xsampa_to_bipa else None,
                    "start": decimal.Decimal(row["start"]),
                    "end": decimal.Decimal(row["end"]),
                    "duration": decimal.Decimal(row["end"]) - decimal.Decimal(row["start"]),
                    # "ref": row["ref"],
                    # "tx": row["tx"],
                    # "ft": row["ft"],
                    "wd_ID": row["Glottocode"] + "_" + row["wd_ID"],
                    'u_ID': None if row['ph'] == SILENT_PAUSE else str(uid),
                    'Token_Type': 'pause' if row['ph'] == SILENT_PAUSE else (
                        'label' if row['ph'].startswith('<<') else 'xsampa'),
                    # "wd": row["wd"],
                    # "mb_ID": row["mb_ID"],
                    # "mb": row["mb"],
                    # "doreco-mb-algn": row["doreco-mb-algn"],
                    # "ps": row["ps"],
                    # "gl": row["gl"]
                })
                if row['ph'] != SILENT_PAUSE:
                    pause = False

        print(inv, valid, len(misaligned_start))

    def create_schema(self, cldf):
        cldf.add_component('ExampleTable')
        cldf['ExampleTable', 'Analyzed_Word'].separator = '\t'
        cldf['ExampleTable', 'Gloss'].separator = '\t'
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Source',
                'datatype': 'string',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'},
            {'name': 'Translation', 'datatype': 'string'},
            {'name': 'Gloss', 'datatype': 'string'},
            {'name': 'ExtendedSpeakers', 'datatype': 'int'},
            {'name': 'ExtendedWordTokens', 'datatype': 'int'},
            {'name': 'ExtendedTexts', 'datatype': 'int'},
            {'name': 'CoreSpeakers', 'datatype': 'int'},
            {'name': 'CoreWordTokens', 'datatype': 'int'},
            {'name': 'CoreTexts', 'datatype': 'int'},
            {'name': 'YearsOfRecordingInCoreSet', 'datatype': 'string'})

        cldf.add_component(
            'ContributionTable',
            {'name': 'Archive', 'datatype': 'string'},
            {'name': 'Archive_link', 'datatype': 'string'},
            {'name': 'AnnotationLicense', 'datatype': 'string'},
            {'name': 'AudioLicense', 'datatype': 'string'},
            {'name': 'DOI', 'datatype': 'string'},
        )
        t = cldf.add_component(
            'ParameterTable',
            {'name': 'CLTS_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#cltsReference'},
        )
        t.common_props['dc:description'] = \
            "The ParameterTable lists IPA phones which appear in the DoReCo corpus (if a " \
            "correspondence to the X-Sampa representation could be determined). If possible, IPA " \
            "phones are linked to CLTS' BIPA representation, giving access to the CLTS feature " \
            "system."

        cldf.add_table(
            'phones.csv',
            {
                'name': 'Language_ID',
                'datatype': 'string',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference'},
            {'name': 'Filename', 'datatype': 'string'},
            {'name': 'speaker', 'datatype': 'string'},
            {'name': 'ph_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {'name': 'ph', 'datatype': 'string'},
            {
                'name': 'IPA',
                'dc:description': "Link to corresponding IPA phoneme, with details given in ParameterTable",
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#parameterReference'},
            {
                'name': 'u_ID',
                'dc:description': 'Utterance ID. Utterances are words/phones delimited by silent pauses.',
                'datatype': 'string'},
            {
                'name': 'Token_Type',
                'dc:description': 'Not all rows in this table correspond to actual phones. If a row does, '
                                  "it's Token_Type is 'xsampa', otherwise it's 'label' or 'pause'.",
                'datatype': {'base': 'string', 'format': 'label|pause|xsampa'}},
            {
                'name': 'start',
                'dc:description': 'Start of the phone in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal'},
            {
                'name': 'end',
                'dc:description': 'End of the phone in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal'},
            {
                'name': 'duration',
                'dc:description': 'Duration of the phone in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal'},
            {
                'name': 'wd_ID',
                'dc:description': 'Link to corresponding word.',
                'datatype': 'string',
            },
        )

        cldf.add_table(
            'words.csv',
            {
                'name': 'Language_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference',
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
                'name': 'duration',
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
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference',
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
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference',
                'datatype': 'string',
            }
        )
        cldf.add_foreign_key('ContributionTable', 'ID', 'LanguageTable', 'ID')
        cldf.add_foreign_key('phones.csv', 'wd_ID', 'words.csv', 'wd_ID')
        cldf.add_foreign_key('phones.csv', 'Filename', 'metadata.csv', 'Filename')
        cldf.add_foreign_key('words.csv', 'Filename', 'metadata.csv', 'Filename')
