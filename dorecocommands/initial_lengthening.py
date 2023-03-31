"""

"""
from cldfbench_doreco import Dataset
from .audio import Database


def run(args):
    ds = Dataset()
    db = Database(ds.dir / 'doreco.sqlite')

    res = db.query("""
    SELECT s.* FROM (
    SELECT
        p.*, 
        row_number() OVER (PARTITION BY wd_ID ORDER BY cldf_id) wnum,
        row_number() OVER (PARTITION BY u_ID ORDER BY cldf_id) unum 
    FROM 
        `phones.csv` AS p) AS s,
        parametertable as ipa
    WHERE
        s.cldf_parameterReference = ipa.cldf_id and
        ipa.cldf_cltsReference like '% consonant' and
        ipa.cldf_cltsReference not like '%long %' and
        s.wnum = 1 AND s.unum != 1 AND s.token_type = 'xsampa';
    """)
    print('Word-initial (but not utterance-initial) not-long consonants in phones.csv: {}'.format(len(res)))

    res = db.query("""
SELECT s.* FROM (
SELECT
    p.*, 
    row_number() OVER (PARTITION BY u_ID ORDER BY cldf_id) rownum 
FROM 
    `phones.csv` AS p) AS s
WHERE
    s.rownum = 1 AND s.token_type = 'xsampa';
""")
    print('Utterance initials in phones.csv: {}'.format(len(res)))

    # UtteranceLength and Speech rate:
    """
    select p.u_id, count(p.cldf_id), count(p.cldf_id)/sum(p.duration) as sr from `phones.csv` as p group by p.u_id limit 10;
    """

    # PhonemesPerWord, logPhonemesPerWord
    # WordsPerFile

    # duration, logDuration
    # np.log : log(exp(1), 10)
