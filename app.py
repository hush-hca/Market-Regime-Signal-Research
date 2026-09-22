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
from regime.data import validate, enrich, quality
from regime.ingest import download
from regime.feed import load_market
from regime.onchain import load_coinmetrics
from regime.options import load_quotes, select_call, inverse_call_payoff
from regime.research import Config, features, walk_forward, events, summarize, strategy, payoff
from regime.i18n import translate, error_text, display_frame, translate_figure

st.set_page_config(page_title='Regime Atlas · Market Research',page_icon='◈',layout='wide')
language=st.sidebar.selectbox('Language / 언어', ['en','ko'],
    format_func=lambda code: {'en':'English','ko':'한국어'}[code], key='language')
def t(text):
    return translate(text,language)

def choice(target,label,options,index=0):
    # Streamlit can retain the previous language's displayed selection when a
    # format_func changes. Recreate only the view, keeping canonical choices.
    saved=st.session_state.setdefault('_choices',{})
    previous=saved.get(label,options[index])
    selection=target.selectbox(t(label),options,
        index=options.index(previous) if previous in options else index,
        format_func=lambda value:str(t(value)),key=f'{label}::{language}')
    saved[label]=selection
    return selection

def show_error(exc, warning=False):
    message=error_text(exc,language)
    (st.warning if warning else st.error)(message)
    if message!=str(exc) or exc.__cause__ is not None:
        with st.expander(t('Technical details')):
            st.code(str(exc),language=None)
            if exc.__cause__ is not None:
                st.code(f'{type(exc.__cause__).__name__}: {exc.__cause__}',language=None)

st.markdown('''<style>
.block-container {padding-top:4rem; max-width:1500px}
[data-testid="stMetric"] {background:#141e30;color:#e5edf8;border:1px solid #28334a;border-radius:12px;padding:18px}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {color:#e5edf8}
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {flex-wrap:wrap !important}
[data-testid="stColumn"]:has([data-testid="stMetric"]) {min-width:180px !important;flex:1 1 180px !important}
h1 {letter-spacing:-1.5px;word-break:keep-all} .eyebrow {color:#208b72;letter-spacing:3px;font-size:12px;font-weight:700}
@media(max-width:700px) {h1 {font-size:2rem !important;letter-spacing:-.7px} .block-container {padding-top:4rem}}
</style>''',unsafe_allow_html=True)
COLORS={'Defensive':'#ff7d85','Soft / mixed':'#d5a65e','Firm / mixed':'#719cff','Expansion':'#42d6ad','Unclassified':'#526078'}

@st.cache_data(ttl=3600,show_spinner=False)
def exchange_data():
    return load_market()

@st.cache_data(ttl=21600,show_spinner=False)
def onchain_data(start,end):
    return load_coinmetrics(start,end)

@st.cache_data(ttl=60,show_spinner=False)
def option_quotes():
    return load_quotes()

@st.cache_data(show_spinner=False)
def analyze(d, oi, chain):
    f=features(d,oi,chain)
    r,p,m=walk_forward(d,f)
    return f,r,p,m

def plot(fig,height=380):
    translate_figure(fig,language)
    fig.update_layout(template='plotly_dark',paper_bgcolor='#0b1120',plot_bgcolor='#0b1120',
        height=height,margin=dict(l=12,r=12,t=35,b=12),legend=dict(orientation='h',y=1.12),font=dict(color='#cbd7e8'))
    st.plotly_chart(fig,width='stretch')

def percent_table(frame):
    formats={t(c):'{:.2%}' for c in frame.select_dtypes('number').columns if c not in ['n','days']}
    st.dataframe(display_frame(frame,language).style.format(formats,na_rep='—'),hide_index=True,width='stretch')

