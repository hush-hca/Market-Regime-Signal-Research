"""Immutable, checksummed snapshots with atomic publication; one writer per root."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import uuid
import pandas as pd
from .data import validate


def dataset_dir(root, dataset):
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}',dataset):
        raise ValueError('Invalid dataset name.')
    return Path(root)/dataset


def atomic_json(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('w',encoding='utf-8') as handle:
            json.dump(value,handle,sort_keys=True,indent=2,allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)


def write_snapshot(frame,metadata,root):
    metadata=dict(metadata)
    directory=dataset_dir(root,metadata['dataset'])
    if metadata.get('synthetic') is not False or not metadata.get('source'):
        raise ValueError('Snapshots require a real source and synthetic=False.')
    if frame.empty:
        raise ValueError('Empty snapshots cannot replace valid data.')
    retrieved=pd.Timestamp(metadata['retrieved_at'])
    if pd.isna(retrieved) or retrieved.tzinfo is None:
        raise ValueError('retrieved_at requires a timezone.')
    if metadata['dataset'].startswith('market_'):
        frame=validate(frame)
    buffer=io.BytesIO()
    frame.to_parquet(buffer,index=False)
    payload=buffer.getvalue()
    digest=hashlib.sha256(payload).hexdigest()
    version=hashlib.sha256((digest+json.dumps(metadata,sort_keys=True,allow_nan=False)).encode()).hexdigest()
    versions=directory/'versions'
    versions.mkdir(parents=True,exist_ok=True)
    path=versions/(version+'.json')
    lock=directory/'.writer.lock'
    # A second writer fails rather than publishing an out-of-order pointer.
    with lock.open('x'):
        pass
    try:
        manifest={**metadata,'sha256':digest,'version_id':version,'rows':len(frame),
                  'validation':'passed','schema_version':1}
        parquet=path.with_suffix('.parquet')
        if not path.exists():
            temporary=parquet.with_suffix('.tmp')
            try:
                temporary.write_bytes(payload)
                os.replace(temporary,parquet)
            finally:
                temporary.unlink(missing_ok=True)
            atomic_json(path,manifest)
        else:
            _read(path,metadata['dataset'])
        atomic_json(directory/'latest.json',{'version_id':version})
        return str(path)
    finally:
        lock.unlink(missing_ok=True)


def _read(path,dataset):
    meta=json.loads(path.read_text(encoding='utf-8'))
    if meta.get('dataset')!=dataset or meta.get('synthetic') is not False or meta.get('version_id')!=path.stem:
        raise ValueError('Invalid snapshot manifest.')
    data=path.with_suffix('.parquet').read_bytes()
    if hashlib.sha256(data).hexdigest()!=meta.get('sha256'):
        raise ValueError('Snapshot checksum mismatch.')
    frame=pd.read_parquet(io.BytesIO(data))
    if len(frame)!=meta.get('rows') or frame.empty:
        raise ValueError('Snapshot row count mismatch.')
    if dataset.startswith('market_'):
        frame=validate(frame)
    return frame,meta


def read_latest(root,dataset):
    directory=dataset_dir(root,dataset)
    pointer=json.loads((directory/'latest.json').read_text(encoding='utf-8'))
    version=pointer.get('version_id','')
    if not re.fullmatch('[0-9a-f]{64}',version):
        raise ValueError('Invalid snapshot pointer.')
    try:
        frame,meta=_read(directory/'versions'/(version+'.json'),dataset)
        return frame,{**meta,'recovered_from_corruption':False}
    except (OSError,ValueError):
        candidates=[]
        for path in (directory/'versions').glob('*.json'):
            try:
                frame,meta=_read(path,dataset)
                candidates.append((pd.Timestamp(meta['retrieved_at']),frame,meta))
            except (OSError,ValueError,KeyError):
                continue
        if not candidates:
            raise ValueError('No intact snapshot versions available.')
        _,frame,meta=max(candidates,key=lambda item:item[0])
        return frame,{**meta,'recovered_from_corruption':True}
