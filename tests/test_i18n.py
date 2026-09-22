from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from regime.i18n import translate, display_frame, error_text

def test_display_translation_preserves_source_and_numbers():
    source=pd.DataFrame({'regime':['Expansion'],'mean':[.12],'n':[10]})
    original=source.copy(deep=True)
    shown=display_frame(source,'ko')
    assert shown.loc[0,'국면']=='확장 국면'
    assert shown.loc[0,'평균 수익률']==.12
    assert shown.loc[0,'표본 수']==10
    pd.testing.assert_frame_equal(source,original)
    assert translate('Expansion','en')=='Expansion'
    assert '605' in error_text('At least 605 daily rows are required.','ko')
    assert error_text('Duplicate dates are not allowed.','ko')=='중복된 날짜는 허용되지 않습니다.'

def test_switching_languages_preserves_choices_and_results(market_snapshot):
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    app.selectbox(key='Forward horizon::en').select(14).run()
    app.number_input(key='One-way fees (bps)').set_value(12.).run()
    prices=[metric.value for metric in app.metric][1:]
    app.selectbox(key='language').select('ko').run()
    assert not app.exception
    assert app.title[0].value=='시장 국면을 이해하고, 근거를 확인하세요.'
    assert [tab.label for tab in app.tabs]==['시장 개요','과거 결과','전략 분석','옵션 손익','데이터 및 분석 방법']
    assert not any('가상 데이터 데모' in message.value for message in app.warning)
    assert app.selectbox(key='Forward horizon::ko').value==14
    assert app.number_input(key='One-way fees (bps)').value==12.
    assert [metric.value for metric in app.metric][1:]==prices
    assert app.selectbox(key='Data source::ko').value=='Exchange data'
    assert '가상 데이터 데모' not in app.selectbox(key='Data source::ko').options
    app.selectbox(key='language').select('en').run()
    assert not app.exception
    assert app.title[0].value=='Understand the regime. Inspect the evidence.'
    assert app.selectbox(key='Forward horizon::en').value==14
