import pathlib

import attr
from cldfbench import Dataset as BaseDataset
from cldfbench import CLDFSpec
import pybtex

# @attr.s
# class CustomLanguage(Language):
#     Area = attr.ib(default=None)
#     Creator = attr.ib(default=None)
#     Source = attr.ib(default=None)
#     Archive = attr.ib(default=None)
#     Archive_link = attr.ib(default=None)
#     Translation = attr.ib(default=None)
#     AnnotationLicense = attr.ib(default=None)
#     AudioLicense = attr.ib(default=None)
#     DOI = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "doreco"
    #language_class = CustomLanguage

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(
                dir=self.cldf_dir, 
                module='StructureDataset'
                )


    def cmd_makecldf(self, args):
        sources = pybtex.database.parse_string(
            'doreco_CITATIONS.bib', bib_format='bibtex'
            )

        args.log.info("added sources")
		
        # args.writer.cldf.add_columns(
        #         "ParameterTable",
        #         "Category",
        #         "Shortname",
        #         "Variable_type",
        #         "Category_esp",  
        #         "Description_esp",
        #         "Comments")

        args.writer.cldf.add_component("ContributionTable")
        args.writer.cldf.add_component("LanguageTable")

        for row in self.etc_dir.read_csv(
            'doreco_languages_metadata.csv',
            dicts=True,
            ):
            args.writer.objects["LanguageTable"].append({
                "ID": row["Language"],
                "Name": row["Language"],
                "Glottocode": row["Glottocode"],
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
                "Creator": row["Creator"],
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
