"""As-recorded frozen models and forward paper observations, never backfilled."""
import hashlib
import json
import os
import inspect
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from .store import read_latest,write_snapshot
from .repository import read_repository_snapshot
from .readiness import MODELS,model_features
from .research import LABELS,features
from .data import enrich

PROTOCOL='frozen-kmeans-v1'


def feature_fingerprint():
    from . import readiness,data
    definition=inspect.getsource(features)+inspect.getsource(model_features)+inspect.getsource(enrich)
    definition+=json.dumps({'models':readiness.MODELS,'price_features':readiness.PRICE,'onchain_columns':data.ONCHAIN},sort_keys=True)
    return hashlib.sha256(definition.replace('\r\n','\n').encode()).hexdigest()


def optional(root,dataset):
    try:
        frame,meta=read_latest(root,dataset)
        if dataset.startswith('forward_'):
            if meta.get('recovered_from_corruption'):
                raise ValueError('Damaged forward history requires explicit recovery; refusing rollback')
            # A valid but rolled-back pointer must not erase later immutable records.
            for path in (Path(root)/dataset/'versions').glob('*.json'):
                version_meta=json.loads(path.read_text(encoding='utf-8'))
                if pd.Timestamp(version_meta['retrieved_at'])>pd.Timestamp(meta['retrieved_at']):
                    raise ValueError('Rolled-back forward history pointer; refusing to rewrite history')
        return frame,meta
    except FileNotFoundError:
        if dataset.startswith('forward_') and (Path(root)/dataset).exists():
            raise ValueError('Existing forward history has a missing pointer; refusing reinitialization')
        return pd.DataFrame(),{}


def freeze(d,name,meta,now):
    f=model_features(d,name).dropna()
    if len(f)<180: return None
    scaler=StandardScaler().fit(f)
    model=KMeans(n_clusters=4,n_init=10,random_state=42).fit(scaler.transform(f))
    centers=scaler.inverse_transform(model.cluster_centers_)
    order=np.argsort(centers[:,list(f.columns).index('momentum_30')])
    labels=['']*4
    for rank,index in enumerate(order): labels[int(index)]=LABELS[rank]
    payload=dict(protocol=PROTOCOL,feature_definition=feature_fingerprint(),model=name,venue=meta['source'],registered_at=now.isoformat(),
        training_snapshot=meta['version_id'],train_end=d.date.max().isoformat(),train_rows=len(f),
        features=list(f.columns),mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),
        centers=model.cluster_centers_.tolist(),labels=labels,
        entry_rule='First UTC daily open strictly after recorded_at',horizons=[7,14,30],
        paper_rule='Long if observed momentum_30 is positive; otherwise abstain. No executed orders.',
        accounting='Gross perpetual-candle price change only; funding, fees, slippage and interest excluded')
    encoded=json.dumps(payload,sort_keys=True,allow_nan=False)
    return dict(model_id=hashlib.sha256(encoded.encode()).hexdigest(),model=name,venue=meta['source'],
        registered_at=now.isoformat(),artifact=encoded)


