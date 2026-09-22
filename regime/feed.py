"""Real exchange data with an explicit, provenance-checked snapshot fallback."""
import json
from pathlib import Path
import pandas as pd
from .data import validate
from .ingest import download

def load_market(snapshot='data/market.parquet'):
    try:
        frame,meta=download('bybit',730)
        return validate(frame),meta,None
    except Exception as exc:
        path=Path(snapshot)
        if not path.exists() or not path.with_suffix('.json').exists():
            raise RuntimeError('Exchange data unavailable and no verified real snapshot exists.') from exc
        meta=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
        if meta.get('synthetic') is not False or meta.get('source') not in ['binance','bybit']:
            raise ValueError('Fallback snapshot is not verified exchange data.') from exc
        return validate(pd.read_parquet(path)),meta,'Refresh failed. Showing the saved real exchange snapshot; check its date.'
