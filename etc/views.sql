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
    count(p.cldf_id) AS num_phones,
    count(p.cldf_id)/sum(p.duration) as speech_rate,
    log(exp(1), count(p.cldf_id)/sum(p.duration)) AS log_speech_rate
FROM
    'phones.csv' AS p
GROUP BY p.u_id;
