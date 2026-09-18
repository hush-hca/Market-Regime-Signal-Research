"""Run with: streamlit run app.py"""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from regime.data import demo, validate, enrich, quality
from regime.ingest import download
from regime.research import Config, features, walk_forward, events, summarize, strategy, payoff

st.set_page_config(page_title='Regime Atlas · Market Research',page_icon='◈',layout='wide')
st.markdown('''<style>
.block-container {padding-top:4rem; max-width:1500px}
[data-testid="stMetric"] {background:#141e30;color:#e5edf8;border:1px solid #28334a;border-radius:12px;padding:18px}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {color:#e5edf8}
h1 {letter-spacing:-1.5px} .eyebrow {color:#208b72;letter-spacing:3px;font-size:12px;font-weight:700}
@media(max-width:700px) {h1 {font-size:2rem !important;letter-spacing:-.7px} .block-container {padding-top:4rem}}
</style>''',unsafe_allow_html=True)
COLORS={'Defensive':'#ff7d85','Soft / mixed':'#d5a65e','Firm / mixed':'#719cff','Expansion':'#42d6ad','Unclassified':'#526078'}

@st.cache_data(show_spinner=False)
def analyze(d, oi, chain):
    f=features(d,oi,chain)
    r,p,m=walk_forward(d,f)
    return f,r,p,m

def plot(fig,height=380):
    fig.update_layout(template='plotly_dark',paper_bgcolor='#0b1120',plot_bgcolor='#0b1120',
        height=height,margin=dict(l=12,r=12,t=35,b=12),legend=dict(orientation='h',y=1.12),font=dict(color='#cbd7e8'))
    st.plotly_chart(fig,width='stretch')

def percent_table(frame):
    formats={c:'{:.2%}' for c in frame.select_dtypes('number').columns if c not in ['n','days']}
    st.dataframe(frame.style.format(formats,na_rep='—'),hide_index=True,width='stretch')

with st.sidebar:
    st.markdown('### ◈ REGIME ATLAS')
    st.caption('BTC / DAILY RESEARCH WORKSPACE')
    source=st.selectbox('Data source',['Synthetic demo','Local snapshot','Upload CSV','Fetch public API'])
    d=None
    meta={'source':'synthetic','synthetic':True,'price_instrument':'synthetic price path'}
    try:
        if source=='Synthetic demo':
            d=demo()
        elif source=='Local snapshot':
            path=Path('data/market.parquet')
            if path.exists():
                d=validate(pd.read_parquet(path))
                meta=json.loads(path.with_suffix('.json').read_text()) if path.with_suffix('.json').exists() else {'source':'local','synthetic':False,'price_instrument':'user-supplied, unverified'}
            else:
                st.info('Create a snapshot with the ingestion command in the README.')
        elif source=='Upload CSV':
            uploaded=st.file_uploader('Daily market CSV',type=['csv'])
            if uploaded:
                d=validate(pd.read_csv(uploaded))
                meta={'source':'uploaded','synthetic':False,'price_instrument':'user-supplied, unverified'}
        else:
            venue=st.selectbox('Venue',['binance','bybit'])
            days=st.selectbox('History requested (days)',[730,1095,1460])
            if st.button('Fetch & validate',type='primary'):
                with st.spinner('Fetching price, funding and available OI…'):
                    st.session_state['downloaded']=download(venue,days)
            if 'downloaded' in st.session_state:
                d,meta=st.session_state['downloaded']
        chain_csv=st.file_uploader('Optional on-chain CSV',type=['csv'],help='Requires available_at and mvrv, sopr or exchange_netflow. Only use data you are licensed to process.')
        if d is not None and chain_csv:
            d=enrich(d,chain_csv.getvalue().decode('utf-8-sig'))
            meta={**meta,'onchain':'user upload; availability timestamps supplied by user'}
    except Exception as exc:
        st.error(f'Data could not be loaded: {exc}')
        d=None
    include_oi=st.checkbox('Include OI features',value=False,help='Requires at least 180 complete training rows. Recent-only Binance OI is insufficient.')
    include_chain=st.checkbox('Include uploaded on-chain features',value=False)
    st.divider()
    audience=st.selectbox('Presentation focus',['Research team','Exchange','Options team'])
    st.caption('Fixed model: four clusters · 365-day warm-up · 90-day refits · final 180-day frozen holdout.')

st.markdown('<div class="eyebrow">MARKET INTELLIGENCE / RESEARCH MVP</div>',unsafe_allow_html=True)
st.title('Understand the regime. Inspect the evidence.')
st.caption('Price, positioning and on-chain context — with transparent historical outcomes.')
if d is None:
    st.info('Select synthetic demo, upload a validated dataset, or fetch a public API in the sidebar.')
    st.stop()
if meta.get('synthetic'):
    st.warning('SYNTHETIC DEMO — generated prices and indicators. All results demonstrate software behavior; they are not market evidence.')
