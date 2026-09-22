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
    frame,meta,notice=load_market(path)
    assert len(frame)==730 and meta['source']=='bybit' and 'Refresh failed' in notice
    metadata.write_text(json.dumps({'synthetic':True,'source':'synthetic'}))
    with pytest.raises(ValueError,match='not verified'): load_market(path)
