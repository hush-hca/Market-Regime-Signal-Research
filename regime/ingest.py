"""Public market-data adapters. Missing historical OI remains missing."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .data import validate

DAY = 86_400_000

class Client:
    def __init__(self, venue, raw_dir='data/raw'):
        self.venue = venue
        self.base = {'binance':'https://fapi.binance.com', 'bybit':'https://api.bybit.com'}[venue]
        self.raw = Path(raw_dir) / venue
        self.raw.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1,
            status_forcelist=[429,500,502,503,504], respect_retry_after_header=True)))

    def get(self, path, **params):
        response = self.session.get(self.base+path, params=params, timeout=30)
        response.raise_for_status()
        body = response.json()
        if self.venue == 'bybit' and body.get('retCode') != 0:
            raise ValueError(f'Bybit API: {body.get("retMsg")}')
        stamp = pd.Timestamp.now(tz='UTC').isoformat()
        record = {'retrieved_at':stamp, 'path':path, 'params':params, 'response':body}
        encoded = json.dumps(record, sort_keys=True)
        key = hashlib.sha256(encoded.encode()).hexdigest()
        (self.raw / f'{key}.json').write_text(encoded, encoding='utf-8')
        time.sleep(.12)
        return body

def funding_daily(rows):
    if not rows:
        return pd.Series(dtype=float, name='funding')
    d = pd.DataFrame(rows)
    d['date'] = pd.to_datetime(pd.to_numeric(d.fundingTime), unit='ms', utc=True).dt.floor('D')
    d['fundingRate'] = pd.to_numeric(d.fundingRate)
    return d.drop_duplicates('fundingTime').groupby('date').fundingRate.sum().rename('funding')

def download(venue='binance', days=730, raw_dir='data/raw', client=None):
    if not 60 <= days <= 2500:
        raise ValueError('Choose 60–2500 days.')
    c = client or Client(venue, raw_dir)
    end = int(pd.Timestamp.now(tz='UTC').normalize().timestamp()*1000)-1
    start = end+1-days*DAY
    candles, rates, oi = [], [], []
    if venue == 'binance':
        cursor = start
        while cursor < end:
            rows = c.get('/fapi/v1/klines', symbol='BTCUSDT', interval='1d', startTime=cursor, endTime=end, limit=1000)
            if not rows:
                break
            candles.extend([[r[0],*r[1:5],r[7]] for r in rows])
            next_cursor = int(rows[-1][0])+DAY
            if next_cursor <= cursor:
                raise ValueError('Non-advancing Binance candle pagination')
            cursor = next_cursor
        cursor = start
        while cursor < end:
            rows = c.get('/fapi/v1/fundingRate', symbol='BTCUSDT', startTime=cursor, endTime=end, limit=1000)
            if not rows:
                break
            rates.extend(rows)
            next_cursor = int(rows[-1]['fundingTime'])+1
            if next_cursor <= cursor:
                raise ValueError('Non-advancing Binance funding pagination')
            cursor = next_cursor
        # Recent window only; failure must not discard otherwise usable price/funding history.
        try:
            rows = c.get('/futures/data/openInterestHist', symbol='BTCUSDT', period='1d', limit=30)
            oi = [[r['timestamp'],r['sumOpenInterestValue']] for r in rows]
            oi_note = 'Binance recent OI only; no historical backfill assumed.'
        except (requests.RequestException, ValueError, KeyError) as exc:
            oi_note = f'OI unavailable: {type(exc).__name__}'
    else:
        cursor = end
        while cursor >= start:
            rows = c.get('/v5/market/kline', category='linear', symbol='BTCUSDT', interval='D', start=start, end=cursor, limit=1000)['result']['list']
            if not rows:
                break
            candles.extend([[r[0],*r[1:5],r[6]] for r in rows])
            next_cursor = min(int(r[0]) for r in rows)-1
            if next_cursor >= cursor:
                raise ValueError('Non-advancing Bybit candle pagination')
            cursor = next_cursor
        cursor = end
        while cursor >= start:
            rows = c.get('/v5/market/funding/history', category='linear', symbol='BTCUSDT', startTime=start, endTime=cursor, limit=200)['result']['list']
            if not rows:
                break
            rates.extend([{'fundingTime':int(r['fundingRateTimestamp']),'fundingRate':r['fundingRate']} for r in rows])
            next_cursor = min(int(r['fundingRateTimestamp']) for r in rows)-1
            if next_cursor >= cursor:
                raise ValueError('Non-advancing Bybit funding pagination')
            cursor = next_cursor
        cursor, seen = '', set()
        try:
            while True:
                params = dict(category='linear', symbol='BTCUSDT', intervalTime='1d', startTime=start,endTime=end,limit=200)
                if cursor:
                    params['cursor'] = cursor
                result = c.get('/v5/market/open-interest', **params)['result']
                oi.extend([[r['timestamp'],r['openInterest']] for r in result['list']])
                cursor = result.get('nextPageCursor','')
                if not cursor:
                    break
                if cursor in seen:
                    raise ValueError('Repeated Bybit OI cursor')
                seen.add(cursor)
            oi_note = 'Bybit native BTC OI converted to USD with daily open; venue-reported coverage.'
        except (requests.RequestException, ValueError, KeyError) as exc:
            oi_note = f'OI incomplete or unavailable: {type(exc).__name__}'
    d = pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume'])
    if d.empty:
        raise ValueError('No market candles returned.')
    d['date'] = pd.to_datetime(pd.to_numeric(d.timestamp), unit='ms',utc=True)
    d = d.drop(columns='timestamp').drop_duplicates('date').set_index('date').sort_index()
    d = d.apply(pd.to_numeric)
    d = d.join(funding_daily(rates))
    if oi:
        o = pd.DataFrame(oi,columns=['timestamp','oi'])
        # Floor alone would expose intraday snapshots too early. Attach each observation
        # to the daily bar whose end occurs after the observation timestamp.
        o['date'] = pd.to_datetime(pd.to_numeric(o.timestamp),unit='ms',utc=True).dt.floor('D')
        o['oi'] = pd.to_numeric(o.oi)
        o = o.sort_values('timestamp').drop_duplicates('date',keep='last').set_index('date')
        d = d.join(o[['oi']])
        if venue == 'bybit':
            d['oi'] = d.oi * d.open
    d = validate(d.reset_index())
    meta = dict(source=venue, symbol='BTCUSDT', downloaded_at=pd.Timestamp.now(tz='UTC').isoformat(),
        oi_note=oi_note, price_instrument='USDT perpetual', volume_unit='USDT quote turnover',
        funding_unit='sum of realized funding fractions per UTC day', synthetic=False,
        note='Current-vintage API history; publication delays and historical revisions are not independently reconstructed.')
    return d, meta

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--venue',choices=['binance','bybit'],default='binance')
    parser.add_argument('--days',type=int,default=730)
    parser.add_argument('--output',default='data/market.parquet')
    args = parser.parse_args()
    d, meta = download(args.venue,args.days)
    out = Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    d.to_parquet(out,index=False)
    out.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(f'Saved {len(d)} daily rows to {out}; {meta["oi_note"]}')

if __name__ == '__main__':
    main()
