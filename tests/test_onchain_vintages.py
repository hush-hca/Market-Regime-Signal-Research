import pandas as pd
import pytest
from regime.data import demo


def test_later_revision_never_rewrites_past_decision():
    from regime.vintages import enrich_vintages
    market=demo(4); market.date=pd.date_range('2025-01-01',periods=4,tz='UTC')
    records=pd.DataFrame([
        dict(observation_time='2025-01-01',available_at='2025-01-02',retrieved_at='2025-01-02',mvrv=2.),
        dict(observation_time='2025-01-01',available_at='2025-01-02',retrieved_at='2025-01-04',mvrv=9.),
        dict(observation_time='2025-01-02',available_at='2025-01-03',retrieved_at='2025-01-03',mvrv=3.),
    ])
    result=enrich_vintages(market,records)
    assert result.mvrv.iloc[0]==2.
    assert result.mvrv.iloc[1]==3.
    assert result.mvrv.iloc[2]==3. # old observation revised later cannot replace newer observation
    pd.testing.assert_series_equal(result.mvrv.iloc[:2],enrich_vintages(market,records.iloc[[0,2]]).mvrv.iloc[:2])


def test_unknown_publication_rejected_and_old_observations_expire():
    from regime.vintages import enrich_vintages
    market=demo(10); market.date=pd.date_range('2025-01-01',periods=10,tz='UTC')
    record=pd.DataFrame([dict(observation_time='2025-01-01',available_at=None,retrieved_at='2025-01-02',mvrv=2)])
    with pytest.raises(ValueError,match='timestamp'): enrich_vintages(market,record)
    record['available_at']='2025-01-02'
    assert pd.isna(enrich_vintages(market,record).mvrv.iloc[-1])
