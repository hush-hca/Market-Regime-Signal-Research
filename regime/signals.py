"""Prespecified context hypotheses; descriptive conditions, not capital-flow claims."""
import pandas as pd
from .research import features


def context_signals(daily):
    funding=daily.funding
    valid=funding.notna() & funding.shift().notna()
    flip=((funding<0)&(funding.shift()>=0)).astype('boolean').where(valid,pd.NA)
    mvrv=daily.get('mvrv',pd.Series(float('nan'),index=daily.index))
    threshold=mvrv.shift(1).rolling(365,min_periods=180).quantile(.2)
    low=(mvrv<threshold).astype('boolean').where(mvrv.notna()&threshold.notna(),pd.NA)
    active=(flip & low).where(flip.notna() & low.notna(),pd.NA)
    return pd.DataFrame({'funding_flip_negative':flip,'mvrv_low':low,'hypothesis_active':active,
                         'mvrv_prior_p20':threshold},index=daily.index)


def feature_sets(daily):
    base=features(daily)
    result={'Price only':base.drop(columns='funding_7'),
            'Price + derivatives':features(daily,include_oi=True)}
    if all(name in daily and daily[name].notna().any() for name in ['mvrv','exchange_netflow']):
        result['Price + derivatives + on-chain']=features(daily,include_oi=True,include_onchain=True)
    return result
