"""Coin Metrics MVRV and exchange net flows, with explicit vintage/lag limits."""
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlparse
import numpy as np
import pandas as pd
from .public_sources import session, get_json

API='https://community-api.coinmetrics.io/v4/timeseries/asset-metrics'
ARCHIVE='https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv'
BUNDLE=Path(__file__).resolve().parents[1]/'bootstrap'/'coinmetrics.parquet'
METRICS='CapMVRVCur,FlowInExUSD,FlowOutExUSD'
LICENSE='CC BY-NC 4.0 · Coin Metrics · noncommercial use with attribution'

def normalize(rows,lag_days=2):
    """Lag is an assumption, not a claim of historical first-publication time."""
    if lag_days<2:
        raise ValueError('Use at least two days from observation start for on-chain lag.')
    data=pd.DataFrame(rows).copy()
    if 'time' not in data or 'CapMVRVCur' not in data:
        raise ValueError('Coin Metrics response is missing time or MVRV.')
    result=pd.DataFrame({'observation_time':pd.to_datetime(data.time,utc=True,errors='raise')})
    if result.observation_time.isna().any() or result.observation_time.duplicated().any():
        raise ValueError('On-chain observation dates must be present and unique.')
    if not result.observation_time.eq(result.observation_time.dt.normalize()).all():
        raise ValueError('Coin Metrics observations must be daily UTC boundaries.')
    result['available_at']=result.observation_time+pd.Timedelta(days=lag_days)
    result['mvrv']=pd.to_numeric(data.CapMVRVCur,errors='raise')
    if {'FlowInExUSD','FlowOutExUSD'}<=set(data):
        incoming=pd.to_numeric(data.FlowInExUSD,errors='raise')
        outgoing=pd.to_numeric(data.FlowOutExUSD,errors='raise')
        if (incoming.dropna()<0).any() or (outgoing.dropna()<0).any():
            raise ValueError('Gross exchange flows cannot be negative.')
        # Never substitute zero for a missing leg.
        result['exchange_netflow']=incoming-outgoing
    numeric=result.select_dtypes('number')
    if np.isinf(numeric).any().any() or (result.mvrv.dropna()<=0).any():
        raise ValueError('Invalid on-chain values.')
    return result.dropna(subset=['mvrv']).sort_values('available_at').reset_index(drop=True)

def load_coinmetrics(start,end,client=None,bundle=BUNDLE):
    client=client or session()
    retrieved_at=pd.Timestamp.now(tz='UTC').isoformat()
    failures=[]
    data=None
    source='Coin Metrics Community API'
    try:
        params=dict(assets='btc',metrics=METRICS,frequency='1d',page_size=1000,
            start_time=str(pd.Timestamp(start).date()),end_time=str(pd.Timestamp(end).date()))
        page=get_json(client,API,**params)
        rows=list(page.get('data',[]))
        seen=set()
        while page.get('next_page_url'):
            url=page['next_page_url']
            parsed=urlparse(url)
            if parsed.scheme!='https' or parsed.netloc!='community-api.coinmetrics.io' or url in seen or len(seen)>=20:
                raise ValueError('Invalid Coin Metrics pagination.')
            seen.add(url)
            page=get_json(client,url)
            rows.extend(page.get('data',[]))
        data=normalize(rows)
        if data.empty:
            raise ValueError('No nonempty MVRV observations returned.')
    except (ValueError,KeyError,OSError) as exc:
        failures.append(type(exc).__name__)
        # Official daily archive, not an unrelated third-party mirror.
        try:
            response=client.get(ARCHIVE,timeout=(5,25))
            response.raise_for_status()
            data=normalize(pd.read_csv(io.StringIO(response.text)))
            source='Coin Metrics official GitHub archive'
        except (ValueError,KeyError,OSError) as archive_error:
            failures.append(type(archive_error).__name__)
            path=Path(bundle)
            meta=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
            if meta.get('source')!='Coin Metrics Community API' or meta.get('synthetic') is not False:
                raise ValueError('Unverified on-chain bundle.') from archive_error
            if hashlib.sha256(path.read_bytes()).hexdigest()!=meta.get('sha256'):
                raise ValueError('On-chain bundle integrity check failed.') from archive_error
            data=pd.read_parquet(path)
            retrieved_at=meta.get('retrieved_at')
            source='Coin Metrics bundled historical snapshot'
    start_stamp=pd.Timestamp(start)
    end_stamp=pd.Timestamp(end)
    start_stamp=start_stamp.tz_localize('UTC') if start_stamp.tzinfo is None else start_stamp.tz_convert('UTC')
    end_stamp=end_stamp.tz_localize('UTC') if end_stamp.tzinfo is None else end_stamp.tz_convert('UTC')
    data=data[data.observation_time.between(start_stamp-pd.Timedelta(days=3),end_stamp)].copy()
    if data.empty:
        raise ValueError('No on-chain coverage for this date range.')
    return data,dict(source=source,retrieved_at=retrieved_at,license=LICENSE,url=API,archive_url=ARCHIVE,
        observation_end=data.observation_time.max().isoformat(),
        availability='Assumed 48 hours after observation start; current-vintage, not point-in-time data',
        metrics=['mvrv']+(['exchange_netflow'] if 'exchange_netflow' in data else []),
        unavailable=['sopr'],netflow_definition='FlowInExUSD minus FlowOutExUSD; provider exchange labels',
        quality='Exchange-flow flash/provisional values may be revised; first-publication vintage not reconstructed',
        fallback_used=bool(failures))
