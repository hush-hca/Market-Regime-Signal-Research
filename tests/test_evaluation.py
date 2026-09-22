import pandas as pd
import pytest
from regime.data import demo


def test_comparison_rejects_mismatched_dates_and_cost_rules():
    from regime.evaluation import compare_feature_sets
    a=pd.DataFrame(dict(signal_date=pd.date_range('2025-01-01',periods=6,tz='UTC'),
        net_return=[.01,-.02,.03,0,.01,.02],benchmark_return=[.01]*6,cost_bps=[10]*6))
    with pytest.raises(ValueError,match='dates'): compare_feature_sets({'a':a,'b':a.iloc[1:]})
    b=a.copy(); b['cost_bps']=20
    with pytest.raises(ValueError,match='cost'): compare_feature_sets({'a':a,'b':b})
    report=compare_feature_sets({'a':a,'b':a.copy()})
    assert report.n.tolist()==[6,6]
    assert report.mean_excess.iloc[0]==pytest.approx(a.net_return.mean()-.01)


def test_suite_uses_same_event_dates_and_documents_missing_features():
    from regime.evaluation import evaluate_feature_sets
    data=demo(900); data['mvrv']=2.; data['exchange_netflow']=100.
    data.loc[750:755,'mvrv']=float('nan')
    result=evaluate_feature_sets(data,horizon=7)
    dates=[tuple(frame.signal_date) for frame in result['events'].values()]
    assert len(set(dates))==1
    assert 'sopr' in result['manifest']['unavailable_metrics']
    assert result['manifest']['evaluation_status']=='Exploratory; previously inspected holdout'
