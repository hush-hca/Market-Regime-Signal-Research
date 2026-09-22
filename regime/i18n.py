"""Presentation-only translations. Research identifiers and export schemas stay stable."""
import re

KO = {
    'Exchange data': '실제 거래소 데이터',
    'Refresh exchange data': '거래소 데이터 새로고침',
    'Bybit BTCUSDT · completed daily bars · cached for up to one hour.': 'Bybit BTCUSDT · 마감된 일봉 · 최대 1시간 캐시',
    'Refresh failed. Showing the saved real exchange snapshot; check its date.': '최신 조회에 실패하여 저장된 실제 거래소 데이터를 표시합니다. 기준일을 확인하세요.',
    'Exchange data unavailable and no verified real snapshot exists.': '거래소 데이터를 가져올 수 없고 확인된 실제 저장 데이터도 없습니다. 공개 API 조회를 다시 시도하거나 CSV를 업로드하세요.',
    'Fallback snapshot is not verified exchange data.': '대체 파일이 출처가 확인된 실제 거래소 데이터가 아닙니다.',
    'Load a real market snapshot, upload your dataset, or fetch a public API in the sidebar.': '실제 시장 데이터를 저장해 불러오거나, 사이드바에서 CSV 업로드 또는 공개 API 수집을 선택하세요.',
    'BTC / DAILY RESEARCH WORKSPACE': 'BTC / 일별 시장 분석',
    'Data source': '데이터 출처', 'Synthetic demo': '가상 데이터 데모',
    'Local snapshot': '저장된 데이터', 'Upload CSV': 'CSV 업로드', 'Fetch public API': '공개 API에서 가져오기',
    'Daily market CSV': '일별 시장 데이터 CSV', 'Venue': '거래소',
    'History requested (days)': '수집 기간(일)', 'Fetch & validate': '가져오기 및 검증',
    'Fetching price, funding and available OI…': '가격·펀딩비·수집 가능한 미결제약정을 가져오는 중…',
    'Optional on-chain CSV': '온체인 CSV(선택)',
    'Requires available_at and mvrv, sopr or exchange_netflow. Only use data you are licensed to process.': 'available_at과 mvrv, sopr, exchange_netflow 중 하나 이상이 필요합니다. 이용 권한이 있는 데이터만 사용하세요.',
    'Create a snapshot with the ingestion command in the README.': 'README의 수집 명령으로 데이터를 먼저 저장하세요.',
    'Include OI features': '미결제약정(OI) 지표 포함',
    'Requires at least 180 complete training rows. Recent-only Binance OI is insufficient.': '결측치 없는 학습 데이터가 최소 180일 필요합니다. 최근 구간만 제공되는 Binance OI로는 부족합니다.',
    'Include uploaded on-chain features': '업로드한 온체인 지표 포함',
    'Presentation focus': '설명 대상', 'Research team': '리서치팀', 'Exchange': '거래소', 'Options team': '옵션팀',
    'Fixed model: four clusters · 365-day warm-up · 90-day refits · final 180-day frozen holdout.': '고정 설정: 군집 4개 · 초기 학습 365일 · 90일마다 재학습 · 마지막 180일은 모델을 고정해 평가',
    'MARKET INTELLIGENCE / RESEARCH MVP': '시장 국면 분석 / 리서치 MVP',
    'Understand the regime. Inspect the evidence.': '시장 국면을 이해하고, 근거를 확인하세요.',
    'Price, positioning and on-chain context — with transparent historical outcomes.': '가격·포지셔닝·온체인 지표로 시장을 살펴보고 과거 결과를 확인합니다.',
    'Select synthetic demo, upload a validated dataset, or fetch a public API in the sidebar.': '사이드바에서 데모를 선택하거나 CSV를 업로드하거나 공개 API 데이터를 가져오세요.',
    'SYNTHETIC DEMO — generated prices and indicators. All results demonstrate software behavior; they are not market evidence.': '가상 데이터 데모 — 인위적으로 생성한 가격과 지표입니다. 결과는 기능 시연용이며 실제 시장의 투자 근거가 아닙니다.',
    'Historical snapshot: the last observation is more than two days old. Latest regime below is not a live signal.': '마지막 데이터가 2일 이상 지난 과거 자료입니다. 아래 국면은 실시간 신호가 아닙니다.',
    'Upload on-chain data before enabling its features.': '온체인 지표를 활성화하기 전에 데이터를 업로드하세요.',
    'Computing causal features and walk-forward regimes…': '미래 정보를 제외한 지표와 순차 검증 국면을 계산하는 중…',
    'Latest historical regime': '마지막 관측일의 국면', 'Last close': '마지막 종가',
    '30-day momentum': '30일 모멘텀', 'Last daily funding': '마지막 일별 펀딩비', 'Missing': '결측',
    'Overview': '시장 개요', 'Historical outcomes': '과거 결과', 'Strategy lab': '전략 분석',
    'Options payoff': '옵션 손익', 'Data & methodology': '데이터 및 분석 방법',
    'Defensive': '방어 국면', 'Soft / mixed': '약세·혼조', 'Firm / mixed': '강세·혼조',
    'Expansion': '확장 국면', 'Unclassified': '미분류',
    'Positive trend / positive funding': '상승 추세 / 양의 펀딩비',
    'Negative trend / negative funding': '하락 추세 / 음의 펀딩비',
    'Positive trend / negative funding': '상승 추세 / 음의 펀딩비',
    'Mixed trend / funding': '추세·펀딩비 혼조',
    'BTC price': 'BTC 가격', 'Price · USD / USDT proxy': '가격 · USD / USDT 대용치',
    'What defines the latest model?': '최신 모델은 어떤 특성을 구분하나요?',
    'Training-period cluster centroids. Names rank 30-day momentum within each fit; identities can change between fits.': '학습 구간의 군집별 중심값입니다. 이름은 학습 시점의 30일 모멘텀 순위에 따라 부여하므로 재학습 시 의미가 달라질 수 있습니다.',
    'Read the signals': '지표 읽는 법', 'Funding': '펀딩비', 'Open interest': '미결제약정(OI)',
    'MVRV & SOPR': 'MVRV와 SOPR', 'Exchange net flows': '거래소 순유입',
    'The daily sum of realized funding fractions. Positive funding usually means longs paid shorts. Negative funding alone does not prove a reversal or capital inflow.': '실제로 발생한 펀딩비율의 일별 합계입니다. 양수이면 보통 롱이 숏에 비용을 지급합니다. 음의 펀딩비만으로 추세 반전이나 자금 유입을 입증할 수는 없습니다.',
    'Outstanding derivative exposure. USD OI moves with both position size and price. Rising OI does not identify which side will win.': '아직 청산되지 않은 파생상품 포지션 규모입니다. 달러 기준 OI는 수량과 가격 모두에 영향을 받습니다. OI 증가만으로 상승·하락 방향을 알 수는 없습니다.',
    'MVRV compares market value with realized value; SOPR describes spent-output profitability. Provider definitions and publication times matter.': 'MVRV는 시장가치를 실현가치와 비교하고, SOPR는 이동한 코인의 손익 비율을 나타냅니다. 제공 업체의 지표 정의와 실제 공개 시점을 확인해야 합니다.',
    'Deposits minus withdrawals for labeled exchange addresses. Transfers are not equivalent to executed selling or buying.': '거래소로 분류된 주소의 입금에서 출금을 뺀 값입니다. 코인 이동이 실제 매수·매도 체결을 뜻하는 것은 아닙니다.',
    'Persistence & transitions': '국면 유지 및 전환',
    'Descriptive transition frequencies across all classified dates, including refit boundaries; not a forecast.': '재학습 경계를 포함한 전체 분류일의 과거 전환 빈도입니다. 미래 예측 확률이 아닙니다.',
    'What happened after similar observations?': '비슷한 상황 이후 어떤 결과가 나타났나요?',
    'Forward horizon': '이후 관찰 기간(일)', 'Evaluation segment': '평가 구간',
    'Final holdout': '최종 별도 평가', 'Walk-forward': '순차 검증', 'Warm-up': '초기 학습',
    'Grouping': '분류 기준', 'ML clusters': '머신러닝 군집', 'Indicator rules': '지표 규칙',
    'Signal at daily close → next daily open entry → open exit after the selected calendar-day horizon. Globally non-overlapping windows; raw asset returns before costs.': '일봉 마감 후 신호 생성 → 다음 날 시가 진입 → 선택한 기간 후 시가 청산. 관찰 구간은 서로 겹치지 않으며 비용 차감 전 자산 수익률입니다.',
    'No complete events in this segment.': '이 구간에는 관찰 기간이 완료된 표본이 없습니다.',
    'Forward return': '이후 수익률',
    'Small samples are expected: 180 days contain at most about six non-overlapping 30-day windows. Intervals are suppressed below five samples and remain approximate above that threshold.': '180일에서 겹치지 않는 30일 관찰 구간은 최대 약 6개뿐입니다. 표본이 5개 미만이면 신뢰구간을 표시하지 않으며, 그 이상이어도 근사치입니다.',
    'Intervals use a moving-block bootstrap. “All sampled dates” uses the same eligible dates. These sampled windows are not independent market episodes. Repeated holdout inspection makes subsequent model choices exploratory.': '신뢰구간은 이동 블록 부트스트랩으로 계산합니다. 전체 표본 기준값도 동일한 관찰일을 사용합니다. 표본이 독립적인 시장 사건을 의미하지는 않습니다. 최종 평가 결과를 보고 모델을 바꾸면 이후 결과는 탐색적 분석입니다.',
    'Download event ledger': '관찰 표본 내려받기',
    'A predefined rule, an explicit ledger': '사전에 정한 규칙과 투명한 거래 내역',
    'Long when the prior completed day has positive 30-day momentum and an available model classification; otherwise cash. Full allocation, no leverage. The strategy uses indicator rules, not a hindsight selection of profitable clusters.': '전일 30일 모멘텀이 양수이고 모델 분류가 가능하면 전액 매수하고, 아니면 현금을 보유합니다. 레버리지는 없습니다. 수익이 좋았던 군집을 사후 선택하지 않고 사전 지표 규칙을 사용합니다.',
    'One-way fees (bps)': '편도 수수료(bps)', 'One-way slippage (bps)': '편도 슬리피지(bps)',
    'Accounting': '손익 계산 방식', 'Spot-like price proxy': '현물 유사 가격 대용치',
    'Perpetual with daily funding': '일별 펀딩비 반영 무기한 선물',
    'Public adapters use perpetual candles. Spot-like mode is a price-only proxy, not an executable spot backtest. Perpetual funding uses daily summed rates on opening notional; intraday mark-notional changes are approximated.': '공개 API는 무기한 선물 가격을 사용합니다. 현물 유사 모드는 가격 대용치이며 실제 현물 체결 백테스트가 아닙니다. 선물 펀딩비는 시작 명목금액에 일별 합산 비율을 적용하므로 장중 금액 변화는 근사 처리합니다.',
    'Growth of 1 unit': '초기 자산 1의 누적 가치', 'Strategy': '전략',
    'Download trading ledger': '거래 내역 내려받기',
    'Covered-call payoff explorer': '커버드콜 만기 손익 분석',
    'SCENARIO SIMULATION — premiums are assumptions. This is not a historical options backtest, a quoted product, or a regime-specific return estimate.': '시나리오 시뮬레이션 — 옵션 프리미엄은 가정값입니다. 실제 과거 옵션 백테스트, 상품 호가 또는 국면별 수익률 추정치가 아닙니다.',
    'Strike (% of entry spot)': '행사가(진입 현물가 대비 %)',
    'Assumed premium (% of entry spot)': '가정 프리미엄(진입 현물가 대비 %)',
    'Total assumed costs (% of entry spot)': '가정 총비용(진입 현물가 대비 %)',
    'Terminal spot (entry = 100)': '만기 현물가(진입가 = 100)',
    'Return on initial spot capital': '초기 현물 투자금 대비 수익률',
    'One unit of owned spot + one same-unit short call, held to expiry. Linear USD cash settlement; no interim mark-to-market or collateral mechanics. Regime-to-options mappings remain hypotheses until quote history is available.': '현물 1단위 보유와 동일 수량 콜옵션 매도를 만기까지 유지합니다. 선형 USD 현금결제를 가정하며 중간 평가손익과 담보 구조는 반영하지 않습니다. 과거 호가를 확보하기 전까지 국면별 옵션 전략의 효과는 가설입니다.',
    'Data quality & reproducibility': '데이터 품질 및 재현성',
    'Lead with sample sizes, out-of-sample distributions, data lineage and negative findings.': '표본 수, 학습 외 구간의 결과 분포, 데이터 출처 및 효과가 없었던 결과를 중심으로 설명합니다.',
    'Lead with derivatives coverage, funding conventions, data freshness and indicator education.': '파생상품 데이터 범위, 펀딩비 관행, 데이터 최신성 및 지표 해설을 중심으로 설명합니다.',
    'Lead with payoff assumptions, capped upside, full downside exposure and the missing historical quote requirement.': '손익 가정, 제한된 상승 수익, 하락 위험 및 과거 옵션 호가 확보 필요성을 중심으로 설명합니다.',
    'Export reproducible research results': '재현 가능한 분석 결과 내려받기', 'Model fit manifest': '모델 학습 기록',
    'regime': '국면', 'date': '날짜', 'momentum_7': '7일 모멘텀', 'momentum_30': '30일 모멘텀',
    'volatility_30': '30일 연환산 변동성', 'funding_7': '7일 평균 펀딩비', 'volume_z': '거래량 Z점수',
    'oi_change_7': '7일 OI 변화율', 'mvrv': 'MVRV', 'sopr': 'SOPR', 'exchange_netflow': '거래소 순유입',
    'n': '표본 수', 'positive_frequency': '상승 빈도', 'mean': '평균 수익률', 'median': '중앙 수익률',
    'p05': '하위 5% 수익률', 'p95': '상위 95% 수익률', 'mean_ci_low': '평균 신뢰구간 하한',
    'mean_ci_high': '평균 신뢰구간 상한', 'positive_ci_low': '상승 빈도 신뢰구간 하한',
    'positive_ci_high': '상승 빈도 신뢰구간 상한', 'mean_adverse': '평균 최대 역행폭',
    'difference_from_all': '전체 표본 대비 평균 차이', 'evidence': '근거 수준',
    'All sampled dates': '전체 관찰 표본', 'Limited sample': '표본 부족', 'Descriptive evidence': '기술통계 수준',
    'strategy': '전략', 'Regime long / cash': '규칙 기반 매수·현금', 'Buy and hold': '매수 후 보유',
    'total_return': '누적 수익률', 'max_drawdown': '최대 낙폭', 'annualized_volatility': '연환산 변동성',
    'days': '일수', 'exposure': '평균 투자 비중', 'equity': '전략 자산 가치', 'benchmark': '매수 후 보유',
    'spot_return': '현물 수익률', 'covered_call_return': '커버드콜 수익률',
    'variable': '항목', 'value': '값',
    'field': '항목', 'missing_pct': '결측 비율(%)', 'funding': '펀딩비', 'oi': '미결제약정',
    'synthetic': '가상 데이터', 'local': '저장 데이터', 'uploaded': '업로드 데이터',
    'synthetic price path': '가상 가격 경로', 'user-supplied, unverified': '사용자 제공·출처 미검증',
    'USDT perpetual': 'USDT 무기한 선물',
    'Data could not be loaded: {error}': '데이터를 불러오지 못했습니다: {error}',
    'Dataset: {source} · {instrument} · as of {date} UTC. Historical API data may contain later revisions.': '데이터: {source} · {instrument} · 기준일 {date} UTC. 과거 API 데이터에는 이후 수정된 값이 포함될 수 있습니다.',
    '{count} daily observations · {start} → {end} · Source: {source}': '일별 관측 {count}개 · {start} → {end} · 출처: {source}',
    'Evaluation: {partition}. Includes entry, position changes and final liquidation costs. Cash earns zero; no taxes, borrow costs or liquidation model.': '평가 구간: {partition}. 진입·포지션 변경·최종 청산 비용을 포함합니다. 현금 이자는 0이며 세금·차입 비용·강제청산 모형은 없습니다.',
    'Maximum covered-call return: {maximum}. Loss if the underlying goes to zero: {loss}. Premium cushions losses and caps gains; it does not remove downside risk.': '커버드콜 최대 수익률: {maximum}. 기초자산이 0이 되면 수익률: {loss}. 프리미엄은 손실을 일부 완화하지만 수익을 제한하며 하락 위험을 없애지 못합니다.',
    'Technical details': '기술 상세',
    'Unable to process this data. Check the format, connection and source availability.': '데이터를 처리하지 못했습니다. 형식, 연결 상태 및 제공처의 이용 가능 여부를 확인하세요.',
    'Duplicate dates are not allowed.': '중복된 날짜는 허용되지 않습니다.',
    'Dates must be UTC daily boundaries.': '날짜는 UTC 자정 기준이어야 합니다.',
    'OHLCV values cannot be missing.': '시가·고가·저가·종가·거래량은 누락될 수 없습니다.',
    'Prices must be positive; volume must be nonnegative.': '가격은 양수, 거래량은 0 이상이어야 합니다.',
    'Invalid OHLC bounds.': '시가·고가·저가·종가의 범위가 올바르지 않습니다.',
    'OI must be nonnegative.': '미결제약정은 0 이상이어야 합니다.',
    'Daily price rows must be contiguous; repair missing dates before research.': '일별 가격 데이터가 연속적이어야 합니다. 누락된 날짜를 먼저 보완하세요.',
    'On-chain CSV needs available_at and at least one of mvrv, sopr, exchange_netflow.': '온체인 CSV에는 available_at과 mvrv, sopr, exchange_netflow 중 하나 이상이 필요합니다.',
    'available_at must be unique and present.': 'available_at은 누락되거나 중복될 수 없습니다.',
    'On-chain values must be finite or missing.': '온체인 값은 유한한 숫자 또는 결측값이어야 합니다.',
    'Insufficient complete training features. Disable OI/on-chain or provide more history.': '결측치 없는 학습 지표가 부족합니다. OI·온체인 지표를 끄거나 더 긴 과거 데이터를 제공하세요.',
    'Perpetual P&L requires complete realized funding for the evaluation period.': '선물 손익을 계산하려면 평가 구간 전체의 실제 펀딩비 데이터가 필요합니다.',
    'No market candles returned.': '거래소에서 가격 데이터를 반환하지 않았습니다.',
}

