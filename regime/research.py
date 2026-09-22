"""Causal features, walk-forward regimes, event studies and long/cash accounting."""
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

BASE_FEATURES = ['momentum_7','momentum_30','volatility_30','funding_7','volume_z']
LABELS = ['Defensive','Soft / mixed','Firm / mixed','Expansion']

@dataclass(frozen=True)
class Config:
    train_days: int = 365
    refit_days: int = 90
    holdout_days: int = 180
    clusters: int = 4
    seed: int = 42

def features(d, include_oi=False, include_onchain=False):
    f = pd.DataFrame(index=d.index)
    f['momentum_7'] = d.close.pct_change(7, fill_method=None)
    f['momentum_30'] = d.close.pct_change(30, fill_method=None)
    f['volatility_30'] = d.close.pct_change(fill_method=None).rolling(30).std()*np.sqrt(365)
    f['funding_7'] = d.funding.rolling(7).mean()
    logv = np.log1p(d.volume)
    f['volume_z'] = (logv-logv.rolling(30).mean())/logv.rolling(30).std().replace(0,np.nan)
    if include_oi:
        f['oi_change_7'] = d.oi.pct_change(7, fill_method=None)
    if include_onchain:
        for c in ['mvrv','sopr','exchange_netflow']:
            if c in d:
                f[c] = d[c]
    return f.replace([np.inf,-np.inf],np.nan)

def walk_forward(d, f, config=Config()):
    if config.clusters != 4:
        raise ValueError('The named MVP taxonomy uses exactly four clusters.')
    n = len(d)
    if n < config.train_days+config.holdout_days+60:
        raise ValueError(f'At least {config.train_days+config.holdout_days+60} daily rows are required.')
    result = pd.DataFrame(index=d.index)
    result['date'] = d.date
    result['regime'] = 'Unclassified'
    result['rule'] = 'Unclassified'
    result['distance'] = np.nan
    result['model_version'] = ''
    cutoff = n-config.holdout_days
    result['partition'] = np.where(np.arange(n)>=cutoff,'Final holdout','Walk-forward')
    result.loc[:config.train_days-1,'partition'] = 'Warm-up'
    valid = f.notna().all(axis=1)
    # Indicator-rule labels are separate from the model's selected feature columns.
    funding_7 = f['funding_7'] if 'funding_7' in f else d.funding.rolling(7).mean()
    rules = np.select([
        (f.momentum_30>0)&(funding_7>0),
        (f.momentum_30<0)&(funding_7<0),
        (f.momentum_30>0)&(funding_7<=0)],
        ['Positive trend / positive funding','Negative trend / negative funding','Positive trend / negative funding'],
        default='Mixed trend / funding')
    result.loc[valid,'rule'] = rules[valid]
    starts = sorted(set(list(range(config.train_days,cutoff,config.refit_days))+[cutoff]))
    profiles, fits = [], []
    for step, start in enumerate(starts):
        stop = starts[step+1] if step+1 < len(starts) else n
        train = f.iloc[:start].dropna()
        if len(train)<180:
            continue
        scaler = StandardScaler().fit(train)
        model = KMeans(n_clusters=4,n_init=10,random_state=config.seed).fit(scaler.transform(train))
        centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_),columns=f.columns)
        order = centers.momentum_30.sort_values().index
        mapping = {int(cluster):LABELS[rank] for rank,cluster in enumerate(order)}
        version = f'fit-{start}'
        centers['regime'] = [mapping[i] for i in range(4)]
        centers['model_version'] = version
        profiles.append(centers)
        fits.append(dict(model_version=version,train_end=d.date.iloc[start-1].isoformat(),train_rows=len(train),
            test_start=d.date.iloc[start].isoformat(),test_end=d.date.iloc[stop-1].isoformat()))
        test = f.iloc[start:stop].dropna()
        if test.empty:
            continue
        x = scaler.transform(test)
        result.loc[test.index,'regime'] = [mapping[int(i)] for i in model.predict(x)]
        result.loc[test.index,'distance'] = model.transform(x).min(axis=1)
        result.loc[test.index,'model_version'] = version
    if not profiles:
        raise ValueError('Insufficient complete training features. Disable OI/on-chain or provide more history.')
    return result, pd.concat(profiles,ignore_index=True), {'config':asdict(config),'features':list(f.columns),'fits':fits}

def events(d, regimes, horizon=30, partition='Final holdout', label='regime'):
    """Sample globally non-overlapping completed forward windows, after signal close."""
    if horizon not in [7,14,30]:
        raise ValueError('Supported horizons: 7, 14, 30 days.')
    rows, next_entry = [], 0
    for i in range(len(d)-horizon-1):
        entry, exit_ = i+1, i+1+horizon
        if regimes.partition.iloc[i] != partition or regimes[label].iloc[i]=='Unclassified':
            continue
        if entry<next_entry or regimes.partition.iloc[exit_] != partition:
            continue
        p = d.open.iloc[entry]
        rows.append(dict(signal_date=d.date.iloc[i],entry_date=d.date.iloc[entry],exit_date=d.date.iloc[exit_],
            regime=regimes[label].iloc[i],return_=d.open.iloc[exit_]/p-1,
            adverse_excursion=min(0,d.low.iloc[entry:exit_].min()/p-1)))
        next_entry = exit_
    return pd.DataFrame(rows,columns=['signal_date','entry_date','exit_date','regime','return_','adverse_excursion'])

