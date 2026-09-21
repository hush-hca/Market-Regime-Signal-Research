import pandas as pd
import pytest
from regime.ingest import download, funding_daily, DAY
from regime.ingest import Client

def test_hosted_raw_snapshots_use_configured_temporary_directory(tmp_path,monkeypatch):
    monkeypatch.setenv('REGIME_RAW_DIR',str(tmp_path/'raw'))
    client=Client('bybit')
    assert client.raw==tmp_path/'raw'/'bybit'
    assert client.raw.is_dir()
    client.session.close()

class FakeClient:
    def __init__(self,venue):
        self.venue=venue
        self.calls={}
        self.end=int(pd.Timestamp.now(tz='UTC').normalize().timestamp()*1000)
        self.start=self.end-60*DAY

    def get(self,path,**params):
        self.calls[path]=self.calls.get(path,0)+1
        if 'klines' in path:
            return [[self.start+i*DAY,100,110,90,105,10,0,1000] for i in range(60)] if self.calls[path]==1 else []
        if 'fundingRate' in path:
            return [{'fundingTime':self.start+i*DAY,'fundingRate':'.001'} for i in range(60)] if self.calls[path]==1 else []
        if 'openInterestHist' in path:
            return [{'timestamp':self.end-DAY,'sumOpenInterestValue':'2000'}]
        if 'kline' in path:
            return {'result':{'list':[[str(self.start+i*DAY),'100','110','90','105','10','1000'] for i in reversed(range(60))]}}
        if 'funding/history' in path:
            rows=[{'fundingRateTimestamp':str(self.start+i*DAY),'fundingRate':'.001'} for i in reversed(range(60))]
            return {'result':{'list':rows}}
        if 'open-interest' in path:
            return {'result':{'list':[{'timestamp':str(self.end-DAY),'openInterest':'20'}],'nextPageCursor':''}}
        raise AssertionError(path)

@pytest.mark.parametrize('venue',['binance','bybit'])
def test_adapter_normalization_and_missing_oi(venue):
    d,meta=download(venue,60,client=FakeClient(venue))
    assert len(d)==60
    assert d.funding.eq(.001).all()
    assert d.volume.eq(1000).all()
    assert d.oi.iloc[-1]==2000
    assert d.oi.isna().sum()==59
    assert meta['synthetic'] is False

def test_funding_duplicates_do_not_double_count():
    rows=[{'fundingTime':1640995200000,'fundingRate':'.001'}]*2
    assert funding_daily(rows).iloc[0]==.001