else:
    st.info(f'Dataset: {meta.get("source")} · {meta.get("price_instrument")} · as of {d.date.max():%Y-%m-%d} UTC. Historical API data may contain later revisions.')
    if d.date.max()<pd.Timestamp.now(tz='UTC').normalize()-pd.Timedelta(days=2):
        st.warning('Historical snapshot: the last observation is more than two days old. Latest regime below is not a live signal.')
if include_chain and not any(c in d for c in ['mvrv','sopr','exchange_netflow']):
    st.error('Upload on-chain data before enabling its features.')
    st.stop()
try:
    with st.spinner('Computing causal features and walk-forward regimes…'):
        f,r,profiles,manifest=analyze(d,include_oi,include_chain)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
manifest.update(source=meta,dataset_sha256=hashlib.sha256(d.to_csv(index=False).encode()).hexdigest(),
    generated_at=pd.Timestamp.now(tz='UTC').isoformat())
latest=r.iloc[-1]
a,b,c,e=st.columns(4)
a.metric('Latest historical regime',latest.regime)
b.metric('Last close',f'${d.close.iloc[-1]:,.0f}',f'{d.close.pct_change().iloc[-1]:+.2%}')
c.metric('30-day momentum',f'{f.momentum_30.iloc[-1]:+.1%}')
e.metric('Last daily funding',f'{d.funding.iloc[-1]:.4%}' if pd.notna(d.funding.iloc[-1]) else 'Missing')
st.caption(f'{len(d):,} daily observations · {d.date.min():%d %b %Y} → {d.date.max():%d %b %Y} · Source: {meta["source"]}')
tabs=st.tabs(['Overview','Historical outcomes','Strategy lab','Options payoff','Data & methodology'])

with tabs[0]:
    chart=d[['date','close']].join(r[['regime','partition']])
    fig=go.Figure(go.Scatter(x=chart.date,y=chart.close,line=dict(color='#50627e',width=1),name='BTC price',showlegend=False))
    for label,color in COLORS.items():
        subset=chart[chart.regime==label]
        fig.add_trace(go.Scatter(x=subset.date,y=subset.close,mode='markers',marker=dict(size=3,color=color),name=label))
    fig.update_yaxes(title='Price · USD / USDT proxy')
    plot(fig,430)
    left,right=st.columns([1.35,1])
    with left:
        st.subheader('What defines the latest model?')
        last_profiles=profiles[profiles.model_version==latest.model_version].drop(columns='model_version')
        st.dataframe(last_profiles.set_index('regime').round(4),width='stretch')
        st.caption('Training-period cluster centroids. Names rank 30-day momentum within each fit; identities can change between fits.')
    with right:
        st.subheader('Read the signals')
        for name,explanation in {
            'Funding':'The daily sum of realized funding fractions. Positive funding usually means longs paid shorts. Negative funding alone does not prove a reversal or capital inflow.',
            'Open interest':'Outstanding derivative exposure. USD OI moves with both position size and price. Rising OI does not identify which side will win.',
            'MVRV & SOPR':'MVRV compares market value with realized value; SOPR describes spent-output profitability. Provider definitions and publication times matter.',
            'Exchange net flows':'Deposits minus withdrawals for labeled exchange addresses. Transfers are not equivalent to executed selling or buying.'}.items():
            with st.expander(name): st.write(explanation)
    st.subheader('Persistence & transitions')
    observed=r[r.regime!='Unclassified'].copy()
    transition=pd.crosstab(observed.regime.shift(),observed.regime,normalize='index')
    st.dataframe(transition.style.format('{:.1%}'),width='stretch')
    st.caption('Descriptive transition frequencies across all classified dates, including refit boundaries; not a forecast.')

with tabs[1]:
    st.subheader('What happened after similar observations?')
    l,m,n=st.columns(3)
    horizon=l.selectbox('Forward horizon',[7,14,30],index=2)
    partition=m.selectbox('Evaluation segment',['Final holdout','Walk-forward'])
    taxonomy=n.selectbox('Grouping',['ML clusters','Indicator rules'])
    ev=events(d,r,horizon,partition,'regime' if taxonomy=='ML clusters' else 'rule')
    summary=summarize(ev)
    st.caption('Signal at daily close → next daily open entry → open exit after the selected calendar-day horizon. Globally non-overlapping windows; raw asset returns before costs.')
    if ev.empty:
        st.info('No complete events in this segment.')
    else:
        percent_table(summary)
        plot(px.box(ev,x='regime',y='return_',points='all',color='regime',color_discrete_map=COLORS,labels={'return_':'Forward return','regime':''}))
        st.warning('Small samples are expected: 180 days contain at most about six non-overlapping 30-day windows. Intervals are suppressed below five samples and remain approximate above that threshold.')
        st.caption('Intervals use a moving-block bootstrap. “All sampled dates” uses the same eligible dates. These sampled windows are not independent market episodes. Repeated holdout inspection makes subsequent model choices exploratory.')
        st.download_button('Download event ledger',ev.to_csv(index=False),'events.csv','text/csv')

