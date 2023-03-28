import types
import urllib.parse

import requests

NAKALA_API = 'https://api.nakala.fr/'
NAKALA_DOI_PREFIX = "10.34847"


class Deposit:
    def __init__(self, doi):
        self.doi = doi if '/' in doi else '{}/{}'.format(NAKALA_DOI_PREFIX, doi)
        self.id = urllib.parse.quote(self.doi, safe='')

    def req(self, path=None, **query):
        url = "{}datas/{}".format(NAKALA_API, self.id)
        if path:
            url += path if path.startswith('/') else ('/' + path)
        if query:
            url += '?' + urllib.parse.urlencode(query)
        return requests.get(url).json()

    @property
    def relations(self):
        """
        {
            "type": "IsSupplementedBy",
            "repository": "nakala",
            "target": "10.34847/nkl.75e79ilu",
            "date": "2022-07-27T18:42:59+02:00",
            "comment": "",
            "uri": "https://nakala.fr/10.34847/nkl.75e79ilu",
            "isInferred": true
        },
        {
            "type": "IsPartOf",
            "repository": "nakala",
            "target": "10.34847/nkl.7cbfq779",
            "date": "2022-07-27T18:42:37+02:00",
            "comment": null,
            "uri": "https://nakala.fr/10.34847/nkl.7cbfq779",
            "isInferred": false
        }
        """
        return [types.SimpleNamespace(**rel) for rel in self.req(path='/relations')]

    @property
    def supplements(self):
        return [
            Deposit(rel.target) for rel in self.relations
            if rel.type == 'IsSupplementedBy' and rel.repository == 'nakala']

    @property
    def files(self):
        """
        name='doreco_teop1238_Mat_01.wav',
        extension='wav',
        size=73206044,
        mime_type='audio/x-wav',
        sha1='...'
        url
        """
        res = []
        for f in self.req(**{'metadata-format': 'dc'})['files']:
            f = types.SimpleNamespace(**f)
            f.url = '{}data/{}/{}'.format(NAKALA_API, self.id, f.sha1)
            res.append(f)
        return res
