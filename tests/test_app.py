from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_snapshot_and_controls_render(market_snapshot):
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    assert not app.exception
    assert app.selectbox(key='Data source::en').value=='Exchange data'
    assert 'Synthetic demo' not in app.selectbox(key='Data source::en').options
    assert len(app.tabs)==5
    assert not any('SYNTHETIC' in w.value for w in app.warning)
    next(s for s in app.selectbox if s.label=='Forward horizon').select(7).run()
    assert not app.exception
    app.checkbox[0].check().run()
    assert not app.exception
    next(s for s in app.selectbox if s.label=='Evaluation segment').select('Walk-forward').run()
    next(s for s in app.selectbox if s.label=='Accounting').select('Perpetual with daily funding').run()
    assert not app.exception

def test_missing_local_snapshot_uses_bundled_real_data(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    import regime.feed
    import streamlit as st
    st.cache_data.clear()
    def offline(*args): raise ConnectionError('offline test')
    monkeypatch.setattr(regime.feed,'download',offline)
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    assert not app.exception
    assert len(app.metric)==4
    assert not any('SYNTHETIC DEMO' in warning.value for warning in app.warning)
    assert any('Refresh failed' in message.value for message in app.warning)
    assert any('2026-09-17' in message.value for message in app.info)