METHODOLOGY_KO = '''**검증 원칙**

- UTC 일봉을 사용하며 중복·날짜 누락·비정상 가격을 거부합니다.
- 미래 값으로 과거 결측치를 채우지 않습니다. 지표가 없으면 해당 날짜는 미분류입니다.
- 표준화와 군집 학습에는 과거의 완전한 관측값만 사용합니다.
- 마지막 180일 평가 구간에서는 재학습을 중단하고 모델을 고정합니다.
- 군집 학습에 미래 수익률 정답을 쓰지 않습니다. 관찰 구간은 평가 경계를 넘지 않습니다.
- 온체인 데이터는 `available_at` 기준으로 결합하며 2일이 지나면 오래된 값으로 처리합니다. 업로더는 실제 과거 공개 시각을 제공해야 합니다.
- 군집명은 학습 시점의 상대적 모멘텀을 설명합니다. 군집까지의 거리는 확률이 아닙니다.
- 자동 최적화는 없습니다. 최종 평가 결과를 본 후 지표를 바꾸면 독립적인 검증으로 해석할 수 없습니다.
'''

def translate(text, language='en'):
    if language != 'ko' or not isinstance(text,str):
        return text
    if text.startswith('**Validation contract**'):
        return METHODOLOGY_KO
    return KO.get(text,text)

