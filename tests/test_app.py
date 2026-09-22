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
    app.selectbox(key='Model::en').select('Price + derivatives').run()
    assert not app.exception
    next(s for s in app.selectbox if s.label=='Evaluation segment').select('Walk-forward').run()
    assert not any('Assumed' in s.label for s in app.slider)
    assert any('No verified forward ledger' in s.value for s in app.info)
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


def test_feature_comparison_and_hypothesis_controls(market_snapshot):
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    app.checkbox(key='compare_feature_sets').check().run()
    assert not app.exception and not app.error
    assert any('Exploratory evaluation' in warning.value for warning in app.warning)
    app.selectbox(key='Grouping::en').select('On-chain hypothesis').run()
    assert not app.exception
    assert any('No complete events' in info.value for info in app.info)
    app.selectbox(key='language').select('ko').run()
    assert not app.exception
    assert app.checkbox(key='compare_feature_sets').label=='동일 날짜에서 특성 조합 비교'


def test_actual_only_models_and_missing_inputs(market_snapshot,monkeypatch):
    import regime.feed
    from regime.feed import read_snapshot,BUNDLED_SNAPSHOT
    d,meta=read_snapshot(BUNDLED_SNAPSHOT,True)
    d.loc[d.index[-10:],'funding']=float('nan')
    monkeypatch.setattr(regime.feed,'download',lambda *a:(d,meta))
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    assert not app.exception
    assert app.selectbox(key='Model::en').value=='Price only'
    assert app.metric[0].value!='Unclassified'
    assert 'Upload CSV' not in app.selectbox(key='Data source::en').options
    assert not app.slider and not app.number_input
    app.selectbox(key='Model::en').select('Price + derivatives').run()
    assert not app.exception and app.metric[0].value=='Unclassified'
    app.selectbox(key='Model::en').select('Price + derivatives + on-chain').run()
    assert not app.exception
    assert any('Selected model is unavailable' in warning.value for warning in app.warning)
