"""UI tests use checksum-verified actual exchange observations, with offline transport."""
import json
import pytest
from regime.feed import read_snapshot,BUNDLED_SNAPSHOT
import regime.feed

@pytest.fixture
def market_snapshot(tmp_path,monkeypatch):
    directory=tmp_path/'data'
    directory.mkdir()
    real,meta=read_snapshot(BUNDLED_SNAPSHOT,True)
    real.to_parquet(directory/'market.parquet',index=False)
    (directory/'market.json').write_text(json.dumps(meta),encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    # Simulated transport only: no network calls or market claims in unit tests.
    monkeypatch.setattr(regime.feed,'download',lambda *args:(real.copy(),meta.copy()))
    import streamlit as st
    st.cache_data.clear()

@pytest.fixture(autouse=True)
def offline_onchain(monkeypatch):
    import regime.onchain
    def unavailable(*args,**kwargs):
        raise ConnectionError('isolated UI test; on-chain adapter tested separately')
    monkeypatch.setattr(regime.onchain,'load_coinmetrics',unavailable)
    monkeypatch.setattr(regime.feed,'read_repository_snapshot',unavailable)
    monkeypatch.setattr(regime.onchain,'read_repository_snapshot',unavailable)
    import regime.panels
    monkeypatch.setattr(regime.panels,'read_forward',unavailable)
    monkeypatch.setattr(regime.panels,'read_collection_status',unavailable)