with tabs[2]:
    st.subheader('A predefined rule, an explicit ledger')
    st.write('Long when the prior completed day has positive 30-day momentum and an available model classification; otherwise cash. Full allocation, no leverage. The strategy uses indicator rules, not a hindsight selection of profitable clusters.')
    x,y,z=st.columns(3)
    fees=x.number_input('One-way fees (bps)',min_value=0.,value=5.,step=1.)
    slip=y.number_input('One-way slippage (bps)',min_value=0.,value=5.,step=1.)
    mode=z.selectbox('Accounting',['Spot-like price proxy','Perpetual with daily funding'])
    st.caption('Public adapters use perpetual candles. Spot-like mode is a price-only proxy, not an executable spot backtest. Perpetual funding uses daily summed rates on opening notional; intraday mark-notional changes are approximated.')
    try:
        ledger,metrics=strategy(d,r,fees,slip,partition,'perpetual' if mode.startswith('Perpetual') else 'spot_proxy')
        if not ledger.empty:
            percent_table(metrics)
            plot(px.line(ledger,x='date',y=['equity','benchmark'],color_discrete_sequence=['#42d6ad','#719cff'],labels={'value':'Growth of 1 unit','variable':'Strategy'}))
            st.caption(f'Evaluation: {partition}. Includes entry, position changes and final liquidation costs. Cash earns zero; no taxes, borrow costs or liquidation model.')
            st.download_button('Download trading ledger',ledger.to_csv(index=False),'strategy-ledger.csv','text/csv')
    except ValueError as exc:
        st.warning(str(exc))
        ledger=pd.DataFrame()

with tabs[3]:
    st.subheader('Covered-call payoff explorer')
    st.info('SCENARIO SIMULATION — premiums are assumptions. This is not a historical options backtest, a quoted product, or a regime-specific return estimate.')
    a,b,c=st.columns(3)
    strike=a.slider('Strike (% of entry spot)',80,150,110)
    premium=b.slider('Assumed premium (% of entry spot)',0.,20.,3.,.25)
    cost=c.slider('Total assumed costs (% of entry spot)',0.,3.,.2,.1)
    pay=payoff(100,strike,premium,cost)
    plot(px.line(pay,x='terminal_price',y=['spot_return','covered_call_return'],color_discrete_sequence=['#719cff','#42d6ad'],labels={'terminal_price':'Terminal spot (entry = 100)','value':'Return on initial spot capital'}))
    st.write(f'Maximum covered-call return: {(strike-100+premium-cost)/100:.1%}. Loss if the underlying goes to zero: {(-100+premium-cost)/100:.1%}. Premium cushions losses and caps gains; it does not remove downside risk.')
    st.caption('One unit of owned spot + one same-unit short call, held to expiry. Linear USD cash settlement; no interim mark-to-market or collateral mechanics. Regime-to-options mappings remain hypotheses until quote history is available.')

with tabs[4]:
    st.subheader('Data quality & reproducibility')
    st.dataframe(quality(d),hide_index=True,width='stretch')
    st.json(meta)
    st.markdown('''**Validation contract**

- UTC daily bars; duplicates, gaps and invalid prices are rejected.
- No backward filling. Missing model features produce unclassified dates.
- Standardization and clustering fit only on past complete observations.
- Expanding refits stop at the final 180-day holdout; its model stays frozen.
- No future-return labels enter clustering, so fitting does not require forward-label purging. Event windows cannot cross evaluation boundaries.
- Optional on-chain imports join by `available_at`, with a two-day staleness limit. The uploader must supply honest historical publication timestamps.
- Cluster names describe relative training momentum, not validated economic states. Distances are not probabilities.
- No automatic parameter search. Changing features after viewing holdout results invalidates an untouched-test interpretation.
''')
    focus={'Research team':'Lead with sample sizes, out-of-sample distributions, data lineage and negative findings.',
        'Exchange':'Lead with derivatives coverage, funding conventions, data freshness and indicator education.',
        'Options team':'Lead with payoff assumptions, capped upside, full downside exposure and the missing historical quote requirement.'}
    st.success(f'{audience}: {focus[audience]}')
    manifest['evaluation']={'horizon':horizon,'partition':partition,'taxonomy':taxonomy,'fee_bps':fees,'slippage_bps':slip,'accounting':mode}
    payload=io.BytesIO()
    with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json',json.dumps(manifest,indent=2))
        archive.writestr('regimes.csv',r.to_csv(index=False))
        archive.writestr('profiles.csv',profiles.to_csv(index=False))
        archive.writestr('events.csv',ev.to_csv(index=False))
        archive.writestr('summary.csv',summary.to_csv(index=False))
        archive.writestr('strategy.csv',ledger.to_csv(index=False))
    st.download_button('Export reproducible research results',payload.getvalue(),'regime-research.zip','application/zip')
    with st.expander('Model fit manifest'): st.json(manifest)
