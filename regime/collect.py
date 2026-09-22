"""Run outside Streamlit: python -m regime.collect --root /durable/snapshots."""
import argparse
import json
from pathlib import Path
import pandas as pd
from .data import validate
from .ingest import download
from .binance_archive import download_archive
from .onchain import load_coinmetrics
from .options import load_quote_archive
from .store import write_snapshot,read_latest,atomic_json


def merge_market(old,new,as_of):
    new=new.copy()
    new['date']=pd.to_datetime(new.date,utc=True)
    if old is not None:
        old=old.set_index('date')
        new=new.set_index('date')
        # Retain earlier observed funding/OI only when the refresh omits them.
        for field in ['funding','oi']:
            if field in new and field in old:
                new[field]=new[field].combine_first(old[field])
        new=pd.concat([old.loc[~old.index.isin(new.index)],new]).sort_index().reset_index()
    cutoff=pd.Timestamp(as_of)
    cutoff=cutoff.tz_localize('UTC') if cutoff.tzinfo is None else cutoff.tz_convert('UTC')
    return validate(new[new.date<cutoff.normalize()])


def collect_once(as_of,root):
    now=pd.Timestamp(as_of)
    now=now.tz_localize('UTC') if now.tzinfo is None else now.tz_convert('UTC')
    report={'as_of':now.isoformat(),'datasets':{}}
    def publish(dataset,frame,meta):
        path=write_snapshot(frame,{**meta,'dataset':dataset,'synthetic':False,
            'retrieved_at':meta.get('retrieved_at') or now.isoformat()},root)
        report['datasets'][dataset]={'status':'ok','manifest':str(Path(path).relative_to(root)),'rows':len(frame)}
    for venue in ['bybit','binance']:
        dataset='market_'+venue
        try:
            try: old,_=read_latest(root,dataset)
            except (OSError,ValueError): old=None
            days=60 if old is not None else 730
            try:
                frame,meta=download(venue,days,raw_dir=str(Path(root)/'raw'))
            except Exception as api_error:
                if venue!='binance': raise
                frame,meta=download_archive(days,as_of=now)
                meta['api_error']=f'{type(api_error).__name__}: {api_error}'
            frame=merge_market(old,frame,now)
            publish(dataset,frame,{**meta,'observation_end':frame.date.max().isoformat(),
                'vintage':'current; revisions retained as immutable snapshots'})
            report['datasets'][dataset]['stale']=bool(now-(frame.date.max()+pd.Timedelta(days=1))>pd.Timedelta(hours=36))
            report['datasets'][dataset]['missing_funding_rows']=int(frame.funding.isna().sum())
        except Exception as exc:
            report['datasets'][dataset]={'status':'error','error':f'{type(exc).__name__}: {exc}'}
    try:
        old,meta=read_latest(root,'onchain')
        recent=pd.Timestamp(meta['retrieved_at']).date()==now.date()
    except (OSError,ValueError,KeyError): recent=False
    if recent:
        report['datasets']['onchain']={'status':'cached','rows':len(old)}
    else:
        try:
            frame,meta=load_coinmetrics(now-pd.Timedelta(days=1095),now)
            if meta.get('fallback_used'):
                raise ValueError('Collector refresh used fallback; preserving previous live snapshot.')
            publish('onchain',frame,meta)
        except Exception as exc:
            report['datasets']['onchain']={'status':'error','error':f'{type(exc).__name__}: {exc}'}
    try:
        archive=load_quote_archive()
        for dataset,frame in archive.items():
            try:
                if frame.empty:
                    raise ValueError(frame.attrs.get('error','No observations returned.'))
                publish(dataset,frame,{'source':'deribit','vintage':'observed live',
                    'license':'Provider public API terms; review before redistribution'})
            except (OSError,ValueError,KeyError) as exc:
                report['datasets'][dataset]={'status':'error','error':f'{type(exc).__name__}: {exc}'}
    except Exception as exc:
        report['datasets']['options']={'status':'error','error':f'{type(exc).__name__}: {exc}'}
    atomic_json(Path(root)/'collection-status.json',report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    args=parser.parse_args()
    report=collect_once(pd.Timestamp.now(tz='UTC').isoformat(),args.root)
    print(json.dumps(report,indent=2))
    if any(value['status']=='error' for value in report['datasets'].values()):
        raise SystemExit(2)


if __name__=='__main__': main()
