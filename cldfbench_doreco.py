"""
This dataset is derived from the DoReCo data as follows:
- DoReCo data is limited to the core data with annotations released under a license without ND (no
  derivatives) clause (because we add annotations which goes against this clause).
- Morpheme-aligned data is converted into IGT instances in an ExampleTable.
- The Beja annotation files are taken from DOI 10.34847/nkl.edd011t1 v6, not the latest, but
  incorrect v7.
- Two minor issues with the DoReCo data are fixed, namely a handful of phones in the Evenki corpus
  being linked to two words, and phones/words in the Yucatec corpus having a typo in the speaker
  reference.
- Links from phones to IPA symbols, and eventually to CLTS sounds are added, based on the
  orthography profile in etc/orthography.tsv

Note that the `cldfbench.Dataset` in this module provides functionality to also
- download the ND-licensed data (which is appropriate for analysis, but not for re-destribution)
- download the audio files on which the DoReCo data is based.

To do so, run
- `cldfbench download cldfbench_doreco.py` and answer appropriately when prompted.
- `cldfbench makecldf cldfbench_doreco.py`, passing the location of a clone of cldf-clts/clts when
  prompted.
"""
import re
import decimal
import pathlib
import itertools
import subprocess
import collections
import urllib.error
import urllib.parse
import urllib.request

from tqdm import tqdm
import pybtex.database
from pyclts import CLTS
from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec
from clldutils.clilib import confirm
from clldutils.jsonlib import dump, load
from clldutils.lgr import ABBRS, PERSONS

from util import nakala
from util import igt

SILENT_PAUSE = '<p:>'
FILLER = '****'
LABEL_PATTERN = re.compile(r'<<(?P<label>fp|fs|pr|fm|sg|bc|id|on|wip|ui)>(?P<content>[^>]+)?>')
LGR_PERSON_AND_ABBR = {p + a for p, a in itertools.product(PERSONS, ABBRS)}


def is_lgr_abbr(s):
    return s in ABBRS or (s in LGR_PERSON_AND_ABBR)


