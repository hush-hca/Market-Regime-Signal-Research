# Real historical fallback

These are real Bybit BTCUSDT perpetual daily observations fetched through the existing public API adapter on 2026-09-18 UTC. They are not generated demo data.

- Coverage: 2024-09-18 through 2026-09-17 UTC, 730 completed daily bars.
- Fields: OHLC, quote turnover, realized daily funding sum and approximate USD OI.
- OI conversion: native BTC OI multiplied by the daily open, consistent with the adapter.
- `bybit.json` preserves original provenance and records the Parquet SHA-256 digest.
- Used only when live refresh fails and no valid local snapshot exists. The app displays a failure warning, date and stale-data warning.

This archive is intentionally historical. Update it using a verified real API collection, preserve its actual retrieval time, and recompute the digest if replacing the file. Never relabel it as current or substitute generated data.
