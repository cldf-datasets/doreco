<a name="ds-genericmetadatajson"> </a>

# Generic CLDF dataset derived from the DoReCo core corpus

**CLDF Metadata**: [Generic-metadata.json](./Generic-metadata.json)

**Sources**: [sources.bib](./sources.bib)

property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | Seifart, Frank, Ludger Paschen & Matthew Stave (eds.). 2022. Language Documentation Reference Corpus (DoReCo) 1.2. Berlin & Lyon: Leibniz-Zentrum Allgemeine Sprachwissenschaft & laboratoire Dynamique Du Langage (UMR5596, CNRS & Université Lyon 2). DOI:10.34847/nkl.7cbfq779
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Generic](http://cldf.clld.org/v1.0/terms.rdf#Generic)
[dc:license](http://purl.org/dc/terms/license) | CC-BY
[dcat:accessURL](http://www.w3.org/ns/dcat#accessURL) | https://github.com/cldf-datasets/doreco/
[prov:wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) | <ol><li><a href="https://github.com/cldf-datasets/doreco//tree/ab2a7f9">cldf-datasets/doreco/ ab2a7f9</a></li><li><a href="https://github.com/glottolog/glottolog/tree/v4.7">Glottolog v4.7</a></li></ol>
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>python</strong>: 3.10.6</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | doreco
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-mediacsv"></a>Table [media.csv](./media.csv)

This table lists audio files which have been transcribed/annotated for DoReCo corpora. Note that only downloadable files are listed.

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF MediaTable](http://cldf.clld.org/v1.0/terms.rdf#MediaTable)
[dc:extent](http://purl.org/dc/terms/extent) | 583


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Media_Type](http://cldf.clld.org/v1.0/terms.rdf#mediaType) | `string` | 
[Download_URL](http://cldf.clld.org/v1.0/terms.rdf#downloadUrl) | `anyURI` | 
`rec_date` | `string` | 
`rec_date_assignment_certain` | `string` | 
`genre` | `string` | 
`genre_stim` | `string` | 
`gloss` | `string` | Information on whether/how the audio has been annotated with glosses.
`transl` | list of `string` (separated by `/`) | Information on meta languages for which the annotations contain translations.
`sound_quality` | `string` | 
`background_noise` | `string` | 
[Corpus_ID](http://cldf.clld.org/v1.0/terms.rdf#contributionReference) | `string` | References [contributions.csv::ID](#table-contributionscsv)
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)

## <a name="table-examplescsv"></a>Table [examples.csv](./examples.csv)

Some corpora in DoReCo contain data annotated with glosses. Such glossed data is extracted into a CLDF ExampleTable.

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ExampleTable](http://cldf.clld.org/v1.0/terms.rdf#ExampleTable)
[dc:extent](http://purl.org/dc/terms/extent) | 94671


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Primary_Text](http://cldf.clld.org/v1.0/terms.rdf#primaryText) | `string` | The example text in the source language.
[Analyzed_Word](http://cldf.clld.org/v1.0/terms.rdf#analyzedWord) | list of `string` (separated by `	`) | The sequence of words of the primary text to be aligned with glosses
[Gloss](http://cldf.clld.org/v1.0/terms.rdf#gloss) | list of `string` (separated by `	`) | The sequence of glosses aligned with the words of the primary text
[Translated_Text](http://cldf.clld.org/v1.0/terms.rdf#translatedText) | `string` | The translation of the example text in a meta language
[Meta_Language_ID](http://cldf.clld.org/v1.0/terms.rdf#metaLanguageReference) | `string` | References the language of the translated text<br>References [languages.csv::ID](#table-languagescsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[File_ID](http://cldf.clld.org/v1.0/terms.rdf#mediaReference) | `string` | Link to the audio file to which start and end markers pertain.<br>References [media.csv::ID](#table-mediacsv)
`start` | `decimal` | Start of the word in the linked sound file in (floating point) seconds.
`end` | `decimal` | End of the word in the linked sound file in (floating point) seconds.
`duration` | `decimal` | Duration of the word in the linked sound file in (floating point) seconds.

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 42


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal` | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal` | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | `string` | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-contributionscsv"></a>Table [contributions.csv](./contributions.csv)

Each DoReCo language corpus is listed as separate contribution in this table.

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ContributionTable](http://cldf.clld.org/v1.0/terms.rdf#ContributionTable)
[dc:extent](http://purl.org/dc/terms/extent) | 42


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key<br>References [languages.csv::ID](#table-languagescsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Contributor](http://cldf.clld.org/v1.0/terms.rdf#contributor) | `string` | 
[Citation](http://cldf.clld.org/v1.0/terms.rdf#citation) | `string` | 
`Archive` | `string` | 
`Archive_link` | `string` | 
`AnnotationLicense` | `string` | 
`AudioLicense` | `string` | 
`DOI` | `string` | 

## <a name="table-parameterscsv"></a>Table [parameters.csv](./parameters.csv)

The ParameterTable lists IPA phones which appear in the DoReCo corpus (if a correspondence to the X-Sampa representation could be determined). If possible, IPA phones are linked to CLTS' BIPA representation, giving access to the CLTS feature system.

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ParameterTable](http://cldf.clld.org/v1.0/terms.rdf#ParameterTable)
[dc:extent](http://purl.org/dc/terms/extent) | 316


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | The IPA representation of the sound.
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[ColumnSpec](http://cldf.clld.org/v1.0/terms.rdf#columnSpec) | `json` | 
[CLTS_ID](http://cldf.clld.org/v1.0/terms.rdf#cltsReference) | `string` | CLTS ID of the sound, i.e. the underscore-separated ordered list of features of the sound.

## <a name="table-speakerscsv"></a>Table [speakers.csv](./speakers.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 289


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
`age` | `integer` | 
`age_assignment_certain` | `string` | 
`sex` | `string` | 

## <a name="table-phonescsv"></a>Table [phones.csv](./phones.csv)

This table lists individual, time-aligned phones.

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 1863834


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ph_ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[ph](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | See the description of the Token_Type column.
[IPA](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | Link to corresponding IPA phoneme, with details given in ParameterTable<br>References [parameters.csv::ID](#table-parameterscsv)
`u_ID` | `string` | Utterance ID. Utterances are words/phones delimited by silent pauses.
`Token_Type` | `string` | Not all rows in this table correspond to actual phones. If a row does the Token_Type is 'xsampa' and the `ph` column holds the X-SAMPA representation of the phone, otherwise it is a 'pause' or a 'label'.  Labels consist of two opening brackets, the label proper, a closing bracket, the content (optional), and another closing bracket, e.g. `<<ui>word>`. Labels may also appear on their own if the content is not known, e.g. `<<ui>>`. Valid proper labels are  - fp: Filled pause - fs: False start - pr: Prolongation - fm: Foreign material - sg: Singing - bc: Backchannel - id: Ideophone - on: Onomatopoeic - wip: Word-internal pause - ui: Unidentifiable  Silent pauses are marked by a special symbol, `<p:>`. The location of silent pauses is manually checked by the DoReCo team, while the symbol itself is inserted by the WebMAUS service. Unlike labels, the <p:> symbol has only one of each bracket, and no other content may be included in it.
`start` | `decimal` | Start of the phone in the linked sound file in (floating point) seconds.
`end` | `decimal` | End of the phone in the linked sound file in (floating point) seconds.
`duration` | `decimal` | Duration of the phone in the linked sound file in (floating point) seconds.
`wd_ID` | `string` | Link to corresponding word.<br>References [words.csv::wd_ID](#table-wordscsv)

## <a name="table-wordscsv"></a>Table [words.csv](./words.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 896661


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[wd_ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[wd](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | The word form transcribed into orthography.
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[File_ID](http://cldf.clld.org/v1.0/terms.rdf#mediaReference) | `string` | Link to the audio file to which start and end markers pertain.<br>References [media.csv::ID](#table-mediacsv)
`Speaker_ID` | `string` | References [speakers.csv::ID](#table-speakerscsv)
`start` | `decimal` | Start of the word in the linked sound file in (floating point) seconds.
`end` | `decimal` | End of the word in the linked sound file in (floating point) seconds.
`duration` | `decimal` | Duration of the word in the linked sound file in (floating point) seconds.
`ref` | `string` | 
[Example_ID](http://cldf.clld.org/v1.0/terms.rdf#exampleReference) | `string` | Words that appear in glossed utterances are linked to an Example.<br>References [examples.csv::ID](#table-examplescsv)
`mb` | list of `string` (separated by ` `) | 
`ps` | list of `string` (separated by ` `) | 
`gl` | list of `string` (separated by ` `) | 

## <a name="table-glossescsv"></a>Table [glosses.csv](./glosses.csv)

Gloss abbreviations used for glosses in a corpus.

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 2053


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Gloss](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`LGR` | `boolean` | Flag, signaling whether a gloss abbreviation is a standard, Leipzig-Glossing-Rules abbreviation.
`Meaning` | `string` | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)

