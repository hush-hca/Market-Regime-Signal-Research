"""Historical quote-based expiry accounting, not a margin-path execution model."""
import numpy as np
import pandas as pd


def _frame(frame,columns,times):
    if not set(columns)<=set(frame):
        raise ValueError(f'Missing option history columns: {sorted(set(columns)-set(frame))}')
    frame=frame.copy()
    for field in times:
        frame[field]=pd.to_datetime(frame[field],utc=True,errors='raise')
        if frame[field].isna().any(): raise ValueError(f'Missing timestamp: {field}')
    return frame


def covered_call_events(signals,spot,quotes,instruments,settlements,fee_config):
    fees={key:float(fee_config.get(key,0.)) for key in ['spot_bps','option_fee_btc','settlement_fee_btc']}
    if not np.isfinite(list(fees.values())).all() or min(fees.values())<0:
        raise ValueError('Fees must be finite and nonnegative.')
    signals=_frame(signals,['date','regime'],['date']).sort_values('date')
    if signals.date.duplicated().any(): raise ValueError('Duplicate signal dates.')
    spot=_frame(spot,['observed_at','spot_index'],['observed_at']).sort_values('observed_at')
    quotes=_frame(quotes,['instrument','observed_at','quote_time','bid_btc','ask_btc'],['observed_at','quote_time'])
    terms=_frame(instruments,['instrument','observed_at','expiry','strike','option_type',
        'contract_size','settlement_currency','quote_currency','base_currency'],['observed_at','expiry'])
    settles=_frame(settlements,['expiry','delivery_price','index_name'],['expiry'])
    if settles.duplicated(['expiry','index_name']).any(): raise ValueError('Conflicting settlement records.')
    if quotes.duplicated(['instrument','observed_at']).any(): raise ValueError('Duplicate option quotes.')
    spot['spot_index']=pd.to_numeric(spot.spot_index,errors='raise')
    settles['delivery_price']=pd.to_numeric(settles.delivery_price,errors='raise')
    if not np.isfinite(spot.spot_index).all() or (spot.spot_index<=0).any():
        raise ValueError('Invalid spot history.')
    if not np.isfinite(settles.delivery_price).all() or (settles.delivery_price<=0).any():
        raise ValueError('Invalid settlement index.')
    for field in ['bid_btc','ask_btc']: quotes[field]=pd.to_numeric(quotes[field],errors='raise')
    for field in ['strike','contract_size']: terms[field]=pd.to_numeric(terms[field],errors='raise')
    rows=[]; occupied_until=pd.Timestamp.min.tz_localize('UTC')
    for signal in signals.itertuples():
        decision=signal.date+pd.Timedelta(days=1)
        row={'signal_date':signal.date,'regime':signal.regime,'decision_at':decision,
            'status':'no_valid_quote','covered_call_return':np.nan,'spot_return':np.nan}
        if signal.regime=='Unclassified':
            row['status']='unclassified'; rows.append(row); continue
        if decision<occupied_until:
            row['status']='position_already_open'; rows.append(row); continue
        window=quotes[quotes.observed_at.between(decision,decision+pd.Timedelta(hours=1))]
        candidates=[]
        for timestamp,group in window.groupby('observed_at',sort=True):
            prices=spot[(spot.observed_at<=timestamp)&(spot.observed_at>=timestamp-pd.Timedelta(minutes=5))]
            if prices.empty: continue
            price=float(prices.iloc[-1].spot_index)
            available=terms[terms.observed_at<=timestamp].sort_values('observed_at').drop_duplicates('instrument',keep='last')
            merged=group.merge(available.drop(columns='observed_at'),on='instrument',how='inner',validate='many_to_one')
            age=(timestamp-merged.quote_time).dt.total_seconds()
            tenor=(merged.expiry-timestamp).dt.total_seconds()/86400
            ok=(age.between(0,300)&tenor.between(16,44)&(merged.strike>=price)&
                merged.option_type.eq('call')&merged.contract_size.eq(1)&
                merged.settlement_currency.eq('BTC')&merged.quote_currency.eq('BTC')&merged.base_currency.eq('BTC')&
                merged.bid_btc.gt(0)&merged.ask_btc.ge(merged.bid_btc)&
                np.isfinite(merged.bid_btc)&np.isfinite(merged.ask_btc)&np.isfinite(merged.strike))
            eligible=merged[ok].copy()
            if eligible.empty: continue
            eligible['tenor_distance']=(tenor[ok]-30).abs()
            eligible['strike_distance']=(eligible.strike/price-1.1).abs()
            selected=eligible.sort_values(['tenor_distance','strike_distance','instrument']).iloc[0]
            candidates=[selected,price,timestamp]
            break
        if not candidates:
            rows.append(row); continue
        selected,price,entry=candidates
        occupied_until=selected.expiry
        row.update(instrument=selected.instrument,entry_at=entry,expiry=selected.expiry,
            spot_index=price,strike=selected.strike,premium_btc=selected.bid_btc,
            quote_time=selected.quote_time,**fees)
        settlement=settles[(settles.expiry==selected.expiry)&settles.index_name.eq('btc_usd')]
        if settlement.empty:
            row['status']='missing_settlement'; rows.append(row); continue
        terminal=float(settlement.iloc[0].delivery_price)
        liability=max(1-float(selected.strike)/terminal,0)
        capital=price*(1+fees['spot_bps']/10000)
        btc=1+float(selected.bid_btc)-fees['option_fee_btc']-fees['settlement_fee_btc']-liability
        row.update(status='completed',settlement_index=terminal,option_liability_btc=liability,
            initial_capital_usd=capital,terminal_wealth_usd=btc*terminal,
            covered_call_return=btc*terminal/capital-1,spot_return=terminal/capital-1,
            accounting='Expiry mark; retained BTC premium; no interim margin or spot exit fee')
        rows.append(row)
    return pd.DataFrame(rows,columns=None if rows else ['signal_date','regime','status','covered_call_return','spot_return'])
