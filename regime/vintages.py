"""As-recorded joins that never overwrite earlier decisions with later revisions."""
import numpy as np
import pandas as pd
from .data import ONCHAIN


def enrich_vintages(daily,records,max_age_days=4):
    records=records.copy()
    required=['observation_time','available_at','retrieved_at']
    if not set(required)<=set(records):
        raise ValueError('Vintage records require observation, publication and retrieval timestamps.')
    for col in required:
        records[col]=pd.to_datetime(records[col],utc=True,errors='raise')
        if records[col].isna().any():
            raise ValueError('Vintage timestamp cannot be missing.')
    if (records.available_at<records.observation_time).any():
        raise ValueError('Publication cannot precede observation.')
    if records.duplicated(required).any():
        raise ValueError('Duplicate vintage timestamps.')
    cols=[c for c in ONCHAIN if c in records]
    if not cols:
        raise ValueError('No supported on-chain metric.')
    for col in cols:
        records[col]=pd.to_numeric(records[col],errors='raise')
        if np.isinf(records[col]).any(): raise ValueError('Infinite on-chain value.')
    # We can only attest that our collector knew it after both timestamps.
    records['known_at']=records[['available_at','retrieved_at']].max(axis=1)
    result=daily.drop(columns=ONCHAIN+required+['known_at'],errors='ignore').copy()
    for col in cols: result[col]=np.nan
    result['known_at']=pd.Series(pd.NaT,index=result.index,dtype='datetime64[ns, UTC]')
    for index,date in result.date.items():
        decision=date+pd.Timedelta(days=1)
        eligible=records[(records.known_at<=decision)&
            (records.observation_time>=decision-pd.Timedelta(days=max_age_days))]
        if eligible.empty: continue
        latest=eligible.sort_values(['observation_time','known_at','retrieved_at']).iloc[-1]
        result.loc[index,cols]=latest[cols].to_numpy()
        result.loc[index,'known_at']=latest.known_at
    return result
