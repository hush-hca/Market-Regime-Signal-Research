import pandas as pd
from regime.feed import read_snapshot,BUNDLED_SNAPSHOT
from regime.store import write_snapshot,read_latest
from regime.forward import collect_forward


def publish(root,d,now):
    return write_snapshot(d,dict(dataset='market_bybit',source='bybit',synthetic=False,
        retrieved_at=now,price_instrument='USDT perpetual'),root)


def test_forward_freezes_and_never_backdates_or_rewrites(tmp_path):
    d,_=read_snapshot(BUNDLED_SNAPSHOT,True)
    first=d.iloc[:650]
    now=(first.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,first,now)
    collect_forward(tmp_path,now)
    models,_=read_latest(tmp_path,'forward_models')
    ledger,_=read_latest(tmp_path,'forward_ledger')
    assert len(ledger)==6  # two available models, three fixed horizons
    assert (pd.to_datetime(ledger.entry_date,utc=True)>pd.Timestamp(now)).all()
    assert ledger.entry_price.isna().all() and ledger.asset_gross_return.isna().all()
    collect_forward(tmp_path,now)
    assert len(read_latest(tmp_path,'forward_ledger')[0])==6
    later=(d.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,d,later)
    collect_forward(tmp_path,later)
    newmodels,_=read_latest(tmp_path,'forward_models')
    pd.testing.assert_frame_equal(models,newmodels)
    after,_=read_latest(tmp_path,'forward_ledger')
    completed=after[after.record_id.isin(ledger.record_id)]
    assert completed.status.eq('completed').all()
    assert completed.outcome_snapshot.notna().all()
    for row in completed.itertuples():
        entry=d.loc[d.date.eq(pd.Timestamp(row.entry_date)),'open'].iloc[0]
        exit_=d.loc[d.date.eq(pd.Timestamp(row.exit_date)),'open'].iloc[0]
        assert row.asset_gross_return==exit_/entry-1
    # Deliberately revise the input copy using other observed prices; this is a
    # corruption/revision test, never a new real-market claim or published input.
    revised=d.copy()
    revised['open']=revised['close']
    publish(tmp_path,revised,later)
    collect_forward(tmp_path,later)
    again=read_latest(tmp_path,'forward_ledger')[0]
    pd.testing.assert_frame_equal(completed.reset_index(drop=True),again[again.record_id.isin(ledger.record_id)].reset_index(drop=True))


def test_missing_funding_is_not_a_forward_prediction(tmp_path):
    d,_=read_snapshot(BUNDLED_SNAPSHOT,True)
    d.loc[d.index[-8:],'funding']=float('nan')
    now=(d.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,d,now)
    collect_forward(tmp_path,now)
    ledger,_=read_latest(tmp_path,'forward_ledger')
    unavailable=ledger[ledger.model.eq('Price + derivatives')]
    assert unavailable.status.eq('missing_inputs').all()
    assert unavailable.regime.eq('Unclassified').all()
    assert unavailable.entry_date.isna().all()


def test_changed_feature_implementation_and_future_receipts_rejected(tmp_path,monkeypatch):
    import pytest
    import regime.forward as forward
    d,_=read_snapshot(BUNDLED_SNAPSHOT,True)
    now=(d.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,d,now)
    collect_forward(tmp_path,now)
    monkeypatch.setattr(forward,'feature_fingerprint',lambda:'changed')
    with pytest.raises(ValueError,match='feature definition'):
        collect_forward(tmp_path,now)
    other=tmp_path/'future'
    publish(other,d,(pd.Timestamp(now)+pd.Timedelta(days=1)).isoformat())
    with pytest.raises(ValueError,match='Future market'):
        collect_forward(other,now)


def test_existing_forward_history_fails_closed_on_missing_pointer(tmp_path):
    import pytest
    d,_=read_snapshot(BUNDLED_SNAPSHOT,True)
    now=(d.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,d,now)
    collect_forward(tmp_path,now)
    (tmp_path/'forward_models'/'latest.json').unlink()
    with pytest.raises(ValueError,match='forward history'):
        collect_forward(tmp_path,now)


def test_corrupt_latest_forward_version_cannot_fall_back_and_rewrite(tmp_path):
    import json
    import pytest
    d,_=read_snapshot(BUNDLED_SNAPSHOT,True)
    now=(d.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,d,now)
    collect_forward(tmp_path,now)
    collect_forward(tmp_path,(pd.Timestamp(now)+pd.Timedelta(hours=1)).isoformat())
    directory=tmp_path/'forward_ledger'
    version=json.loads((directory/'latest.json').read_text())['version_id']
    (directory/'versions'/(version+'.parquet')).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='forward history'):
        collect_forward(tmp_path,(pd.Timestamp(now)+pd.Timedelta(hours=2)).isoformat())


def test_older_market_snapshot_cannot_backfill_prediction_date(tmp_path):
    d,_=read_snapshot(BUNDLED_SNAPSHOT,True)
    now=(d.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,d,now)
    collect_forward(tmp_path,now)
    before=read_latest(tmp_path,'forward_ledger')[0]
    publish(tmp_path,d.iloc[:-1],now)
    collect_forward(tmp_path,now)
    pd.testing.assert_frame_equal(before,read_latest(tmp_path,'forward_ledger')[0])


def test_valid_pointer_rollback_and_global_feature_change_are_rejected(tmp_path,monkeypatch):
    import pytest
    import regime.readiness as readiness
    from regime.store import atomic_json
    d,_=read_snapshot(BUNDLED_SNAPSHOT,True)
    now=(d.date.max()+pd.Timedelta(days=1,hours=12)).isoformat()
    publish(tmp_path,d,now)
    collect_forward(tmp_path,now)
    _,first=read_latest(tmp_path,'forward_ledger')
    later=(pd.Timestamp(now)+pd.Timedelta(hours=1)).isoformat()
    collect_forward(tmp_path,later)
    atomic_json(tmp_path/'forward_ledger'/'latest.json',{'version_id':first['version_id']})
    with pytest.raises(ValueError,match='forward history'):
        collect_forward(tmp_path,later)
    other=tmp_path/'changed'
    publish(other,d,now)
    collect_forward(other,now)
    monkeypatch.setattr(readiness,'PRICE',readiness.PRICE[:-1])
    with pytest.raises(ValueError,match='feature definition'):
        collect_forward(other,later)
