# Market Regime Research Dashboard Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. These execution skills are not currently listed in the session; do not assume they are installed. This deliverable is a plan only, not authorization to schedule jobs, purchase data, or start implementation.

**Goal:** Deliver a reliably deployed, bilingual dashboard that identifies BTC market regimes using real price, derivatives and on-chain data, reports honest forward-return statistics, and evaluates historical covered calls when suitable quote history exists.

**Architecture:** Preserve the existing Streamlit, pandas and scikit-learn application. Separate collection and durable data storage from interactive analysis; retain versioned inputs and reproducible run manifests. Deliver reliability, data, modeling, evaluation and options as independently testable increments.

**Tech Stack:** Existing Python/Streamlit/pandas/Parquet/scikit-learn/Plotly stack; an external scheduled collector and durable object storage, selected at the infrastructure milestone. No new model framework is required.

**Spec:** The five requirements in the user's project goal, captured below, plus existing source research in `../../free-data-sources.md` and validation contract in `../../validation.md`.

## Scope and current baseline

1. Real price, funding, OI and volume; MVRV, SOPR and exchange net flows with documented access and publication timing.
2. Interpretable AI regime identification, with economic interpretations treated as hypotheses.
3. Conditional 7/14/30-day returns, positive-return frequencies and uncertainty, without exaggerated predictive claims.
4. Historical spot-plus-short-call results by regime, supported by historical executable quotes and settlement data.
5. English/Korean Streamlit views with indicator education and reproducible exports.

Already implemented: public Bybit/Binance adapters; verified historical exchange fallback; Coin Metrics MVRV and exchange flows; optional on-chain features; walk-forward four-cluster KMeans; non-overlapping forward-return statistics; long/cash ledger; current Deribit option quotes and payoff scenarios; bilingual UI.

Still unverified: the user's running deployment. Local offline fallback tests pass, but GitHub/Vercel access was blocked during the previous repair. Do not count the reported deployment issue as resolved until the actual URL is tested.

Not implemented: durable scheduled collection, true historical on-chain vintages, verified SOPR integration, research comparison report, historical option-chain backtesting and production monitoring. Current option payoff scenarios are not historical performance.

## Global constraints

- Initial scope is BTC, daily regime decisions, no leverage and no order execution.
- Production displays real data only. Archived data must show observation date and stale status.
- Do not splice exchange price, funding or OI series across venues; compare complete venue datasets separately.
- Coin Metrics usage must follow the licensing conditions recorded in the source research. Current bundled research data is noncommercial; obtain suitable rights before commercial use.
- The existing assumed 48-hour on-chain lag does not establish historical first-publication timing. Retain an explicit current-vintage label.
- Missing SOPR is unavailable, never zero and never replaced by MVRV. An audited Dune query is optional, not an assumed source of equivalent SOPR.
- Fit preprocessing and models on past observations only. Freeze research choices before evaluating a fresh holdout.
- Do not describe negative funding plus low MVRV as proven capital inflow. Use descriptive names and test the hypothesis separately.
- Quote simulations and realized option backtests remain separate throughout UI, exports and documentation.

## Review focus

- A fresh deployment with no writable local data and blocked APIs must still load verified historical data: Task 1.
- Partial or repeated collection must preserve older valid data and avoid duplicate rows: Task 2.
- Revised metrics and missing publication timestamps must not masquerade as point-in-time evidence: Task 3.
- Future-data changes and feature-availability differences must not create apparent model improvements: Tasks 4 and 5.
- Missing option bids, BTC premium units and expiry-specific settlement must not create fictitious profits: Task 6.

## Delivery sequence and effort

| Priority | Increment | Estimated focused engineering effort | Dependency |
|---|---|---|---|
| P0 | Verify and repair running deployment | 0.5–1 day | Deployment access/URL |
| P1 | Durable collection and quality monitoring | 3–5 days | P0; storage and scheduler choice |
| P1 | On-chain provenance and SOPR feasibility | 2–4 days | Can begin alongside collection |
| P2 | Regime features and comparison design | 3–5 days | Validated datasets |
| P2 | Statistical validation and research report | 3–5 days | Frozen model specification |
| P3 | Historical covered-call engine | 4–7 days | Historical quote and settlement coverage |
| P3 | Bilingual UX, documentation and release | 2–3 days | Each corresponding analysis increment |

Estimate: roughly 4–6 developer-weeks, excluding access approvals, provider procurement and waiting for future observations. Scheduling free quote collection today cannot produce several years of historical option data tomorrow. Start quote archiving during Task 2, not after model work.

