SELECT
    phone.*,
    word.cldf_languageReference AS Language,
    word.speaker_id AS Speaker,
    utt.speech_rate AS SpeechRate,
    ps.num_phones AS num_phones,
	(ps.num_phones - z_p.avg_num_phones) / ps.num_phones AS z_num_phones,
    CASE
        WHEN phone.cldf_id in (select cldf_id from utterance_initials) then 1 else 0
        END utt_initial,
    CASE
        WHEN phone.cldf_id in (select cldf_id from word_initials) then 1 else 0
        END word_initial,
    CASE
        WHEN sound.cldf_cltsReference like '%stop%' then 'stop' else 'dunno'
        END sound_class,
	-- standardize speech rate
	(utt.log_speech_rate - z.avg_speech_rate) / z.speech_rate AS z_speech_rate,
    ws.WordFreq AS freq,
	ls.WordCount AS count
	-- ws.WordFreq/ls.WordCount AS relation
FROM
    "phones.csv" AS phone,
    "words.csv" AS word,
    ParameterTable AS sound,
    wordstats AS ws,  -- language-level stats on words.
	langstats AS ls
LEFT JOIN
    (
        SELECT
            -- Here we compute the threshold for exclusion of unusually long phones.
            w.speaker_id, avg(p.duration) + 3 * stdev(p.duration) AS threshold
        FROM
            `phones.csv` AS p,
            `words.csv` AS w
        WHERE
            p.cldf_parameterreference IS NOT NULL AND
            p.wd_id = w.cldf_id
        GROUP BY w.speaker_id  -- Thresholds are computed per speaker.
    ) AS t
ON
    word.speaker_id = t.speaker_id
LEFT JOIN
	phonestats as ps -- number of phones per word
ON
	phone.wd_id = ps.wd_id
LEFT JOIN
	(
	    SELECT stdev(ps.num_phones) AS num_phones, AVG(ps.num_phones) AS avg_num_phones FROM phonestats as ps
    ) AS z_p
LEFT JOIN
    utterances AS utt  -- utterance-level stats such as speech rate.
ON
    phone.u_ID = utt.u_id
LEFT JOIN
	(
	    SELECT stdev(u.log_speech_rate) AS speech_rate, AVG(u.log_speech_rate) AS avg_speech_rate FROM utterances as u
    ) AS z
WHERE
    (ws.cldf_languageReference = word.cldf_languageReference AND ws.cldf_name = word.cldf_name) AND
    ls.cldf_languageReference = word.cldf_languageReference AND
    phone.wd_id = word.cldf_id AND
    phone.cldf_parameterReference = sound.cldf_id AND
    -- We only consider non-long, pulmonic consonants ...
    sound.cldf_cltsReference LIKE '%_consonant' AND
    sound.cldf_cltsReference NOT LIKE '%click%' AND
    sound.cldf_cltsReference NOT LIKE '%implosive%' AND
    sound.cldf_cltsReference NOT LIKE '%ejective%' AND
    sound.cldf_cltsReference NOT LIKE '%long%' AND
    -- ... and exclude utterance-initial stops.
    NOT (phone.cldf_id in (select cldf_id from utterance_initials) AND sound.cldf_cltsReference LIKE '%stop%'
	) AND
    -- We also exclude phonemes with unusually long durations, which hint at annotation errors.
    phone.duration < t.threshold
;