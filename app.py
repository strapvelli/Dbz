import streamlit as st
import sqlite3, re, datetime, math
from pathlib import Path
DB=Path(__file__).with_name('signals.db')
SPORTS=['Soccer','Hockey','Basketball','Tennis','NFL','eSoccer']
def conn():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS tips(id INTEGER PRIMARY KEY,created TEXT,source TEXT,sport TEXT,event TEXT,market TEXT,odds REAL,prob REAL,status TEXT DEFAULT "Pending",notes TEXT DEFAULT "")')
 c.commit();return c
def add(source,sport,event,market,odds,prob,notes=''):
 with conn() as c:c.execute('INSERT INTO tips(created,source,sport,event,market,odds,prob,notes) VALUES(?,?,?,?,?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),source,sport,event,market,odds,prob,notes))
def rows():
 with conn() as c:return [dict(r) for r in c.execute('SELECT * FROM tips ORDER BY id DESC')]
def ev(p,o):return p*o-1
def parse_tip(t):
 odds=re.search(r'(?:odds?\s*[:=@-]?\s*|@\s*)(\d+(?:\.\d+)?)',t,re.I)
 market=re.search(r'((?:over|under)\s*\d+(?:\.\d+)?(?:\s*(?:goals?|points?))?|(?:home|away)\s*(?:win|to score)|both teams to score)',t,re.I)
 return (market.group(1) if market else '',float(odds.group(1)) if odds else None)
st.set_page_config(page_title='STRAPDON In-Play',page_icon='📡',layout='centered')
st.markdown('''<style>.block-container{padding-top:1rem;max-width:850px}div[data-testid="stMetric"]{background:#142033;border-radius:12px;padding:12px} .stApp{background:#080e19;color:#f0f5ff}</style>''',unsafe_allow_html=True)
st.title('STRAPDON • IN-PLAY')
st.caption('Local MVP • manual/imported tips • no live feed connected • no automatic betting')
data=rows();settled=[r for r in data if r['status'] in ('Won','Lost')];wins=sum(r['status']=='Won' for r in settled)
profit=sum((r['odds']-1 if r['status']=='Won' else -1) for r in settled)
a,b,c=st.columns(3);a.metric('Tracked tips',len(data));b.metric('Verified win rate',f'{wins/len(settled):.1%}' if settled else 'N/A');c.metric('Flat-unit ROI',f'{profit/len(settled):+.1%}' if settled else 'N/A')
tabs=st.tabs(['Signals','Add / Parse','Tipsters','Paper results','Settings'])
with tabs[0]:
 sportfilter=st.selectbox('Filter sport',['All']+SPORTS)
 eligible=[r for r in data if sportfilter=='All' or r['sport']==sportfilter]
 if not eligible:st.info('No signals yet. Add a tip to begin.')
 for r in eligible:
  value=ev(r['prob']/100,r['odds']) if r['prob'] is not None else None
  with st.container(border=True):
   st.write(f"**{r['event']}** · {r['sport']} · {r['status']}")
   st.write(f"{r['market']} · Odds **{r['odds']:.2f}** · Source: {r['source']}")
   st.caption(f"User-estimated probability {r['prob']:.1f}% · Illustrative EV {value:+.1%}" if value is not None else 'Probability unavailable')
   if value is not None and value>0:st.warning('Positive calculated EV based on an unverified probability estimate; not a validated betting edge.')
with tabs[1]:
 st.subheader('Enter or paste a Telegram tip')
 raw=st.text_area('Message text',placeholder='Over 2.5 goals @ 1.85')
 market0,odds0=parse_tip(raw)
 with st.form('add'):
  source=st.text_input('Telegram channel / tipster',value='Manual')
  sport=st.selectbox('Sport',SPORTS)
  event=st.text_input('Match / event',placeholder='Team A vs Team B')
  market=st.text_input('Betting market',value=market0)
  odds=st.number_input('Decimal odds (snapshot)',min_value=1.01,max_value=1000.0,value=float(odds0 or 1.80),step=.05)
  prob=st.number_input('Your estimated true probability (%) — not AI verified',min_value=1.0,max_value=99.0,value=50.0,step=1.0)
  submitted=st.form_submit_button('Save tracked tip',use_container_width=True)
  if submitted:
   if not event.strip() or not market.strip():st.error('Enter event and market.')
   else:add(source,sport,event,market,odds,prob,raw);st.success('Saved. Open Signals or Paper results.')
 st.caption('Parsing recognizes a few common over/under and winner phrases; always verify before saving.')
with tabs[2]:
 st.subheader('Tipster leaderboard')
 sources=sorted(set(r['source'] for r in data))
 if not sources:st.info('No tipsters tracked yet.')
 for s in sources:
  rs=[r for r in settled if r['source']==s];w=sum(r['status']=='Won' for r in rs)
  p=sum((r['odds']-1 if r['status']=='Won' else -1) for r in rs)
  st.write(f"**{s}** · {len(rs)} settled · Win rate: {w/len(rs):.1%} · ROI: {p/len(rs):+.1%}" if rs else f'**{s}** · No settled results')
 st.caption('Results are manually settled and are not independently verified until an official results feed is integrated.')
with tabs[3]:
 st.subheader('Paper settlement')
 pending=[r for r in data if r['status']=='Pending']
 if not pending:st.info('No pending paper tips.')
 for r in pending:
  st.write(f"#{r['id']} {r['event']} — {r['market']} @ {r['odds']:.2f}")
  col1,col2,col3=st.columns(3)
  for col,status in [(col1,'Won'),(col2,'Lost'),(col3,'Void')]:
   if col.button(status,key=f'{r["id"]}{status}',use_container_width=True):
    with conn() as db:db.execute('UPDATE tips SET status=? WHERE id=?',(status,r['id']))
    st.rerun()
 st.caption('Paper profit uses 1 unit per settled bet. Void bets are excluded. No real bets placed.')
with tabs[4]:
 st.subheader('Integrations')
 st.error('Telegram listener: NOT CONNECTED')
 st.error('Live odds: NOT CONNECTED')
 st.error('Official scores / settlement: NOT CONNECTED')
 st.info('For production: run an authorized Telethon listener on a persistent server; integrate licensed sports scores and odds feeds, normalize market IDs, log immutable odds snapshots, and authenticate webhook imports. Never put Telegram credentials in a public dashboard.')
 st.write('Supported tracking categories: '+', '.join(SPORTS))
 st.caption('Streamlit server must remain running; an iPhone browser cannot independently host a 24/7 Telegram scanner.')