## Task 1: Make the deployed application demonstrably reliable

**Files:** `Dockerfile.vercel`, `.dockerignore`, `.vercelignore`, `regime/feed.py`, `app.py`, `tests/test_feed.py`, `tests/test_app.py`, `docs/vercel-deployment.md`.

**Interfaces:** Preserve `load_market(snapshot, bundled_snapshot) -> (DataFrame, dict, notice)` and `read_snapshot(path, require_digest=False)`. Record deployed commit ID, snapshot hash, source and newest observation in the release report.

- [ ] Identify the URL, deployed commit and deployment root. Confirm the running code includes the latest fallback, not just that the local repository does.
- [ ] Run the existing isolated deployment-tree test and inspect the image build's snapshot verification output.
- [ ] Deploy the verified commit using the repository root; inspect build/runtime logs for missing files, integrity errors and exchange restrictions.
- [ ] Exercise normal API refresh, both exchanges blocked, corrupt local cache and corrupt bundled snapshot. Valid fallback must render; corrupt data must be rejected with a specific diagnostic.
- [ ] Verify health, browser WebSocket, chart rendering and source timestamps on the real URL. Add a visible build identifier to distinguish deployments.
- [ ] Record evidence and commit any required correction independently.

Verification command:

```powershell
python -m pytest tests/test_feed.py tests/test_app.py -q
```

**Done:** A fresh deployed instance with no private local files renders all tabs from verified data while both exchange APIs are unavailable. Its date and stale warning are visible. This is a release blocker.

## Task 2: Collect data outside Streamlit and keep it durably

**Files:** Create `regime/store.py`, `regime/collect.py`, `tests/test_collection.py`, `docs/operations.md`; modify `regime/ingest.py`, `regime/onchain.py`, `regime/options.py`, `regime/feed.py`.

**Interfaces:** `collect_once(as_of: str, root: str) -> dict` returns a collection manifest. `write_snapshot(frame, metadata, root) -> str` returns the committed manifest path. `read_latest(root, dataset) -> (DataFrame, dict)` reads only a completed, validated version. Preserve current adapters as the collection inputs.

- [ ] Define manifest fields: dataset, venue, instrument, units, observation interval, retrieved_at, published_at if known, vintage, license, checksum, validation result and version ID.
- [ ] Add fixture tests for duplicate collection, interrupted writes, missing funding, incomplete current-day bars, HTTP 429, out-of-order rows and a corrupt latest version.
- [ ] Implement atomic version publication: write immutable data and manifest, validate, then update the latest pointer. Never overwrite the last valid version on failure.
- [ ] Collect completed market bars/funding hourly with overlap for late updates; collect OI and option quotes hourly to retain observations before provider retention expires; refresh daily on-chain series with revision tracking.
- [ ] Select a scheduler and persistent storage after confirming access, expected retention, budget and network access. The Streamlit container's temporary directory is not durable storage.
- [ ] Store option instrument metadata, quote timestamps and expiry settlement records alongside bid/ask data from the start.
- [ ] Expose last success, lag, gaps and source failure reason. Specify a warning after 36 hours without a completed daily bar and exclude option quotes older than the configured execution tolerance.
- [ ] Run repeated collection and recovery fixtures, then observe seven daily collection cycles. Document operation and commit.

Verification command: `python -m pytest tests/test_collection.py tests/test_ingest.py -q`.

**Done:** Repeated jobs are idempotent, failures preserve valid data, data survives restarts, and every analysis input has an immutable version. Alert delivery requires a separately configured destination; do not send messages without authorization.

## Task 3: Complete the on-chain contract and resolve SOPR

**Files:** `regime/onchain.py`, `regime/data.py`, `tests/test_public_sources.py`; create `tests/test_onchain_vintages.py`, `docs/data-dictionary.md`; update `docs/free-data-sources.md`.

**Interfaces:** Preserve `enrich(daily, csv_text)`. Normalize provider inputs to observation_time, available_at, retrieved_at, source, vintage, mvrv, sopr and exchange_netflow where supported. Unknown availability must remain explicitly unknown rather than silently claiming a historical publication date.