def error_text(error, language='en'):
    text=str(error)
    if language=='ko' and text.startswith('Exchange data unavailable and no verified real snapshot exists. Redeploy'):
        return '거래소 연결과 실제 스냅샷 로딩에 실패했습니다. bootstrap/bybit.parquet 및 bootstrap/bybit.json이 포함된 최신 저장소를 다시 배포하세요. 기술 세부 정보에서 누락 경로 또는 검증 오류를 확인할 수 있습니다.'
    translated=translate(text,language)
    if translated!=text or language!='ko':
        return translated
    for pattern, replacement in [
        (r'^At least (\d+) daily rows are required\.$', r'최소 \1일의 일별 데이터가 필요합니다.'),
        (r'^Missing columns: (.+)$', r'필수 열이 누락되었습니다: \1'),
        (r'^Infinite values in (.+)$', r'무한대 값이 포함된 열: \1'),
    ]:
        if re.match(pattern,text):
            return re.sub(pattern,replacement,text)
    return translate('Unable to process this data. Check the format, connection and source availability.',language)

def display_frame(frame, language='en'):
    """Copy and localize display labels; never mutate canonical numeric/export data."""
    result=frame.copy()
    t=lambda value:translate(value,language)
    for col in result.select_dtypes(include=['object','string']).columns:
        result[col]=result[col].map(t)
    result=result.rename(columns=t,index=t)
    result.index.name=t(result.index.name)
    result.columns.name=t(result.columns.name)
    return result

