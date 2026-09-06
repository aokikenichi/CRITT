from __future__ import annotations
import csv,io,zipfile,json,gzip,base64,re,math
from collections import defaultdict,Counter
from datetime import datetime,date,timezone
from pathlib import Path

ZIP=Path('tmp/t20s_female_csv2.zip'); TEMPLATE=Path('t20-men.html'); OUT=Path('t20-women.html')
START=date(2022,10,10); PRIOR=300.0
BOWL_W={'bowled','caught','caught and bowled','lbw','stumped','hit wicket'}
NOT_OUT={'retired hurt','retired not out','absent hurt'}

def ph(ball):
    try:o=int(float(ball))
    except:return None
    return 0 if o<=5 else 1 if o<=14 else 2 if o<=19 else None

def num(x):return isinstance(x,(int,float)) and math.isfinite(x)
def rnd(x,n=1):return round(x,n) if num(x) else None
def pct(vals,v,inv=False):
    vals=[x for x in vals if num(x)]
    if not num(v) or not vals:return None
    if len(vals)==1:return 50.0
    w=sum((x>v if inv else x<v) for x in vals); e=sum(x==v for x in vals)
    return max(0,min(100,(w+max(0,e-1)/2)/(len(vals)-1)*100))

def rec(pid,name=''):
    if pid not in P:
        P[pid]={'id':pid,'name':name or pid,'teams':Counter(),'last_team':None,'last_date':date.min,'matches':set(),'jp':False,
        'bat':{'inn':set(),'tot':[0,0,0],'phase':[[0,0,0] for _ in range(3)],'seg':defaultdict(lambda:[0,0,0])},
        'bowl':{'inn':set(),'tot':[0,0,0],'phase':[[0,0,0] for _ in range(3)],'seg':defaultdict(lambda:[0,0,0])},'field':[0,0,0]}
    if name and P[pid]['name']==pid:P[pid]['name']=name
    return P[pid]

def info(z,n):
    d={'teams':[],'players':[],'reg':{},'date':None,'gender':None,'team_type':None,'match_type':None}; dates=[]
    with io.TextIOWrapper(z.open(n),encoding='utf-8-sig',newline='') as f:
        for r in csv.reader(f):
            if len(r)<3 or r[0]!='info':continue
            k=r[1]
            if k=='team':d['teams'].append(r[2])
            elif k=='date':dates.append(r[2])
            elif k in ('gender','team_type','match_type'):d[k]=r[2]
            elif k=='player' and len(r)>=4:d['players'].append((r[2],r[3]))
            elif k=='registry' and len(r)>=5 and r[2]=='people':d['reg'][r[3]]=r[4]
    if dates:d['date']=datetime.strptime(dates[0],'%Y/%m/%d').date()
    return d

