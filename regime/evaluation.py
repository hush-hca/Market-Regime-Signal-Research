"""Common-date exploratory feature comparisons and paired net-return summaries."""
from dataclasses import asdict
import hashlib
import pandas as pd
from .research import Config,walk_forward,events,summarize,interval
from .signals import feature_sets


def compare_feature_sets(results):
    if not results: return pd.DataFrame()
    baseline=None
    rows=[]
    for name,frame in results.items():
        required=['signal_date','net_return','benchmark_return','cost_bps']
        if not set(required)<=set(frame): raise ValueError('Missing comparison fields.')
        frame=frame.sort_values('signal_date').reset_index(drop=True)
        if frame.signal_date.duplicated().any() or frame[required].isna().any().any():
            raise ValueError('Comparison requires unique dates and complete values.')
        if baseline is None: baseline=frame
        if not frame.signal_date.equals(baseline.signal_date): raise ValueError('Comparison dates differ.')
        if not frame.cost_bps.equals(baseline.cost_bps): raise ValueError('Comparison cost rules differ.')
        if not frame.benchmark_return.equals(baseline.benchmark_return): raise ValueError('Comparison benchmark differs.')
        excess=frame.net_return-frame.benchmark_return
        lo,hi=interval(excess)
        rows.append(dict(feature_set=name,n=len(frame),mean=frame.net_return.mean(),
            mean_excess=excess.mean(),excess_ci_low=lo,excess_ci_high=hi,
            evidence='Limited sample' if len(frame)<30 else 'Exploratory paired evidence'))
    return pd.DataFrame(rows)


def evaluate_feature_sets(daily,horizon=30,partition='Final holdout',config=Config()):
    fits={}; profiles={}; manifests={}; unavailable={}; frames=feature_sets(daily)
    for name,frame in frames.items():
        try:
            fits[name],profiles[name],manifests[name]=walk_forward(daily,frame,config)
        except ValueError as exc:
            unavailable[name]=str(exc)
    if not fits: raise ValueError('No feature set has enough complete training observations.')
    common=pd.Series(True,index=daily.index)
    for result in fits.values(): common &= result.regime.ne('Unclassified')
    ledgers={}; summaries=[]; coverage=[]
    for name,result in fits.items():
        aligned=result.copy()
        aligned.loc[~common,'regime']='Unclassified'
        ledger=events(daily,aligned,horizon,partition)
        ledgers[name]=ledger
        summary=summarize(ledger)
        summary['feature_set']=name
        # A contiguous episode counts a new label or an intervening unclassified day.
        segment=result[result.partition.eq(partition)]
        starts=segment.regime.ne(segment.regime.shift()) & segment.regime.ne('Unclassified')
        episodes=segment.loc[starts,'regime'].value_counts()
        if not summary.empty:
            summary['episodes_in_segment']=summary.regime.map(episodes).fillna(int(starts.sum())).astype(int)
        summaries.append(summary)
        coverage.append(dict(feature_set=name,classified_dates=int(segment.regime.ne('Unclassified').sum()),
            common_dates=int((common & result.partition.eq(partition)).sum()),events=len(ledger)))
    return dict(events=ledgers,summary=pd.concat(summaries,ignore_index=True),coverage=pd.DataFrame(coverage),
        profiles=profiles,manifest=dict(config=asdict(config),horizon=horizon,partition=partition,
            evaluation_status='Exploratory; previously inspected holdout',
            feature_columns={name:list(frame.columns) for name,frame in frames.items()},
            unavailable_feature_sets=unavailable,
            unavailable_metrics=[name for name in ['oi','mvrv','sopr','exchange_netflow']
                if name not in daily or not daily[name].notna().any()],
            dataset_sha256=hashlib.sha256(daily.to_csv(index=False).encode()).hexdigest(),fits=manifests,
            interpretation='Conditional distributions on common eligible dates; not model-selected trading performance.'))
