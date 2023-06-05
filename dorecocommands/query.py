"""
Query the DoReCo SQLite database.
"""
import math
import typing
import pathlib
import sqlite3
import contextlib
import collections

from clldutils.clilib import Table, add_format, PathType
from cldfbench_doreco import Dataset


class StdevFunc:
    """
    stdev as user-defined function for SQLite.

    Taken from Alex Forencich, see
    https://alexforencich.com/wiki/en/scripts/python/stdev
    """
    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 1

    def step(self, value):
        if value is None:
            return
        tM = self.M
        self.M += (value - tM) / self.k
        self.S += (value - tM) * (value - self.M)
        self.k += 1

    def finalize(self):
        if self.k < 3:
            return None
        return math.sqrt(self.S / (self.k-2))


class Database:
    """
    Provides SQLite database access through Python's sqlite3, meaning SQLite's built-in math
    functions (https://www.sqlite.org/lang_mathfunc.html) are available.
    In addition, we provide a `stdev` aggregate function.

    Usage:

        >>> with Database('doreco.sqlite').connection() as conn:
        ...     for row in conn.execute('select count(*) from `phones.csv`'):
        ...         print(row)
        ...
        (2389790,)
    """
    def __init__(self, fname):
        self.fname = fname

    def connection(self):
        conn = sqlite3.connect(str(self.fname))
        conn.create_aggregate("stdev", 1, StdevFunc)
        return contextlib.closing(conn)

    def query(self,
              sql: str,
              params: typing.Optional[tuple] = None,
              dicts: bool = False) -> typing.List[dict]:
        """
        Run `sql` on the database, returning the list of results.

        >>> Database('doreco.sqlite').query(
        ... "SELECT count(*) AS n FROM `phones.csv` WHERE duration > ?", (0.5,), dicts=True)
        [OrderedDict([('n', 107648)])]
        """
        with self.connection() as conn:
            cu = conn.execute(sql, params or ())
            if dicts:
                cols = [tuple[0] for tuple in cu.description]
                return [collections.OrderedDict(zip(cols, row)) for row in cu.fetchall()]
            return list(cu.fetchall())


def register(parser):
    parser.add_argument(
        'sql',
        type=PathType(type='file'),
        help='Path to a file containing the SQL to be run.')
    parser.add_argument(
        'parameters',
        nargs='*',
        help="If the SQL query uses placeholders (see "
             "https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders), the values for "
             "these can be passed as additional, positional arguments."
    )
    add_format(parser, 'simple')


def run(args):
    ds = Dataset()
    db = Database(ds.dir / 'doreco.sqlite')
    rows = db.query(
        pathlib.Path(args.sql).read_text(encoding='utf8'),
        params=args.parameters or None,
        dicts=True)

    with Table(args, *rows[0].keys()) as t:
        for row in rows:
            t.append(row.values())
