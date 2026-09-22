"""Offline UI fixtures are explicitly synthetic; production has no demo mode."""
import json
import pytest
from regime.data import demo
import regime.feed

@pytest.fixture
def market_snapshot(tmp_path,monkeypatch):
    directory=tmp_path/'data'
    directory.mkdir()
    demo().to_parquet(directory/'market.parquet',index=False)
    (directory/'market.json').write_text(json.dumps({
        'source':'test-fixture','synthetic':True,'price_instrument':'test-only generated data'
    }),encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    # Simulated transport only: no network calls or market claims in unit tests.
    monkeypatch.setattr(regime.feed,'download',lambda *args:(demo(),{
        'source':'bybit','synthetic':False,'price_instrument':'test-only mocked exchange response'
    }))
    import streamlit as st
    st.cache_data.clear()
