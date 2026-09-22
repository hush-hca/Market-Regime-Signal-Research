"""Run with: streamlit run app.py"""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from regime.data import enrich, quality
from regime.ingest import download
from regime.feed import load_market, read_snapshot
from regime.onchain import load_onchain
from regime.options import load_quotes, select_call
from regime.signals import context_signals
from regime.evaluation import evaluate_feature_sets
from regime.build import build_id
from regime.research import events, summarize
from regime.readiness import MODELS,model_features,model_states
from regime.panels import health_panel,evidence_panel,forward_panel,collection_status,forward_data
from regime.i18n import translate, error_text, display_frame, translate_figure

BUILD_ID=build_id()

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
    return load_onchain(start,end)

@st.cache_data(ttl=60,show_spinner=False)
def option_quotes():
    return load_quotes()

@st.cache_data(show_spinner=False)
def analyze_models(d):
    return model_states(d)

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
    st.caption(t('Build')+': '+BUILD_ID)
    source=choice(st,'Data source',['Exchange data','Local snapshot','Fetch public API'])
    d=None
    meta={}
    chain=None
    try:
        if source=='Exchange data':
            if st.button(t('Refresh exchange data'),key='refresh_exchange'):
                exchange_data.clear()
                onchain_data.clear()
                collection_status.clear()
                forward_data.clear()
            st.caption(t('Bybit → Binance → verified snapshot · completed daily bars · one-hour cache.'))
            with st.spinner(t('Fetching price, funding and available OI…')):
                d,meta,notice=exchange_data()
            if notice:
                st.warning(t(notice))
        elif source=='Local snapshot':
            path=Path('data/market.parquet')
            if path.exists():
                d,meta=read_snapshot(path,require_digest=True)
            else:
                st.info(t('Create a snapshot with the ingestion command in the README.'))
        else:
            venue=choice(st,'Venue',['binance','bybit'])
            days=choice(st,'History requested (days)',[730,1095,1460])
            if st.button(t('Fetch & validate'),type='primary', key='Fetch & validate'):
                with st.spinner(t('Fetching price, funding and available OI…')):
                    st.session_state['downloaded']=download(venue,days)
            if 'downloaded' in st.session_state:
                d,meta=st.session_state['downloaded']
        chain_source=choice(st,'On-chain source',['Coin Metrics (noncommercial)','Off'])
        if d is not None and chain_source=='Coin Metrics (noncommercial)':
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
    selected_model=choice(st,'Model',MODELS)
    st.divider()
    audience=choice(st,'Presentation focus',['Research team','Exchange','Options team'])
    st.caption(t('Fixed model: four clusters · 365-day warm-up · 90-day refits · final 180-day frozen holdout.'))

st.markdown('<div class="eyebrow">'+t('MARKET INTELLIGENCE / RESEARCH MVP')+'</div>',unsafe_allow_html=True)
st.title(t('Understand the regime. Inspect the evidence.'))
st.caption(t('Price, positioning and on-chain context — with transparent historical outcomes.'))
if d is None:
    st.info(t('Load a verified real market snapshot or fetch a public API in the sidebar.'))
    st.stop()
if meta.get('synthetic'):
    st.error(t('Synthetic data is not allowed.'))
    st.stop()
else:
    st.info(t(t('Dataset: {source} · {instrument} · as of {date} UTC. Historical API data may contain later revisions.').format(source=t(meta.get('source')),instrument=t(meta.get('price_instrument')),date=f'{d.date.max():%Y-%m-%d}')))
    if d.date.max()<pd.Timestamp.now(tz='UTC').normalize()-pd.Timedelta(days=2):
        st.warning(t('Historical snapshot: the last observation is more than two days old. Latest regime below is not a live signal.'))
if meta.get('transport')=='official public archive':
    st.caption(t('Source: checksum-verified Binance public archives. Funding is published monthly and may lag prices.'))
if pd.isna(d.funding.iloc[-1]):
    st.warning(t('Latest funding is missing. Derivative regimes may be unclassified; no funding values are estimated.'))
    funding_dates=d.loc[d.funding.notna(),'date']
    st.caption(t('Last available funding date')+': '+(f'{funding_dates.max():%Y-%m-%d} UTC' if len(funding_dates) else t('Missing')))
