# Historical option expiry accounting

The Options tab has three distinct functions: uploaded historical quote/settlement analysis, current Deribit quotes, and an assumed-premium linear payoff explorer. Their results must never be pooled.

Historical selection: daily regime at close; search collected snapshots within the following hour. Use the first snapshot with valid spot and BTC call quotes. Quote age is 0–300 seconds; spot age at most five minutes. Instrument terms must have been observed by execution. Choose nearest expiry to 30 days inside 16–44 days, then nearest strike to 110% of spot among OTM calls. Own one BTC, short a contract of size one, hold to expiry, no overlapping trades. Missing quotes or settlement records are disclosed in the ledger. Missing settlement does not allow a later overlapping trade.

Use positive bid and ask >= bid, no fictitious midpoint fill. A bid does not prove sufficient size; this implementation assumes one-BTC fill and is a research ledger. Supported terms are BTC base/quote/settlement, inverse calls only. Official btc_usd delivery index must match the exact expiry. Futures forward prices and daily candle close are not substitutes.

Per initial BTC, with terminal settlement S and strike K:

- Liability in BTC = max(1 - K/S, 0).
- Initial USD capital = entry spot * (1 + spot entry fee bps / 10000).
- Terminal BTC = 1 + premium BTC - option entry fee BTC - settlement fee BTC - liability BTC.
- Expiry-accounting return = terminal BTC * S / initial capital - 1.
- Benchmark = same BTC marked at S / same initial capital - 1.

Premium remains BTC-denominated. Fee inputs are explicit assumptions, not verified historical provider schedules. Remaining spot is marked rather than sold; no spot exit fee, taxes, intraday drawdown, margin-path or liquidation simulation. Thus returns are expiry accounting, not a claim of fully realized cash trading or an executable margin backtest. Report sample size and missing-trade counts beside regime averages. Current archives have no multi-year quote history; synthetic test fixtures are never production evidence.

Official settlement endpoint: https://docs.deribit.com/api-reference/market-data/public-get_delivery_prices
