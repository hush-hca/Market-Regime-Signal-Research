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

## Korean localization follow-up

The expanded suite passes 16 tests. Language tests verify Korean tabs and warnings, canonical data preservation, unchanged metric values and retained horizon/fee settings when switching both ways. Browser inspection verified Korean selections, chart legends and tables. Metric cards now wrap at narrow widths. Export schemas and raw provenance identifiers remain stable in English; framework controls and raw diagnostic details may remain English.

## Real-data default

The dashboard now defaults to an automatic real Bybit API fetch with a one-hour cache and manual refresh. The synthetic choice is removed. A verified local snapshot is used with a warning only if the API fails. The local Bybit snapshot contains 730 completed daily bars through 2026-09-17 UTC, with no missing daily funding or OI. A fresh download attempted on 2026-09-22 was blocked by this execution environment's network restrictions, so the existing real snapshot was retained with its original retrieval time and a stale-data warning. New deployments need API access or an uploaded/saved dataset. Offline tests simulate API transport using generated fixtures; these are not production inputs. Regression tests cover API failure with no snapshot and rejection of a synthetic fallback snapshot.
