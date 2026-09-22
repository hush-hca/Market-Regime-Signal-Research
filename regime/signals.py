"""Prespecified context hypotheses; descriptive conditions, not capital-flow claims."""
import pandas as pd
from .readiness import MODELS,model_features


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
    result={name:model_features(daily,name) for name in MODELS[:2]}
    if all(name in daily and daily[name].notna().any() for name in ['mvrv','exchange_netflow']):
        result[MODELS[2]]=model_features(daily,MODELS[2])
    return result
