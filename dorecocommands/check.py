"""

"""
from cldfbench_doreco import Dataset, SILENT_PAUSE, LABEL_PATTERN


def valid_word(row):
    wd = row['wd'].strip()
    return bool(wd) and wd != SILENT_PAUSE and not LABEL_PATTERN.fullmatch(wd)


def run(args):
    ds = Dataset()

    for row in ds.raw_dir.read_csv('languages.csv', dicts=True):
        words = ds.raw_dir.read_csv('{}_wd.csv'.format(row['Glottocode']), dicts=True)
        valid = sum(1 for w in words if valid_word(w))
        if valid != int(row['Extended word tokens']):
            args.log.warning('{}: expected {} word tokens, got {}'.format(
                row['Glottocode'], row['Extended word tokens'], valid))
