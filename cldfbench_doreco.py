import pathlib
from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec
import pybtex


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "doreco"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(
                dir=self.cldf_dir, 
                module='StructureDataset'
                )

    def cmd_makecldf(self, args):
        self.create_schema(args.writer.cldf)

        sources = pybtex.database.parse_string(
            'doreco_CITATIONS.bib', bib_format='bibtex'
            )
        args.writer.cldf.add_sources(sources)
        args.log.info("added sources")

        for row in self.etc_dir.read_csv(
            'doreco_languages_metadata.csv',
            dicts=True,
            ):
            args.writer.objects["LanguageTable"].append({
                "ID": row["Language"],
                "Name": row["Language"],
                "Glottocode": row["Glottocode"],
                "Latitude": row["Latitude"],
                "Longitude": row["Longitude"],
                "Macroarea": row["Area"],
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
                "ID": row["Language"],
                "Name": row["Language"],
                "Contributor": row["Creator"],
                "Archive": row["Archive"],
                "Archive_link": row["Archive_link"],
                "AnnotationLicense": row["Annotation license"],
                "AudioLicense": row["Audio license"],
                "DOI": row["DOI"]
            })
        args.log.info("added languages and contributions")

        for row in self.raw_dir.read_csv(
            'file_metadata.csv',
            dicts=True,
            ):
            args.writer.objects["metadata.csv"].append({
                "ID": row["Glottocode"] + "_" + row["id"],
                "Filename": row["name"],
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

        for row in self.raw_dir.read_csv(
            'glosses.csv',
            dicts=True,
            ):
            args.writer.objects["glosses.csv"].append({
                "Gloss": row["Gloss"],
                "LGR": row["LGR"],
                "Meaning": row["Meaning"],
                "Glottocode": row["Glottocode"]
            })

        for row in self.raw_dir.read_csv(
            'wd_data.csv',
            dicts=True,
            ):
            args.writer.objects["words.csv"].append({
                "Language_ID": row["lang"],
                "Filename": row["file"],
                # "core_extended": row["core_extended"],
                "speaker": row["speaker"],
                "wd_ID": row["wd_ID"],
                "wd": row["wd"],
                "start": row["start"],
                "end": row["end"],
                "ref": row["ref"],
                "tx": row["tx"],
                "ft": row["ft"],
                "mb_ID": row["mb_ID"],
                "mb": row["mb"],
                "doreco-mb-algn": row["doreco-mb-algn"],
                "ps": row["ps"],
                "gl": row["gl"],
                "ph_ID": row["ph_ID"],
                "ph": row["ph"]
            })

        for row in self.raw_dir.read_csv(
            'ph_data.csv',
            dicts=True,
            ):
            args.writer.objects["ValueTable"].append({
                "Language_ID": row["lang"],
                "Filename": row["file"],
                # "core_extended": row["core_extended"],
                "speaker": row["speaker"],
                "ph_ID": row["ph_ID"],
                "ph": row["ph"],
                "start": row["start"],
                "end": row["end"],
                # "ref": row["ref"],
                # "tx": row["tx"],
                # "ft": row["ft"],
                "wd_ID": row["wd_ID"],
                # "wd": row["wd"],
                # "mb_ID": row["mb_ID"],
                # "mb": row["mb"],
                # "doreco-mb-algn": row["doreco-mb-algn"],
                # "ps": row["ps"],
                # "gl": row["gl"]
            })

    def create_schema(self, cldf):

        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Translation',
                'datatype': 'str',
            },
            {
                'name': 'Gloss',
                'datatype': 'str',
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
                'datatype': 'str',
            })

        cldf.add_component(
            'ContributionTable',
            {
                'name': 'Archive',
                'datatype': 'str',
            },
            {
                'name': 'Archive_link',
                'datatype': 'str',
            },
            {
                'name': 'AnnotationLicense',
                'datatype': 'str',
            },
            {
                'name': 'AudioLicense',
                'datatype': 'str',
            },
            {
                'name': 'DOI',
                'datatype': 'str',
            },
        )

        cldf.add_table(
            'phones.csv',
            {
                'name': 'Language_ID',
                'datatype': 'str',
            },
            {
                'name': 'Filename',
                'datatype': 'str',
            },
            {
                'name': 'speaker',
                'datatype': 'str',
            },
            {
                'name': 'ph_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'ph',
                'datatype': 'str',
            },
            {
                'name': 'start',
                'datatype': 'str',
            },
            {
                'name': 'end',
                'datatype': 'str',
            },
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
                'datatype': 'str',
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
                'datatype': 'str',
            },
            {
                'name': 'Filename',
                'datatype': 'str',
            },
            {
                'name': 'Speaker_ID',
                'datatype': 'str',
            },
            {
                'name': 'start',
                'datatype': 'str',
            },
            {
                'name': 'end',
                'datatype': 'str',
            },
            {
                'name': 'ref',
                'datatype': 'str',
            },
            {
                'name': 'tx',
                'datatype': 'str',
            },
            {
                'name': 'ft',
                'datatype': 'str',
            },
            {
                'name': 'wd_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'wd',
                'datatype': 'str',
            },
            {
                'name': 'mb_ID',
                'datatype': 'str',
            },
            {
                'name': 'mb',
                'datatype': 'str',
            },
            {
                'name': 'doreco-mb-algn',
                'datatype': 'str',
            },
            {
                'name': 'ps',
                'datatype': 'str',
            },
            {
                'name': 'gl',
                'datatype': 'str',
            },
            {
                'name': 'ph_id',
                'datatype': 'str',
            },
            {
                'name': 'ph',
                'datatype': 'str',
            },
        )

        T = cldf.add_table(
            'metadata.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'Filename',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
            },
            {
                'name': 'spk_code',
                'datatype': 'int',
            },
            {
                'name': 'spk_age',
                'datatype': 'int',
            },
            {
                'name': 'spk_age_c',
                'datatype': 'str',
            },
            {
                'name': 'spk_sex',
                'datatype': 'str',
            },
            {
                'name': 'rec_date',
                'datatype': 'str',
            },
            {
                'name': 'rec_date_c',
                'datatype': 'str',
            },
            {
                'name': 'genre',
                'datatype': 'str',
            },
            {
                'name': 'genre_stim',
                'datatype': 'str',
            },
            {
                'name': 'gloss',
                'datatype': 'str',
            },
            {
                'name': 'transl',
                'datatype': 'str',
            },
            {
                'name': 'sound_quality',
                'datatype': 'str',
            },
            {
                'name': 'background_noise',
                'datatype': 'str',
            },
            {
                'name': 'word_tokens',
                'datatype': 'int',
            },
            {
                'name': 'extended',
                'datatype': 'str',
            },
            {
                'name': 'Glottocode',
                'datatype': 'str',
            }
            )
        T.common_props['dc:conformsTo'] = None

        cldf.add_table(
            'glosses.csv',
            {
                'name': 'Gloss',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'LGR',
                'datatype': 'str',
            },
            {
                'name': 'Meaning',
                'datatype': 'str',
            },
            {
                'name': 'Glottocode',
                'datatype': 'str',
            }
            )

        cldf.add_foreign_key('metadata.csv', 'Glottocode', 'LanguageTable', 'Glottocode')
        cldf.add_foreign_key('glosses.csv', 'Glottocode', 'LanguageTable', 'Glottocode')
        cldf.add_foreign_key('ContributionTable', 'ID', 'LanguageTable', 'ID')
        cldf.add_foreign_key('ValueTable', 'wd_ID', 'words.csv', 'wd_ID')
        cldf.add_foreign_key('ValueTable', 'Language_ID', 'LanguageTable', 'ID')
        cldf.add_foreign_key('ValueTable', 'Filename', 'metadata.csv', 'Filename')
        cldf.add_foreign_key('words.csv', 'Language_ID', 'LanguageTable', 'Name')
        cldf.add_foreign_key('words.csv', 'Filename', 'metadata.csv', 'Filename')