with st.sidebar:
    st.markdown('### ◈ REGIME ATLAS')
    st.caption(t('BTC / DAILY RESEARCH WORKSPACE'))
    source=choice(st,'Data source',['Exchange data','Local snapshot','Upload CSV','Fetch public API'])
    d=None
    meta={}
    try:
        if source=='Exchange data':
            if st.button(t('Refresh exchange data'),key='refresh_exchange'):
                exchange_data.clear()
            st.caption(t('Bybit → Binance → verified snapshot · completed daily bars · one-hour cache.'))
            with st.spinner(t('Fetching price, funding and available OI…')):
                d,meta,notice=exchange_data()
            if notice:
                st.warning(t(notice))
        elif source=='Local snapshot':
            path=Path('data/market.parquet')
            if path.exists():
                d=validate(pd.read_parquet(path))
                meta=json.loads(path.with_suffix('.json').read_text()) if path.with_suffix('.json').exists() else {'source':'local','synthetic':False,'price_instrument':'user-supplied, unverified'}
            else:
                st.info(t('Create a snapshot with the ingestion command in the README.'))
        elif source=='Upload CSV':
            uploaded=st.file_uploader(t('Daily market CSV'),type=['csv'], key='Daily market CSV')
            if uploaded:
                d=validate(pd.read_csv(uploaded))
                meta={'source':'uploaded','synthetic':False,'price_instrument':'user-supplied, unverified'}
        else:
            venue=choice(st,'Venue',['binance','bybit'])
            days=choice(st,'History requested (days)',[730,1095,1460])
            if st.button(t('Fetch & validate'),type='primary', key='Fetch & validate'):
                with st.spinner(t('Fetching price, funding and available OI…')):
                    st.session_state['downloaded']=download(venue,days)
            if 'downloaded' in st.session_state:
                d,meta=st.session_state['downloaded']
        chain_source=choice(st,'On-chain source',['Coin Metrics (noncommercial)','CSV only / off'])
        chain_csv=st.file_uploader(t('Optional on-chain CSV'),type=['csv'],help=t('Requires available_at and mvrv, sopr or exchange_netflow. Only use data you are licensed to process.'), key='Optional on-chain CSV')
        if d is not None and chain_csv:
            d=enrich(d,chain_csv.getvalue().decode('utf-8-sig'))
            meta={**meta,'onchain':'user upload; availability timestamps supplied by user'}
        elif d is not None and chain_source=='Coin Metrics (noncommercial)':
            try:
                chain,chain_meta=onchain_data(d.date.min(),d.date.max())
                d=enrich(d,chain.to_csv(index=False))
                meta['onchain']=chain_meta
                st.caption(t('Coin Metrics · CC BY-NC 4.0 · noncommercial research only.'))
                st.caption(t('MVRV and net flows: assumed 48-hour lag; revised historical data. SOPR is unavailable from this free source.'))
                if chain_meta['fallback_used']:
                    st.warning(t('On-chain fallback in use. Check observation_end in the data manifest.'))
            except Exception as chain_error:
                st.warning(t('On-chain data unavailable; price and derivatives remain usable.'))
                with st.expander(t('Technical details')): st.code(str(chain_error))
    except Exception as exc:
        show_error(exc)
        d=None
    include_oi=st.checkbox(t('Include OI features'),value=False,help=t('Requires at least 180 complete training rows. Recent-only Binance OI is insufficient.'), key='Include OI features')
    include_chain=st.checkbox(t('Include on-chain features (exploratory)'),value=False, key='Include uploaded on-chain features')
    st.divider()
    audience=choice(st,'Presentation focus',['Research team','Exchange','Options team'])
    st.caption(t('Fixed model: four clusters · 365-day warm-up · 90-day refits · final 180-day frozen holdout.'))

st.markdown('<div class="eyebrow">'+t('MARKET INTELLIGENCE / RESEARCH MVP')+'</div>',unsafe_allow_html=True)
st.title(t('Understand the regime. Inspect the evidence.'))
st.caption(t('Price, positioning and on-chain context — with transparent historical outcomes.'))
if d is None:
    st.info(t('Load a real market snapshot, upload your dataset, or fetch a public API in the sidebar.'))
    st.stop()
if meta.get('synthetic'):
    st.warning(t('SYNTHETIC DEMO — generated prices and indicators. All results demonstrate software behavior; they are not market evidence.'))
