# Free-source research and integration — 2026-09-22

## Implemented

| Layer | Selected source | Access and limits |
|---|---|---|
| Price, funding, OI | Bybit, then Binance public APIs | No key. Whole-venue fallback; never splice funding/OI across exchanges. Binance historical OI retention is limited. Verified Bybit snapshot remains final fallback. |
| BTC MVRV | Coin Metrics Community API, CapMVRVCur | No key; actual endpoint response verified. |
| Exchange net flows | Coin Metrics FlowInExUSD minus FlowOutExUSD | Actual responses verified. USD flow for provider-labeled exchange addresses; missing legs stay missing. |
| On-chain resilience | Official Coin Metrics GitHub CSV, then bundled API snapshot | Snapshot has 751 observations, 2024-09-01 through 2026-09-21, retrieval timestamp and SHA-256. Data is CC BY-NC 4.0; attribution required and commercial use needs separate permission. |
| Current options | Deribit public instruments, book summaries, BTC index | No key. Active BTC inverse calls with positive bids and valid asks. Button fetches quotes, exports timestamps and regime date, and plots gross expiry payoff. |

Coin Metrics on-chain features are optional and off by default for classification. The dashboard displays the metrics automatically for noncommercial research, and CSV uploads take precedence. Enable exploratory on-chain features in the sidebar to include them in the existing walk-forward KMeans model and conditional-return statistics. No new profitable-regime claim is made by these integrations.

The 48-hour lag starts at the observation day's midnight. It is an explicit assumption, NOT reconstructed historical publication time. Exchange flows may be provisional (flash) and revised. Historical model results incorporating these series remain current-vintage exploratory results even with causal joins. Missing values are not filled; the existing two-day staleness tolerance applies. Downloaded manifests disclose vintage, definitions, freshness and licensing.

Deribit selection targets the closest expiry to 30 days within ±14 days, then the closest OTM strike to 110% of current index. Index spot is fetched separately; expiry-specific underlying forward prices are not substituted for spot. Premium is denominated and retained in BTC. Terminal USD wealth per initial BTC is ST*(1+premiumBTC-feesBTC)-max(ST-K,0). The displayed scenario assumes zero fees and ignores execution size, margin and interim liquidation. Current quotes are never reused as historical premiums. Export quotes regularly to start collecting an auditable history; no scheduler is installed.

## Evaluated but not falsely advertised as free

- **SOPR:** the actual Coin Metrics SOPR request was rejected for community credentials. Remains unavailable unless supplied via licensed CSV with availability timestamps. MVRV is not a substitute for SOPR.
- **Glassnode:** API access is a Professional add-on; a free dashboard account does not establish free API access.
- **CryptoQuant:** on-chain API requires Professional or higher according to its API page.
- **Dune:** API query-result access requires a key and consumes credits. Useful when the user supplies an audited query and account; arbitrary labeled-exchange or Bitcoin UTXO coverage cannot be assumed. No invented query or API key is included.
- **CCXT:** MIT-licensed unified exchange adapter. Existing focused adapters already cover the required endpoints; adding CCXT would not restore expired history or remove exchange network restrictions, so no extra dependency was added.

## Remaining work for production research

1. Schedule immutable collection with source timestamps, revisions, freshness alerts and monitored storage; archive OI before exchange retention expires.
2. Obtain licensed SOPR and point-in-time on-chain vintages. Audit address coverage and publication delays. Arrange commercial permission before using Coin Metrics data commercially.
3. Collect or license historical option chains with bid/ask, expiry, settlement and instrument metadata; incorporate fees, executable size, collateral and settlement accounting before reporting regime-specific realized covered-call returns.
4. Pre-register model choices, compare price-only versus derivatives/on-chain models, extend independent holdouts and report sample sizes and uncertainty. Do not tune against the displayed holdout.

## Primary sources

- Coin Metrics community API: https://docs.coinmetrics.io/api/v4/
- Official data archive and license: https://github.com/coinmetrics/data
- Valuation definitions: https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/economics/valuation
- Glassnode API access: https://docs.glassnode.com/basic-api/api
- CryptoQuant API plans: https://www.cryptoquant.com/apis
- Dune query results: https://docs.dune.com/api-reference/executions/endpoint/get-query-result
- Dune credits: https://docs.dune.com/resources/credits-billing/overview
- Deribit summaries: https://docs.deribit.com/api-reference/market-data/public-get_book_summary_by_currency
- Inverse option conventions: https://support.deribit.com/hc/en-us/articles/31424939096093-Inverse-Options
- CCXT: https://github.com/ccxt/ccxt

## Verification scope

Actual public endpoint responses were downloaded on 2026-09-22 and normalized locally. Automated tests use isolated transport fixtures and the checksum-verified on-chain bundle. Deployment-specific network access still determines whether live refresh succeeds; archived data is explicitly identified and never labeled live.
