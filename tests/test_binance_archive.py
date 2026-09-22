from io import BytesIO
import hashlib
import zipfile
import pandas as pd
import pytest
from regime.binance_archive import decode, normalize, download_archive


def test_checksum_and_normalization():
    stream=BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        z.writestr('prices.csv','open_time,open,high,low,close,volume,quote_volume\n0,10,12,9,11,2,22\n86400000,11,13,10,12,3,36\n')
    payload=stream.getvalue()
    with pytest.raises(ValueError,match='checksum'):
        decode(payload,'0'*64)
    prices=decode(payload,hashlib.sha256(payload).hexdigest())
    rates=pd.DataFrame({'calc_time':[0,28800000,57600000,86400000],
        'funding_interval_hours':[8]*4,'last_funding_rate':[.001]*4})
    metrics=pd.DataFrame({'create_time':['1970-01-01 01:00','1970-01-01 23:55'],
        'sum_open_interest_value':[100,200]})
    result=normalize(prices,rates,metrics)
    assert result.volume.tolist()==[22,36]
    assert result.funding.iloc[0]==pytest.approx(.003)
    assert pd.isna(result.funding.iloc[1])
    assert result.oi.iloc[0]==200 and pd.isna(result.oi.iloc[1])


def test_missing_month_uses_daily_prices_without_inventing_funding():
    def fetch(path):
        if '/daily/' in '/'+path and '/klines/' in path:
            stamp=path.split('BTCUSDT-1d-')[1].removesuffix('.zip')
            return pd.DataFrame({'open_time':[pd.Timestamp(stamp,tz='UTC').value//10**6],
                'open':[10],'high':[12],'low':[9],'close':[11],'quote_volume':[22]})
        return None
    frame,meta=download_archive(2,'2026-09-23T00:00Z',fetcher=fetch)
    assert len(frame)==2 and frame.funding.isna().all() and frame.oi.isna().all()
    assert frame.date.max()==pd.Timestamp('2026-09-22',tz='UTC')
    assert meta['checksum_verified'] and meta['source']=='binance'


def test_collector_uses_archive_only_for_same_venue(tmp_path,monkeypatch):
    import regime.collect as collector
    from regime.data import demo
    def offline(*args,**kwargs): raise ConnectionError('offline')
    monkeypatch.setattr(collector,'download',offline)
    monkeypatch.setattr(collector,'load_coinmetrics',offline)
    monkeypatch.setattr(collector,'load_quote_archive',offline)
    monkeypatch.setattr(collector,'download_archive',lambda *a,**k:(demo(730),{'source':'binance'}))
    report=collector.collect_once('2026-09-23T00:00Z',tmp_path)
    assert report['datasets']['market_binance']['status']=='ok'
    assert report['datasets']['market_bybit']['status']=='error'