else:
    st.info(t(t('Dataset: {source} · {instrument} · as of {date} UTC. Historical API data may contain later revisions.').format(source=t(meta.get('source')),instrument=t(meta.get('price_instrument')),date=f'{d.date.max():%Y-%m-%d}')))
    if d.date.max()<pd.Timestamp.now(tz='UTC').normalize()-pd.Timedelta(days=2):
        st.warning(t('Historical snapshot: the last observation is more than two days old. Latest regime below is not a live signal.'))
if include_chain and not any(c in d for c in ['mvrv','sopr','exchange_netflow']):
    st.error(t('Upload on-chain data before enabling its features.'))
    st.stop()
try:
    with st.spinner(t('Computing causal features and walk-forward regimes…')):
        f,r,profiles,manifest=analyze(d,include_oi,include_chain)
except ValueError as exc:
    show_error(exc)
    st.stop()
manifest.update(source=meta,dataset_sha256=hashlib.sha256(d.to_csv(index=False).encode()).hexdigest(),
    generated_at=pd.Timestamp.now(tz='UTC').isoformat())
latest=r.iloc[-1]
a,b,c,e=st.columns(4)
a.metric(t('Latest historical regime'),t(latest.regime))
b.metric(t('Last close'),f'${d.close.iloc[-1]:,.0f}',f'{d.close.pct_change().iloc[-1]:+.2%}')
c.metric(t('30-day momentum'),f'{f.momentum_30.iloc[-1]:+.1%}')
e.metric(t('Last daily funding'),f'{d.funding.iloc[-1]:.4%}' if pd.notna(d.funding.iloc[-1]) else t('Missing'))
st.caption(t(t('{count} daily observations · {start} → {end} · Source: {source}').format(count=f'{len(d):,}',start=f'{d.date.min():%Y-%m-%d}',end=f'{d.date.max():%Y-%m-%d}',source=t(meta['source']))))
tabs=st.tabs([t(name) for name in ['Overview','Historical outcomes','Strategy lab','Options payoff','Data & methodology']])

with tabs[0]:
    available_metrics=[name for name in ['mvrv','sopr','exchange_netflow'] if name in d]
    if available_metrics:
        st.subheader(t('On-chain observations aligned to market dates'))
        columns=st.columns(len(available_metrics))
        for column,name in zip(columns,available_metrics):
            value=d[name].iloc[-1]
            column.metric(t(name),f'{value:,.3f}' if pd.notna(value) else t('Missing'))
        st.caption(t('Net flows are USD deposits minus withdrawals. A negative value does not prove buying. Missing observations stay missing.'))
        metric=choice(st,'On-chain chart',available_metrics)
        plot(px.line(d,x='date',y=metric))
    chart=d[['date','close']].join(r[['regime','partition']])
    fig=go.Figure(go.Scatter(x=chart.date,y=chart.close,line=dict(color='#50627e',width=1),name='BTC price',showlegend=False))
    for label,color in COLORS.items():
        subset=chart[chart.regime==label]
        fig.add_trace(go.Scatter(x=subset.date,y=subset.close,mode='markers',marker=dict(size=3,color=color),name=label))
    fig.update_yaxes(title='Price · USD / USDT proxy')
    plot(fig,430)
    left,right=st.columns([1.35,1])
    with left:
        st.subheader(t('What defines the latest model?'))
        last_profiles=profiles[profiles.model_version==latest.model_version].drop(columns='model_version')
        st.dataframe(display_frame(last_profiles.set_index('regime').round(4),language),width='stretch')
        st.caption(t('Training-period cluster centroids. Names rank 30-day momentum within each fit; identities can change between fits.'))
    with right:
        st.subheader(t('Read the signals'))
        for name,explanation in {
            'Funding':'The daily sum of realized funding fractions. Positive funding usually means longs paid shorts. Negative funding alone does not prove a reversal or capital inflow.',
            'Open interest':'Outstanding derivative exposure. USD OI moves with both position size and price. Rising OI does not identify which side will win.',
            'MVRV & SOPR':'MVRV compares market value with realized value; SOPR describes spent-output profitability. Provider definitions and publication times matter.',
            'Exchange net flows':'Deposits minus withdrawals for labeled exchange addresses. Transfers are not equivalent to executed selling or buying.'}.items():
            with st.expander(t(name)): st.write(t(explanation))
    st.subheader(t('Persistence & transitions'))
    observed=r[r.regime!='Unclassified'].copy()
    transition=pd.crosstab(observed.regime.shift(),observed.regime,normalize='index')
    st.dataframe(display_frame(transition,language).style.format('{:.1%}'),width='stretch')
    st.caption(t('Descriptive transition frequencies across all classified dates, including refit boundaries; not a forecast.'))

