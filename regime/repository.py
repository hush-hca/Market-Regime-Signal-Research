"""Read the collector's public research-data branch without GitHub credentials."""
import hashlib
import io
import re
import pandas as pd
from .public_sources import session
from .data import validate

ROOT='https://raw.githubusercontent.com/hush-hca/Market-Regime-Signal-Research/research-data/snapshots'


def read_repository_snapshot(dataset,client=None):
    if not re.fullmatch('[a-z][a-z0-9_]{0,63}',dataset):
        raise ValueError('Invalid dataset name.')
    client=client or session()
    def get(path):
        response=client.get(f'{ROOT}/{dataset}/{path}',timeout=(3,8))
        response.raise_for_status()
        return response
    pointer=get('latest.json').json()
    version=pointer.get('version_id','')
    if not re.fullmatch('[0-9a-f]{64}',version):
        raise ValueError('Invalid snapshot pointer.')
    meta=get(f'versions/{version}.json').json()
    if meta.get('dataset')!=dataset or meta.get('version_id')!=version or meta.get('synthetic') is not False:
        raise ValueError('Invalid repository provenance.')
    payload=get(f'versions/{version}.parquet').content
    if hashlib.sha256(payload).hexdigest()!=meta.get('sha256'):
        raise ValueError('Repository snapshot checksum mismatch.')
    frame=pd.read_parquet(io.BytesIO(payload))
    if len(frame)!=meta.get('rows') or frame.empty:
        raise ValueError('Repository snapshot row count mismatch.')
    if dataset.startswith('market_'):
        if meta.get('source')!=dataset.removeprefix('market_'):
            raise ValueError('Snapshot venue mismatch.')
        frame=validate(frame)
    return frame,{**meta,'delivery':'GitHub research-data snapshot'}
