"""

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
from clldutils.jsonlib import dump, load
import pybtex.database
from tqdm import tqdm

from util import nakala
from util import igt

SILENT_PAUSE = '<p:>'
FILLER = '****'
LABEL_PATTERN = re.compile(r'<<(?P<label>fp|fs|pr|fm|sg|bc|id|on|wip|ui)>(?P<content>[^>]+)?>')


def global_id(glottocode, local_id):
    return '{}_{}'.format(glottocode, local_id)


#
# FIXME: determine valid words (for core):
# - core speaker (check spk_code split by "/") in metadata!
# - no pause, no filler, no label
#


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
            # 'https://sharedocs.huma-num.fr/wl/?id=s947TcfRfDZR643QURdyncdku4EmeKyb&fmode=download',  # v1.1
            "https://sharedocs.huma-num.fr/wl/?id=3LuEgKRrEUrdkAeDVskK46eNFqes5s6F&fmode=download",  # v1.2
            'languages.csv')
        self.raw_dir.download(
            # 'https://sharedocs.huma-num.fr/wl/?id=xqkUR3WoFOKB8cRb0MdHYJxIDEXEXlVG&fmode=download',  # v1.1
            "https://sharedocs.huma-num.fr/wl/?id=6OkBYGXrPkLEuHchF4kOXpsJf7MOKcLv&fmode=download",  # v1.2
            'sources.bib')

        with_nd_data = confirm('Include ND data?', default=False)
        with_audio_data = confirm('Include audio files?', default=False)
        for row in self.raw_dir.read_csv('languages.csv', dicts=True):
            if with_nd_data or ('ND' not in row['Annotation license']):
                print(row['Glottocode'], row['DOI'])
                doi = row['DOI']
                if row['Glottocode'] == 'beja1238':
                    # Known issue with https://nakala.fr/10.34847/nkl.edd011t1 v7 including wrong
                    # language files.
                    doi += '.v6'

                dep = nakala.Deposit(doi)
                for f in dep.files:
                    for s in ['_wd.csv', '_ph.csv', '_metadata.csv', '_gloss-abbreviations.csv']:
                        if f.name.endswith(s):
                            print(f.name, f.sha1)
                            self.raw_dir.download(f.url, '{}{}'.format(row['Glottocode'], s))
                            break
                audio = collections.OrderedDict()
                for supp in dep.supplements:
                    for f in supp.files:
                        if f.mime_type == 'audio/x-wav':
                            audio[f.name.replace('.wav', '')] = (f.url, f.size)
                            if with_audio_data:
                                target = self.dir / 'audio' / row['Glottocode'] / f.name
                                target.parent.mkdir(parents=True, exist_ok=True)
                                if not target.exists():
                                    try:
                                        urllib.request.urlretrieve(f.url, target)
                                    except urllib.error.HTTPError as e:
                                        if int(e.code) == 401:
                                            pass
                dump(audio, self.raw_dir / '{}_files.json'.format(row['Glottocode']), indent=4)

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
                    # raise ValueError(p)
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
        #
        # FIXME: add MediaTable !
        #
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

        speakers = set()
        filemd = collections.defaultdict(dict)
        for p in self.raw_dir.glob('*_files.json'):
            filemd[p.stem.split('_')[0]] = load(p)
        for i, row in enumerate(self.iter_rows('*_metadata.csv'), start=1):
            if row['extended'] == 'yes':
                continue
            fid = 'doreco_{}'.format(global_id(row['Glottocode'], row["name"]))
            if fid in filemd[row['Glottocode']]:
                args.writer.objects["MediaTable"].append({
                    "ID": fid,
                    'Name': '{}.wav'.format(row['name']),
                    "rec_date": row["rec_date"],
                    "rec_date_c": row["rec_date_c"],
                    "genre": row["genre"],
                    "genre_stim": row["genre_stim"],
                    "gloss": row["gloss"],
                    "transl": row["transl"],
                    "sound_quality": row["sound_quality"],
                    "background_noise": row["background_noise"],
                    "Glottocode": row["Glottocode"],
                    "Download_URL": filemd[row['Glottocode']][fid][0],
                    'Media_Type': 'audio/x-wav',
                })
            age_c = row['spk_age_c'].split('/') if '/' in row['spk_age_c'] else row['spk_age_c']
            for i, (code, age, sex) in enumerate(
                    itertools.zip_longest(row['spk_code'].split('/'), row['spk_age'].split('/'), row['spk_sex'].split('/'))):
                assert code and age and sex, '{} {} {} {}'.format(row['Glottocode'], code, age, sex)
                code = global_id(row['Glottocode'], code)
                if code not in speakers:
                    args.writer.objects['speakers.csv'].append(dict(
                        ID=code,
                        age=None if age == 'na' else int(age),
                        sex=sex,
                        age_assignment_certain=age_c[i] if isinstance(age_c, list) else age_c,
                        Language_ID=row['Glottocode'],
                    ))
                    speakers.add(code)

        for i, row in enumerate(self.iter_rows('*_gloss-abbreviations.csv'), start=1):
            args.writer.objects["glosses.csv"].append({
                "ID": global_id(row['Glottocode'], str(i)),
                "Gloss": row["Gloss"],
                "LGR": row["LGR"],
                "Meaning": row["Meaning"],
                "Glottocode": row["Glottocode"]
            })

        wd_intervals = {}  # We store start and end of words - as specified by contained phones.
        uid = 0  # We are adding utterance IDs.
        gc = None
        for wid, rows in tqdm(itertools.groupby(self.iter_rows('*_ph.csv'), lambda r: r['wd_ID']), desc='phones'):
            i, core, row, global_wid = 0, True, None, None
            while core:
                try:
                    row = next(rows)
                except StopIteration:  # row is now the last phone in the word.
                    wd_intervals['{}_{}'.format(gc, wid)][1] = decimal.Decimal(row["end"])
                    break
                core = row['core_extended'] != 'extended'
                if not core:
                    break
                start, end = decimal.Decimal(row["start"]), decimal.Decimal(row["end"])
                if i == 0:  # The first phone in the word.
                    if row['Glottocode'] != gc:
                        # A new corpus, make sure we are not conflating utterance.
                        # FIXME: Should be done per file!
                        uid += 1
                    gc = row['Glottocode']
                    if wid.split()[0] != wid:
                        # Known problem of the Evenki corpus, see
                        # https://github.com/DoReCo/doreco/issues/13
                        assert gc == 'even1259'
                        wid = wid.split()[-1]
                    global_wid = global_id(gc, wid)
                    wd_intervals[global_wid] = [start, None]
                    speaker = global_id(gc, row['speaker'])
                    if speaker.startswith('yuca1254_0'):
                        # Known problem of the Yucatec corpus, see
                        # https://github.com/DoReCo/doreco/issues/5#issuecomment-1490180631
                        speaker = speaker.replace('0', '')
                    assert speaker in speakers, 'Unknown speaker: {}'.format(speaker)
                else:
                    assert start >= args.writer.objects["phones.csv"][-1]['end']
                if row['ph'] == SILENT_PAUSE:  # Silent pauses delimit utterances.
                    uid += 1
                args.writer.objects["phones.csv"].append({
                    "ph_ID": gc + "_" + row["ph_ID"],
                    "ph": row["ph"],
                    "IPA": xsampa_to_bipa[row['ph']] if row['ph'] in xsampa_to_bipa else None,
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "wd_ID": global_wid,
                    'u_ID': None if row['ph'] == SILENT_PAUSE else str(uid),
                    'Token_Type': 'pause' if row['ph'] == SILENT_PAUSE else (
                        'label' if row['ph'].startswith('<<') else 'xsampa'),
                })
                i += 1

        misaligned_start, max_misalignment = [], decimal.Decimal('0')
        eids = collections.defaultdict(int)
        for (f, tx, ft), rows in tqdm(itertools.groupby(self.iter_rows('*_wd.csv'), lambda r: (r['file'], r['tx'], r['ft'])), desc='words'):
            rows = list(rows)
            eid = None
            # Create an entry in ExampleTable if tx not in ['', None, '****', '<p:>']
            if tx and ft and ft not in {FILLER, SILENT_PAUSE}:
                ex = igt.igt(rows, tx, ft, eids)
                if ex:
                    args.writer.objects['ExampleTable'].append(ex)
                    eid = ex['ID']

            for row in rows:
                gc = row['Glottocode']
                wid = global_id(gc, row['wd_ID'])
                sid = None
                start, end = decimal.Decimal(row["start"]), decimal.Decimal(row["end"])
                if wid in wd_intervals:
                    ps, pe = wd_intervals[wid]
                    assert start <= ps and pe <= end, 'Conflicting time alignment of wd and ph.'
                    sid = global_id(gc, row["speaker"])
                    del wd_intervals[wid]
                core = row['core_extended'] != 'extended'
                args.writer.objects["words.csv"].append({
                    "Language_ID": gc,
                    "File_ID": row["file"] if core and row['file'] in filemd[gc] else None,
                    "core": core,
                    # Only speakers for core words are normalized.
                    "Speaker_ID": sid,
                    "Example_ID": eid,
                    "wd_ID": wid,
                    "wd": row["wd"],
                    "start": start,
                    "end": end,
                    "duration": end - start,
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
                })
        assert not wd_intervals, '{} missing wd_IDs linked from phones!'.format(len(wd_intervals))


    def create_schema(self, cldf):
        #
        # FIXME: mediatable should have contributionReference!
        #
        cldf.add_component(
            'MediaTable',
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
                'name': 'Glottocode',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference',
                'datatype': 'string',
            }
        )
        cldf.remove_columns('MediaTable', 'Description', 'Path_In_Zip')
        cldf.add_component('ExampleTable')
        cldf['ExampleTable', 'Analyzed_Word'].null = []
        cldf['ExampleTable', 'Gloss'].null = []
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
            'speakers.csv',
            {'name': 'ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'Language_ID',
                'datatype': 'string',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference'},
            {'name': 'age', 'datatype': 'integer'},
            {'name': 'age_assignment_certain',
             'datatype': {'base': 'str', 'format': 'certain|approximate'},
             },
            {'name': 'sex',
             'datatype': {'base': 'str', 'format': 'm|f'},
             },
        )
        cldf.add_table(
            'phones.csv',
            {'name': 'ph_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'ph',
                'dc:description': 'See the description of the Token_Type column.',
                'datatype': 'string'},
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
                'dc:description': """\
Not all rows in this table correspond to actual phones. If a row does the Token_Type is 'xsampa'
and the `ph` column holds the X-SAMPA representation of the phone, otherwise it is a 'pause' or a
'label'.

Labels consist of two opening brackets, the label proper, a closing bracket, the content (optional),
and another closing bracket, e.g. `<<ui>word>`. Labels may also appear on their own if the content
is not known, e.g. `<<ui>>`. Valid proper labels are

- fp: Filled pause
- fs: False start
- pr: Prolongation
- fm: Foreign material
- sg: Singing
- bc: Backchannel
- id: Ideophone
- on: Onomatopoeic
- wip: Word-internal pause
- ui: Unidentifiable

Silent pauses are marked by a special symbol, `<p:>`. The location of silent pauses is manually
checked by the DoReCo team, while the symbol itself is inserted by the WebMAUS service. Unlike
labels, the <p:> symbol has only one of each bracket, and no other content may be included in it.\
""",
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
                'name': 'File_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference',
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
                'dc:description': 'The word form transcribed into orthography.',
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
        cldf.add_foreign_key('words.csv', 'Speaker_ID', 'speakers.csv', 'ID')
