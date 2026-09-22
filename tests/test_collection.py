import json
from pathlib import Path
import pandas as pd
import pytest
from regime.data import demo


def metadata():
    return dict(dataset='market_bybit',source='bybit',synthetic=False,
                retrieved_at='2026-09-23T00:00:00Z',vintage='current')


def test_immutable_idempotent_and_corrupt_latest_recovery(tmp_path):
    from regime.store import write_snapshot, read_latest
    first=write_snapshot(demo(730),metadata(),tmp_path)
    assert write_snapshot(demo(730),metadata(),tmp_path)==first
    revised=demo(730); revised.loc[729,'funding']=.001
    second=write_snapshot(revised,{**metadata(),'retrieved_at':'2026-09-24T00:00:00Z'},tmp_path)
    assert second!=first
    m=json.loads(Path(second).read_text())
    Path(second).with_suffix('.parquet').write_bytes(b'corrupt')
    frame,meta=read_latest(tmp_path,'market_bybit')
    assert meta['recovered_from_corruption'] and len(frame)==730
    assert frame.funding.iloc[-1]==demo(730).funding.iloc[-1]


def test_reject_invalid_without_replacing_valid(tmp_path):
    from regime.store import write_snapshot,read_latest
    write_snapshot(demo(730),metadata(),tmp_path)
    broken=demo(730).drop(index=10)
    with pytest.raises(ValueError): write_snapshot(broken,metadata(),tmp_path)
    with pytest.raises(ValueError): write_snapshot(demo(730),{**metadata(),'dataset':'../escape'},tmp_path)
    with pytest.raises(ValueError): write_snapshot(demo(730),{**metadata(),'synthetic':True},tmp_path)
    assert len(read_latest(tmp_path,'market_bybit')[0])==730


def test_interrupted_publication_preserves_previous(tmp_path,monkeypatch):
    import regime.store as store
    first=store.write_snapshot(demo(730),metadata(),tmp_path)
    replace=store.os.replace
    def fail_pointer(source,destination):
        if Path(destination).name=='latest.json': raise OSError('disk full')
        return replace(source,destination)
    monkeypatch.setattr(store.os,'replace',fail_pointer)
    with pytest.raises(OSError):
        store.write_snapshot(demo(731),metadata(),tmp_path)
    assert len(store.read_latest(tmp_path,'market_bybit')[0])==730


def test_collection_partial_failure_keeps_last_good(tmp_path,monkeypatch):
    import regime.collect as collect
    from regime.store import read_latest
    market=demo(730)
    monkeypatch.setattr(collect,'download',lambda venue,days,**kwargs:(market,{'source':venue,'synthetic':False}))
    def offline(*args,**kwargs): raise ConnectionError('offline')
    monkeypatch.setattr(collect,'load_coinmetrics',offline)
    monkeypatch.setattr(collect,'load_quote_archive',offline)
    report=collect.collect_once('2026-09-23T00:00:00Z',str(tmp_path))
    assert report['datasets']['market_bybit']['status']=='ok'
    assert report['datasets']['onchain']['status']=='error'
    monkeypatch.setattr(collect,'download',offline)
    collect.collect_once('2026-09-24T00:00:00Z',str(tmp_path))
    assert len(read_latest(tmp_path,'market_bybit')[0])==730


def test_merge_preserves_known_funding_and_excludes_open_day():
    from regime.collect import merge_market
    old=demo(730); update=old.tail(60).copy()
    update.loc[update.index[-1],'funding']=float('nan')
    result=merge_market(old,update,old.date.max()+pd.Timedelta(days=1))
    assert result.funding.iloc[-1]==old.funding.iloc[-1]
    result=merge_market(old,update,old.date.max())
    assert len(result)==729


def test_missing_settlements_are_reported_without_losing_quotes(tmp_path,monkeypatch):
    import regime.collect as collect
    from regime.store import read_latest
    def offline(*args,**kwargs): raise ConnectionError('offline')
    monkeypatch.setattr(collect,'download',offline)
    monkeypatch.setattr(collect,'load_coinmetrics',offline)
    quotes=pd.DataFrame({'instrument':['BTC-call'],'observed_at':[pd.Timestamp('2026-09-22',tz='UTC')]})
    missing=pd.DataFrame(); missing.attrs['error']='settlement service offline'
    monkeypatch.setattr(collect,'load_quote_archive',lambda:{'option_quotes':quotes,'option_settlements':missing})
    report=collect.collect_once('2026-09-23T00:00:00Z',str(tmp_path))
    assert report['datasets']['option_quotes']['status']=='ok'
    assert report['datasets']['option_settlements']['status']=='error'
    assert len(read_latest(tmp_path,'option_quotes')[0])==1
