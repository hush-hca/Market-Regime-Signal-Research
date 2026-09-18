import numpy as np
import pandas as pd
import pytest
from regime.data import demo, validate, enrich
from regime.research import features, walk_forward, events, strategy, payoff, interval

def test_validate_rejects_gaps_duplicates_and_invalid_prices():
    d=demo(100)
    for bad in [d.drop(index=10),pd.concat([d,d.iloc[[0]]]),d.assign(close=-1)]:
        with pytest.raises(ValueError): validate(bad)

def test_future_price_change_cannot_change_prior_features_or_predictions():
    d=demo(900)
    altered=d.copy()
    altered.loc[800:,'close']*=3
    f1,f2=features(d),features(altered)
    pd.testing.assert_frame_equal(f1.iloc[:800],f2.iloc[:800])
    a,_,_=walk_forward(d,f1)
    b,_,_=walk_forward(altered,f2)
    pd.testing.assert_frame_equal(a.iloc[:800],b.iloc[:800])
    assert a.iloc[-180:].model_version.nunique()==1
    assert a.iloc[:365].regime.eq('Unclassified').all()

def test_missing_features_are_unclassified_and_not_backfilled():
    d=demo(900)
    d.loc[800,'funding']=np.nan
    r,_,_=walk_forward(d,features(d))
    assert r.loc[800:806,'regime'].eq('Unclassified').all()
    assert r.loc[807,'regime']!='Unclassified'

def test_onchain_uses_availability_not_observation_date_and_expires():
    d=demo(10)
    csv='available_at,mvrv\n2022-01-04T12:00:00Z,1.1\n'
    merged=enrich(d,csv)
    assert merged.loc[:2,'mvrv'].isna().all()
    assert merged.loc[3,'mvrv']==1.1
    assert np.isnan(merged.loc[6,'mvrv'])

def test_event_timing_nonoverlap_and_partition_boundaries():
    d=demo(900)
    r,_,_=walk_forward(d,features(d))
    ev=events(d,r,30)
    assert len(ev)>0
    assert (ev.entry_date==ev.signal_date+pd.Timedelta(days=1)).all()
    assert (ev.exit_date==ev.entry_date+pd.Timedelta(days=30)).all()
    assert all(ev.entry_date.iloc[i]>=ev.exit_date.iloc[i-1] for i in range(1,len(ev)))
    first=ev.iloc[0]
    prices=d.set_index('date').open
    assert first.return_==pytest.approx(prices[first.exit_date]/prices[first.entry_date]-1)
    assert ev.exit_date.max()<=d.date.max()

def test_strategy_lags_signal_and_charges_round_trip():
    d=demo(10)
    d['open']=100.
    r=pd.DataFrame({'rule':['Mixed']*10,'regime':['Expansion']*10,'partition':['Final holdout']*10})
    r.loc[2,'rule']='Positive trend / positive funding'
    ledger,_=strategy(d,r,fee_bps=10,slippage_bps=0)
    assert ledger.loc[ledger.position==1,'entry_date'].iloc[0]==d.date.iloc[3]
    assert ledger.loc[ledger.position==1,'date'].iloc[0]==d.date.iloc[4]
    assert ledger.equity.iloc[-1]==pytest.approx(.999**2)

def test_terminal_liquidation_and_benchmark_costs():
    d=demo(10)
    d['open']=100.
    r=pd.DataFrame({'rule':['Positive trend']*10,'regime':['Expansion']*10,'partition':['Final holdout']*10})
    ledger,_=strategy(d,r,10,0)
    assert ledger.equity.iloc[-1]==pytest.approx(.999**2)
    assert ledger.benchmark.iloc[-1]==pytest.approx(.999**2)

def test_perpetual_rejects_missing_funding():
    d=demo(10)
    d.loc[4,'funding']=np.nan
    r=pd.DataFrame({'rule':['Positive trend']*10,'regime':['Expansion']*10,'partition':['Final holdout']*10})
    with pytest.raises(ValueError,match='funding'): strategy(d,r,instrument='perpetual')

def test_insufficient_oi_history_fails_explicitly():
    d=demo(900)
    d.loc[:870,'oi']=np.nan
    with pytest.raises(ValueError,match='Insufficient'): walk_forward(d,features(d,True))

def test_payoff_caps_upside_preserves_downside():
    p=payoff(100,110,3,1)
    assert p.covered_call_return.max()==pytest.approx(.12)
    assert p.covered_call_return.iloc[0]==pytest.approx(-.98)
    assert all(np.isnan(interval([.1,.2])))
