# Regime Atlas

[한국어 설명](README.ko.md) · [운영 전환 로드맵](docs/roadmap.ko.md)

Use **Language / 언어** in the sidebar to switch between English and Korean. Display labels, explanations, charts and validation messages are localized; canonical CSV fields and research identifiers remain unchanged. Widget selections survive language changes. Some built-in Streamlit/Plotly controls and raw technical details remain in English.

**AI market regime identification and signal research for BTC.** A Streamlit dashboard combining causal features, walk-forward clustering, transparent conditional statistics and an explicit long/cash ledger.

The default view **automatically fetches real Bybit BTCUSDT data** (730 completed daily bars, funding and available OI). Results are cached for up to one hour during app use; use **Refresh exchange data** to retry immediately. If the API is inaccessible, a previously saved, provenance-checked Binance/Bybit snapshot is shown with a warning and its original date. Without one, the app displays an error. There is no synthetic demo option or synthetic fallback. The covered-call page remains a payoff simulator, not a historical options backtest.

## Quick start

For Vercel, see [container deployment and verification](docs/vercel-deployment.md). The configuration uses Vercel's container/WebSocket beta; sessions and runtime files are ephemeral, and remote behavior must be verified after deployment.

Python 3.12 is the tested runtime. Run from the repository root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The default API view needs outbound network access to Bybit; regional restrictions may prevent access. A small **real historical fallback** is included in `bootstrap/` and copied into the deployment image: 730 Bybit BTCUSDT daily bars through **2026-09-17 UTC**, collected on 2026-09-18. Its metadata records source, retrieval time and SHA-256 integrity digest. If API access fails, the app first tries a verified local snapshot, then this bundled snapshot, always showing a warning and the data date. It never presents this archive as live or generates replacement prices. Other raw responses and local snapshots remain excluded from Git.

For the exact tested environment, install `requirements-lock.txt` instead. The lock was generated on Windows/Python 3.12; use the supported ranges in `requirements.txt` if platform-specific transitive packages need different resolution.

Fetch real BTCUSDT perpetual data, then select **Local snapshot**:

```bash
python -m regime.ingest --venue binance --days 730
# Or use Bybit (overwrites the local snapshot with that venue):
python -m regime.ingest --venue bybit --days 730
python -m pytest -q
```

The sidebar also offers **Fetch public API** and **Upload CSV**. Public endpoints can be blocked by geography, networking or exchange policy. Errors are shown; the app never silently substitutes synthetic results for real data.

## Problem Definition

Crypto indicators describe different aspects of positioning and valuation, but isolated charts rarely quantify what happened under comparable historical conditions. This project links a documented regime definition to forward outcome distributions, sample sizes and reproducible trading assumptions.

Users can inspect five pages: overview, historical outcomes, strategy lab, options payoff, and data/methodology. Every indicator has a plain-language explanation and a limitation. Export a ZIP containing the dataset hash, source information, configuration, fit windows, regime labels, centroids, event statistics and trading ledger.

## Hypothesis

1. Price and funding features identify recurring descriptive market states.
2. Some states may have different subsequent 7-, 14- or 30-day return distributions.
3. Optional OI and on-chain features may add information beyond price and funding.

These are hypotheses, not reported discoveries. No model setting is selected by maximizing future return. Negative funding plus low valuation does not establish that sidelined capital is entering the market.

### Implemented models

- **Rules:** combinations of 30-day momentum and seven-day average funding signs.
- **ML:** four-cluster K-means, deterministic seed 42 and ten initializations. Standardization fits exclusively on earlier complete observations. Warm-up is 365 days, expanding refits occur every 90 days, and the final 180 days use a frozen model fitted before that segment.
- **Features:** 7-/30-day momentum, 30-day annualized volatility, seven-day funding average and rolling log-volume z-score. Optional seven-day OI change and uploaded on-chain columns.
- **Cluster names:** rank training centroids by momentum. Defensive/Expansion are descriptive relative names, not fixed economic states or buy/sell advice. Cluster identity may change at refits.

Minimum dataset length is 605 daily rows. A fit requires 180 complete training observations. Missing features yield **Unclassified**, with no backward fill or full-history imputation.

