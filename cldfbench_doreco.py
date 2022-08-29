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
                "YearsOfRecordingInCoreSet": row["Years of recordings in core set"]
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

            #  print(row["Creator"])
        args.log.info("added languages")
        
        # for row in self.raw_dir.read_csv(
        #     'gata_raw.csv',
        #     dicts=True,
        #     ):
        #     row["Source"] = [row["Source"]]
        #     args.writer.objects['ValueTable'].append(row)
        # args.log.info("added values")

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
                'datatype': 'int',
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
