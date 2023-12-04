# Releasing the DoReCo CLDF dataset

- Adapt the URLs for languages metadata and citations in `cmd_download` to the ones linked from 
  https://doreco.huma-num.fr/languages
- Adapt/remove the fixes in `cldfbench_doreco.py` if the corresponding issues in the "raw" data
  have been fixed.
- Download the data running
  ```shell
  cldfbench download cldfbench_doreco.py
  ```
  agreeing to the defaults whenever prompted.  
- Re-create the CLDF dataset running
  ```shell
  cldfbench makecldf cldfbench_doreco.py --glottolog-version v4.8 --with-cldfreadme --with-zenodo
  cldfbench readme cldfbench_doreco.py
  ```
- Make sure the data is valid running
  ```shell
  pytest
  ```
- Make sure data can be loaded into SQLite
  ```shell
  rm -f doreco.sqlite
  cldf createdb cldf/Generic-metadata.json doreco.sqlite
  ```
- Commit all changes, tag the release, push code and tags.
- Create a release on GitHub and make sure it is picked up by Zenodo.
