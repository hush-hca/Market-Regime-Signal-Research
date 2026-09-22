"""Reproduce the checked-in exploratory report without network access."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
from .data import enrich
from .feed import read_snapshot,BUNDLED_SNAPSHOT
from .onchain import BUNDLE
from .evaluation import evaluate_feature_sets
from .build import build_id


def generate_report(output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    daily,market_meta=read_snapshot(BUNDLED_SNAPSHOT,require_digest=True)
    chain_meta=json.loads(BUNDLE.with_suffix('.json').read_text(encoding='utf-8'))
    if hashlib.sha256(BUNDLE.read_bytes()).hexdigest()!=chain_meta['sha256']:
        raise ValueError('On-chain report input failed checksum verification.')
    daily=enrich(daily,pd.read_parquet(BUNDLE).to_csv(index=False))
    summaries=[]; coverage=[]; manifest={'source':market_meta,'onchain':chain_meta,'build_id':build_id(),
        'evaluation_status':'Exploratory; previously inspected holdout','horizons':{}}
    for horizon in [7,14,30]:
        result=evaluate_feature_sets(daily,horizon)
        summaries.append(result['summary'].assign(horizon=horizon))
        coverage.append(result['coverage'].assign(horizon=horizon))
        manifest['horizons'][str(horizon)]=result['manifest']
        ledger=pd.concat([frame.assign(feature_set=name) for name,frame in result['events'].items()],ignore_index=True)
        ledger.to_csv(output/f'events-{horizon}d.csv',index=False)
    pd.concat(summaries,ignore_index=True).to_csv(output/'summary.csv',index=False)
    pd.concat(coverage,ignore_index=True).to_csv(output/'coverage.csv',index=False)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='data/research-report')
    args=parser.parse_args()
    generate_report(args.output)
    print(f'Report written to {args.output}; exploratory, current-vintage data.')


if __name__=='__main__': main()
