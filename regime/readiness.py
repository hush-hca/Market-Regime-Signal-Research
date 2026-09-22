"""Explicit model contracts, observation health and descriptive evidence."""
import pandas as pd
from .research import features, walk_forward, events, summarize, LABELS

MODELS=['Price only','Price + derivatives','Price + derivatives + on-chain']
PRICE=['momentum_7','momentum_30','volatility_30','volume_z']


def model_features(d,name):
    if name not in MODELS: raise ValueError('Unknown model')
    frame=features(d,include_oi=name!=MODELS[0],include_onchain=name==MODELS[2])
    columns=PRICE.copy()
    if name!=MODELS[0]: columns+=['funding_7','oi_change_7']
    if name==MODELS[2]: columns+=['mvrv','exchange_netflow']
    return frame.reindex(columns=columns)


def model_states(d):
    rows=[]; fits={}
    for name in MODELS:
        f=model_features(d,name)
        missing=list(f.columns[f.iloc[-1].isna()])
        last=pd.NaT; latest=False; reason=''
        try:
            result,profiles,manifest=walk_forward(d,f)
            manifest['model']=name
            fits[name]=(result,profiles,manifest)
            classified=result.loc[result.regime.ne('Unclassified'),'date']
            last=classified.max()
            latest=bool(result.regime.iloc[-1]!='Unclassified')
            status='Ready' if latest else 'Missing latest inputs'
        except ValueError as exc:
            status='Unavailable'; reason=str(exc)
        rows.append(dict(model=name,status=status,latest_ready=latest,last_classified_date=last,
            missing_features=', '.join(missing),complete_training_candidates=int(f.notna().all(axis=1).sum()),
            feature_columns=', '.join(f.columns),reason=reason))
    return pd.DataFrame(rows),fits


def metric_health(d,meta,chain=None,now=None):
    now=pd.Timestamp.now(tz='UTC') if now is None else pd.Timestamp(now)
    rows=[]
    for metric in ['close','volume','funding','oi','mvrv','exchange_netflow','sopr']:
        values=d.get(metric,pd.Series(float('nan'),index=d.index))
        dates=d.loc[values.notna(),'date']
        usable=dates.max()
        is_chain=metric in ['mvrv','exchange_netflow','sopr']
        source_meta=meta.get('onchain',{}) if is_chain else meta
        if not isinstance(source_meta,dict): source_meta={'source':str(source_meta)}
        original=usable if not is_chain else pd.NaT
        if is_chain and chain is not None and metric in chain and 'observation_time' in chain:
            original=pd.to_datetime(chain.loc[chain[metric].notna(),'observation_time'],utc=True).max()
        age=(now-original).total_seconds()/86400 if pd.notna(original) else float('nan')
        status='Missing' if dates.empty else ('Stale' if pd.isna(original) or age>3 else 'Available')
        rows.append(dict(metric=metric,status=status,observation_date=original,usable_market_date=usable,
            age_days=age,missing_rows=int(values.isna().sum()),total_rows=len(d),
            provider=source_meta.get('source','Missing'),
            retrieved_at=source_meta.get('retrieved_at',source_meta.get('downloaded_at'))))
    return pd.DataFrame(rows)


def evidence_cards(d,r,horizon=30,partition='Final holdout'):
    ev=events(d,r,horizon,partition)
    summary=summarize(ev)
    segment=r[r.partition.eq(partition)].copy()
    # Count sampled contiguous episodes, not daily observations or all segment episodes.
    episode=(r.regime.ne(r.regime.shift()) | r.model_version.ne(r.model_version.shift())).cumsum()
    episode_by_date=pd.Series(episode.to_numpy(),index=pd.DatetimeIndex(r.date))
    rows=[]
    for label in LABELS:
        found=summary[summary.regime.eq(label)] if not summary.empty else pd.DataFrame()
        row=found.iloc[0].to_dict() if not found.empty else dict(regime=label,n=0,mean=float('nan'),
            median=float('nan'),positive_frequency=float('nan'),difference_from_all=float('nan'),
            mean_ci_low=float('nan'),mean_ci_high=float('nan'),evidence='No completed events')
        selected=ev[ev.regime.eq(label)]
        row.update(benchmark_mean=ev.return_.mean(),sampled_episodes=selected.signal_date.map(episode_by_date).nunique(),
            evaluation_start=segment.date.min(),evaluation_end=segment.date.max(),horizon_days=horizon,
            event_start=selected.entry_date.min(),event_end=selected.exit_date.max())
        rows.append(row)
    return pd.DataFrame(rows)