def interval(values, statistic='mean', repetitions=1000):
    """Moving-block bootstrap over chronological non-overlapping events."""
    a = np.asarray(values,dtype=float)
    if len(a)<5:
        return (np.nan,np.nan)
    rng = np.random.default_rng(42)
    block = max(2,int(np.sqrt(len(a))))
    starts = rng.integers(0,len(a),size=(repetitions,int(np.ceil(len(a)/block))))
    samples = a[(starts[:,:,None]+np.arange(block))%len(a)].reshape(repetitions,-1)[:,:len(a)]
    stats = samples.mean(axis=1) if statistic=='mean' else (samples>0).mean(axis=1)
    return tuple(np.quantile(stats,[.025,.975]))

def summarize(ev):
    rows=[]
    if ev.empty:
        return pd.DataFrame()
    benchmark = ev.return_.mean()
    for name, g in [('All sampled dates',ev)]+list(ev.groupby('regime',sort=True)):
        lo,hi = interval(g.return_)
        wlo,whi = interval(g.return_,'positive')
        rows.append(dict(regime=name,n=len(g),positive_frequency=(g.return_>0).mean(),mean=g.return_.mean(),
            median=g.return_.median(),p05=g.return_.quantile(.05),p95=g.return_.quantile(.95),
            mean_ci_low=lo,mean_ci_high=hi,positive_ci_low=wlo,positive_ci_high=whi,
            mean_adverse=g.adverse_excursion.mean(),difference_from_all=g.return_.mean()-benchmark,
            evidence='Limited sample' if len(g)<30 else 'Descriptive evidence'))
    return pd.DataFrame(rows)

def strategy(d,r,fee_bps=5,slippage_bps=5,partition='Final holdout',instrument='spot_proxy'):
    """Prior day's positive-momentum rule determines next-open long/cash position.

    Each ledger row holds from its open to the following open. Costs apply to
    position changes; terminal holdings are liquidated. No leverage or interest.
    """
    if min(fee_bps,slippage_bps)<0:
        raise ValueError('Costs cannot be negative.')
    if instrument not in ['spot_proxy','perpetual']:
        raise ValueError('Unknown instrument.')
    signal = r.rule.str.startswith('Positive trend') & r.regime.ne('Unclassified')
    allowed = r.partition.eq(partition)
    indices = [i for i in range(1,len(d)-1) if allowed.iloc[i-1] and allowed.iloc[i] and allowed.iloc[i+1]]
    if not indices:
        return pd.DataFrame(),pd.DataFrame()
    pos = signal.shift(1,fill_value=False).iloc[indices].astype(float).to_numpy()
    returns = (d.open.shift(-1)/d.open-1).iloc[indices].to_numpy()
    funding = d.funding.iloc[indices].to_numpy() if instrument=='perpetual' else np.zeros(len(indices))
    if np.isnan(funding).any():
        raise ValueError('Perpetual P&L requires complete realized funding for the evaluation period.')
    cost = (fee_bps+slippage_bps)/10000
    turn = np.abs(np.diff(np.r_[0.,pos]))
    net = (1-turn*cost)*(1+pos*(returns-funding))-1
    net[-1] = (1+net[-1])*(1-pos[-1]*cost)-1
    bh = returns-funding
    bh[0] = (1-cost)*(1+bh[0])-1
    bh[-1] = (1+bh[-1])*(1-cost)-1
    ledger = pd.DataFrame(dict(date=d.date.iloc[[i+1 for i in indices]].to_numpy(),entry_date=d.date.iloc[indices].to_numpy(),position=pos,asset_return=returns,
        funding=funding,turnover=turn,net_return=net,benchmark_return=bh,
        equity=np.cumprod(1+net),benchmark=np.cumprod(1+bh)))
    stats=[]
    for name,col in [('Regime long / cash','net_return'),('Buy and hold','benchmark_return')]:
        a = ledger[col].to_numpy()
        eq = np.r_[1.,np.cumprod(1+a)]
        stats.append(dict(strategy=name,total_return=eq[-1]-1,max_drawdown=(eq/np.maximum.accumulate(eq)-1).min(),
            annualized_volatility=a.std()*np.sqrt(365),days=len(a),
            exposure=pos.mean() if col=='net_return' else 1.))
    return ledger,pd.DataFrame(stats)

def payoff(spot=100.,strike=110.,premium=3.,cost=0.,points=161):
    terminal=np.linspace(0,spot*2,points)
    return pd.DataFrame({'terminal_price':terminal,'spot_return':(terminal-spot)/spot,
        'covered_call_return':(terminal-spot+premium-np.maximum(terminal-strike,0)-cost)/spot})
