-- Word initial phones
CREATE VIEW IF NOT EXISTS word_initials AS
SELECT s.* FROM (
    SELECT
        p.*,
        -- We use a window function to be able to determine the first row in a batch.
        row_number() OVER (PARTITION BY wd_ID ORDER BY cldf_id) rownum
    FROM
        'phones.csv' AS p
    ) AS s
WHERE
    s.rownum = 1 AND s.token_type = 'xsampa';

-- Utterance initial phones
CREATE VIEW IF NOT EXISTS utterance_initials AS
SELECT s.* FROM (
    SELECT
        p.*,
        -- We use a window function to be able to determine the first row in a batch.
        row_number() OVER (PARTITION BY u_ID ORDER BY cldf_id) rownum
    FROM
        'phones.csv' AS p
    ) AS s
WHERE
    s.rownum = 1 AND s.token_type = 'xsampa';

-- Utterance information
DROP VIEW IF EXISTS utterances;
CREATE VIEW IF NOT EXISTS utterances AS
SELECT
    p.u_id AS u_id,
	-- count of utterance to see how many phones in utterance
    count(p.u_id)/sum(p.duration) AS speech_rate,
    log(exp(1), count(p.cldf_id)/sum(p.duration)) AS log_speech_rate,
	w.cldf_languageReference AS cldf_languageReference
FROM
    'phones.csv' AS p
LEFT JOIN
	'words.csv' AS w
ON
	p.wd_id = w.cldf_id
GROUP BY p.u_id;

-- Number of phones per word
DROP VIEW IF EXISTS phones_per_word;
CREATE VIEW phones_per_word AS
SELECT
    wd_id,
	log(exp(1), count(cldf_id)) AS num_phones
FROM
    'phones.csv'
GROUP BY wd_id;

-- Number of spoken words per language
DROP VIEW IF EXISTS words_per_language;
CREATE VIEW words_per_language AS
SELECT
	w.cldf_languageReference,
	count(w.cldf_id) AS num_words
FROM
	'words.csv' AS w
GROUP BY w.cldf_languageReference;

-- Table of forms, i.e. of distinct word forms per language.
DROP VIEW IF EXISTS forms;
CREATE VIEW forms AS
SELECT
	log(exp(1), (count(ws.cldf_id) / cast(ls.num_words AS float))) AS freq,
	ws.cldf_name AS form,
	ls.cldf_languageReference AS cldf_languageReference
FROM
	'words.csv' AS ws
LEFT JOIN
	words_per_language AS ls
ON
	ws.cldf_languageReference = ls.cldf_languageReference
GROUP BY ws.cldf_name, ws.cldf_languageReference;