with tabs[1]:
    st.subheader(t('What happened after similar observations?'))
    l,m,n=st.columns(3)
    horizon=choice(l,'Forward horizon',[7,14,30],index=2)
    partition=choice(m,'Evaluation segment',['Final holdout','Walk-forward'])
    taxonomy=choice(n,'Grouping',['ML clusters','Indicator rules'])
    ev=events(d,r,horizon,partition,'regime' if taxonomy=='ML clusters' else 'rule')
    summary=summarize(ev)
    st.caption(t('Signal at daily close → next daily open entry → open exit after the selected calendar-day horizon. Globally non-overlapping windows; raw asset returns before costs.'))
    if ev.empty:
        st.info(t('No complete events in this segment.'))
    else:
        percent_table(summary)
        plot(px.box(ev,x='regime',y='return_',points='all',color='regime',color_discrete_map=COLORS,labels={'return_':'Forward return','regime':''}))
        st.warning(t('Small samples are expected: 180 days contain at most about six non-overlapping 30-day windows. Intervals are suppressed below five samples and remain approximate above that threshold.'))
        st.caption(t('Intervals use a moving-block bootstrap. “All sampled dates” uses the same eligible dates. These sampled windows are not independent market episodes. Repeated holdout inspection makes subsequent model choices exploratory.'))
        st.download_button(t('Download event ledger'),ev.to_csv(index=False),'events.csv','text/csv', key='Download event ledger')

with tabs[2]:
    st.subheader(t('A predefined rule, an explicit ledger'))
    st.write(t('Long when the prior completed day has positive 30-day momentum and an available model classification; otherwise cash. Full allocation, no leverage. The strategy uses indicator rules, not a hindsight selection of profitable clusters.'))
    x,y,z=st.columns(3)
    fees=x.number_input(t('One-way fees (bps)'),min_value=0.,value=5.,step=1., key='One-way fees (bps)')
    slip=y.number_input(t('One-way slippage (bps)'),min_value=0.,value=5.,step=1., key='One-way slippage (bps)')
    mode=choice(z,'Accounting',['Spot-like price proxy','Perpetual with daily funding'])
    st.caption(t('Public adapters use perpetual candles. Spot-like mode is a price-only proxy, not an executable spot backtest. Perpetual funding uses daily summed rates on opening notional; intraday mark-notional changes are approximated.'))
    try:
        ledger,metrics=strategy(d,r,fees,slip,partition,'perpetual' if mode.startswith('Perpetual') else 'spot_proxy')
        if not ledger.empty:
            percent_table(metrics)
            plot(px.line(ledger,x='date',y=['equity','benchmark'],color_discrete_sequence=['#42d6ad','#719cff'],labels={'value':'Growth of 1 unit','variable':'Strategy'}))
            st.caption(t(t('Evaluation: {partition}. Includes entry, position changes and final liquidation costs. Cash earns zero; no taxes, borrow costs or liquidation model.').format(partition=t(partition))))
            st.download_button(t('Download trading ledger'),ledger.to_csv(index=False),'strategy-ledger.csv','text/csv', key='Download trading ledger')
    except ValueError as exc:
        show_error(exc,warning=True)
        ledger=pd.DataFrame()

