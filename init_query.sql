SELECT
    phone.cldf_id AS ID,
	phone.cldf_name AS Value,
	phone.duration AS Duration,
    word.cldf_languageReference AS Language,
    word.speaker_id AS Speaker,
    CASE
        WHEN phone.cldf_id in (select cldf_id FROM utterance_initials) THEN 1 ELSE 0
        END utt_initial,
    CASE
        WHEN phone.cldf_id in (select cldf_id FROM word_initials) THEN 1 ELSE 0
        END word_initial,
	CASE
		WHEN sound.cldf_cltsReference LIKE '%voiced%' THEN 'voiced' ELSE 'voiceless'
		END voicing,
    CASE
        WHEN sound.cldf_cltsReference LIKE '%stop%' THEN 'stop' 
		WHEN sound.cldf_cltsReference LIKE '%fricative%' THEN 'fricative' ELSE 'sonorant'
        END sound_class
	(ps.num_phones - sd.avg_num_phones) / sd.num_phones AS z_num_phones,
	(utt.log_speech_rate - sd.avg_speech_rate) / sd.speech_rate AS z_speech_rate,
	(fs.word_freq - sd.avg_word_freq) / sd.word_freq AS z_word_freq
FROM
    "phones.csv" AS phone,
    "words.csv" AS word,
    ParameterTable AS sound
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
	formstats as fs -- word frequency
ON
	word.cldf_name = fs.cldf_name AND
	word.cldf_languageReference = fs.cldf_languageReference
LEFT JOIN
    utterances AS utt  -- utterance-level stats such as speech rate.
ON
    phone.u_ID = utt.u_id
LEFT JOIN
	sdev AS sd
ON 
	word.cldf_languageReference = sd.cldf_languageReference
WHERE
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
    phone.duration < t.threshold AND
	phone.duration > 0.03
;