- [ ] Document exact definitions and units, exchange-address coverage, missing-value rules and redistribution rights for each available metric.
- [ ] Verify SOPR access using a real sample from an authorized provider or audited query. Confirm chain, spent-output methodology, adjusted/unadjusted definition, coverage and historical publication information.
- [ ] Choose the gate outcome: integrate validated SOPR; accept licensed CSV; or release the narrower MVRV/net-flow dashboard with SOPR clearly unavailable. The full stated metric goal is not complete in the third case.
- [ ] Retain original fetched vintages and publish-time metadata. Keep assumed-lag and reconstructed point-in-time datasets as separate research modes.
- [ ] Test delayed publication, a later revision, a missing flow leg and stale metrics. No feature may become visible before its declared availability.
- [ ] Document why current-vintage studies remain exploratory even after a lag is applied; commit schema, tests and dictionary together.

Verification command: `python -m pytest tests/test_onchain_vintages.py tests/test_public_sources.py -q`.

**Done:** Every on-chain value has documented meaning and timing; SOPR is either genuinely integrated or explicitly recorded as a remaining blocker. Do not invent a free-provider guarantee.

## Task 4: Strengthen interpretable regime identification

**Files:** `regime/research.py`; create `regime/signals.py`, `tests/test_signals.py`, `docs/model-specification.md`; update `tests/test_research.py`.

**Interfaces:** Preserve `features` and `walk_forward`. Add `context_signals(daily: DataFrame) -> DataFrame` returning funding_flip_negative, mvrv_low and hypothesis_active, with missing values preserved.

- [ ] Freeze a baseline and three feature sets: price-only; price plus derivatives; price plus derivatives plus available on-chain metrics. Evaluate on common eligible dates and report excluded coverage separately.
- [ ] Define the example hypothesis descriptively: daily funding changes from nonnegative to negative, and MVRV is below its trailing prior-365-observation 20th percentile with at least 180 prior observations. Thresholds are prespecified research choices, not established trading truths.
- [ ] Use shifted historical thresholds; keep no-signal distinct from unavailable-input. Describe the result as negative-funding/low-MVRV context, not confirmed sidelined-capital inflow.
- [ ] Retain four-cluster KMeans as baseline. Report cluster centroids, observation counts, persistence and changes between refits. Distance to centroid is not a confidence probability.
- [ ] Add future-perturbation tests: changing observations after date T must not change features or labels through T. Test insufficient training data and optional metric removal explicitly.
- [ ] Freeze the model configuration, feature availability rules and seed in a versioned specification before Task 5; commit.

Verification command: `python -m pytest tests/test_signals.py tests/test_research.py -q`.

**Done:** Each displayed regime has a reproducible model version and measurable indicator description; the example on-chain hypothesis can be evaluated without a causal claim. More complicated classifiers are deferred until they outperform this baseline on genuinely unseen data.

## Task 5: Produce defensible regime-based backtest evidence

**Files:** `regime/research.py`, `tests/test_research.py`; create `regime/evaluation.py`, `tests/test_evaluation.py`, `docs/research-report.md`; update `docs/validation.md`.

**Interfaces:** Preserve `events`, `summarize` and `strategy`. Add `compare_feature_sets(results: dict[str, DataFrame]) -> DataFrame`, requiring aligned signal dates and the same execution/cost rules.

- [ ] Mark the already-viewed final holdout as exploratory for subsequent model changes. Choose a genuinely untouched historical period if available or begin a frozen forward evaluation; do not relabel the same inspected data as new evidence.
- [ ] Verify daily-close signal, next-open entry, horizon boundaries and globally non-overlapping sampling with hand-calculated fixtures.
- [ ] Report 7/14/30-day positive-return frequency, mean, median, 5th/95th percentiles, sample count, distinct episodes and uncertainty by regime. Include the same-date unconditional benchmark and missing-date coverage.
- [ ] For N below 5, suppress confidence intervals; label every N below 30 as low-sample exploratory. These are display policies, not thresholds proving significance. About six non-overlapping monthly windows in 180 days cannot support strong regime-specific claims.
- [ ] Compare feature sets on common dates. Report paired benchmark differences and block-bootstrap uncertainty; record all tried configurations and acknowledge multiple comparisons.
- [ ] Keep gross conditional asset returns separate from net strategy returns. Run fee/slippage sensitivity and report turnover, drawdown and performance across market subperiods.
- [ ] Verify identical inputs/configuration reproduce the same event ledger and manifest; publish positive, negative or inconclusive findings and commit.

Verification command: `python -m pytest tests/test_evaluation.py tests/test_research.py -q`.

**Done:** A reader can reproduce every quoted frequency and average from exported events. A failure to find predictive improvement is an acceptable research result, not a reason to tune the holdout.

