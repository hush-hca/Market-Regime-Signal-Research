# MVP implementation plan

Approved scope: BTC daily research, rules and training-only clustering, honest out-of-sample statistics, Streamlit, reproducible repository. Historical options quotes and paid on-chain access are not assumed.

- [x] Implement validated daily data contract and deterministic synthetic fixture.
- [x] Implement paginated Binance/Bybit price, funding and OI adapters with retry and raw snapshots.
- [x] Implement causal feature generation and expanding-window clustering.
- [x] Implement non-overlapping event sampling, bootstrap intervals and executable long/cash ledger.
- [x] Implement optional point-in-time on-chain import and covered-call payoff scenarios.
- [x] Build dashboard, explanatory cards, exports and methodology.
- [x] Test timing, no-future-dependence, accounting, ingestion normalization and Streamlit rendering.
- [x] Document setup, hypotheses, limitations and company-specific presentation.

Delivery target: `https://github.com/hush-hca/Market-Regime-Signal-Research.git`. Fetch existing history before the initial commit; verify remote commit identity after pushing.