P={}; fallback={}; BT=defaultdict(lambda:[0,0,0]); BM=defaultdict(lambda:[0,0,0]); BG=defaultdict(lambda:[0,0,0]); BGM=defaultdict(lambda:[0,0,0]); OT=defaultdict(lambda:[0,0,0]); OM=defaultdict(lambda:[0,0,0]); OG=defaultdict(lambda:[0,0,0]); OGM=defaultdict(lambda:[0,0,0])
cm=cd=jm=am=ad=0; dates=[]; jlast=None
with zipfile.ZipFile(ZIP) as z:
    names=[n for n in z.namelist() if n.endswith('.csv') and not n.endswith('_info.csv')]; am=len(names)
    for dn in names:
        mid=dn[:-4]; inf=f'{mid}_info.csv'
        if inf not in z.namelist():continue
        I=info(z,inf)
        if I['gender']!='female' or I['team_type']!='international' or I['match_type']!='T20' or not I['date']:continue
        with io.TextIOWrapper(z.open(dn),encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        ad+=len(rows); dt=I['date']
        if dt<START:continue
        cm+=1; cd+=len(rows); dates.append(dt); isjp='Japan' in I['teams']
        if isjp:jm+=1; jlast=max(jlast,dt) if jlast else dt
        def pid(name,team=''):
            if not name:return None
            if name in I['reg']:return I['reg'][name]
            k=(team,name)
            if k not in fallback:fallback[k]='name:'+re.sub(r'[^A-Za-z0-9]+','_',team+'_'+name).strip('_')
            return fallback[k]
        for team,name in I['players']:
            p=rec(pid(name,team),name); p['matches'].add(mid); p['teams'][team]+=1
            if dt>=p['last_date']:p['last_date']=dt;p['last_team']=team
            if team=='Japan':p['jp']=True
        for r in rows:
            try:inn=int(r['innings'])
            except:continue
            q=ph(r['ball'])
            if inn not in (1,2) or q is None:continue
            bt,ot=r['batting_team'],r['bowling_team']; sn,nn,bn=r['striker'],r['non_striker'],r['bowler']; s=rec(pid(sn,bt),sn); n=rec(pid(nn,bt),nn); b=rec(pid(bn,ot),bn)
            for p,t in ((s,bt),(n,bt),(b,ot)):
                if dt>=p['last_date']:p['last_date']=dt;p['last_team']=t
                if t=='Japan':p['jp']=True
            s['bat']['inn'].add((mid,inn)); n['bat']['inn'].add((mid,inn)); b['bowl']['inn'].add((mid,inn))
            rb=int(r['runs_off_bat'] or 0); w=int(r['wides'] or 0); nb=int(r['noballs'] or 0); legal=w==0 and nb==0; bball=w==0; br=rb+w+nb
            if bball:
                s['bat']['tot'][0]+=1;s['bat']['tot'][1]+=rb;s['bat']['phase'][q][0]+=1;s['bat']['phase'][q][1]+=rb;s['bat']['seg'][(mid,ot,q)][0]+=1;s['bat']['seg'][(mid,ot,q)][1]+=rb
                for D,K in ((BT,(ot,q)),(BM,(mid,ot,q)),(BG,q),(BGM,(mid,q))):D[K][0]+=1;D[K][1]+=rb
            if legal:
                b['bowl']['tot'][0]+=1;b['bowl']['phase'][q][0]+=1;b['bowl']['seg'][(mid,bt,q)][0]+=1
                for D,K in ((OT,(bt,q)),(OM,(mid,bt,q)),(OG,q),(OGM,(mid,q))):D[K][0]+=1
            b['bowl']['tot'][1]+=br;b['bowl']['phase'][q][1]+=br;b['bowl']['seg'][(mid,bt,q)][1]+=br
            for D,K in ((OT,(bt,q)),(OM,(mid,bt,q)),(OG,q),(OGM,(mid,q))):D[K][1]+=br
            for wf,pf in (('wicket_type','player_dismissed'),('other_wicket_type','other_player_dismissed')):
                wt=(r.get(wf) or '').strip().lower(); dn=(r.get(pf) or '').strip()
                if not wt or not dn:continue
                d=rec(pid(dn,bt),dn)
                if wt not in NOT_OUT:
                    d['bat']['tot'][2]+=1;d['bat']['phase'][q][2]+=1;d['bat']['seg'][(mid,ot,q)][2]+=1
                    for D,K in ((BT,(ot,q)),(BM,(mid,ot,q)),(BG,q),(BGM,(mid,q))):D[K][2]+=1
                if wt in BOWL_W:
                    b['bowl']['tot'][2]+=1;b['bowl']['phase'][q][2]+=1;b['bowl']['seg'][(mid,bt,q)][2]+=1
                    for D,K in ((OT,(bt,q)),(OM,(mid,bt,q)),(OG,q),(OGM,(mid,q))):D[K][2]+=1
                fs=[r.get('fielder_1',''),r.get('fielder_2',''),r.get('fielder_3','')]
                if wt=='caught' and fs[0]:rec(pid(fs[0],ot),fs[0])['field'][0]+=1
                elif wt=='stumped' and fs[0]:rec(pid(fs[0],ot),fs[0])['field'][1]+=1
                elif wt=='run out':
                    for fn in set(x for x in fs if x):rec(pid(fn,ot),fn)['field'][2]+=1

def rate(kind,mid,opp,q,ix):
    T,M,G,GM=(BT,BM,BG,BGM) if kind=='bat' else (OT,OM,OG,OGM); t=T[(opp,q)];m=M[(mid,opp,q)];g=G[q];gm=GM[(mid,q)];den=max(0,t[0]-m[0]);nu=t[ix]-m[ix];gd=max(0,g[0]-gm[0]);gn=g[ix]-gm[ix];gr=gn/gd if gd else (g[ix]/g[0] if g[0] else 0);return (nu+PRIOR*gr)/(den+PRIOR) if den+PRIOR else gr

for p in P.values():
    for R in ('bat','bowl'):p[R]['n']=len(p[R]['inn'])
    b,o=p['bat'],p['bowl']; bb,rr,oo=b['tot']; ob,orr,ow=o['tot']; b['strike']=rr*100/bb if bb else None;b['avg']=rr/oo if oo else None;b['bpd']=bb/oo if oo else None;o['econ']=orr*6/ob if ob else None;o['w100']=ow*100/ob if ob else None;b['eligible']=b['n']>=10 and bb>=200;o['eligible']=o['n']>=10 and ob>=120 and ow>=5
    er=eo=0
    for (m,opp,q),s in b['seg'].items():er+=s[0]*rate('bat',m,opp,q,1);eo+=s[0]*rate('bat',m,opp,q,2)
    b['ax']=rr/er*100 if er else None;b['ay']=eo/(oo if oo else .5)*100 if bb and eo else None
    er=ew=0
    for (m,opp,q),s in o['seg'].items():er+=s[0]*rate('bowl',m,opp,q,1);ew+=s[0]*rate('bowl',m,opp,q,2)
    o['ax']=er/(orr if orr else .5)*100 if ob and er else None;o['ay']=ow/ew*100 if ew else None
    for R,kind in ((b,'bat'),(o,'bowl')):
        R['pc']=[]
        for q,s in enumerate(R['phase']):
            balls,runs,wk=s; er=ex=0
            for (m,opp,qq),sg in R['seg'].items():
                if qq==q:er+=sg[0]*rate(kind,m,opp,q,1);ex+=sg[0]*rate(kind,m,opp,q,2)
            if kind=='bat':R['pc'].append({'balls':balls,'raw':runs*100/balls if balls else None,'ax':runs/er*100 if er else None,'ay':ex/(wk if wk else .5)*100 if balls and ex else None})
            else:R['pc'].append({'balls':balls,'raw':runs*6/balls if balls else None,'ax':er/(runs if runs else .5)*100 if balls and er else None,'ay':wk/ex*100 if ex else None})

for role in ('bat','bowl'):
    E=[p for p in P.values() if p[role]['eligible']]; xv=[p[role]['strike'] if role=='bat' else p[role]['econ'] for p in E];yv=[p[role]['bpd'] if role=='bat' else p[role]['w100'] for p in E];ax=[p[role]['ax'] for p in E];ay=[p[role]['ay'] for p in E]
    for p in P.values():
        r=p[role]
        if r['eligible']:
            r['xp']=pct(xv,r['strike'] if role=='bat' else r['econ'],role=='bowl');r['yp']=pct(yv,r['bpd'] if role=='bat' else r['w100']);r['op']=(r['xp']+r['yp'])/2;r['axp']=pct(ax,r['ax']);r['ayp']=pct(ay,r['ay']);r['aop']=(r['axp']+r['ayp'])/2
        else:r['xp']=r['yp']=r['op']=r['axp']=r['ayp']=r['aop']=None
    for q in range(3):
        S=[p for p in P.values() if p[role]['pc'][q]['balls']>=60 and num(p[role]['pc'][q]['ax']) and num(p[role]['pc'][q]['ay'])]; xx=[p[role]['pc'][q]['ax'] for p in S];yy=[p[role]['pc'][q]['ay'] for p in S]
        for p in P.values():
            z=p[role]['pc'][q];z['p']=(pct(xx,z['ax'])+pct(yy,z['ay']))/2 if z['balls']>=60 and num(z['ax']) and num(z['ay']) else None

def packrole(r,bat):
    ps=[[x['balls'],rnd(x['raw']),rnd(x['ax']),rnd(x['ay']),rnd(x['p'])] for x in r['pc']]
    return [1 if r['eligible'] else 0,r['n'],r['tot'][0],r['tot'][1],r['tot'][2],rnd(r['avg'] if bat else r['econ']),rnd(r['strike'] if bat else r['w100']),rnd(r['xp']),rnd(r['yp']),rnd(r['op']),rnd(r['ax']),rnd(r['ay']),rnd(r['axp']),rnd(r['ayp']),rnd(r['aop']),ps,None]
def badges(r,bat):
    if not r['eligible']:return []
    a=[]
    if num(r['axp']) and r['axp']>=75:a.append('速攻型' if bat else '省エネ型')
    if num(r['ayp']) and r['ayp']>=75:a.append('粘り型' if bat else '奪取型')
    for z,l in zip(r['pc'],['序盤に強い','中盤に強い','終盤に強い']):
        if num(z['p']) and z['p']>=75:a.append(l)
    return a or ['バランス型']
packed=[]
for p in sorted(P.values(),key=lambda x:(not x['jp'],x['name'].lower(),x['id'])):
    c=p['last_team'] or (p['teams'].most_common(1)[0][0] if p['teams'] else '—');packed.append([p['id'],p['name'],p['name'],c,1 if p['jp'] else 0,0,len(p['matches']),badges(p['bat'],1),badges(p['bowl'],0),packrole(p['bat'],1),packrole(p['bowl'],0),p['field']])
leaders={}
for role,k in (('bat','batting'),('bowl','bowling')):
    for mode in ('raw','adjusted'):
        vals=[]
        for p in P.values():
            r=p[role];v=r['op'] if mode=='raw' else r['aop']
            if r['eligible'] and num(v):vals.append({'id':p['id'],'name':p['name'],'value':rnd(v)})
        leaders[f'{k}_{mode}']=sorted(vals,key=lambda x:(-x['value'],x['name']))[:10]
meta={'title':'120球で見る、日本女子の現在地','source':"Cricsheet Women's T20 Internationals (CSV Ashwin)",'source_file':'t20s_female_csv2.zip','generated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'archive_matches':am,'archive_deliveries':ad,'comparison_start':START.isoformat(),'comparison_end':max(dates).isoformat(),'comparison_matches':cm,'comparison_deliveries':cd,'japan_matches':jm,'japan_players':sum(p['jp'] for p in P.values()),'japan_last_match':jlast.isoformat() if jlast else None,'eligible_batters':sum(p['bat']['eligible'] for p in P.values()),'eligible_bowlers':sum(p['bowl']['eligible'] for p in P.values()),'generated_players':len(P)}
method={'scope':f'女子T20Iのみ。国内・フランチャイズ戦は含まない。比較は{START.isoformat()}以降、通常の第1・第2イニングのみ。','eligibility':{'batting':'10イニング以上かつ200打球以上','bowling':'10イニング以上、120合法球以上、投手帰属5ウィケット以上','phase':'局面内60球以上'},'phases':{'powerplay':'0–5オーバー','middle':'6–14オーバー','death':'15–19オーバー'},'adjustment':'相手国×局面の当該試合を除く率を同局面の世界平均300球で縮約した部分補正。','percentiles':'女子T20Iの資格達成選手内で同値を中間順位として百分位化。総合は2軸百分位の単純平均。','wickets':'投手ウィケットはbowled/caught/caught and bowled/lbw/stumped/hit wicket。run out等は除外。'}
data={'format':2,'meta':meta,'players':packed,'leaders':leaders,'methodology':method};enc=base64.b64encode(gzip.compress(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode(),9)).decode()
h=TEMPLATE.read_text();h=re.sub(r'(<script id="t20-data" type="application/gzip">).*?(</script>)',lambda m:m.group(1)+enc+m.group(2),h,flags=re.S);h=h.replace('<title>120球で見る、日本の現在地</title>','<title>女子T20I｜120球で見る、日本の現在地</title>').replace("Men's T20 International · Data Story","Women's T20 International · Data Story").replace('男子T20インターナショナルのみを対象とし','女子T20インターナショナルのみを対象とし').replace('Cricsheetの男子T20Iデータを独自集計した','Cricsheetの女子T20Iデータを独自集計した')
OUT.write_text(h);print(json.dumps(meta,ensure_ascii=False,indent=2))
