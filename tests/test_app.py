from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_demo_and_controls_render():
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    assert not app.exception
    assert len(app.tabs)==5
    assert any('SYNTHETIC' in w.value for w in app.warning)
    next(s for s in app.selectbox if s.label=='Forward horizon').select(7).run()
    assert not app.exception
    app.checkbox[0].check().run()
    assert not app.exception
    next(s for s in app.selectbox if s.label=='Evaluation segment').select('Walk-forward').run()
    next(s for s in app.selectbox if s.label=='Accounting').select('Perpetual with daily funding').run()
    assert not app.exception
