"""
This module combines all zip.files from the data folder
and merges them into individual csv-files.
Languages with a ND-license are not included.
"""
import glob
import os
import csv
import zipfile

PATH = './data/'
full_ph_corpus = []
full_wd_corpus = []
file_metadata = []
glosses = []


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
    for d in dirs:
        path_sub = os.path.join(root, d)  # this is the current subfolder
        for filename in glob.glob(os.path.join(path_sub, '*_ph.csv')):
            with open(filename, mode='r', encoding="utf8") as file:
                data = csv.reader(file)
                for entry in data:
                    full_ph_corpus.append(entry)
        for filename in glob.glob(os.path.join(path_sub, '*_wd.csv')):
            with open(filename, mode='r', encoding="utf8") as file:
                data = csv.reader(file)
                for entry in data:
                    full_wd_corpus.append(entry)
        for filename in glob.glob(os.path.join(path_sub, '*_metadata.csv')):
            with open(filename, mode='r', encoding="utf8") as file:
                data = csv.reader(file)
                for entry in data:
                    file_metadata.append(entry)
        for filename in glob.glob(os.path.join(path_sub, '*_gloss-abbreviations.csv')):
            with open(filename, mode='r', encoding="utf8") as file:
                data = csv.reader(file)
                for entry in data:
                    glosses.append(entry)

# print(len(full_corpus))

with open('ph_data.csv', 'w', encoding="utf8") as file:
    writer = csv.writer(file)
    writer.writerows(full_ph_corpus)
with open('wd_data.csv', 'w', encoding="utf8") as file:
    writer = csv.writer(file)
    writer.writerows(full_wd_corpus)
with open('file_metadata.csv', 'w', encoding="utf8") as file:
    writer = csv.writer(file)
    writer.writerows(file_metadata)
with open('glosses.csv', 'w', encoding="utf8") as file:
    writer = csv.writer(file)
    writer.writerows(glosses)
