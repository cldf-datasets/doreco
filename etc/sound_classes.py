import csv
from pyclts import CLTS
clts = CLTS('/Users/blum/Library/Application Support/cldf/clts')

# print(clts.bipa['ts'].name)

sounds = []
with open('orthography.tsv', 'r', encoding="utf8") as ortho:
    data = csv.reader(ortho, delimiter='\t')
    for row in data:
        sounds.append(row)


for sound in sounds:
    # print(sound)
    # print(clts.bipa[sound[1]].name)
    sound_class = clts.bipa[sound[1]].name

    if sound_class == None:
        pass
    else:
        if "voiced" in sound_class:
            vc = "voiced"
        elif "voiceless" in sound_class:
            vc = "voiceless"
        else:
            vc = "Should this really happen? Please consult your CLTS doctor"

        if "vowel" in sound_class:
            sc = "vowel"

        elif "geminate" in sound_class:
            sc = "geminate"
        
        elif "sonorant" in sound_class:
            sc = "sonorant"
        
        elif "sibilant" in sound_class:
            sc = "sonorant"

        elif "affricate" in sound_class:
            sc = "stop"
        
        elif "stop" in sound_class:
            sc = "stop"
        
        elif "fricative" in sound_class:
            sc = "fricative"

        else:
            sc = "Problem"

        print(vc, sc)