def translate_figure(fig, language='en'):
    t=lambda value:translate(value,language)
    for trace in fig.data:
        original=trace.name
        trace.name=t(original)
        if trace.hovertemplate and original and original!=t(original):
            trace.hovertemplate=trace.hovertemplate.replace(original,t(original))
        if trace.hovertemplate and language=='ko':
            for english,korean in KO.items():
                trace.hovertemplate=trace.hovertemplate.replace(english+'=',korean+'=')
        if trace.x is not None:
            trace.x=[t(value) for value in trace.x]
    for axis in ['xaxis','yaxis']:
        obj=getattr(fig.layout,axis,None)
        if obj and obj.title:
            obj.title.text=t(obj.title.text)
    if fig.layout.legend.title:
        fig.layout.legend.title.text=t(fig.layout.legend.title.text)
    return fig

KO.update({
'On-chain source':'온체인 데이터 소스',
'Coin Metrics (noncommercial)':'Coin Metrics (비상업적 이용)',
'CSV only / off':'CSV만 사용 / 끄기',
'Coin Metrics · CC BY-NC 4.0 · noncommercial research only.':'Coin Metrics · CC BY-NC 4.0 · 비상업적 연구 전용.',
'MVRV and net flows: assumed 48-hour lag; revised historical data. SOPR is unavailable from this free source.':'MVRV·순유입: 48시간 지연 가정, 사후 수정된 과거 데이터입니다. 이 무료 소스는 SOPR을 제공하지 않습니다.',
'On-chain fallback in use. Check observation_end in the data manifest.':'온체인 대체 데이터를 사용 중입니다. 데이터 명세의 observation_end를 확인하세요.',
'On-chain data unavailable; price and derivatives remain usable.':'온체인 데이터를 가져오지 못했습니다. 가격·파생상품 분석은 계속 사용할 수 있습니다.',
'Include on-chain features (exploratory)':'온체인 특성 포함 (탐색적 분석)',
'On-chain observations aligned to market dates':'시장 날짜에 맞춘 온체인 관측값',
'Net flows are USD deposits minus withdrawals. A negative value does not prove buying. Missing observations stay missing.':'순유입은 달러 기준 입금에서 출금을 뺀 값입니다. 음수가 매수를 입증하지는 않습니다. 결측값은 그대로 유지합니다.',
'On-chain chart':'온체인 차트',
'Deribit public BTC call quotes':'Deribit 공개 BTC 콜옵션 호가',
'Current quotes only; no historical option returns. Target: 30 days ± 14, nearest 110% strike among OTM calls.':'현재 호가이며 과거 옵션 수익률이 아닙니다. 목표: 만기 30일 ± 14일, 외가격 콜 중 110%에 가장 가까운 행사가.',
'Fetch current option quote':'현재 옵션 호가 가져오기',
'Inverse BTC settlement; premium retained in BTC. Gross expiry scenario using bid, zero fees. Execution and collateral effects are not modeled.':'BTC 역방향 결제, 프리미엄은 BTC로 보유합니다. 매수호가·수수료 0 기준 만기 시나리오이며 체결 및 담보 효과는 반영하지 않습니다.',
'Download timestamped option quotes':'조회 시각이 기록된 옵션 호가 다운로드',
})

KO["Bybit → Binance → verified snapshot · completed daily bars · one-hour cache."]="Bybit → Binance → 검증된 스냅샷 · 완료된 일봉 · 1시간 캐시."
