# MVP validation record

Validation performed on Windows with Python 3.12. Exact installed versions are recorded in `requirements-lock.txt`.

## Automated verification

`python -m pytest -q`: 14 passed. Includes UI interaction tests, no-future-dependence, frozen holdout model, next-open timing, cost accounting, on-chain availability, missing data, exchange normalization and payoff bounds. The installed pandas/NumPy combination emits timedelta deprecation warnings; these do not affect current test outcomes.

## Live public API verification

Both adapters successfully fetched 730 completed daily BTCUSDT perpetual bars, from 2024-09-18 through 2026-09-17 UTC, during this run:

| Venue | Funding missing | OI missing | Analysis |
| --- | --- | --- | --- |
| Binance | 0% | 96.03% | Base model: 365 classified dates after warm-up |
| Bybit | 0% | 0% | OI-enabled model: 365 classified dates after warm-up |

The Binance final segment contains only five fully completed non-overlapping 30-day events under the entry/exit rules. No return or positive-frequency claim is made from this smoke test. API data snapshots remain local and are not committed.

## UI verification

Streamlit's AppTest successfully renders all five pages, switches the forward horizon and evaluation partition, enables OI on demo data, and selects perpetual accounting. Browser inspection verified the rendered overview, indicator cards, chart, source banner and controls. Mobile-width typography and metric contrast were adjusted during inspection.

## Deferred scope

No automatic scheduled/incremental ingestion, direct paid on-chain integration, historical options quote backtest, production deployment, portfolio optimization, automated feature ablation or independently reconstructed point-in-time archive is claimed. See the README for assumptions and setup.
