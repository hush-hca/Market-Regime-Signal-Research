# Regime Atlas

[한국어](README.ko.md) · [Live dashboard](https://market-regime-research-choas-projects-d5c2c283.vercel.app/)

BTC regime research using actual exchange and on-chain observations. English/Korean Streamlit dashboard; no production demo data, assumed option premiums, preset execution costs or fabricated forward results.

## Problem Definition
Traders need to distinguish a market description from evidence of a trading advantage. The dashboard connects explicit model inputs, their freshness, historical outcome distributions and a timestamped forward paper record.

## Hypothesis
Price, derivatives and on-chain features may identify states with different subsequent outcomes. This is unproven. Negative funding plus low MVRV does not establish capital inflow, and cluster names are not trade recommendations.

Choose a model explicitly:
- **Price only** (default): 7/30-day momentum, 30-day volatility and observed volume z-score.
- **Price + derivatives**: adds seven-day funding average and OI change.
- **Price + derivatives + on-chain**: adds MVRV and exchange net flows. SOPR is unavailable and is not silently imputed.

Historical models use past-only standardization, four KMeans clusters, a 365-day warm-up, 90-day refits and an already-inspected final 180-day frozen segment. Missing inputs produce unclassified dates; models never switch automatically. A fit needs 180 complete training rows and the historical workflow needs at least 605 daily rows.

## Data
GitHub Actions collects real observations hourly into the `research-data` branch. The dashboard reads checksum-verified snapshots, then APIs or verified historical fallback data if necessary. Binance API failures can fall back to official checksum-verified USD-M archives: monthly/daily prices, daily OI and monthly funding. Publication delays remain visible. A fresh price does not imply fresh funding.

Coin Metrics provides real MVRV and exchange-flow observations under CC BY-NC 4.0 for noncommercial research. Historical values can be revised. The explicit 48-hour on-chain alignment delay is a research policy, not a verified first-publication timestamp. Deribit supplies actual current option quotes and collected terms/settlements. No hypothetical payoff curves or claimed option returns are displayed.

The data-health panel separates original observation dates, market-aligned usable dates, receipt times, missingness and collection errors. Older than three calendar days is an operational stale-data flag. The bundled Bybit fallback ends 2026-09-17 and is clearly historical. Unverified CSV uploads are disabled in this actual-only release.

## Validation
Evidence cards show each regime's completed events, sampled episodes, evaluation dates, mean/median, positive frequency, same-eligible-date baseline and descriptive difference. Approximate bootstrap mean intervals are withheld below five events; fewer than 30 is labeled limited. These policies do not establish significance. Nonoverlapping historical event samples differ from the overlapping forward horizons.

The **forward paper ledger** freezes one numerical model artifact per venue/model when first registered. It stores input versions, feature values, registration/recording timestamps and model ID. It never backfills historical predictions or refits the artifact. The fixed paper rule is long on positive observed 30-day momentum with complete inputs, otherwise abstain. Entry is the first UTC open strictly after recording. Actual later bars resolve 7/14/30-day outcomes, and previously recorded outcomes remain unchanged. Returns are gross perpetual-candle price changes, excluding funding, fees, slippage and interest; they are not fills or executable net P&L. Missing outcomes stay pending. New feature definitions require a deliberate new protocol.

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements-lock.txt
streamlit run app.py
python -m pytest -q
python -m regime.report --output data/research-report
```

Python 3.12 is tested. For macOS/Linux use `source .venv/bin/activate`. Live reads need network access; tests isolate transport and UI tests use verified real bundled observations. Existing mathematical unit fixtures are software tests, never production datasets or evidence.

```powershell
python -m regime.collect --root data/archive
python -m regime.ingest --venue binance --days 730
```

Use `REGIME_SNAPSHOT_ROOT` for a local durable archive. See [operations](docs/operations.md), [forward protocol](docs/forward-protocol.md), [research report](docs/research-report.md) and [Vercel deployment](docs/vercel-deployment.md).

## Limitations
No trading edge has been demonstrated. The checked-in report has only five nonoverlapping monthly events per feature set; regime-specific estimates are weak. Historical current-vintage data is not a reconstructed point-in-time feed. Bybit may reject the collector; Binance monthly funding may lag daily prices. GitHub scheduling is best-effort. Forward evidence takes real elapsed time to accumulate. SOPR access, executed fill/cost evidence and sufficient historical options coverage are still missing. No automatic orders or paid services are configured.
