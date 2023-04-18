"""

"""
from time import time

from cldfbench_doreco import Dataset
from .audio import Database


def run(args):
    import collections
    ds = Dataset()
    db = Database(ds.dir / 'doreco.sqlite')
    s = time()
    res = db.query("""
    SELECT s.cldf_name, s.* FROM (
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
    print('{:.1f}secs: Word-initial (but not utterance-initial) not-long consonants in phones.csv: {}'.format(time() - s, len(res)))
    s = time()

    #c = collections.Counter()
    #for row in res:
    #    c.update([row[0]])
    #for k, v in c.most_common(10):
    #    print(k, v)
    #return

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
    print('{:.1f}secs: Utterance initials in phones.csv: {}'.format(time() - s, len(res)))
    s = time()

    # UtteranceLength and Speech rate as view:
    """
    create view utterance as
    select
        p.u_id as uid, 
        count(p.cldf_id) as length,
        count(p.cldf_id)/sum(p.duration) as speech_rate 
    from `phones.csv` as p group by p.u_id;
    """

    # PhonemesPerWord, logPhonemesPerWord
    # WordsPerFile

    # duration, logDuration
    # np.log : log(exp(1), 10)
