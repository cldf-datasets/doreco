"""
optionally download wav

select utterance initial and utterance final, then start and end, and chunk audio accordingly

https://github.com/dlce-eva/pyvoices/blob/main/src/pyvoices/commands/chunk.py

adding fade in/out and saving as mp3

sqlite> select distinct p.u_id from `phones.csv` as p, `words.csv` as w where p.wd_id = w.cldf_id and w.filename = 'doreco_anal1239_anm_20151216_10_Ngahring_WB_proverbs1';

"""
def run(args):
    pass