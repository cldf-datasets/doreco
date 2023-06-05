"""

"""
import math
import pathlib
import datetime
import dataclasses
from html import escape

import pydub
from clldutils.clilib import PathType

from cldfbench_doreco import Dataset
from .query import Database


# FIXME: get all phones for a filename, including IPA.
SQL = """
select
    p.u_id, p.ph, p.start, p.end, p.wd_id, ipa.cldf_name as ipa
from
    `phones.csv` as p,
    `words.csv` as w
left outer join 
    parametertable as ipa on p.cldf_parameterreference = ipa.cldf_id
where
    p.wd_id = w.cldf_id and w.filename = ?
order by p.cldf_id;
"""

FADE_TIME = INTERVAL_OFFSET = 50


@dataclasses.dataclass
class Word:
    id: str
    start: float
    end: float
    ipa: str
    left: float = None
    width: float = None

    def html(self, player):
        return """
        <div onclick="ws_{1}.play({0.start}, {0.end});" class="word" style="float: left; width: {0.width}; text-align: center; border: 1px solid black;">
        {2}
        </div>
        """.format(self, player, escape(self.ipa))
        return """
<div onclick="ws_{1}.play({0.start} - 0.05, {0.end} + 0.05);" class="word" style="float: left; position: relative; left: {0.left}; width: {0.width}; text-align: center; border: 1px solid black;">
{2}
</div>
""".format(self, player, escape(self.ipa))


def get_mono_channel(audio, channel=1):
    assert 0 < channel <= audio.channels
    if audio.channels > 1:
        return audio.split_to_mono()[channel - 1]
    return audio


def register(parser):
    parser.add_argument('audio', type=PathType())
    parser.add_argument('out', type=PathType())


def iter_utterances(db, filename):
    def to_word(phones):
        return Word(
            id=phones[0][0], start=phones[0][1], end=phones[-1][2], ipa=''.join(p[-1] for p in phones))

    curr_uid, curr_wid = None, None
    words, word = [], []
    for row in db.query(SQL, (filename,)):
        # p.u_id, p.ph, p.start, p.end, p.wd_id, ipa.cldf_name as ipa
        uid, ph, s, e, wid, ipa = row
        if not uid:
            continue
        if uid != curr_uid:
            if words:
                yield curr_uid, [to_word(w) for w in words]
            curr_uid = uid
            curr_wid = wid
            words, word = [], []
        if curr_wid != wid:
            words.append(word)
            word = []
            curr_wid = wid
        word.append((curr_wid, s, e, ipa or ph))
    if words:
        yield curr_uid, [to_word(w) for w in words]


def run(args):
    ds = Dataset()
    db = Database(ds.dir / 'doreco.sqlite')

    if not args.out.exists():
        args.out.mkdir()

    def percent(f):
        return '{}%'.format(math.floor(f * 1000) / 10)

    audio = get_mono_channel(pydub.AudioSegment.from_wav(args.audio))
    uts = []
    for i, (uid, words) in enumerate(iter_utterances(db, args.audio.stem)):
        if i > 20:
            break
        s, e = words[0].start, words[-1].end
        s -= 0.05
        utterance(audio, words[0].start, words[-1].end, args.out / '{}.mp3'.format(uid))

        # FIXME: create the HTML! start the http server, open in browser!
        duration = e - s
        uts.append((uid, duration, words))
        for w in words:
            w.start -= s
            w.end -= s
            w.left = percent(w.start / duration)
            w.width = percent((w.end - w.start) / duration)
        #print(uid, s, e, ' '.join(w.ipa for w in words))
    args.out.joinpath('index.html').write_text(html(uts), encoding='utf8')
    return

    for row in db.query(SQL_END, (args.audio.stem,)):
        #print('{}\t{}'.format(row[0], row[1]))
        utterances[row[0]][1] = row[1]

    c = 0
    for u, (s, e) in utterances.items():
        #
        # FIXME: compute percentage of utterance duration per word.
        #
        text, wid = '', None
        for r in db.query(SQL_U, (u,)):
            if wid and r[1] != wid:
                text += ' '
            wid = r[1]
            text += r[0]
        print(u, text)
        if u:
            c += 1
            if c > 10: break
            utterance(audio, s, e, pathlib.Path('{}.mp3'.format(u)))


def utterance(audio, start, end, out):
    audio_chunk = audio[start * 1000 - INTERVAL_OFFSET:end * 1000 + INTERVAL_OFFSET]
    # fade in and out
    audio_chunk = audio_chunk.fade_in(duration=FADE_TIME).fade_out(duration=FADE_TIME)
    tags = {
        'artist': '',
        'title': '',
        'album': '',
        'date': datetime.date.today().isoformat(),
        'genre': 'Speech'}

    audio_chunk.export(str(out), tags=tags, format='mp3', bitrate="128k")


def audioplayer(width, uid, words):
    player = 'ws_{}'.format(uid)
    return """
<div style="width: {4}%;">
    <div id="{0}"></div>
    <div id="tr_{0}" style="width: 100%;">
    {2}
    </div>
    <div class="controls" style="clear: both;">
        <button onclick="{1}.playPause();" class="btn btn-primary" data-action="play">
            <i class="glyphicon glyphicon-play"></i> Play / <i class="glyphicon glyphicon-pause"></i> Pause
        </button>
    </div>
</div>
<script>
var {1};
document.addEventListener('DOMContentLoaded', function() {{
    {1} = WaveSurfer.create({{
    container: '#{0}',
    waveColor: 'violet',
    backend: 'MediaElement',
    progressColor: 'purple'
}});
{1}.load('http://localhost:8000/{3}.mp3');
}})
</script>
    """.format(uid, player, ''.join(w.html(uid) for w in words), uid[1:], width)


def html(utterances):
    maxdur = max(i[1] for i in utterances)
    return """<html>
<head>
<meta charset="utf-8" /> 
 <link href="//maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" rel="stylesheet">
<script src="https://unpkg.com/wavesurfer.js"></script>
</head>
<body>
<h1>Title</h1>
{}
</body>
</html>
""".format('\n'.join(audioplayer(math.floor(dur * 100 / maxdur), 'u' + uid, words) for uid, dur, words in utterances))
