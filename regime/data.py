"""Daily UTC data contract, synthetic fixture, and optional on-chain enrichment."""
from io import StringIO
import numpy as np
import pandas as pd

REQUIRED = ['date', 'open', 'high', 'low', 'close', 'volume', 'funding']
ONCHAIN = ['mvrv', 'sopr', 'exchange_netflow']

def validate(frame):
    d = frame.copy()
    missing = set(REQUIRED) - set(d.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    d['date'] = pd.to_datetime(d['date'], utc=True, errors='raise')
    if d.date.duplicated().any():
        raise ValueError('Duplicate dates are not allowed.')
    if not d.date.eq(d.date.dt.normalize()).all():
        raise ValueError('Dates must be UTC daily boundaries.')
    d = d.sort_values('date').reset_index(drop=True)
    for col in REQUIRED[1:] + [c for c in ['oi'] + ONCHAIN if c in d]:
        d[col] = pd.to_numeric(d[col], errors='raise')
        if np.isinf(d[col]).any():
            raise ValueError(f'Infinite values in {col}')
    if d[REQUIRED[1:6]].isna().any().any():
        raise ValueError('OHLCV values cannot be missing.')
    if (d[['open', 'high', 'low', 'close']] <= 0).any().any() or (d.volume < 0).any():
        raise ValueError('Prices must be positive; volume must be nonnegative.')
    if ((d.high < d[['open','close','low']].max(axis=1)) | (d.low > d[['open','close','high']].min(axis=1))).any():
        raise ValueError('Invalid OHLC bounds.')
    if 'oi' not in d:
        d['oi'] = np.nan
    if (d.oi.dropna() < 0).any():
        raise ValueError('OI must be nonnegative.')
    if len(d) < 2 or not d.date.diff().iloc[1:].eq(pd.Timedelta(days=1)).all():
        raise ValueError('Daily price rows must be contiguous; repair missing dates before research.')
    return d

def demo(days=1460):
    rng = np.random.default_rng(42)
    phase = (np.arange(days) // 100) % 4
    returns = rng.normal(np.choose(phase, [.0012,-.001,.0002,.0005]), np.choose(phase,[.015,.028,.008,.02]))
    close = 23000 * np.exp(np.cumsum(returns))
    opening = np.r_[23000, close[:-1]]
    spread = rng.uniform(.003,.025,days)
    return validate(pd.DataFrame(dict(date=pd.date_range('2022-01-01', periods=days, tz='UTC'),
        open=opening, close=close, high=np.maximum(opening,close)*(1+spread), low=np.minimum(opening,close)*(1-spread),
        volume=rng.lognormal(22, .4, days), funding=rng.normal(np.choose(phase,[.0003,-.0002,.00005,.0004]),.00015),
        oi=np.exp(22+np.cumsum(rng.normal(.0001,.012,days))))))

def enrich(daily, csv_text):
    """Join on earliest availability, never on the metric's observation date."""
    chain = pd.read_csv(StringIO(csv_text))
    cols = [c for c in ONCHAIN if c in chain]
    if not cols or 'available_at' not in chain:
        raise ValueError('On-chain CSV needs available_at and at least one of mvrv, sopr, exchange_netflow.')
    chain['available_at'] = pd.to_datetime(chain.available_at, utc=True, errors='raise')
    if chain.available_at.isna().any() or chain.available_at.duplicated().any():
        raise ValueError('available_at must be unique and present.')
    for c in cols:
        chain[c] = pd.to_numeric(chain[c], errors='raise')
        if np.isinf(chain[c]).any():
            raise ValueError('On-chain values must be finite or missing.')
    d = daily.drop(columns=ONCHAIN + ['available_at'], errors='ignore').copy()
    d['decision_at'] = d.date + pd.Timedelta(days=1)
    return pd.merge_asof(d.sort_values('decision_at'), chain[['available_at']+cols].sort_values('available_at'),
        left_on='decision_at', right_on='available_at', direction='backward', tolerance=pd.Timedelta(days=2)).drop(columns='decision_at')

def quality(d):
    return pd.DataFrame({'field': ['funding','oi']+[c for c in ONCHAIN if c in d],
        'missing_pct': [round(d[c].isna().mean()*100,2) for c in ['funding','oi']+[c for c in ONCHAIN if c in d]]})
