"""Portable, bounded CSV bundles for historical options research."""
import argparse
import io
import json
from pathlib import Path
import zipfile
import pandas as pd
from .store import _read

FILES={'quotes.csv','instruments.csv','settlements.csv','spot.csv'}


def read_history_zip(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names=archive.namelist()
        if set(names)!=FILES|{'manifest.json'} or len(names)!=5:
            raise ValueError('History ZIP must contain exactly quotes.csv, instruments.csv, settlements.csv, spot.csv and manifest.json.')
        if sum(info.file_size for info in archive.infolist())>20_000_000:
            raise ValueError('Expanded history bundle exceeds 20 MB; export a shorter range.')
        manifest=json.loads(archive.read('manifest.json'))
        if manifest.get('synthetic') is not False:
            raise ValueError('Historical bundle must declare synthetic=False; provenance still requires review.')
        return {name.removesuffix('.csv'):pd.read_csv(io.BytesIO(archive.read(name))) for name in FILES}


def export_history(root):
    tables={}; lineage={}
    for dataset,key in [('option_quotes','quotes'),('option_instruments','instruments'),('option_settlements','settlements')]:
        frames=[]; versions=[]
        for path in sorted((Path(root)/dataset/'versions').glob('*.json')):
            frame,meta=_read(path,dataset)
            frames.append(frame); versions.append(meta['version_id'])
        if not frames: raise ValueError(f'No archived observations for {dataset}.')
        tables[key]=pd.concat(frames,ignore_index=True)
        lineage[key]=versions
    tables['quotes']=tables['quotes'].drop_duplicates(['instrument','observed_at'],keep='last')
    tables['instruments']=tables['instruments'].drop_duplicates(['instrument','observed_at'],keep='last')
    tables['settlements']=tables['settlements'].sort_values('observed_at').drop_duplicates(['expiry','index_name'],keep='last')
    tables['spot']=tables['quotes'][['observed_at','spot_index']].drop_duplicates()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for key,frame in tables.items(): archive.writestr(key+'.csv',frame.to_csv(index=False))
        archive.writestr('manifest.json',json.dumps({'source':'deribit','synthetic':False,'versions':lineage,
            'note':'Snapshots are observed quotes, not guaranteed fills; validate data rights before sharing.'},indent=2))
    return buffer.getvalue()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    Path(args.output).write_bytes(export_history(args.root))


if __name__=='__main__': main()
