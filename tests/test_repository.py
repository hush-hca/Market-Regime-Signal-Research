import hashlib
import io
import pandas as pd
import pytest
from regime.data import demo


def test_repository_checks_hash_before_decoding():
    from regime.repository import read_repository_snapshot
    buffer=io.BytesIO(); demo(730).to_parquet(buffer,index=False)
    payload=buffer.getvalue(); version='a'*64
    class Response:
        content=payload
        def __init__(self,value): self.value=value
        def raise_for_status(self): pass
        def json(self): return self.value
    class Client:
        corrupt=False
        def get(self,url,**kwargs):
            if url.endswith('latest.json'): return Response({'version_id':version})
            if url.endswith('.json'): return Response(dict(version_id=version,dataset='market_bybit',source='bybit',
                synthetic=False,rows=730,sha256='bad' if self.corrupt else hashlib.sha256(payload).hexdigest()))
            return Response(None)
    client=Client()
    frame,meta=read_repository_snapshot('market_bybit',client=client)
    assert len(frame)==730 and meta['version_id']==version
    client.corrupt=True
    with pytest.raises(ValueError,match='checksum'): read_repository_snapshot('market_bybit',client=client)


def test_feed_prefers_recent_configured_store(tmp_path,monkeypatch):
    from regime.store import write_snapshot
    import regime.feed as feed
    frame=demo(730)
    frame.date=pd.date_range(end=pd.Timestamp.now(tz='UTC').normalize()-pd.Timedelta(days=1),periods=730)
    write_snapshot(frame,dict(dataset='market_bybit',source='bybit',synthetic=False,
        retrieved_at=pd.Timestamp.now(tz='UTC').isoformat()),tmp_path)
    monkeypatch.setenv('REGIME_SNAPSHOT_ROOT',str(tmp_path))
    def unexpected(*args): raise AssertionError('fresh durable store should precede live exchange')
    monkeypatch.setattr(feed,'download',unexpected)
    data,meta,notice=feed.load_market()
    assert len(data)==730 and 'version_id' in meta and notice is None


def test_onchain_uses_collected_snapshot_before_live_api(tmp_path,monkeypatch):
    import regime.onchain as onchain
    from regime.store import write_snapshot
    now=pd.Timestamp.now(tz='UTC')
    chain=onchain.normalize([{'time':str((now.normalize()-pd.Timedelta(days=2)).date()),'CapMVRVCur':'2'}])
    write_snapshot(chain,dict(dataset='onchain',source='Coin Metrics Community API',synthetic=False,
        retrieved_at=now.isoformat(),observation_end=chain.observation_time.max().isoformat()),tmp_path)
    monkeypatch.setenv('REGIME_SNAPSHOT_ROOT',str(tmp_path))
    def unexpected(*args,**kwargs): raise AssertionError('must use stored on-chain snapshot')
    monkeypatch.setattr(onchain,'load_coinmetrics',unexpected)
    frame,meta=onchain.load_onchain(now-pd.Timedelta(days=10),now)
    assert len(frame)==1 and meta['delivery']=='Collected snapshot'