with tabs[3]:
    st.subheader(t('Deribit public BTC call quotes'))
    st.caption(t('Current quotes only; no historical option returns. Target: 30 days ± 14, nearest 110% strike among OTM calls.'))
    if st.button(t('Fetch current option quote'),key='fetch_options'):
        try:
            quotes=option_quotes()
            selected=select_call(quotes)
            st.dataframe(selected.to_frame('value').astype(str),width='stretch')
            quoted_payoff=inverse_call_payoff(selected.spot_index,selected.strike,selected.bid_btc)
            plot(px.line(quoted_payoff,x='terminal_price',y=['spot_return','covered_call_return']))
            st.caption(t('Inverse BTC settlement; premium retained in BTC. Gross expiry scenario using bid, zero fees. Execution and collateral effects are not modeled.'))
            quotes['regime']=latest.regime
            quotes['regime_date']=str(d.date.max())
            st.download_button(t('Download timestamped option quotes'),quotes.to_csv(index=False),'deribit-quotes.csv','text/csv')
        except Exception as exc:
            show_error(exc,warning=True)
    st.divider()
    st.subheader(t('Covered-call payoff explorer'))
    st.info(t('SCENARIO SIMULATION — premiums are assumptions. This is not a historical options backtest, a quoted product, or a regime-specific return estimate.'))
    a,b,c=st.columns(3)
    strike=a.slider(t('Strike (% of entry spot)'),80,150,110, key='Strike (% of entry spot)')
    premium=b.slider(t('Assumed premium (% of entry spot)'),0.,20.,3.,.25, key='Assumed premium (% of entry spot)')
    cost=c.slider(t('Total assumed costs (% of entry spot)'),0.,3.,.2,.1, key='Total assumed costs (% of entry spot)')
    pay=payoff(100,strike,premium,cost)
    plot(px.line(pay,x='terminal_price',y=['spot_return','covered_call_return'],color_discrete_sequence=['#719cff','#42d6ad'],labels={'terminal_price':'Terminal spot (entry = 100)','value':'Return on initial spot capital'}))
    st.write(t(t('Maximum covered-call return: {maximum}. Loss if the underlying goes to zero: {loss}. Premium cushions losses and caps gains; it does not remove downside risk.').format(maximum=f'{(strike-100+premium-cost)/100:.1%}',loss=f'{(-100+premium-cost)/100:.1%}')))
    st.caption(t('One unit of owned spot + one same-unit short call, held to expiry. Linear USD cash settlement; no interim mark-to-market or collateral mechanics. Regime-to-options mappings remain hypotheses until quote history is available.'))

with tabs[4]:
    st.subheader(t('Data quality & reproducibility'))
    st.dataframe(display_frame(quality(d),language),hide_index=True,width='stretch')
    st.json(meta)
    st.markdown(t('''**Validation contract**

- UTC daily bars; duplicates, gaps and invalid prices are rejected.
- No backward filling. Missing model features produce unclassified dates.
- Standardization and clustering fit only on past complete observations.
- Expanding refits stop at the final 180-day holdout; its model stays frozen.
- No future-return labels enter clustering, so fitting does not require forward-label purging. Event windows cannot cross evaluation boundaries.
- Optional on-chain imports join by `available_at`, with a two-day staleness limit. The uploader must supply honest historical publication timestamps.
- Cluster names describe relative training momentum, not validated economic states. Distances are not probabilities.
- No automatic parameter search. Changing features after viewing holdout results invalidates an untouched-test interpretation.
'''))
    focus={'Research team':'Lead with sample sizes, out-of-sample distributions, data lineage and negative findings.',
        'Exchange':'Lead with derivatives coverage, funding conventions, data freshness and indicator education.',
        'Options team':'Lead with payoff assumptions, capped upside, full downside exposure and the missing historical quote requirement.'}
    st.success(t(f'{t(audience)}: {t(focus[audience])}'))
    manifest['evaluation']={'horizon':horizon,'partition':partition,'taxonomy':taxonomy,'fee_bps':fees,'slippage_bps':slip,'accounting':mode}
    payload=io.BytesIO()
    with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json',json.dumps(manifest,indent=2))
        archive.writestr('regimes.csv',r.to_csv(index=False))
        archive.writestr('profiles.csv',profiles.to_csv(index=False))
        archive.writestr('events.csv',ev.to_csv(index=False))
        archive.writestr('summary.csv',summary.to_csv(index=False))
        archive.writestr('strategy.csv',ledger.to_csv(index=False))
    st.download_button(t('Export reproducible research results'),payload.getvalue(),'regime-research.zip','application/zip', key='Export reproducible research results')
    with st.expander(t('Model fit manifest')): st.json(manifest)