def collect_forward(root,as_of):
    now=pd.Timestamp(as_of)
    if now.tzinfo is None: raise ValueError('Forward recording requires timezone')
    now=now.tz_convert('UTC')
    models,_=optional(root,'forward_models')
    ledger,_=optional(root,'forward_ledger')
    model_rows=models.to_dict('records'); rows=ledger.to_dict('records')
    if rows and not set(ledger.model_id)<=set(models.get('model_id',[])):
        raise ValueError('Inconsistent forward history: ledger references missing models')
    chain,chain_meta=optional(root,'onchain')
    for venue in ['bybit','binance']:
        d,meta=optional(root,'market_'+venue)
        if d.empty: continue
        if meta.get('source')!=venue or meta.get('synthetic') is not False:
            raise ValueError('Forward source provenance mismatch')
        if pd.Timestamp(meta['retrieved_at'])>now: raise ValueError('Future market snapshot receipt')
        d=d[d.date+pd.Timedelta(days=1)<=now].reset_index(drop=True)
        if d.empty: continue
        prices=d.set_index('date')
        # Resolve existing records from actual later bars; keep completed observations immutable.
        for row in rows:
            if row['venue']!=venue or row['status'] not in ['awaiting_entry','awaiting_exit']: continue
            entry=pd.Timestamp(row['entry_date']); exit_=pd.Timestamp(row['exit_date'])
            if pd.isna(row['entry_price']) and entry in prices.index:
                row.update(entry_price=float(prices.loc[entry,'open']),entry_snapshot=meta['version_id'],status='awaiting_exit')
            if pd.notna(row['entry_price']) and exit_ in prices.index:
                change=float(prices.loc[exit_,'open'])/row['entry_price']-1
                row.update(exit_price=float(prices.loc[exit_,'open']),asset_gross_return=change,
                    paper_gross_return=change if row['paper_action']=='Long' else None,
                    outcome_snapshot=meta['version_id'],resolved_at=now.isoformat(),status='completed')
        if now-(d.date.max()+pd.Timedelta(days=1))>pd.Timedelta(hours=36): continue
        if not chain.empty and pd.Timestamp(chain_meta['retrieved_at'])<=now:
            d=enrich(d,chain.to_csv(index=False))
        for name in MODELS:
            match=[m for m in model_rows if m['venue']==venue and m['model']==name]
            if match: registered=match[0]
            else:
                registered=freeze(d,name,meta,now)
                if registered is None: continue
                artifact=json.loads(registered['artifact'])
                if name==MODELS[2]:
                    artifact['onchain_training_snapshot']=chain_meta.get('version_id')
                    registered['artifact']=json.dumps(artifact,sort_keys=True,allow_nan=False)
                    registered['model_id']=hashlib.sha256(registered['artifact'].encode()).hexdigest()
                model_rows.append(registered)
            model_id=registered['model_id']
            artifact=json.loads(registered['artifact'])
            if artifact['protocol']!=PROTOCOL: raise ValueError('Unsupported frozen protocol; do not overwrite registry')
            if artifact.get('feature_definition')!=feature_fingerprint():
                raise ValueError('Frozen feature definition changed; create an explicitly versioned protocol')
            if pd.Timestamp(registered['registered_at'])>now: raise ValueError('Recording before model registration')
            signal_date=d.date.iloc[-1].isoformat()
            previous=[pd.Timestamp(row['signal_date']) for row in rows if row['model_id']==model_id]
            if previous and pd.Timestamp(signal_date)<=max(previous): continue
            feature=model_features(d,name).iloc[-1].reindex(artifact['features'])
            ready=bool(feature.notna().all())
            regime='Unclassified'
            if ready:
                x=(feature.to_numpy()-np.asarray(artifact['mean']))/np.asarray(artifact['scale'])
                cluster=int(np.linalg.norm(np.asarray(artifact['centers'])-x,axis=1).argmin())
                regime=artifact['labels'][cluster]
            for horizon in artifact['horizons']:
                entry=now.normalize()+pd.Timedelta(days=1)
                key=f'{model_id}:{signal_date}:{horizon}'
                rows.append(dict(record_id=hashlib.sha256(key.encode()).hexdigest(),model_id=model_id,
                    model=name,venue=venue,signal_date=signal_date,recorded_at=now.isoformat(),
                    source_snapshot=meta['version_id'],onchain_snapshot=chain_meta.get('version_id') if name==MODELS[2] else None,
                    feature_values=json.dumps({key:float(value) if pd.notna(value) else None for key,value in feature.items()},allow_nan=False),
                    regime=regime,horizon_days=horizon,paper_action=('Long' if feature.momentum_30>0 else 'Abstain') if ready else 'Unavailable',
                    entry_date=entry.isoformat() if ready else None,
                    exit_date=(entry+pd.Timedelta(days=horizon)).isoformat() if ready else None,
                    entry_price=None,exit_price=None,asset_gross_return=None,paper_gross_return=None,
                    entry_snapshot=None,outcome_snapshot=None,resolved_at=None,
                    status='awaiting_entry' if ready else 'missing_inputs'))
    info=dict(source='as-recorded collector',synthetic=False,retrieved_at=now.isoformat(),protocol=PROTOCOL,
        note='Paper observations, not actual fills. Overlapping horizons; gross price changes exclude funding and costs.')
    # Publish registry before ledger, so every referenced model artifact already exists.
    if model_rows: write_snapshot(pd.DataFrame(model_rows),{**info,'dataset':'forward_models'},root)
    if rows: write_snapshot(pd.DataFrame(rows),{**info,'dataset':'forward_ledger'},root)
    return dict(models=len(model_rows),records=len(rows),completed=sum(row['status']=='completed' for row in rows))


def read_forward(root=None):
    root=root or os.environ.get('REGIME_SNAPSHOT_ROOT')
    reader=(lambda dataset:optional(root,dataset)) if root else read_repository_snapshot
    ledger,meta=reader('forward_ledger')
    models,model_meta=reader('forward_models')
    if not set(ledger.model_id)<=set(models.model_id): raise ValueError('Missing forward model artifact')
    return ledger,models,meta
