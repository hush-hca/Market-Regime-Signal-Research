"""Bilingual actual-observation UI panels; no sample data or assumed execution."""
import json
import pandas as pd
import streamlit as st
from .readiness import metric_health,evidence_cards
from .repository import read_collection_status
from .forward import read_forward
from .i18n import display_frame


@st.cache_data(ttl=300,show_spinner=False)
def collection_status(): return read_collection_status()


@st.cache_data(ttl=300,show_spinner=False)
def forward_data(): return read_forward()


def health_panel(d,meta,chain,states,t,language):
    st.subheader(t('Data health and model readiness'))
    st.caption(t('Observation dates and usable market dates are different. Older than three calendar days is flagged stale; this is an operational policy.'))
    st.dataframe(display_frame(metric_health(d,meta,chain),language),hide_index=True,width='stretch')
    st.dataframe(display_frame(states,language),hide_index=True,width='stretch')
    st.caption(t('Price only uses observed price and volume. Derivatives adds funding and OI. On-chain adds MVRV and net flows; SOPR is not included. No automatic model substitution.'))
    with st.expander(t('Collector status and failures')):
        try:
            status=collection_status()
            st.caption(t('Collection started at')+': '+str(status.get('as_of')))
            st.dataframe(display_frame(pd.DataFrame([{'dataset':key,**value} for key,value in status['datasets'].items()]),language),hide_index=True)
        except Exception:
            st.info(t('Collection status unavailable. This does not establish that collection succeeded.'))


def evidence_panel(d,r,t,language):
    st.subheader(t('Evidence by regime'))
    horizon=st.selectbox(t('Evidence horizon (days)'),[7,14,30],index=2,key='evidence_horizon')
    cards=evidence_cards(d,r,horizon,'Final holdout')
    st.caption(t('Exploratory gross asset outcomes, not forecasts or net trading returns. Baseline: all eligible sampled dates. The mean difference is descriptive, not a paired strategy edge.'))
    for row in cards.to_dict('records'):
        with st.expander(t(row['regime'])+' · '+str(row['n'])+' '+t('completed events'),expanded=row['regime']==r.regime.iloc[-1]):
            st.write(t('Evaluation period')+f": {row['evaluation_start']:%Y-%m-%d} → {row['evaluation_end']:%Y-%m-%d}")
            st.write(t('Sampled episodes')+': '+str(row['sampled_episodes']))
            if row['n']==0:
                st.info(t('No completed events in this segment.')); continue
            st.write(t('Positive frequency')+f": {row['positive_frequency']:.1%}")
            st.write(t('Mean / median return')+f": {row['mean']:.2%} / {row['median']:.2%}")
            st.write(t('Baseline mean / descriptive difference')+f": {row['benchmark_mean']:.2%} / {row['difference_from_all']:+.2%}")
            if pd.isna(row['mean_ci_low']): st.caption(t('Mean uncertainty interval unavailable: fewer than five events.'))
            else: st.caption(t('Approximate 95% bootstrap interval for the mean')+f": {row['mean_ci_low']:.2%} → {row['mean_ci_high']:.2%}")
            st.warning(t('Limited sample; no demonstrated predictive edge.') if row['n']<30 else t('Descriptive evidence; no demonstrated predictive edge.'))
    st.download_button(t('Download regime evidence'),cards.to_csv(index=False),'regime-evidence.csv','text/csv')


def forward_panel(t,language):
    st.subheader(t('Frozen forward paper ledger'))
    st.caption(t('Only observations recorded after model registration appear here. Frozen models never refit. Entry is scheduled for the first UTC open after recording; outcomes wait for actual later bars.'))
    st.warning(t('Paper research, not executed trades. Returns are gross perpetual-candle price changes; funding, fees, slippage and interest are excluded. Overlapping horizons are not independent samples.'))
    if st.button(t('Refresh forward ledger'),key='refresh_forward'): forward_data.clear()
    try:
        ledger,models,meta=forward_data()
    except Exception:
        st.info(t('No verified forward ledger is available yet. No example predictions or returns are shown.'))
        return pd.DataFrame()
    st.caption(t('Recorded models')+': '+str(len(models))+' · '+t('Completed outcomes')+': '+str(int(ledger.status.eq('completed').sum())))
    st.caption(t('Paper rule: long when observed 30-day momentum is positive and inputs are complete; otherwise abstain. This rule is fixed at registration and has no proven edge.'))
    st.dataframe(display_frame(ledger.drop(columns=['feature_values']),language),hide_index=True,width='stretch')
    if not ledger.status.eq('completed').any(): st.info(t('Outcomes are pending. No forward performance exists yet.'))
    with st.expander(t('Frozen model artifacts')):
        st.json([{'model_id':row.model_id,**json.loads(row.artifact)} for row in models.itertuples()])
    st.download_button(t('Download forward ledger'),ledger.to_csv(index=False),'forward-ledger.csv','text/csv')
    st.download_button(t('Download frozen models'),models.to_json(orient='records'),'forward-models.json','application/json')
    return ledger
