"""Build index.html from src/template.html + data/*.json, and build/game.js for the node tests.
Usage: python3 tools/build.py            (writes index.html at the repo root and build/game.js)
"""
import pathlib,re
R=pathlib.Path(__file__).resolve().parent.parent
t=(R/'src/template.html').read_text(encoding='utf-8')
rd=lambda p:(R/p).read_text(encoding='utf-8')
out=(t.replace('__BALANCE__',rd('data/balance.json')).replace('__SKIN__',rd('data/skin_f1_2026.json'))
      .replace('__TROPHY__',rd('data/trophies.json')).replace('__SLOGO__',rd('data/series_logos.json')).replace('__AVATAR__',rd('data/avatars.json')))
assert '__BALANCE__' not in out and '__SKIN__' not in out and '__TROPHY__' not in out and '__SLOGO__' not in out and '__AVATAR__' not in out
(R/'index.html').write_text(out,encoding='utf-8')
(R/'build').mkdir(exist_ok=True)
(R/'build/game.js').write_text(re.search(r'<script>(.*)</script>',out,re.S).group(1),encoding='utf-8')
print('built index.html',len(out),'bytes')
