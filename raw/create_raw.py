"""
This module combines all zip.files from the data folder
and merges them into individual csv-files.
Languages with a ND-license are not included.
"""
import glob
import re
import os
import csv
import zipfile

PATH = './data/'
HEADER = 0
full_ph_corpus = [
    [
        "lang", "file", "core_extended", "speaker", "ph_ID", "ph", "start",
        "end", "ref", "tx", "ft", "wd_ID", "wd", "mc-zero", "mb_ID", "mb",
        "doreco-mb-algn", "ps", "gl"
        ]
]

full_wd_corpus = [
    [
        "lang", "file", "core_extended", "speaker", "wd_ID", "wd", "start",
        "end", "ref", "tx", "ft", "mb_ID", "mb", "doreco-mb-algn", "ps", "gl",
        "ph_ID", "ph"
        ]
]
file_metadata = []
glosses = [
    ["Gloss", "LGR", "Meaning", "Glottocode"]
]


def unpack(path, file, out, add_glotto=False, check_cols=False, skip_header=False):
    """Function unzips and merges the indicated csv-files."""
    glottocode = re.sub(r"./data/doreco_(.*)_dataset", "\\1", path)
    for files in glob.glob(os.path.join(path, file)):
        with open(files, mode='r', encoding="utf8") as doc:
            data = csv.reader(doc)

            if HEADER > 1 or skip_header is True:
                next(data, None)

            glotto_count = 0
            for entry in data:
                if check_cols is True:
                    # doreco-mb-algn col missing in some files of _ph
                    if len(entry) == 17:
                        entry = entry[:13] + [""] + entry[13:15] + [""] + entry[15:]

                    elif len(entry) == 18:
                        entry = entry[:13] + [""] + entry[13:]
                        # print(len(entry))

                if add_glotto is True:
                    glotto_count += 1
                    if glotto_count == 1 and HEADER == 1 and out != glosses:
                        # add Glottocode column to the header
                        entry.append("Glottocode")
                    else:
                        entry.append(glottocode)

                out.append(entry)


def write_corpus(corpus, output):
    """Function writes a list to an indicated csv-file."""
    with open(output, 'w', encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerows(corpus)


for filename in os.listdir(PATH):
    if filename.endswith(".zip"):
        name = os.path.join(
            PATH,
            os.path.splitext(os.path.basename(filename))[0]
            )

        if not os.path.isdir(name):
            filename = PATH + filename
            zipper = zipfile.ZipFile(filename)
            os.mkdir(name)
            zipper.extractall(path=PATH)

for root, dirs, _ in os.walk(PATH):
    sorted_dirs = sorted(dirs)

    for d in sorted_dirs:
        path_sub = os.path.join(root, d)
        HEADER += 1

        unpack(path_sub, '*_ph.csv', full_ph_corpus, check_cols=True, skip_header=True)
        unpack(path_sub, '*_wd.csv', full_wd_corpus, skip_header=True)
        unpack(path_sub, '*_metadata.csv', file_metadata, add_glotto=True)
        unpack(path_sub, '*_gloss-abbreviations.csv', glosses, add_glotto=True)

write_corpus(full_ph_corpus, 'ph_data.csv')
write_corpus(full_wd_corpus, 'wd_data.csv')
write_corpus(file_metadata, 'file_metadata.csv')
write_corpus(glosses, 'glosses.csv')
