-- Word initial phones
CREATE VIEW IF NOT EXISTS word_initials AS
SELECT s.* FROM (
    SELECT
        p.*,
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
        row_number() OVER (PARTITION BY u_ID ORDER BY cldf_id) rownum
    FROM
        'phones.csv' AS p
    ) AS s
WHERE
    s.rownum = 1 AND s.token_type = 'xsampa';

-- Utterance information
CREATE VIEW IF NOT EXISTS utterances AS
SELECT
    p.u_id AS u_id,
	-- count of utterance to see how many phones in utterance
    count(p.u_id)/sum(p.duration) as speech_rate,
    log(exp(1), count(p.cldf_id)/sum(p.duration)) AS log_speech_rate
FROM
    'phones.csv' AS p
GROUP BY p.u_id;


-- Utterance information
DROP VIEW IF EXISTS phonestats;
CREATE VIEW phonestats AS
SELECT
    w.cldf_id as wd_id,
	-- count of words as count of phones
	-- needs to be calculated before exclusion
	count(p.wd_id) AS num_phones
FROM
    'phones.csv' AS p,
	'words.csv' AS w
WHERE
	p.wd_id = w.cldf_id
	-- I need to group on wd_id instead
GROUP BY p.wd_id;


-- Word count per lang
DROP VIEW IF EXISTS langstats;
CREATE VIEW langstats AS                                 
SELECT                                                             
	w.cldf_languageReference,
	-- word form frequency
	count(w.cldf_id) as WordCount
FROM
	'words.csv' as w
GROUP BY w.cldf_languageReference;


-- Word form frequency
DROP VIEW IF EXISTS wordstats;
CREATE VIEW wordstats AS                                 
SELECT                                                             
	w.cldf_languageReference,
	w.cldf_name,
	-- word form frequency
	count(w.cldf_id) as WordFreq
FROM
	'words.csv' as w
GROUP BY w.cldf_languageReference, w.cldf_name;

-- filter non-pulmonic consonants, i.e. click, ejective, implosive (other manners?)