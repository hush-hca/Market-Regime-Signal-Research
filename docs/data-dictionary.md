# Data definitions and timing

| Field | Unit / meaning | Availability and limitation |
|---|---|---|
| OHLC | USDT perpetual price | Completed daily UTC bars, not executable spot prices |
| volume | USDT quote turnover | Venue-specific; derivatives activity is not capital inflow |
| funding | Sum of realized rate fractions per UTC day | Missing values remain missing; partial provider histories require inspection |
| oi | USD proxy of outstanding exposure | Bybit native BTC OI times daily open; Binance reported USD OI; recent retention differs |
| mvrv | Market cap / realized cap ratio | Coin Metrics CapMVRVCur; current-vintage revisions; assumed 48h lag for legacy historical research |
| sopr | Spent-output profit ratio | No verified free API entitlement. Licensed CSV is supported; mark unavailable until obtained |
| exchange_netflow | USD inflow minus outflow | Coin Metrics FlowInExUSD minus FlowOutExUSD, provider exchange labels, provisional/revisable |
| bid_btc / ask_btc | BTC per one-BTC inverse call | Observed public quotes, no executable-size guarantee |
| delivery_price | USD BTC delivery index | Official expiry settlement, not an arbitrary daily close |

Legacy CSV: available_at plus one or more mvrv/sopr/exchange_netflow. User attests publication timing; vintage is not independently verified. A CSV also containing observation_time and retrieved_at uses the as-recorded join: only records whose publication and receipt timestamps precede the daily decision are eligible. Later revisions cannot rewrite earlier decisions. The newest eligible observation wins, rather than a late revision of an older date. Observations older than four days at decision time expire (48h assumed lag plus two-day tolerance).

Unknown publication times must not be advertised as original publication times. For locally recorded data, receipt time establishes when this collector knew a value, not when the market first knew it. Starting collection now does not reconstruct years of point-in-time history.

Coin Metrics attribution/license: https://github.com/coinmetrics/data (CC BY-NC 4.0 in the researched archive). This project is configured for the user's noncommercial research choice. Provider definitions and permissions must be reviewed before redistribution or commercial use.

SOPR integration remains an external data gate, not a code-completion claim. CSV imports accept SOPR, but no paid subscription is purchased and no alternate metric is falsely labeled SOPR.
