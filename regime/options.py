"""Public Deribit inverse BTC option quotes and correctly denominated payoff."""
import numpy as np
import pandas as pd
from .public_sources import session, get_json

BASE='https://www.deribit.com/api/v2/public/'

def normalize_quotes(instruments,summaries,index_price,observed_at):
    now=pd.Timestamp(observed_at)
    now=now.tz_localize('UTC') if now.tzinfo is None else now.tz_convert('UTC')
    if not np.isfinite(index_price) or index_price<=0:
        raise ValueError('Invalid Deribit spot index.')
    instruments={i['instrument_name']:i for i in instruments
        if i.get('option_type')=='call' and i.get('is_active')
        and i.get('settlement_currency')=='BTC' and i.get('quote_currency')=='BTC'
        and i.get('base_currency')=='BTC' and i.get('contract_size')==1}
    rows=[]
    for quote in summaries:
        instrument=instruments.get(quote.get('instrument_name'))
        if instrument is None:
            continue
        bid,ask=quote.get('bid_price'),quote.get('ask_price')
        if bid is None or ask is None or not np.isfinite([bid,ask]).all() or bid<=0 or ask<bid:
            continue
        expiry=pd.to_datetime(instrument['expiration_timestamp'],unit='ms',utc=True)
        strike=float(instrument['strike'])
        if expiry<=now or not np.isfinite(strike) or strike<=0:
            continue
        quote_time=pd.to_datetime(quote.get('creation_timestamp'),unit='ms',utc=True)
        if pd.notna(quote_time) and not -60<=(now-quote_time).total_seconds()<=300:
            continue
        rows.append(dict(instrument=quote['instrument_name'],observed_at=now,expiry=expiry,
            quote_time=quote_time,
            days_to_expiry=(expiry-now).total_seconds()/86400,strike=strike,
            spot_index=index_price,bid_btc=float(bid),ask_btc=float(ask),
            bid_usd=float(bid)*index_price,moneyness=strike/index_price,
            open_interest=quote.get('open_interest'),volume=quote.get('volume')))
    return pd.DataFrame(rows,columns=['instrument','observed_at','quote_time','expiry','days_to_expiry','strike',
        'spot_index','bid_btc','ask_btc','bid_usd','moneyness','open_interest','volume'])

def load_quotes(client=None):
    client=client or session()
    instruments=get_json(client,BASE+'get_instruments',currency='BTC',kind='option',expired='false')['result']
    summaries=get_json(client,BASE+'get_book_summary_by_currency',currency='BTC',kind='option')['result']
    spot=get_json(client,BASE+'get_index_price',index_name='btc_usd')['result']['index_price']
    quotes=normalize_quotes(instruments,summaries,spot,pd.Timestamp.now(tz='UTC'))
    if quotes.empty:
        raise ValueError('No active BTC calls with a valid bid and ask.')
    return quotes

def select_call(quotes,tenor=30,target_moneyness=1.10):
    """Predefined nearest expiry, then nearest OTM strike; no performance fitting."""
    eligible=quotes[quotes.days_to_expiry.between(tenor-14,tenor+14)&(quotes.moneyness>=1)].copy()
    if eligible.empty:
        raise ValueError('No quoted out-of-the-money call within fourteen days of target expiry.')
    eligible['tenor_distance']=(eligible.days_to_expiry-tenor).abs()
    eligible['strike_distance']=(eligible.moneyness-target_moneyness).abs()
    return eligible.sort_values(['tenor_distance','strike_distance','instrument']).iloc[0]

def inverse_call_payoff(spot,strike,premium_btc,fees_btc=0.):
    if not np.isfinite([spot,strike,premium_btc,fees_btc]).all() or min(spot,strike)<=0 or min(premium_btc,fees_btc)<0:
        raise ValueError('Invalid inverse option inputs.')
    terminal=np.linspace(0,spot*2,161)
    # Coin premium retained in BTC; inverse settlement's USD equivalent is call intrinsic.
    terminal_wealth=terminal*(1+premium_btc-fees_btc)-np.maximum(terminal-strike,0)
    return pd.DataFrame(dict(terminal_price=terminal,spot_return=terminal/spot-1,
        covered_call_return=terminal_wealth/spot-1))
