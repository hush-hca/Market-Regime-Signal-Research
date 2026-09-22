"""Checksum-verified official USD-M archives; unpublished derivatives stay missing."""
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import hashlib
import zipfile
import pandas as pd
import requests
from .data import validate

BASE='https://data.binance.vision/data/futures/um/'


def decode(payload, checksum):
    if hashlib.sha256(payload).hexdigest()!=checksum.split()[0]:
        raise ValueError('Binance archive checksum mismatch')
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        files=archive.infolist()
        if len(files)!=1 or files[0].file_size>20_000_000:
            raise ValueError('Unexpected archive contents')
        return pd.read_csv(archive.open(files[0]))


def fetch(path):
    response=requests.get(BASE+path,timeout=30)
    if response.status_code==404:
        return None
    response.raise_for_status()
    checksum=requests.get(BASE+path+'.CHECKSUM',timeout=30)
    checksum.raise_for_status()
    return decode(response.content,checksum.text)


def normalize(prices,rates,metrics):
    d=prices.copy()
    d['date']=pd.to_datetime(d.open_time,unit='ms',utc=True)
    d=d.rename(columns={'quote_volume':'turnover'})
    d=d[['date','open','high','low','close','turnover']].rename(columns={'turnover':'volume'})
    d=d.drop_duplicates('date').set_index('date').sort_index()
    d['funding']=float('nan')
    if not rates.empty:
        rates=rates.drop_duplicates('calc_time').copy()
        rates['date']=pd.to_datetime(rates.calc_time,unit='ms',utc=True).dt.floor('D')
        grouped=rates.groupby('date')
        # Incomplete funding days must never be presented as a full daily sum.
        funding=grouped.last_funding_rate.sum().where(grouped.funding_interval_hours.sum().eq(24))
        d['funding']=funding
    d['oi']=float('nan')
    if not metrics.empty:
        metrics=metrics.copy()
        metrics['timestamp']=pd.to_datetime(metrics.create_time,utc=True)
        metrics['date']=metrics.timestamp.dt.floor('D')
        last=metrics.sort_values('timestamp').drop_duplicates('date',keep='last').set_index('date')
        d['oi']=last.sum_open_interest_value
    return validate(d.reset_index())


def download_archive(days=730,as_of=None,fetcher=fetch):
    now=pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.now(tz='UTC')
    now=now.tz_localize('UTC') if now.tzinfo is None else now.tz_convert('UTC')
    end=now.normalize()-pd.Timedelta(days=1)
    start=end-pd.Timedelta(days=days-1)
    months=pd.date_range(start.replace(day=1),end.replace(day=1),freq='MS')
    tasks=[]
    for month in months:
        stamp=month.strftime('%Y-%m')
        tasks.extend([('price',f'monthly/klines/BTCUSDT/1d/BTCUSDT-1d-{stamp}.zip'),
                      ('funding',f'monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{stamp}.zip')])
    tables={'price':[],'funding':[],'oi':[]}
    missing=[]
    def run(tasks):
        with ThreadPoolExecutor(max_workers=4) as pool:
            for (kind,path),frame in zip(tasks,pool.map(fetcher,[path for _,path in tasks])):
                if frame is None: missing.append(path)
                else: tables[kind].append(frame)
    run(tasks)
    # Daily prices fill months that are not published yet; no alternate API hosts.
    covered=set()
    for frame in tables['price']:
        covered.update(pd.to_datetime(frame.open_time,unit='ms',utc=True))
    tasks=[]
    for day in pd.date_range(start,end):
        stamp=day.strftime('%Y-%m-%d')
        if day not in covered:
            tasks.append(('price',f'daily/klines/BTCUSDT/1d/BTCUSDT-1d-{stamp}.zip'))
        tasks.append(('oi',f'daily/metrics/BTCUSDT/BTCUSDT-metrics-{stamp}.zip'))
    run(tasks)
    frames={key:pd.concat(value,ignore_index=True) if value else pd.DataFrame() for key,value in tables.items()}
    if frames['price'].empty: raise ValueError('No published Binance price archive')
    prices=frames['price']
    dates=pd.to_datetime(prices.open_time,unit='ms',utc=True)
    frame=normalize(prices.loc[dates.between(start,end)],frames['funding'],frames['oi'])
    return frame,dict(source='binance',synthetic=False,transport='official public archive',
        retrieved_at=now.isoformat(),symbol='BTCUSDT',price_instrument='USDT perpetual',
        volume_unit='USDT quote turnover',funding_unit='sum of realized funding fractions per UTC day',
        missing_archive_files=missing,checksum_verified=True,
        note='Current-vintage official archives. Monthly funding publication can lag prices; missing values are not filled.',
        oi_note='Last published intraday USD open-interest observation per UTC day.')