states,fits=analyze_models(d)
health_panel(d,meta,chain,states,t,language)
if selected_model not in fits:
    st.warning(t('Selected model is unavailable. Choose an available model explicitly; inputs are never substituted.'))
    st.stop()
f=model_features(d,selected_model)
r,profiles,manifest=fits[selected_model]
manifest.update(build_id=BUILD_ID,evaluation_status='Exploratory; previously inspected holdout',source=meta,dataset_sha256=hashlib.sha256(d.to_csv(index=False).encode()).hexdigest(),
    generated_at=pd.Timestamp.now(tz='UTC').isoformat())
latest=r.iloc[-1]
a,b,c,e=st.columns(4)
a.metric(t('Latest historical regime'),t(latest.regime))
b.metric(t('Last close'),f'${d.close.iloc[-1]:,.0f}',f'{d.close.pct_change().iloc[-1]:+.2%}')
c.metric(t('30-day momentum'),f'{f.momentum_30.iloc[-1]:+.1%}')
e.metric(t('Last daily funding'),f'{d.funding.iloc[-1]:.4%}' if pd.notna(d.funding.iloc[-1]) else t('Missing'))
st.caption(t(t('{count} daily observations · {start} → {end} · Source: {source}').format(count=f'{len(d):,}',start=f'{d.date.min():%Y-%m-%d}',end=f'{d.date.max():%Y-%m-%d}',source=t(meta['source']))))
tabs=st.tabs([t(name) for name in ['Overview','Historical outcomes','Forward ledger','Options data','Data & methodology']])

with tabs[0]:
    evidence_panel(d,r,t,language)
    context=context_signals(d)
    with st.expander(t('Negative funding + low MVRV hypothesis')):
        st.write(t('Daily funding flips below zero and MVRV falls below its prior 365-observation 20th percentile, with at least 180 prior observations. This describes context; it does not establish capital inflow.'))
        st.dataframe(display_frame(context.tail(1),language),hide_index=True)
        st.caption(t('Missing inputs remain unknown. Thresholds use only earlier observations.'))
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
            with st.expander(t(name)):
                st.markdown('**'+t('If you are new to this metric')+'**')
                st.write(t(explanation))
                details={
                    'Funding':('Rate fraction per day; displayed as a percent.','Compare the sign and persistence across days.','The sign does not identify future returns or prove a reversal.'),
                    'Open interest':('USD exposure proxy.','Compare OI changes with price and volume together.','A rise can reflect price changes or new positions; it is not a directional vote.'),
                    'MVRV & SOPR':('Dimensionless ratios.','Read historical percentiles and provider definitions; low is relative to the chosen history.','Neither ratio alone establishes undervaluation or a profitable entry.'),
                    'Exchange net flows':('USD deposits minus withdrawals.','Positive means net deposits; negative means net withdrawals for labeled addresses.','Transfers do not prove executed purchases or sales.')
                }
                units,reading,limitation=details[name]
                st.markdown('**'+t('Units')+'**: '+t(units))
                st.markdown('**'+t('How to read this chart')+'**: '+t(reading))
                st.markdown('**'+t('What this cannot tell you')+'**: '+t(limitation))
                if name in ['MVRV & SOPR','Exchange net flows']:
                    chain_source_meta=meta.get('onchain',{})
                    if isinstance(chain_source_meta,dict):
                        st.caption(t('Source and freshness')+': '+str(chain_source_meta.get('source',t('Missing')))+' · '+str(chain_source_meta.get('observation_end',t('Missing'))))
                    else:
                        st.caption(t('Source and freshness')+': '+str(chain_source_meta))
                    st.caption(t('On-chain source and original observation dates are recorded in Data & methodology. SOPR stays unavailable unless supplied.'))
                else:
                    st.caption(t('Source and freshness')+': '+str(meta.get('source'))+' · '+f'{d.date.max():%Y-%m-%d} UTC')
    st.subheader(t('Persistence & transitions'))
    observed=r[r.regime!='Unclassified'].copy()
    transition=pd.crosstab(observed.regime.shift(),observed.regime,normalize='index')
    st.dataframe(display_frame(transition,language).style.format('{:.1%}'),width='stretch')
    st.caption(t('Descriptive transition frequencies across all classified dates, including refit boundaries; not a forecast.'))

