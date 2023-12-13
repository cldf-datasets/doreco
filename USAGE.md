# Using the DoReCo CLDF data

Before you use the DoReCo CLDF data you should read through the data model description at
[cldf/README.md](cldf/README.md).

## Coverage

This dataset is derived from the DoReCo data as follows:

- DoReCo data is 
  **limited to the core data with annotations released under a license without [ND (no derivatives) clause](https://pitt.libguides.com/openlicensing/cc-noderivatives)**
  (because we add annotations which would violate this license).
- Morpheme-aligned data is converted into IGT instances in an ExampleTable.
- Two minor issues with the DoReCo data are fixed, namely a handful of phones in the Evenki corpus
  being linked to two words, and phones/words in the Yucatec corpus having a typo in the speaker
  reference.
- Links from phones to IPA symbols, and eventually to CLTS sounds are added, based on the
  orthography profile in [etc/orthography.tsv](etc/orthography.tsv)

Note that the `cldfbench.Dataset` implementation in the Python module [cldfbench_doreco.py](cldfbench_doreco.py)
provides functionality to also

- download the ND-licensed data (which is appropriate for analysis, but not for re-destribution)
- download the audio files on which the DoReCo data is based.

To do so,

1. Install the required Python packages (preferably in a fresh virtual environment) via

   ```shell
   pip install -e .
   ```

2. Download (and unpack) the CLTS v2.2.0 data from [DOI: 10.5281/zenodo.5583682](https://doi.org/10.5281/zenodo.5583682).
3. Download (and unpack) the Glottolog v4.8 data from [DOI: 10.5281/zenodo.7398962](https://doi.org/10.5281/zenodo.8131084).
4. Then run

   ```shell
   cldfbench download cldfbench_doreco.py
   ```

   and answer appropriately when prompted.
5. The CLDF data can then be created running

   ```shell
   cldfbench makecldf cldfbench_doreco.py --glottolog PATH/TO/glottolog-4.8/
   ```

## Overview

Due to the size of the DoReCo corpus - ~ 2,000,000 annotated phones (if ND-licensed data is incuded) - analysing
the data is made a lot easier (and quicker) when data is accessed via SQL[^1] from the
[CLDF SQLite](https://github.com/cldf/cldf/blob/master/extensions/sql.md) database.

Create the SQLite database by running

```shell
cldf createdb cldf/Generic-metadata.json doreco.sqlite
```

An [entity relationship diagram](https://en.wikipedia.org/wiki/Entity%E2%80%93relationship_model),
visualizing the schema of the resulting database looks as follows:

![ERD](erd.svg)

Notes:

- CLDF's `ParameterTable` stores metadata about sounds, linked from `phones.csv`, if `Token_Type` is
  `xsampa` and an IPA sound corresponding to the X-SAMPA symbol could be determined.
- The database has 4 non-CLDF-standard tables:
  - `glosses.csv`, listing gloss abbreviations used in IGT examples,
  - `speakers.csv`, providing metadata about (core) speakers. Linked from `words.csv`, if available.
  - `words.csv`, listing the time-aligned words in the corpus, 
  - `phones.csv`, listing the time-aligned phones in the corpus.

  These non-CLDF-standard tables are named after the corresponding filename. Thus, to prevent the
  `.` in the name from confusing SQLite, the [names must always be quoted](https://www.sqlite.org/lang_keywords.html), i.e. wrapped in
  quotes.

## Data access via SQL queries

Time-aligned phones and words make up the core contribution of the DoReCo dataset. This data is stored
in the `phones.csv` and `words.csv` tables, respectively, and can be queried in a straightforward way.

Retrieving particular phones, e.g. word initials is best done using somewhat advanced
SQL constructs like [window functions](https://www.sqlitetutorial.net/sqlite-window-functions/), though.

An SQL query to retrieve these could look as follows:

```sql
SELECT s.* FROM (
    SELECT
        p.*,
        row_number() OVER (PARTITION BY wd_ID ORDER BY cldf_id) rownum
    FROM
        'phones.csv' AS p
    ) AS s
WHERE
    s.rownum = 1 AND s.token_type = 'xsampa';
```

Now, since SQLite supports [views](https://en.wikipedia.org/wiki/View_(SQL)), we can hide this complexity
by creating a corresponding view:

```sql
CREATE VIEW word_initials AS
SELECT s.* FROM (
    SELECT
        p.*,
        row_number() OVER (PARTITION BY wd_ID ORDER BY cldf_id) rownum
    FROM
        'phones.csv' AS p
    ) AS s
WHERE
    s.rownum = 1 AND s.token_type = 'xsampa';
```

and then use this view just like the `phones.csv` table:

```sql
SELECT COUNT(*) FROM word_initials;
```

Note that views are regular SQL schema objects, and thus persisted in the database, i.e. will survive
closing the database connection. Views can be deleted by running a `DROP VIEW <name>` query.

Some useful views are defined in [etc/views.sql](etc/views.sql), and can be "installed" in the database
by running

```shell
sqlite3 -echo doreco.sqlite < etc/views.sql
```

## IPA metadata for phones

The default representation for phones in the DoReCo corpus is [X-SAMPA](https://en.wikipedia.org/wiki/X-SAMPA).
But the CLDF dataset adds IPA representations as well as mappings to CLTS sounds.
Thus, information about features of phones can be inferred from the `cldf_cltsReference` column, which
stores IDs from https://raw.githubusercontent.com/cldf-clts/clts/v2.2.0/data/sounds.tsv

```sql
SELECT
  sound_class,
  count(cldf_id) AS word_initial_instances
FROM (
       SELECT
         wi.cldf_id,
         CASE WHEN ipa.cldf_cltsReference LIKE '%_consonant' THEN 'consonant' ELSE 'vowel' END sound_class
       FROM
         word_initials AS wi,
         parametertable AS ipa
       WHERE
         wi.cldf_parameterReference = ipa.cldf_id
     ) AS s
GROUP BY sound_class;
```

Which will output a result similar to

sound class | word_initial_instances
--- | ---
consonant|313569
vowel|80820


## Utterances

Some kinds of analysis make most sense on utterance level, e.g. computing speech rate. (Utterances are
defined as any chunk of speech delimited by silent pauses.) To make this possible, `phones.csv` contains
a column `u_id` which allows for aggregating or partitioning phone data by utterance.

Computing speech rate per utterance as *ln(phones per second)* can be done with the following query:

```sql
SELECT
    p.u_id AS u_id, 
    count(p.cldf_id)/sum(p.duration) AS speech_rate 
FROM
    'phones.csv' AS p
GROUP BY p.u_id;
```

Again, this could be stored as a view (e.g. `utterances` in [etc/views.sql](etc/views.sql)), and joined as
needed for speech-rate sensitive analysis.

With a view `utterance_inititials` (see [etc/views.sql](etc/views.sql)) we could compute average
speech rates per language as follows:

```sql
SELECT
    w.cldf_languagereference,
    AVG(u.speech_rate) AS sr
FROM
    utterance_initials AS ui,
    'words.csv' AS w,
    utterances AS u
WHERE 
    u.u_id = ui.u_id AND ui.wd_id = w.cldf_id 
GROUP BY w.cldf_languagereference 
ORDER BY sr;
```

After storing this query in a file `sr_by_lang.sql` we can run it and pipe the output to a tool such
as [termgraph](https://pypi.org/project/termgraph/) to get a quick overview:

```shell
$ sqlite3 -csv doreco.sqlite < sr_by_lang.sql | termgraph

kama1351: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 8.50 
nngg1234: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 9.43 
lowe1385: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 9.49 
trin1278: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 10.15
yong1270: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 10.21
resi1247: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 10.45
sadu1234: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 10.54
arap1274: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 10.92
tsim1256: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.40
even1259: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.56
sanz1248: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.57
beja1238: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.58
orko1234: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.59
jeha1242: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.62
bora1263: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.72
sout3282: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.76
svan1243: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.86
dolg1241: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.89
goem1240: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 11.97
movi1243: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.03
cash1254: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.05
anal1239: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.18
kaka1265: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.20
stan1290: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.30
teop1238: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.35
taba1259: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.41
kark1256: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.49
pnar1238: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.54
ngal1292: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.78
sout2856: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.84
ruul1235: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 12.99
komn1238: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 13.03
jeju1234: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 13.08
savo1255: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 13.12
port1286: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 13.30
sumi1235: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 13.43
apah1238: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 13.81
goro1270: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 14.08
nort2641: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 14.11
bain1259: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 14.27
texi1237: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 14.41
vera1241: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 14.85
```

## Speaker information

Speaker information is available from the `speakers.csv` table, which can be joined to phones via
`words.csv`. E.g. the following query counts phones per speaker sex.

```sql
SELECT
    s.sex AS sex,
    count(p.cldf_id) AS num_phones
FROM
    'phones.csv' as p, 
    'words.csv' as w, 
    'speakers.csv' as s
WHERE
    p.wd_id = w.cldf_id AND w.speaker_id = s.cldf_id
GROUP BY s.sex;
```

sex | num_phones
--- | ---
f|721358
m|1142344


Correlations between speaker metadata and IPA phone metadata can be assessed by joining
the ParameterTable as well

```sql
SELECT
    s.sex AS sex, 
    ipa.cldf_name AS IPA, 
    count(p.cldf_id) AS num
FROM
    'phones.csv' AS p,
    'words.csv' AS w, 
    'speakers.csv' AS s, 
    parametertable AS ipa 
WHERE 
    p.wd_id = w.cldf_id AND
    w.speaker_id = s.cldf_id AND
    p.cldf_parameterReference = ipa.cldf_id AND
    ipa.cldf_cltsreference LIKE '%breathy%' 
GROUP BY p.cldf_name, s.sex;
```

lending superficial support to the hypothesis of "breathiness as a feminine voice characteristic"
(DOI: [10.1016/j.jvoice.2007.08.002](https://doi.org/10.1016/j.jvoice.2007.08.002)):

sex | IPA | num
--- | --- | ---
f|lʱ|31
m|lʱ|4
f|nʱ|16
m|nʱ|7

## IGT examples

Although the main focus of the DoReCo dataset are the time-aligned phones, the data also contains
many glossed example sentences. These are available in the CLDF ExampleTable.

So, for example, if we are interested in particular phenomena, we can first inspect the gloss labels
used for a language, and the number of examples containing the label:

```sql
SELECT 
    g.cldf_name AS label,         
    count(DISTINCT e.cldf_id) AS freq 
FROM
    'glosses.csv' AS g, 
    exampletable AS e 
WHERE 
    e.cldf_gloss LIKE '%' || g.cldf_name || '%' AND 
    g.cldf_languagereference = 'sout3282' AND 
    e.cldf_languagereference = 'sout3282' 
GROUP BY g.cldf_name 
ORDER BY freq 
LIMIT 3;
```

Notes:

- We use SQLite's string concatenation operator `||` to string together a suitable argument for
  the `LIKE` operator, making sure we match gloss containing `HORT`.
- To make sure the `LIKE` operator matches in a case sensitive way, you may have to issue a
  [`PRAGMA` statement](https://www.sqlite.org/pragma.html#pragma_case_sensitive_like) to force the correct behaviour:

  ```sql
  sqlite> PRAGMA case_sensitive_like=ON; 
  ```

label | freq
--- | ---
SUBJ|1
HORT|3
SUPR|7

And now we can list the aligned analyzed words and gloss lines of the matching IGT examples:

```sql
SELECT 
    cldf_analyzedword || char(10) || cldf_gloss || char(10) 
FROM 
    exampletable 
WHERE 
    cldf_gloss LIKE '%HORT%' AND cldf_languagereference = 'sout3282' ;
```

Note: We use SQLite's `char` function to insert newline characters in the output to "align" the IGTs.

```text
****	and	he	says	****	put	tha'	pony	in	****	he	says	and	****	in	the	cart	****	and	****	let's	try	him	****	he	says	****	I	want	that	for	Tom-Smith	atFaversham	****	if	it	suit-s	him
****	and	3SG.M	say.PRS.3SG	****	put.IMP	DIST.SG	pony	in	****	3SG.M	say.PRS.3SG	and	****	in	the	cart	****	and	****	HORT	try.INF	3SG.M.OBL	****	3SG.M	say.PRS.3SG	****	1SG	want.PRS	DIST.SG	for	Tom-Smith	at	Faversham	****	if	3SG.N	suit-PRS.3SG	3SG.M.OBL

****	well	****	put	him	in	****	let's	try	him
****	well	****	put.IMP	3SG.M.OBL	in	****	HORT	try.INF	3SG.M.OBL

[INT]	****	let's	leave	that	for	another	occasion	shall-we
[INT]	****	HORT	leave.INF	DIST.SG	for	another	occasion	shall-2PL
```

## Audio files

The DoReCo CLDF dataset also includes information about the publicly available audio files underlying the
corpora. The `start` and `end` columns in `words.csv` and `phones.csv` provide time stamps relative
to the linked files.

Thus, the following query retrieves the longest word in the sout3282 corpus, and its position in the
audio file:

```sql
sqlite> 
    SELECT 
        w.cldf_id, 
        w.cldf_exampleReference,
        w.cldf_name,
        count(p.cldf_id) AS wl,
        f.cldf_downloadUrl, 
        w.start, 
        w.end 
    FROM 
        'phones.csv' AS p, 
        'words.csv' AS w, 
        mediatable AS f 
    WHERE
        p.wd_id = w.cldf_id AND
        w.cldf_languageReference = 'sout3282' AND
        w.cldf_mediaReference = f.cldf_id 
    GROUP BY w.cldf_id 
    ORDER BY wl DESC 
    LIMIT 1;
sout3282_w020797|sout3282-1322|agricultural|12|https://api.nakala.fr/data/10.34847%2Fnkl.dcfbh2yw/830afcf32230aa859b39a92137edbdb18c5b174f|1950.493|1951.383
```

Plugging this data into HTML as follows

```html
<html>
<body>
<p>agricultural</p>
<audio preload="auto"
       controls="controls" 
       src="https://api.nakala.fr/data/10.34847%2Fnkl.dcfbh2yw/830afcf32230aa859b39a92137edbdb18c5b174f#t=1950.493,1951.383">
</audio>
</body>
</html>
```

and saving the file as `agricultural.html` you can get a light-weight corpus viewer by opening the file
in your browser and clicking the play button to listen to the word.

> ![audio player](audio.png)

IGT examples are linked to audio files as well. So we can do the same for the glossed example linked to
the word *agricultural*:

```sql
SELECT
    e.cldf_primaryText, 
    '<table><tr>' || char(10) || '<td>' || replace(e.cldf_analyzedword, char(9), '</td><td>') || '</td></tr>' || char(10) || '<tr><td>' || replace(e.cldf_gloss, char(9), '</td><td>') || '</td></tr></table>', 
    e.cldf_translatedText, 
    f.cldf_downloadUrl, 
    e.start, 
    e.end 
FROM 
    exampletable AS e, 
    mediatable AS f 
WHERE 
    e.cldf_mediareference = f.cldf_id AND e.cldf_id = 'sout3282-1322';
```

Note: While somewhat cumbersome, basic HTML can be strung together in SQL. In the above code we use the SQLite operator
`||` to concatenate strings, and the [char](https://www.sqlite.org/lang_corefunc.html#char) function to express the
"special" characters `\n` - newline - and `\t` - tab, and the [replace](https://www.sqlite.org/lang_corefunc.html#replace) function
to turn the tab-separated aligned words into HTML table cells.

Again, we can plug the result

```text
He knew all the -- Well, they kne-- the farms -- the bank managers them days, in the agricultural, knew as much about a farm as the farmer did, pretty well.|
<table><tr>
<td>he</td><td>knew</td><td>all</td><td>****</td><td><p:></td><td>well</td><td>they</td><td>kne</td><td>****</td><td>farm-s</td><td>the</td><td>****</td><td>bank-manager</td><td>them</td><td>day-s</td><td><p:></td><td>in</td><td>the</td><td>agricultural</td><td><p:></td><td>knew</td><td>as</td><td>much</td><td>about</td><td>a</td><td>farm</td><td>as</td><td>the</td><td>farmer</td><td>did</td><td>pretty</td><td>well</td></tr>
<tr><td>3SG.M</td><td>know.PST</td><td>all</td><td>****</td><td><p:></td><td>well</td><td>3PL</td><td>NC</td><td>****</td><td>farm-PL</td><td>the</td><td>****</td><td>bank_manager-PL</td><td>DIST.PL</td><td>day-PL</td><td><p:></td><td>in</td><td>the</td><td>agricultural</td><td><p:></td><td>know.PST</td><td>as</td><td>much</td><td>about</td><td>a</td><td>farm</td><td>as</td><td>the</td><td>farmer</td><td>do.PST</td><td>pretty</td><td>well</td></tr></table>
The bank managers in those days, in the agricultural, knew as much about a farm as the farmer did, pretty well.
https://api.nakala.fr/data/10.34847%2Fnkl.dcfbh2yw/830afcf32230aa859b39a92137edbdb18c5b174f
1944.132
1955.501
```

into an HTML file to get a (very) basic corpus viewer:

```html
<html>
<body>
<p><i>
He knew all the -- Well, they kne-- the farms -- the bank managers them days, in the agricultural, knew as much about a farm as the farmer did, pretty well.
</i></p>
<table><tr>
<td>he</td><td>knew</td><td>all</td><td>****</td><td><p:></td><td>well</td><td>they</td><td>kne</td><td>****</td><td>farm-s</td><td>the</td><td>****</td><td>bank-manager</td><td>them</td><td>day-s</td><td><p:></td><td>in</td><td>the</td><td>agricultural</td><td><p:></td><td>knew</td><td>as</td><td>much</td><td>about</td><td>a</td><td>farm</td><td>as</td><td>the</td><td>farmer</td><td>did</td><td>pretty</td><td>well</td></tr>
<tr><td>3SG.M</td><td>know.PST</td><td>all</td><td>****</td><td><p:></td><td>well</td><td>3PL</td><td>NC</td><td>****</td><td>farm-PL</td><td>the</td><td>****</td><td>bank_manager-PL</td><td>DIST.PL</td><td>day-PL</td><td><p:></td><td>in</td><td>the</td><td>agricultural</td><td><p:></td><td>know.PST</td><td>as</td><td>much</td><td>about</td><td>a</td><td>farm</td><td>as</td><td>the</td><td>farmer</td><td>do.PST</td><td>pretty</td><td>well</td></tr></table>
<p>
The bank managers in those days, in the agricultural, knew as much about a farm as the farmer did, pretty well.
</p>
<audio id="audio2" 
       preload="auto"
       controls="controls" 
       src="https://api.nakala.fr/data/10.34847%2Fnkl.dcfbh2yw/830afcf32230aa859b39a92137edbdb18c5b174f#t=1944.132,1955.501">
</audio>
</body>
</html>
```

[^1]: For a short overview of SQL and how to access SQL databases (and links to further reading), see https://github.com/dlce-eva/dlce-eva/blob/main/doc/sql.md

## Going further

### Parametrized queries

To make it easier to run parametrized queries (aka 
[queries with placeholders](https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders)),
this dataset - when installed via `pip install -e .` -
registers a [cldfbench command](https://github.com/cldf/cldfbench/blob/master/src/cldfbench/commands/README.md)
`query`. So, with a query

```sql
SELECT count(*) from `phones.csv` where duration > ?;                                                     
```

in a file called `phones_by_duration.sql` you can run the parametrized query from the commandline:

```shell
$ cldfbench doreco.query phones_by_duration.sql 0.7
  count(*)
----------
     60218
```

### Filtering phones based on features

Since phones are mapped to [BIPA sounds](https://clts.clld.org/parameters) listed in
`ParameterTable`, they can be filtered based on [feature values](https://github.com/cldf-clts/clts/blob/master/data/features.tsv),
because the column `ParameterTable.cldf_cltsReference` contains the sound name, which is a `_` delimited
concatenation of feature values for the sound.

Thus, for example selecting [pulmonic consonants](https://enunciate.arts.ubc.ca/linguistics/world-sounds/consonants-non-pulmonic/) 
can be done with SQL as follows

```sql
SELECT * FROM 
    `phones.csv` AS phone, 
    parametertable as sound
WHERE
    phone.cldf_parameterReference = sound.cldf_id AND 
    sound.cldf_cltsReference LIKE '%_consonant' AND 
    sound.cldf_cltsReference NOT LIKE '%click%' AND 
    sound.cldf_cltsReference NOT LIKE '%implosive%' AND 
    sound.cldf_cltsReference NOT LIKE '%ejective%'
;
```

### Filtering outliers

If you are accessing the DoReCo SQLite data from R, you can make use of 
[math extensions available with RSQLite](https://rsqlite.r-dbi.org/reference/initextension#available-functions-in-the-math-extension-1)
to push the "heavy lifting" when filtering outliers down to the database.

Thus, filtering out phones that are unusually long for the respective speaker (indicating incorrect
annotation) can be done running SQL as follows

```sql
> sql = "SELECT
    count(*) 
FROM 
    `phones.csv` AS phone,
    `words.csv` AS word
LEFT JOIN
    (
        SELECT
            w.speaker_id, avg(p.duration) + 3 * stdev(p.duration) AS threshold 
        FROM 
            `phones.csv` AS p, 
            `words.csv` AS w 
        WHERE 
            p.cldf_parameterreference IS NOT NULL AND
            p.wd_id = w.cldf_id 
        GROUP BY w.speaker_id
    ) AS t 
ON
    word.speaker_id = t.speaker_id
WHERE
    phone.cldf_parameterReference IS NOT NULL AND
    phone.wd_id = word.cldf_id AND
    phone.duration < t.threshold
;"
```

via RSQLite:

```r
> library(DBI)
> library(RSQLite)
> db <- dbConnect(RSQLite::SQLite(), "doreco.sqlite")
> RSQLite::initExtension(db)
> dbGetQuery(db, sql)
count(*)
1  1681433
```

Note that the SQLite library used in `cldfbench doreco.query` does also support
[math functions](https://www.sqlite.org/lang_mathfunc.html) as well as `stdev` as aggregate function. Thus, the above query can also be
run by saving the SQL as `query.sql` and running
```shell
cldfbench doreco.query q.sql 
  count(*)
----------
   1681433
```
