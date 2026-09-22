from pathlib import Path
import pandas as pd
from regime.feed import read_snapshot, BUNDLED_SNAPSHOT
from regime.readiness import model_features, model_states, metric_health, evidence_cards


def real():
    return read_snapshot(BUNDLED_SNAPSHOT,True)


def test_price_model_survives_missing_derivatives():
    d,meta=real()
    d.loc[d.index[-10:],'funding']=float('nan')
    states,fits=model_states(d)
    status=states.set_index('model')
    assert status.loc['Price only','latest_ready']
    assert not status.loc['Price + derivatives','latest_ready']
    assert status.loc['Price + derivatives + on-chain','status']=='Unavailable'
    assert 'funding_7' not in model_features(d,'Price only')
    assert fits['Price only'][0].regime.iloc[-1]!='Unclassified'


def test_health_separates_original_and_aligned_dates():
    d,meta=real()
    chain=pd.read_parquet(Path(BUNDLED_SNAPSHOT).with_name('coinmetrics.parquet'))
    from regime.data import enrich
    joined=enrich(d,chain.to_csv(index=False))
    health=metric_health(joined,{**meta,'onchain':{'source':'Coin Metrics'}},chain).set_index('metric')
    assert health.loc['sopr','status']=='Missing'
    assert health.loc['mvrv','observation_date']==chain.loc[chain.mvrv.notna(),'observation_time'].max()
    assert health.loc['mvrv','usable_market_date']<=d.date.max()


def test_evidence_has_all_regimes_and_matches_events():
    d,_=real()
    _,fits=model_states(d)
    r=fits['Price only'][0]
    cards=evidence_cards(d,r,30,'Final holdout')
    assert len(cards)==4
    assert cards.n.sum()<=6
    assert cards.mean_ci_low.isna().all()
    assert cards.evaluation_start.notna().all()


def test_comparison_uses_the_same_fixed_onchain_columns():
    from regime.signals import feature_sets
    from regime.data import enrich
    d,_=real()
    chain=pd.read_parquet(Path(BUNDLED_SNAPSHOT).with_name('coinmetrics.parquet'))
    d=enrich(d,chain.to_csv(index=False))
    d['sopr']=float('nan')
    comparison=feature_sets(d)['Price + derivatives + on-chain']
    pd.testing.assert_frame_equal(comparison,model_features(d,'Price + derivatives + on-chain'))
