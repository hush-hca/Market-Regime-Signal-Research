# Collection and recovery

The user selected free, noncommercial research using GitHub Actions and repository snapshots. `.github/workflows/collect.yml` runs at minute 17 each hour once merged into the default branch and enabled in GitHub. Actions schedules are best-effort, not a trading clock. Repository/account usage limits still apply; no paid infrastructure is provisioned.

The collector commits only to `research-data`. Application deployments must track the application branch, not the data branch. Both application configuration and the data branch disable Vercel builds for `research-data`. Verify this setting before enabling the schedule. The dashboard reads public, checksum-verified snapshots from that branch; a private repository requires a private delivery mechanism and is not supported by the public reader. The existing verified bootstrap remains available when GitHub and exchanges cannot be reached.

## One-off collection

```powershell
python -m regime.collect --root data/archive
```

The root must be durable for local operations. `REGIME_RAW_DIR` may point to temporary scratch storage; normalized snapshots and instrument terms remain in the archive. Never use a container's ephemeral filesystem as the only archive. `REGIME_SNAPSHOT_ROOT` tells the dashboard to read a local archive instead of the public repository branch.

Datasets: market_bybit, market_binance, onchain, option_quotes, option_instruments, option_settlements, forward_models, forward_ledger. Daily market history refreshes a 60-day overlap after the initial 730-day collection. Venue records never mix. Current incomplete UTC bars are removed. Missing refreshed funding/OI preserves previously observed values for the same venue/date, not a zero. On-chain refresh is daily; option quotes, instrument terms and the latest 100 official BTC delivery prices are archived hourly. Long collector outages may require explicit settlement backfill.

Each version has Parquet data, source metadata, receipt time, content digest, version ID and row count. Publication replaces only a small latest.json pointer after validated files have been written. Versions are retained for audit. A single-writer lock prevents concurrent local publication. The workflow also serializes runs.

The job exits nonzero for partial failure, but still commits successful snapshots and collection-status.json. Inspect that status for missing funding rows, freshness, source errors and last collection attempt. The daily-market staleness warning starts 36 hours after the last bar's close. No external messages or alerts are configured; GitHub run status and dashboard warnings are the initial monitoring surfaces.

## Recovery

1. Inspect collection-status.json and the failed Actions log. Exchange IP restrictions may affect GitHub-hosted runners; retries cannot remove such restrictions.
2. Verify the latest manifest checksum and schema. Local readers can recover an earlier intact version if the pointed version is corrupt. The public reader rejects corrupt data and proceeds to other sources.
3. Re-run the workflow manually after transient failures. Do not modify old versions to make a checksum pass.
4. For a local crashed writer, confirm no collector is running before removing its .writer.lock. The code never automatically deletes another writer's lock.
5. The archive grows over time. Measure repository size and Actions usage weekly. Move older immutable versions to suitable durable storage before repository limits become a problem. No automatic destructive retention policy is installed.

## Export option history

```powershell
python -m regime.history --root data/archive --output data/options-history.zip
```

The ZIP is a research export for offline inspection; arbitrary-fee historical return uploads are disabled in the actual-only dashboard. Required files are quotes.csv, instruments.csv, settlements.csv, spot.csv and manifest.json. UI bundles have a 20 MB expanded-size limit and the existing 4 MB upload limit; use a shorter exported dataset if needed. Export currently includes the entire archive, so archive partitioning is needed once the bundle exceeds these limits. Empty or corrupted history is rejected, not replaced with current quotes.

## Release checks

Run `python -m pytest -q`; run `python -m regime.report --output data/research-report`; verify the deployed source fingerprint matches `python -c "from regime.build import build_id; print(build_id())"`. Confirm health, WebSocket, English/Korean, real-data timestamps, fallback behavior and downloads on the actual authenticated deployment.

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax


### Official archive fallback
When the Binance futures API fails, the collector reads checksum-verified USD-M ZIP archives from https://data.binance.vision/. It uses monthly prices plus daily prices for unpublished months, monthly funding, and the last published daily OI observation. No cross-venue splice is performed. Funding can lag by a month; missing funding and OI remain missing, so recent derivative regimes may be unclassified. Price freshness does not imply derivative freshness. See https://github.com/binance/binance-public-data for archive timing and checksum documentation.


## Frozen forward ledger
The collector registers frozen models and appends timestamped observations after source collection. See [protocol](forward-protocol.md). Never delete or reset forward_models to improve results. Changed feature definitions fail closed. A new protocol must explicitly establish a new evaluation stream. The dashboard exposes raw records and artifacts; pending outcomes have no displayed return.
