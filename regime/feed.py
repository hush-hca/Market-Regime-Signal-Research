"""Real exchange data with an explicit, provenance-checked snapshot fallback."""
import json
import hashlib
import logging
import os
from pathlib import Path
import pandas as pd
from .data import validate
from .ingest import download
from .store import read_latest
from .repository import read_repository_snapshot

BUNDLED_SNAPSHOT=Path(__file__).resolve().parents[1]/'bootstrap'/'bybit.parquet'

def read_snapshot(path, require_digest=False):
    path=Path(path)
    meta=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
    if meta.get('synthetic') is not False or meta.get('source') not in ['binance','bybit']:
        raise ValueError('Fallback snapshot is not verified exchange data.')
    digest=meta.get('sha256')
    if require_digest and not digest:
        raise ValueError('Bundled snapshot is missing its integrity digest.')
    if digest and hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise ValueError('Snapshot integrity check failed.')
    return validate(pd.read_parquet(path)),meta

def load_market(snapshot='data/market.parquet', bundled_snapshot=BUNDLED_SNAPSHOT):
    last_error=None
    diagnostics=[]
    stored=[]
    for venue in ['bybit','binance']:
        try:
            root=os.environ.get('REGIME_SNAPSHOT_ROOT')
            frame,meta=(read_latest(root,'market_'+venue) if root else read_repository_snapshot('market_'+venue))
            if frame.date.max()>=pd.Timestamp.now(tz='UTC').normalize()-pd.Timedelta(days=2):
                return frame,meta,None
            stored.append((frame,meta))
        except (OSError,ValueError,KeyError) as exc:
            diagnostics.append(f'Stored {venue}: {type(exc).__name__}: {exc}')
    for venue in ['bybit','binance']:
        try:
            frame,meta=download(venue,730)
            return validate(frame),meta,None
        except Exception as exc:
            last_error=exc
            diagnostics.append(f'{venue}: {type(exc).__name__}: {exc}')
            logging.getLogger(__name__).warning('%s refresh failed: %s: %s',venue,type(exc).__name__,exc)
    if stored:
        frame,meta=max(stored,key=lambda item:item[0].date.max())
        return frame,meta,'Refresh failed. Showing the saved real exchange snapshot; check its date.'
    for candidate,require_digest in [(snapshot,False),(bundled_snapshot,True)]:
        if candidate is None:
            continue
        path=Path(candidate)
        if not path.exists() or not path.with_suffix('.json').exists():
            diagnostics.append(f'Snapshot or provenance file missing: {path.resolve()}')
            continue
        try:
            frame,meta=read_snapshot(path,require_digest)
        except (ValueError,OSError) as invalid:
            diagnostics.append(f'Snapshot rejected: {path.resolve()}: {invalid}')
            logging.getLogger(__name__).warning('Rejected snapshot %s: %s',path,invalid)
            continue
        return frame,meta,'Refresh failed. Showing the saved real exchange snapshot; check its date.'
    detail=RuntimeError('\n'.join(diagnostics))
    detail.__cause__=last_error
    raise RuntimeError('Exchange data unavailable and no verified real snapshot exists. '
        'Redeploy the latest repository including bootstrap/bybit.parquet and bootstrap/bybit.json. '
        'See Technical details for the missing file or validation failure.') from detail
