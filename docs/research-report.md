# Exploratory research report

Run `python -m regime.report --output docs/research-results` to regenerate the tables offline from checksum-verified bundled inputs. The manifest records data digests, source metadata, model settings, exact features and a source-code fingerprint.

## Scope

Real Bybit BTCUSDT perpetual daily data, 2024-09-18 through 2026-09-17. Coin Metrics MVRV and exchange flows use current-vintage observations with an assumed 48-hour lag. SOPR is absent. The final 180 days have already been inspected; this is exploratory evaluation, not a new untouched test.

## Findings

All three available feature sets have 180 classified dates in the final segment. Common-date sampling produces 25 seven-day, 12 fourteen-day and **five thirty-day events** per feature set. Splitting five monthly events among four regimes cannot support credible regime-specific win-rate claims. Confidence intervals remain suppressed below five observations; sample counts below 30 are labeled limited.

The feature comparison tables describe conditional return distributions on identical event dates. They do not demonstrate that on-chain features improve prediction. No profitable regime was selected after inspecting these tables; no calibrated forward probability or statistical significance is claimed.

## Outputs

- `research-results/summary.csv`: conditional summaries and episode counts for every horizon/feature set.
- `research-results/events-7d.csv`, `events-14d.csv`, `events-30d.csv`: the underlying ledgers.
- `research-results/coverage.csv`: eligible and common date counts.
- `research-results/manifest.json`: reproducibility and provenance.

No historical option performance is reported because an adequately long actual quote archive has not been collected. The engine is validated with software fixtures, which are not market evidence.

## Next evidence gate

Collect immutable as-recorded vintages and quotes; preregister a future evaluation start/configuration before outcomes; accumulate sufficient independent market episodes; and publish unfavorable or inconclusive outcomes as carefully as favorable ones. Current-vintage historical revisions and exchange-specific coverage remain limitations.

The actual-only release removes assumed-cost strategy tables from this report. Conditional outcomes are observed gross asset price changes, not net or executed performance. Forward performance is a separate timestamped evidence stream; pending records are not results.