with tabs[1]:
    st.warning(t('Exploratory evaluation: this holdout has already been inspected. New model choices require a new untouched evaluation period.'))
    st.subheader(t('What happened after similar observations?'))
    l,m,n=st.columns(3)
    horizon=choice(l,'Forward horizon',[7,14,30],index=2)
    partition=choice(m,'Evaluation segment',['Final holdout','Walk-forward'])
    taxonomy=choice(n,'Grouping',['ML clusters','Indicator rules','On-chain hypothesis'])
    grouped_regimes=r.copy()
    if taxonomy=='On-chain hypothesis':
        observed_context=context_signals(d).hypothesis_active
        grouped_regimes['rule']='Unclassified'
        grouped_regimes.loc[observed_context.notna(),'rule']='Other observed context'
        grouped_regimes.loc[observed_context.fillna(False),'rule']='Negative funding / low MVRV'
    ev=events(d,grouped_regimes,horizon,partition,'regime' if taxonomy=='ML clusters' else 'rule')
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

    if st.checkbox(t('Compare feature sets on common dates'),key='compare_feature_sets'):
        try:
            comparison=evaluate_feature_sets(d,horizon,partition)
            st.dataframe(display_frame(comparison['coverage'],language),hide_index=True)
            st.dataframe(display_frame(comparison['summary'],language),hide_index=True)
            st.caption(t('Price-only, derivatives and on-chain clusters use common eligible event dates. Different conditional distributions do not prove predictive improvement. Missing feature sets are listed in the manifest.'))
            st.download_button(t('Download feature comparison'),comparison['summary'].to_csv(index=False),'feature-comparison.csv','text/csv')
            st.json(comparison['manifest'])
        except ValueError as exc:
            show_error(exc,warning=True)

with tabs[2]:
    ledger=forward_panel(t,language)

with tabs[3]:
    st.subheader(t('Deribit public BTC call quotes'))
    st.caption(t('Actual observed quotes only. Assumed-premium scenarios and unverified net option returns are not displayed.'))
    if st.button(t('Fetch current option quote'),key='fetch_options'):
        try:
            quotes=option_quotes()
            selected=select_call(quotes)
            st.dataframe(selected.to_frame('value').astype(str),width='stretch')
            st.caption(t('A quoted bid is not proof of an executable fill. Historical option returns require recorded quotes, settlements and verified costs.'))
            st.download_button(t('Download timestamped option quotes'),quotes.to_csv(index=False),'deribit-quotes.csv','text/csv')
        except Exception as exc:
            show_error(exc,warning=True)

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
- On-chain observations join by an explicit 48-hour availability policy, with a two-day alignment tolerance. Historical first-publication timing is not independently verified.
- Cluster names describe relative training momentum, not validated economic states. Distances are not probabilities.
- No automatic parameter search. Changing features after viewing holdout results invalidates an untouched-test interpretation.
'''))
    focus={'Research team':'Lead with sample sizes, out-of-sample distributions, data lineage and negative findings.',
        'Exchange':'Lead with derivatives coverage, funding conventions, data freshness and indicator education.',
        'Options team':'Lead with observed quotes, settlement conventions and historical coverage gaps.'}
    st.success(t(f'{t(audience)}: {t(focus[audience])}'))
    manifest['evaluation']={'horizon':horizon,'partition':partition,'taxonomy':taxonomy,'accounting':'Observed gross asset returns; costs excluded'}
    payload=io.BytesIO()
    with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json',json.dumps(manifest,indent=2))
        archive.writestr('regimes.csv',r.to_csv(index=False))
        archive.writestr('profiles.csv',profiles.to_csv(index=False))
        archive.writestr('events.csv',ev.to_csv(index=False))
        archive.writestr('summary.csv',summary.to_csv(index=False))
        archive.writestr('forward-ledger.csv',ledger.to_csv(index=False))
    st.download_button(t('Export reproducible research results'),payload.getvalue(),'regime-research.zip','application/zip', key='Export reproducible research results')
    with st.expander(t('Model fit manifest')): st.json(manifest)
