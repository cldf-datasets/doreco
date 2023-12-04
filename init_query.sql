SELECT
    phone.cldf_id AS ID,
	phone.cldf_name AS Value,
	1000*phone.duration AS Duration,
    word.cldf_languageReference AS Language,
    word.speaker_id AS Speaker,
    CASE
        WHEN phone.cldf_id in (select cldf_id FROM utterance_initials) THEN 1 ELSE 0
        END utt_initial, -- whether or not the phone is in utterance initial position
    CASE
        WHEN phone.cldf_id in (select cldf_id FROM word_initials) THEN 1 ELSE 0
        END word_initial, -- whether or not the phone is in word initial position
	CASE
		WHEN sound.cldf_cltsReference LIKE '%voiced%' THEN 'voiced' ELSE 'voiceless'
		END voicing,
    CASE
        WHEN sound.cldf_cltsReference LIKE '%stop%' THEN 'stop' 
		WHEN sound.cldf_cltsReference LIKE '%fricative%' THEN 'fricative' ELSE 'sonorant'
        END sound_class,
    -- normalized word length:
	ROUND(((phones_per_word.num_phones - sd_num_phones.avg_num_phones) / sd_num_phones.num_phones), 3) AS z_num_phones,
	-- normalized speech rate of the utterance:
	ROUND(((utt.log_speech_rate - sd_speech_rate.avg_speech_rate) / sd_speech_rate.speech_rate), 3) AS z_speech_rate,
	-- normalized frequency of the word form:
	ROUND(((forms.freq - sd_word_freq.avg_word_freq) / sd_word_freq.word_freq), 3) AS z_word_freq
FROM
    "phones.csv" AS phone,
    "words.csv" AS word, -- word-level metadata joined ON phone.wd_id = word.cldf_id
    ParameterTable AS sound -- sound-level metadata joined ON phone.cldf_parameterReference = sound.cldf_id
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
	phones_per_word
ON
	phone.wd_id = phones_per_word.wd_id
LEFT JOIN
	forms
ON
	word.cldf_name = forms.form AND
	word.cldf_languageReference = forms.cldf_languageReference
LEFT JOIN
    utterances AS utt  -- utterance-level stats such as speech rate.
ON
    phone.u_ID = utt.u_id
LEFT JOIN -- summary stats on word length per language
    (
        SELECT
            stdev(p.num_phones) AS num_phones,
            AVG(p.num_phones) AS avg_num_phones,
            w.cldf_languageReference
        FROM
            phones_per_word as p
        LEFT JOIN
            'words.csv' AS w
        ON
            p.wd_id = w.cldf_id
        GROUP BY
            w.cldf_languageReference
    ) AS sd_num_phones
ON word.cldf_languageReference = sd_num_phones.cldf_languageReference
LEFT JOIN -- summary stats on speech rate per language
    (
        SELECT
            stdev(log_speech_rate) AS speech_rate,
	        AVG(log_speech_rate) AS avg_speech_rate,
	        cldf_languageReference
        FROM
            utterances
        GROUP BY
            cldf_languageReference
    ) AS sd_speech_rate
ON word.cldf_languageReference = sd_speech_rate.cldf_languageReference
LEFT JOIN -- summary stats on word form frequency per language
    (
        SELECT
            stdev(freq) AS word_freq,
            AVG(freq) AS avg_word_freq,
            cldf_languageReference
        FROM
            forms
        GROUP BY
            cldf_languageReference
    ) AS sd_word_freq
ON 
	word.cldf_languageReference = sd_word_freq.cldf_languageReference
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