## Data

```text
Public API / licensed CSV
  -> immutable raw API responses
  -> validated daily Parquet snapshot + provenance JSON
  -> causal features -> expanding models
  -> event study / trading ledger -> Streamlit + ZIP export
```

### Market contract

| Column | Meaning |
| --- | --- |
| date | UTC midnight at the start of a completed daily bar |
| open, high, low, close | Positive USD/USDT prices |
| volume | Daily quote-currency turnover |
| funding | Sum of realized funding fractions on that UTC day, e.g. 0.0003 |
| oi | Optional USD notional OI; missing history stays missing |

OHLCV is required; funding may be missing but such rows cannot create valid features. Duplicates, calendar gaps, infinite values and invalid OHLC bounds are rejected. Data rows represent daily observations, not assertions that on-chain data was published at midnight.

Both exchange adapters paginate price and funding history and preserve each API response with retrieval time and request parameters. Requests have timeouts, bounded retries and rate-limit backoff. Re-running normalizes to one record per day. The CLI refreshes the requested window in full; scheduling and incremental-only updates are not implemented in this MVP.

Binance OI history is recent-only on its standard endpoint; do not enable OI for a long Binance backtest without additional history. Bybit linear OI is converted from native BTC units to approximate USD with the corresponding daily open. Cross-exchange OI is not aggregated. Funding is summed from native events rather than assuming every venue always uses eight-hour settlements.

