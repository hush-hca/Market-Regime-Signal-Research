import json
from pathlib import Path
import pandas as pd
import pytest
from regime.onchain import normalize, load_coinmetrics, BUNDLE
from regime.options import normalize_quotes, select_call, inverse_call_payoff

def test_lag_and_missing_flow_leg():
    frame=normalize([dict(time='2025-01-01',CapMVRVCur='2',FlowInExUSD='5',FlowOutExUSD=None)])
    assert frame.available_at.iloc[0]==pd.Timestamp('2025-01-03',tz='UTC')
    assert pd.isna(frame.exchange_netflow.iloc[0])
    with pytest.raises(ValueError): normalize([dict(time='2025-01-01',CapMVRVCur='-1')])

class Offline:
    def get(self,*args,**kwargs): raise ConnectionError('offline')

def test_real_bundle_and_integrity(tmp_path):
    frame,meta=load_coinmetrics('2024-09-18','2026-09-21',client=Offline())
    assert len(frame)>700 and meta['fallback_used']
    assert 'sopr' not in frame and frame.mvrv.notna().all()
    assert meta['retrieved_at']
    broken=tmp_path/'broken.parquet'
    broken.write_bytes(b'bad')
    broken.with_suffix('.json').write_text(BUNDLE.with_suffix('.json').read_text())
    with pytest.raises(ValueError,match='integrity'):
        load_coinmetrics('2025-01-01','2025-02-01',client=Offline(),bundle=broken)

def test_option_units_and_selection():
    instrument=dict(instrument_name='BTC-test',option_type='call',is_active=True,
        settlement_currency='BTC',quote_currency='BTC',base_currency='BTC',contract_size=1,
        expiration_timestamp=pd.Timestamp('2025-01-31',tz='UTC').value//10**6,strike=110)
    quotes=normalize_quotes([instrument],[dict(instrument_name='BTC-test',bid_price=.03,ask_price=.04)],100,'2025-01-01')
    selected=select_call(quotes)
    assert selected.bid_usd==3 and selected.days_to_expiry==30
    payoff=inverse_call_payoff(100,110,.03)
    assert payoff.iloc[-1].covered_call_return==pytest.approx(.16)
    assert payoff.iloc[0].covered_call_return==-1
    assert normalize_quotes([instrument],[dict(instrument_name='BTC-test',bid_price=None,ask_price=.04)],100,'2025-01-01').empty

def test_exchange_fallback_does_not_mix_venues(monkeypatch):
    import regime.feed
    from regime.data import demo
    calls=[]
    def fetch(venue,days):
        calls.append(venue)
        if venue=='bybit': raise ConnectionError('blocked')
        return demo(),{'source':'binance','synthetic':False}
    monkeypatch.setattr(regime.feed,'download',fetch)
    frame,meta,notice=regime.feed.load_market()
    assert calls==['bybit','binance'] and meta['source']=='binance' and notice is None

def test_pagination_and_causal_join():
    from regime.data import demo, enrich
    class Response:
        def __init__(self,data): self.data=data
        def raise_for_status(self): pass
        def json(self): return self.data
    class Client:
        def __init__(self): self.calls=0
        def get(self,url,**kwargs):
            self.calls+=1
            if self.calls==1:
                return Response({'data':[{'time':'2025-01-01','CapMVRVCur':'2'}],
                    'next_page_url':'https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?next_page_token=a'})
            return Response({'data':[{'time':'2025-01-02','CapMVRVCur':'3'}]})
    client=Client()
    frame,meta=load_coinmetrics('2025-01-01','2025-01-03',client=client)
    assert client.calls==2 and not meta['fallback_used']
    market=demo(730)
    market['date']=pd.date_range('2025-01-01',periods=len(market),tz='UTC')
    joined=enrich(market,frame.to_csv(index=False))
    assert pd.isna(joined.mvrv.iloc[0])
    assert joined.mvrv.iloc[1]==2 and joined.mvrv.iloc[2]==3

def test_dashboard_with_real_onchain_bundle(tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    import streamlit as st
    import regime.onchain
    import regime.feed
    monkeypatch.chdir(tmp_path)
    def offline(*args): raise ConnectionError('offline')
    monkeypatch.setattr(regime.feed,'download',offline)
    monkeypatch.setattr(regime.onchain,'load_coinmetrics',
        lambda start,end:load_coinmetrics(start,end,client=Offline()))
    st.cache_data.clear()
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    assert not app.exception and len(app.metric)==6
    app.checkbox(key='Include uploaded on-chain features').check().run()
    assert not app.exception and len(app.tabs)==5 and not app.error


def test_settlement_outage_preserves_quote_archive(monkeypatch):
    import regime.options as options
    now=pd.Timestamp.now(tz='UTC')
    def response(client,url,**kwargs):
        if url.endswith('get_instruments'):
            return {'result':[dict(instrument_name='BTC-call',option_type='call',is_active=True,
                settlement_currency='BTC',quote_currency='BTC',base_currency='BTC',contract_size=1,
                expiration_timestamp=(now+pd.Timedelta(days=30)).value//10**6,strike=110)]}
        if url.endswith('get_book_summary_by_currency'):
            return {'result':[dict(instrument_name='BTC-call',bid_price=.03,ask_price=.04,creation_timestamp=now.value//10**6)]}
        if url.endswith('get_index_price'): return {'result':{'index_price':100}}
        raise ConnectionError('settlement endpoint offline')
    monkeypatch.setattr(options,'get_json',response)
    archive=options.load_quote_archive()
    assert len(archive['option_quotes'])==1
    assert archive['option_settlements'].empty and archive['option_settlements'].attrs['error']
