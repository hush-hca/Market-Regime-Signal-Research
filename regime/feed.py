"""Real exchange data with an explicit, provenance-checked snapshot fallback."""
import json
import hashlib
import logging
from pathlib import Path
import pandas as pd
from .data import validate
from .ingest import download

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
    try:
        frame,meta=download('bybit',730)
        return validate(frame),meta,None
    except Exception as exc:
        logging.getLogger(__name__).warning('Exchange refresh failed: %s: %s',type(exc).__name__,exc)
        for candidate,require_digest in [(snapshot,False),(bundled_snapshot,True)]:
            if candidate is None:
                continue
            path=Path(candidate)
            if not path.exists() or not path.with_suffix('.json').exists():
                continue
            try:
                frame,meta=read_snapshot(path,require_digest)
            except (ValueError,OSError) as invalid:
                logging.getLogger(__name__).warning('Rejected snapshot %s: %s',path,invalid)
                continue
            return frame,meta,'Refresh failed. Showing the saved real exchange snapshot; check its date.'
        raise RuntimeError('Exchange data unavailable and no verified real snapshot exists.') from exc