## Task 6: Implement genuine historical covered-call evaluation

**Files:** `regime/options.py`; create `regime/options_backtest.py`, `tests/test_options_backtest.py`, `docs/options-methodology.md`; update `app.py`, `regime/i18n.py`.

**Interfaces:** `covered_call_events(signals, spot, quotes, instruments, settlements, fee_config) -> DataFrame`. Inputs must include actual timestamps, instrument identifiers, bid/ask, contract and settlement units, expiry and settlement index. Return one ledger row per completed trade with entry/expiry, regime, spot cost, premium, fees, option liability and total return.

- [ ] Audit historical coverage and redistribution rights before promising dates or sample size. If quotes are unavailable, continue forward archiving and keep this milestone blocked; current quotes cannot substitute for old premiums.
- [ ] Prespecify a simple strategy: own one BTC; sell one matching BTC call at the first valid scheduled execution after the signal, using the nearest 30-day expiry within 14 days and nearest 110% OTM strike. Hold to expiry; no overlapping positions or leverage.
- [ ] Require actual spot/index and historical bid at execution. Skip missing, stale or zero-bid quotes and record the reason. Bid is a conservative quote input, not proof of fill; apply explicit size assumptions or depth data where available.
- [ ] Use the exchange's actual settlement index at expiry. Account for BTC-denominated premium, fees and option settlement without applying linear-USD premium assumptions.
- [ ] Specify fully covered collateral and interim margin treatment. Until margin-path data is implemented, describe outcomes as expiry-accounting research, not an executable margin backtest.
- [ ] Test ATM/ITM/OTM expiry, expiry index different from daily close, missing quotes, premium denomination, fees and contract-size rejection with hand-calculated ledgers.
- [ ] Compare covered call against holding the same BTC over identical dates, including total return, upside foregone, drawdown coverage limitations and sample sizes by entry regime; commit.

Verification command: `python -m pytest tests/test_options_backtest.py tests/test_public_sources.py -q`.

**Done:** Every historical option return traces to a historical quote and settlement record. If insufficient history exists, only the current quote/scenario capability may be released, explicitly short of the full options goal.

## Task 7: Complete bilingual explanations and release evidence

**Files:** `app.py`, `regime/i18n.py`, `tests/test_app.py`, `tests/test_i18n.py`, `README.md`, `README.ko.md`, `docs/operations.md`, `docs/research-report.md`.

**Interfaces:** Preserve exported machine-readable field names while translating display labels. Expose dataset version, model version, observation date and research mode on every result view.

- [ ] Give each indicator card five fields: what it measures, units, how to read it, what it cannot establish, and source/freshness. Link full definitions without overwhelming new users.
- [ ] Distinguish live data, historical fallback, unavailable data and current-vintage research in both languages. Disable unsupported comparisons with an explanation rather than silently selecting a weaker dataset.
- [ ] Keep market-state description, historical conditional statistics and option scenarios in distinct sections. Show sample size and evaluation period next to each statistic.
- [ ] Test language switching, stale and missing inputs, enabled on-chain features, CSV uploads, downloads and option-history-unavailable states. Check mobile layout and deployed WebSocket behavior in the browser.
- [ ] Run the full suite once after integration, then repeat only failed or affected checks. Attach deployed commit, checksums, coverage report and validation results to the release record.
- [ ] Update both READMEs in the order Problem → Hypothesis → Data → Validation → Limitations. Document how to refresh, recover and reproduce each research result; commit and release after all applicable gates pass.

Verification command: `python -m pytest -q`.

**Done:** A new user can identify the dataset age, explain the latest regime, interpret a 30-day result without confusing it with a forecast, and reproduce that result from exports in either language.

## Decision gates and final definition of success

The only early infrastructure choices needed are the actual deployment target, persistent storage/scheduler access and intended commercial versus noncommercial use. Data acquisition decisions concern SOPR and historical option quotes. Default to the existing stack and free authorized sources while exposing unsupported requirements; do not purchase data automatically.

A reliable research release can ship after Tasks 1–5 and 7 with options clearly labeled as current scenarios. Full completion of the user's stated goal also requires supported SOPR and Task 6 historical evidence. Completion means a working, reproducible and honest research system; it does not require a profitable strategy or statistically significant signal.

Self-review: all five requested components map to tasks; failure cases map to explicit validation steps; existing APIs are preserved and proposed interfaces named; no synthetic production fallback or unsupported performance claim is planned. Implementation has not started as part of this planning request.
