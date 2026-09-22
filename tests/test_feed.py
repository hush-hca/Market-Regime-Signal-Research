import json
import pytest
from regime.data import demo
from regime.feed import load_market

def test_failure_uses_only_verified_real_snapshot(tmp_path,monkeypatch):
    import regime.feed
    def offline(*args): raise ConnectionError('offline')
    monkeypatch.setattr(regime.feed,'download',offline)
    path=tmp_path/'market.parquet'
    demo(730).to_parquet(path,index=False)
    metadata=path.with_suffix('.json')
    metadata.write_text(json.dumps({'synthetic':False,'source':'bybit'}))
    frame,meta,notice=load_market(path,bundled_snapshot=None)
    assert len(frame)==730 and meta['source']=='bybit' and 'Refresh failed' in notice
    metadata.write_text(json.dumps({'synthetic':True,'source':'synthetic'}))
    with pytest.raises(RuntimeError,match='no verified'): load_market(path,bundled_snapshot=None)

def test_bundled_real_snapshot_works_without_local_data(tmp_path,monkeypatch):
    import regime.feed
    def offline(*args): raise ConnectionError('blocked in deployment')
    monkeypatch.setattr(regime.feed,'download',offline)
    monkeypatch.chdir(tmp_path)
    frame,meta,notice=load_market()
    assert len(frame)==730
    assert meta['synthetic'] is False and meta['source']=='bybit'
    assert frame.date.max().strftime('%Y-%m-%d')=='2026-09-17'
    assert 'Refresh failed' in notice

def test_corrupt_bundled_snapshot_is_rejected(tmp_path):
    from regime.feed import read_snapshot
    path=tmp_path/'broken.parquet'
    path.write_bytes(b'corrupt')
    path.with_suffix('.json').write_text(json.dumps({'synthetic':False,'source':'bybit','sha256':'0'*64}))
    with pytest.raises(ValueError,match='integrity'): read_snapshot(path,require_digest=True)

def test_missing_bundle_explains_deployment_repair(tmp_path,monkeypatch):
    import regime.feed
    def offline(*args): raise ConnectionError('exchange blocked')
    monkeypatch.setattr(regime.feed,'download',offline)
    absent=tmp_path/'bootstrap'/'bybit.parquet'
    with pytest.raises(RuntimeError,match='Redeploy') as error:
        load_market(tmp_path/'local.parquet',bundled_snapshot=absent)
    assert str(absent.resolve()) in str(error.value.__cause__)
    assert 'bybit: ConnectionError' in str(error.value.__cause__)
    assert 'binance: ConnectionError' in str(error.value.__cause__)

def test_isolated_deployment_tree_has_offline_fallback(tmp_path):
    import shutil
    import subprocess
    import sys
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    # Only files shipped in the container; no local data folder or original cwd.
    shutil.copytree(root/'regime',tmp_path/'regime',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(root/'bootstrap',tmp_path/'bootstrap')
    script="""
import regime.feed
def offline(*args): raise ConnectionError('deployment cannot reach exchange')
regime.feed.download=offline
frame,meta,notice=regime.feed.load_market()
assert len(frame)==730 and meta['synthetic'] is False
assert frame.date.max().strftime('%Y-%m-%d')=='2026-09-17'
assert 'Refresh failed' in notice
"""
    result=subprocess.run([sys.executable,'-c',script],cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