Official references: [Binance market data](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data), [Bybit candles](https://bybit-exchange.github.io/docs/v5/market/kline), [Bybit funding](https://bybit-exchange.github.io/docs/v5/market/history-fund-rate), [Bybit OI](https://bybit-exchange.github.io/docs/v5/market/open-interest).

### Optional on-chain import

Upload a separate CSV with unique `available_at` UTC timestamps and one or more of `mvrv`, `sopr`, `exchange_netflow`:

```csv
available_at,mvrv,sopr,exchange_netflow
2025-01-02T12:00:00Z,1.8,1.01,-1200
2025-01-03T12:00:00Z,1.9,1.02,500
```

These are illustrative schema values. The backward as-of join uses the daily decision timestamp (bar end), never a future publication. Observations expire after two days. The importer cannot verify user-supplied availability timestamps or historical revisions. Keep a consistent metric definition and net-flow unit across the file.

No Glassnode/CryptoQuant subscription is bundled or assumed. Their on-chain APIs may require paid access. No Dune query is bundled: a query must independently establish metric definitions and availability timing before importing its results. Check data redistribution rights before publishing source data.

## Validation

### Conditional outcomes

At daily bar close, a label is formed from data through that bar. Entry is the next open; exit is the open 7, 14 or 30 calendar days later. Windows are sampled chronologically without overlap across the whole evaluation segment. They never cross the segment's end. This limits sample inflation but does not make events statistically independent or equivalent to distinct regimes/episodes.

Outputs include positive-return frequency, mean, median, 5th/95th percentiles, mean adverse excursion, difference versus all sampled eligible dates and approximate 95% moving-block-bootstrap intervals. Fewer than five events suppress intervals; fewer than thirty show a limited-sample label. Regime-filtered bootstrap samples may still retain complicated dependence; these are exploratory uncertainty estimates, not formal proof of an edge.

### Trading ledger

The predefined long/cash rule takes full exposure at the next open when the previous bar has positive momentum and an available classification. No profitable-cluster selection occurs. Buy-and-hold is evaluated on the same date range. One-way fees and slippage apply on entry and position changes; the final position is liquidated with costs.

The displayed equation is a daily approximation: apply rebalance cost, then exposure times open-to-next-open return less realized daily funding in perpetual mode. Funding uses opening notional; intraday changes of mark-price notional are not reconstructed. A missing funding observation blocks perpetual accounting.

Public candles are perpetual prices. The default **spot-like price proxy** excludes funding and is not an executable spot-market backtest. Cash earns zero. No leverage, liquidation, taxes or borrowing is modeled. The full ledger is downloadable.

### Test coverage

Automated checks cover rejection of bad market rows, future-data perturbations, frozen holdout fits, missing-feature handling, publication-aware joins and staleness, event entry/exit timing, non-overlap, transaction and final-liquidation costs, missing funding, API unit normalization, duplicate funding, options payoff bounds and Streamlit controls. CI runs the same suite.

Changing features or rules after reviewing final-holdout results makes the next run exploratory. For a formal study, register the configuration and data hash before inspection, then obtain new untouched data. Clustering uses no forward-return labels; a future supervised model must purge overlapping target windows before fitting.

## Limitations

- Synthetic data validates functionality, not investment performance.
- Current-vintage exchange history is not an independently reconstructed point-in-time archive. Historical provider corrections and actual publication latency remain limitations.
- The next-open assumption has effectively zero processing delay and can be optimistic. Costs approximate execution friction.
- A six-month holdout supports only about six non-overlapping monthly observations. A useful-looking win rate can have very little evidence behind it.
- Clusters are descriptive, may drift, and are not calibrated outcome probabilities. Transitions across refits can reflect taxonomy changes.
- No automated ablation report, hyperparameter sweep or cross-asset validation is implemented. Run controlled comparisons on common dates and preserve all configurations.
- Options output is a linear, hold-to-expiry payoff scenario with user-assumed premiums. It does not model historical quote availability, interim risk or exchange collateral mechanics.
- Daily fetching is manual; alerts, scheduled ingestion, incremental-only updates, paid vendor integrations and order execution are outside this MVP.
- Uploaded data and ZIP exports are local to the running app process/browser interaction; avoid hosting confidential licensed datasets on a public instance.

## Repository map

```text
app.py                    Streamlit UI and research exports
regime/data.py            Validation, synthetic fixture, on-chain as-of join
regime/ingest.py          Binance/Bybit adapters and snapshot CLI
regime/research.py        Features, clustering, event study, strategy, payoff
tests/                    Behavioral and dashboard tests
docs/                     Delivery plan and validation record
.github/workflows/        Test CI
```

## Company-specific presentation

The sidebar changes the suggested presentation emphasis, without altering research results:

- **Research teams:** reproducibility, sample sizes, out-of-sample distributions and negative findings.
- **Exchanges:** funding conventions, derivatives coverage, freshness and indicator education.
- **Options teams:** payoff assumptions, capped upside and requirements for a historical quote dataset.

To deploy on a Streamlit-compatible host, install `requirements.txt` and use `app.py` as the entrypoint. Fetch a real snapshot on the host or use the public-API control; no exchange trading credentials are required. Raw data, credentials and local snapshots are ignored by Git.

## Free real-data integrations

Coin Metrics MVRV and USD exchange net flows now load automatically for noncommercial research (CC BY-NC 4.0). Optional on-chain model features remain exploratory and off by default because historical values may be revised. Bybit falls back to Binance, then verified real snapshots. The Options tab fetches current Deribit BTC call bids and exports timestamped quotes; it does not claim historical options returns.

See [source research, licensing, limitations and production next steps](docs/free-data-sources.md).

## Implemented completion-plan increments

- Hourly GitHub Actions collection to the separate `research-data` branch; immutable verified snapshots, partial-failure status and durable history. The schedule starts only after this workflow reaches the default branch and Actions is enabled.
- Common-date price/derivatives/on-chain comparisons, explicit negative-funding/low-MVRV hypothesis, and as-recorded CSV vintage joins.
- Historical covered-call expiry accounting from uploaded real quote bundles, separate from current quote scenarios. Historical quote coverage is still an external dependency.
- English/Korean explanations, source fingerprint and exported research provenance.

[Operations](docs/operations.md) · [Data definitions](docs/data-dictionary.md) · [Model specification](docs/model-specification.md) · [Actual exploratory findings](docs/research-report.md) · [Option accounting](docs/options-methodology.md) · [Execution status and external gates](docs/execution-ledger.md).

Reproduce results: `python -m regime.report --output data/research-report`. Collect once: `python -m regime.collect --root data/archive`. No provider credentials are required for the selected public feeds; access restrictions may still prevent a refresh. SOPR and authenticated deployment verification are not claimed complete.
