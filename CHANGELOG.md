# Changelog

All notable changes to this dataset will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## [1.2.1] - 2024-04-18

- Added a `Family` column to `LanguageTable`:
  ```
  $ csvstat -c Family cldf/languages.csv 
  9. "Family"

	Type of data:          Text
	Contains null values:  False
	Unique values:         25
	Longest value:         24, characters
	Most common values:    Austronesian (5x)
	                       Sino-Tibetan (4x)
	                       Indo-European (4x)
	                       Afro-Asiatic (3x)
	                       Atlantic-Congo (2x)
  ```
- Added `LGR_Conformance` column (new in CLDF 1.3) to `ExampleTable`:
  ```
$ csvstat -c LGR_Conformance cldf/examples.csv 
  8. "LGR_Conformance"

	Type of data:          Text
	Contains null values:  False
	Unique values:         2
	Longest value:         16, characters
	Most common values:    MORPHEME_ALIGNED (93933x)
	                       WORD_ALIGNED (739x)
  ```


## [1.2]

Initial release of the CLDF dataset for DoReCo.

