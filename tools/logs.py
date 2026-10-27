"""Fetch the anonymous play log (Google Sheet via Apps Script) and print a quick summary.
Usage: LOG_KEY=... python3 tools/logs.py [log files...]
  The key is the Apps Script KEY (not committed). Log files = "플레이 기록 파일 받기" downloads (unsent queue), merged in.
  Without LOG_KEY only the files are used. Merged records are saved to play_logs.json (gitignored).
"""
import os,sys,json,urllib.request,urllib.parse,collections
URL='https://script.google.com/macros/s/AKfycbwQLNST9m47Rbh9GRou9a2Yrl0L0cYt8ImopVt-ZC0TKSZcxVAWrTCNkuFCChwJuKIE/exec'
key=os.environ.get('LOG_KEY');files=sys.argv[1:]
if not key and not files:sys.exit('LOG_KEY env var or log files needed')
recs=[]
if key:
    for r in json.load(urllib.request.urlopen(URL+'?key='+urllib.parse.quote(key))):
        try:recs.append(json.loads(r[4]))
        except Exception:pass
for f in files:recs+=json.load(open(f))
seen=set();recs=[d for d in recs if not((d.get('uid'),d.get('t'),d.get('kind')) in seen or seen.add((d.get('uid'),d.get('t'),d.get('kind'))))]
json.dump(recs,open('play_logs.json','w'),ensure_ascii=False)
K=collections.defaultdict(list)
for d in recs:K[d.get('kind')].append(d)
print(f"records {len(recs)} · players {len({d['uid'] for d in recs})} · careers {len({d['cid'] for d in recs})} (new {len(K['new'])}, retired {len(K['retire'])})")
R=K['retire']
if R:
    n=len(R);pct=lambda c:f"{100*sum(1 for d in R if c(d))/n:.0f}%"
    print(f"retired {n}: F1 debut {pct(lambda d:d['debut'])} · champ1+ {pct(lambda d:d['titles']>=1)} · champ5+ {pct(lambda d:d['titles']>=5)} · avg age {sum(d['age'] for d in R)/n:.1f}")
S=K['season']
if S:
    print('seasons by series:',dict(collections.Counter(d['lk'] for d in S)))
    m0=[d['morale0'] for d in S if d.get('morale0') is not None]
    if m0:print(f"stamina at season start: avg {sum(m0)/len(m0):.0f}, <60 {100*sum(1 for x in m0 if x<60)/len(m0):.0f}%")
    print('training:',dict(collections.Counter(d.get('train') for d in S)))
    ch=[d['ch'] for d in S if d.get('ch')]
    if ch:print('challenge go/no:',dict(collections.Counter(c.split(':')[1] for c in ch)))
    ev=collections.Counter(e for d in S for e in d.get('ev') or [])
    if ev:print('event picks (id:choice):',dict(ev.most_common()))
    # per-stat change: in season (growth + break gamble) = stats - s0; preseason (events) = s0 - previous season's stats
    prev={};pre=collections.Counter();ins=collections.Counter();cnt=0
    for d in sorted(S,key=lambda d:(d['cid'],d['year'])):
        s0=d.get('s0')
        if s0:
            cnt+=1
            for k,v in d['stats'].items():ins[k]+=v-s0[k]
            p=prev.get(d['cid'])
            if p:
                for k in s0:pre[k]+=s0[k]-p[k]
        prev[d['cid']]=d['stats']
    if cnt:print('avg stat change / season (in season):',{k:round(v/cnt,2) for k,v in ins.items()});print('total preseason change:',dict(pre))
    ga=collections.Counter((d.get('ga') or '').split(':')[1] for d in S if d.get('ga'))
    if ga:print('break gamble:',dict(ga))
# where careers stop: last series of careers with no retire record
last={}
for d in S:last[d['cid']]=d['lk']
stop=collections.Counter(v for c,v in last.items() if c not in {d['cid'] for d in R})
if stop:print('unfinished careers stopped at:',dict(stop))
