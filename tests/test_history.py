import io
import zipfile
import pandas as pd
import pytest


def test_import_rejects_missing_or_unexpected_members():
    from regime.history import read_history_zip
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as archive: archive.writestr('../quotes.csv','x')
    with pytest.raises(ValueError,match='exactly'): read_history_zip(buffer.getvalue())


def test_archive_exports_verified_versions(tmp_path):
    from regime.history import export_history,read_history_zip
    from regime.store import write_snapshot
    time=pd.Timestamp('2025-01-01',tz='UTC')
    tables={'option_quotes':pd.DataFrame(dict(instrument=['BTC-C'],observed_at=[time],quote_time=[time],spot_index=[100.],bid_btc=[.03],ask_btc=[.04])),
        'option_instruments':pd.DataFrame(dict(instrument=['BTC-C'],observed_at=[time],expiry=[time+pd.Timedelta(days=30)],strike=[110.])),
        'option_settlements':pd.DataFrame(dict(expiry=[time+pd.Timedelta(days=30)],index_name=['btc_usd'],delivery_price=[120.],observed_at=[time+pd.Timedelta(days=31)]))}
    for dataset,frame in tables.items():
        write_snapshot(frame,dict(dataset=dataset,source='deribit',synthetic=False,retrieved_at=time.isoformat()),tmp_path)
    payload=export_history(tmp_path)
    data=read_history_zip(payload)
    assert data['quotes'].iloc[0].bid_btc==.03 and len(data['spot'])==1
