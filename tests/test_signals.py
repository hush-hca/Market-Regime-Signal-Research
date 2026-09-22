import numpy as np
import pandas as pd
from regime.data import demo


def test_context_uses_prior_threshold_and_preserves_unknown():
    from regime.signals import context_signals
    data=demo(400); data['mvrv']=2.; data['funding']=.001
    data.loc[200,['funding','mvrv']]=[-.001,1.]
    result=context_signals(data)
    assert pd.isna(result.mvrv_low.iloc[100])
    assert result.hypothesis_active.iloc[200]
    changed=data.copy(); changed.loc[201:,'mvrv']=1000
    pd.testing.assert_frame_equal(result.iloc[:201],context_signals(changed).iloc[:201])
    data.loc[199,'funding']=np.nan
    assert pd.isna(context_signals(data).hypothesis_active.iloc[200])


def test_feature_sets_are_explicit_and_missing_chain_not_silently_ignored():
    from regime.signals import feature_sets
    data=demo(730)
    sets=feature_sets(data)
    assert set(sets)=={'Price only','Price + derivatives'}
    assert 'funding_7' not in sets['Price only']
    data['mvrv']=2.; data['exchange_netflow']=100.
    sets=feature_sets(data)
    assert 'Price + derivatives + on-chain' in sets
    assert 'sopr' not in sets['Price + derivatives + on-chain']