def global_id(glottocode, local_id):
    return '{}_{}'.format(glottocode, local_id)


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

    def cmd_readme(self, args):
        subprocess.check_call([
            'cldfbench',
            'cldfviz.map',
            str(self.cldf_specs().metadata_path),
            '--output', str(self.dir / 'map.png'),
            '--width', '20',
            '--height', '10',
            '--format', 'png',
            '--with-ocean',
            '--language-properties', 'Macroarea',
            '--markersize', '15',
            '--no-legend',
            '--language-labels',
            '--padding-top', '3',
            '--padding-bottom', '3',
            '--pacific-centered'])
        desc = ['\n![](map.png)\n']
        pre, head, post = super().cmd_readme(args).partition('## CLDF ')
        return pre + '\n'.join(desc) + head + post

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
                    if '_wd' in pattern:
                        for k in ['ft', 'tx']:
                            if k in row:
                                row[k] = igt.fix_text(row[k], k, row['Glottocode'])
                yield row

    def cmd_makecldf(self, args):
        clts_data = pathlib.Path('cldf-clts-clts-6dc73af')
        if not clts_data.exists():
            clts_data = pathlib.Path(input('Path to clts data: '))
        clts = CLTS(clts_data)
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
                CLTS_ID=bipa.name.replace(' ', '_'),
            ))
            xsampa_to_bipa[xsampa] = str(i)

        args.log.info("added sources")

        for row in self.raw_dir.read_csv('languages.csv', dicts=True):
            if not self.raw_dir.joinpath('{}_metadata.csv'.format(row['Glottocode'])).exists():
                continue
            args.writer.objects["LanguageTable"].append({
                "ID": row["Glottocode"],
                "Name": row["Language"],
                "Glottocode": row["Glottocode"],
                "Latitude": row["Latitude"],
                "Longitude": row["Longitude"],
                "Macroarea": row["Area"],
                "Source": "doreco-" + row["Glottocode"],
            })

            args.writer.objects["ContributionTable"].append({
                "ID": row["Glottocode"],
                "Name": "{}  DoReCo dataset".format(row["Language"]),
                "Citation": str(args.writer.cldf.sources["doreco-" + row["Glottocode"]]),
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
                    "rec_date_assignment_certain": row["rec_date_c"],
                    "genre": row["genre"],
                    "genre_stim": row["genre_stim"],
                    "gloss": row["gloss"],
                    "transl": row["transl"].split('/'),
                    "sound_quality": row["sound_quality"],
                    "background_noise": row["background_noise"],
                    "Glottocode": row["Glottocode"],
                    "Corpus_ID": row["Glottocode"],
                    "Download_URL": filemd[row['Glottocode']][fid][0],
                    'Media_Type': 'audio/x-wav',
                })
            age_c = row['spk_age_c'].split('/') if '/' in row['spk_age_c'] else row['spk_age_c']
            for i, (code, age, sex) in enumerate(
                    itertools.zip_longest(
                        row['spk_code'].split('/'),
                        row['spk_age'].split('/'),
                        row['spk_sex'].split('/'))):
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
                "LGR": is_lgr_abbr(row["LGR"]),
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
                ex = igt.igt(
                    rows,
                    tx,
                    ft,
                    eids,
                    rows[0]['file'] if rows[0]['core_extended'] != 'extended' and rows[0]['file'] in filemd[rows[0]['Glottocode']] else None)
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
                    "mb": row["mb"].split(),
                    # FIXME: add ps and gl to ExampleTable!
                    "ps": row["ps"].split(),
                    "gl": row["gl"].split(),
                })
        assert not wd_intervals, '{} missing wd_IDs linked from phones!'.format(len(wd_intervals))


    def create_schema(self, cldf):
        t = cldf.add_component(
            'MediaTable',
            {
                'name': 'rec_date',
                'datatype': {'base': 'string', 'format': '[0-9]{4}(-[0-9]{2})?(-[0-9]{2})?'}},
            {
                'name': 'rec_date_assignment_certain',
                'datatype': {'base': 'str', 'format': 'certain|approximate'}},
            {
                'name': 'genre',
                'datatype': {'base': 'str', 'format': 'traditional narrative|personal narrative|conversation|stimulus retelling|procedural|procedural/conversation'}},
            {
                'name': 'genre_stim', 'datatype': 'string'},
            {
                'name': 'gloss',
                'dc:description': 'Information on whether/how the audio has been annotated with glosses.',
                'datatype': 'string',
            },
            {
                'name': 'transl',
                'dc:description': 'Information on meta languages for which the annotations contain translations.',
                'separator': '/',
                'null': ['na'],
                'datatype': 'string',
            },
            {
                'name': 'sound_quality',
                'datatype': {'base': 'str', 'format': 'good|medium|bad|middle'}},
            {
                'name': 'background_noise',
                'null': ['na'],
                'datatype': {'base': 'str', 'format': 'punctual|none|constant|medium'}},
            {
                'name': 'Corpus_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference',
                'datatype': 'string',
            },
            {
                'name': 'Glottocode',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference',
                'datatype': 'string',
            }
        )
        t.common_props['dc:description'] = \
            "This table lists audio files which have been transcribed/annotated for DoReCo corpora. " \
            "Note that only downloadable files are listed."
        cldf.remove_columns('MediaTable', 'Description', 'Path_In_Zip')
        t = cldf.add_component(
            'ExampleTable',
            {
                'name': 'File_ID',
                'dc:description': 'Link to the audio file to which start and end markers pertain.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference',
                'datatype': 'string',
            },
            {
                'name': 'start',
                'dc:description': 'Start of the word in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal',
            },
            {
                'name': 'end',
                'dc:description': 'End of the word in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal',
            },
            {
                'name': 'duration',
                'dc:description': 'Duration of the word in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal',
            },
        )
        t.common_props['dc:description'] = \
            "Some corpora in DoReCo contain data annotated with glosses. Such glossed data is " \
            "extracted into a CLDF ExampleTable."
        cldf['ExampleTable', 'Analyzed_Word'].null = []
        cldf['ExampleTable', 'Gloss'].null = []
        cldf['ExampleTable', 'Analyzed_Word'].separator = '\t'
        cldf['ExampleTable', 'Gloss'].separator = '\t'
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Source',
                'datatype': 'string',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'})

        t = cldf.add_component(
            'ContributionTable',
            {'name': 'Archive', 'datatype': 'string', 'null': ['na']},
            {'name': 'Archive_link', 'datatype': 'string', 'null': ['na']},
            {'name': 'AnnotationLicense', 'datatype': 'string'},
            {'name': 'AudioLicense', 'datatype': 'string'},
            {'name': 'DOI', 'datatype': 'string'},
        )
        t.common_props['dc:description'] = \
            "Each DoReCo language corpus is listed as separate contribution in this table."
        t = cldf.add_component(
            'ParameterTable',
            {'name': 'CLTS_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#cltsReference'},
        )
        t.common_props['dc:description'] = \
            "The ParameterTable lists IPA phones which appear in the DoReCo corpus (if a " \
            "correspondence to the X-Sampa representation could be determined). If possible, IPA " \
            "phones are linked to CLTS' BIPA representation, giving access to the CLTS feature " \
            "system."
        cldf[t, 'Name'].common_props['dc:description'] = "The IPA representation of the sound."
        cldf[t, 'CLTS_ID'].common_props['dc:description'] = \
            "CLTS ID of the sound, i.e. the underscore-separated ordered list of features of the " \
            "sound."
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
            {'name': 'sex', 'datatype': {'base': 'str', 'format': 'm|f'}},
        )
        t = cldf.add_table(
            'phones.csv',
            {'name': 'ph_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'ph',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
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
        t.common_props['dc:description'] = 'This table lists individual, time-aligned phones.'

        cldf.add_table(
            'words.csv',
            {'name': 'wd_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'wd',
                'dc:description': 'The word form transcribed into orthography.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
                'datatype': 'string',
            },
            {
                'name': 'Language_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference',
                'datatype': 'string',
            },
            {
                'name': 'File_ID',
                'dc:description': 'Link to the audio file to which start and end markers pertain.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference',
                'datatype': 'string',
            },
            {'name': 'Speaker_ID', 'datatype': 'string'},
            {
                'name': 'start',
                'dc:description': 'Start of the word in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal',
            },
            {
                'name': 'end',
                'dc:description': 'End of the word in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal',
            },
            {
                'name': 'duration',
                'dc:description': 'Duration of the word in the linked sound file in (floating point) seconds.',
                'datatype': 'decimal',
            },
            {
                'name': 'ref',
                'datatype': 'string',
            },
            {
                'name': 'Example_ID',
                'dc:description': 'Words that appear in glossed utterances are linked to an Example.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#exampleReference',
            },
            {
                'name': 'mb',
                'separator': ' ',
                'datatype': 'string',
            },
            {
                'name': 'ps',
                'separator': ' ',
                'datatype': 'string',
            },
            {
                'name': 'gl',
                'separator': ' ',
                'datatype': 'string',
            },
        )
        t = cldf.add_table(
            'glosses.csv',
            {'name': 'ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {'name': 'Gloss', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name'},
            {
                'name': 'LGR',
                'dc:description': 'Flag, signaling whether a gloss abbreviation is a standard, '
                                  'Leipzig-Glossing-Rules abbreviation.',
                'datatype': 'boolean',
            },
            {'name': 'Meaning', 'datatype': 'string'},
            {
                'name': 'Glottocode',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference',
                'datatype': 'string',
            }
        )
        t.common_props['dc:description'] = 'Gloss abbreviations used for glosses in a corpus.'
        cldf.add_foreign_key('ContributionTable', 'ID', 'LanguageTable', 'ID')
        cldf.add_foreign_key('phones.csv', 'wd_ID', 'words.csv', 'wd_ID')
        cldf.add_foreign_key('words.csv', 'Speaker_ID', 'speakers.csv', 'ID')
