import pandas as pd
import pytest


def inputs():
    entry=pd.Timestamp('2025-01-02T00:17:00Z'); expiry=pd.Timestamp('2025-02-01T08:00:00Z')
    signals=pd.DataFrame({'date':[pd.Timestamp('2025-01-01',tz='UTC')],'regime':['Expansion']})
    spot=pd.DataFrame({'observed_at':[entry],'spot_index':[100.]})
    quotes=pd.DataFrame({'instrument':['BTC-C'],'observed_at':[entry],'quote_time':[entry],
                         'bid_btc':[.03],'ask_btc':[.04]})
    instruments=pd.DataFrame({'instrument':['BTC-C'],'expiry':[expiry],'strike':[110.],
        'option_type':['call'],'contract_size':[1.],'settlement_currency':['BTC'],
        'quote_currency':['BTC'],'base_currency':['BTC'],'observed_at':[entry]})
    settlements=pd.DataFrame({'expiry':[expiry],'delivery_price':[200.],'index_name':['btc_usd']})
    return signals,spot,quotes,instruments,settlements


def test_inverse_settlement_and_fees_are_in_btc():
    from regime.options_backtest import covered_call_events
    rows=covered_call_events(*inputs(),fee_config={'spot_bps':10,'option_fee_btc':.001,'settlement_fee_btc':.001})
    row=rows.iloc[0]
    assert row.status=='completed'
    assert row.option_liability_btc==pytest.approx(.45)
    assert row.covered_call_return==pytest.approx((200*(1+.03-.001-.001-.45)-100.1)/100.1)
    assert row.spot_return==pytest.approx(200/100.1-1)


@pytest.mark.parametrize('price',[50.,110.,150.])
def test_itm_atm_otm_expiry_uses_settlement_index(price):
    from regime.options_backtest import covered_call_events
    items=list(inputs()); items[-1]['delivery_price']=price
    row=covered_call_events(*items,fee_config={}).iloc[0]
    assert row.covered_call_return==pytest.approx((price*1.03-max(price-110,0))/100-1)


def test_missing_stale_quotes_settlement_and_terms_skip_without_fabrication():
    from regime.options_backtest import covered_call_events
    items=list(inputs()); items[2]['bid_btc']=0.
    assert covered_call_events(*items,fee_config={}).iloc[0].status=='no_valid_quote'
    items=list(inputs()); items[2]['quote_time']-=pd.Timedelta(minutes=10)
    assert covered_call_events(*items,fee_config={}).iloc[0].status=='no_valid_quote'
    items=list(inputs()); items[-1]=items[-1].iloc[:0]
    assert covered_call_events(*items,fee_config={}).iloc[0].status=='missing_settlement'
    items=list(inputs()); items[3]['contract_size']=10.
    assert covered_call_events(*items,fee_config={}).iloc[0].status=='no_valid_quote'


def test_no_overlapping_trades_even_when_settlement_missing():
    from regime.options_backtest import covered_call_events
    items=list(inputs())
    items[0]=pd.DataFrame({'date':pd.to_datetime(['2025-01-01','2025-01-02'],utc=True),'regime':['Expansion']*2})
    rows=covered_call_events(*items,fee_config={})
    assert rows.status.tolist()==['completed','position_already_open']
