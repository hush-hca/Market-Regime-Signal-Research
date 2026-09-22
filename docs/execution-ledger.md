# Execution ledger — research-dashboard-completion

Plan: `superpowers/plans/2026-09-22-research-dashboard-completion.md`
Base: ce78474. Execution approved by the user; branch implement-research-plan.

Ruling: Work in the existing checkout on a feature branch, preserving the user's deployment configuration. No isolated checkout is needed for this single implementer.
Ruling: Execute native implementation, with one independent whole-branch review as required by the executing-plans skill.
Ruling: Use a repository ledger instead of POSIX-only helper scripts on this Windows environment. Keep external milestone failures visible; do not mark the overall plan complete based on unit tests.

Pre-flight: Task 2 snapshots are consumed by Task 1 feed; keep load_market's tuple return and expose storage metadata through its existing metadata dict.
Pre-flight: Tasks 3/4 consume existing enriched daily frames; preserve enrich while adding a distinct vintage-aware join.
Pre-flight: Tasks 4/5 use regime/event DataFrames; compare identical signal dates and never pool different feature definitions into one claim.
Pre-flight: Task 6 consumes Task 2 option archive; preserve instrument and settlement metadata, not just the selected option.
Pre-flight: Task 7 translates display labels only, preserving canonical export fields.

Task 1: Local offline tests already exist. Remote deployment inspection attempted; network/CLI access is restricted. URL requested. Build identifier will be added before release verification.
Task 2: In progress. Storage implementation uses a configured filesystem root suitable for a durable mounted volume. Scheduling/storage destination requested; no paid resources provisioned.


Task 1: Live deployment verified after user sign-in: real Bybit fallback, 730 observations through 2026-09-17, explicit stale warning, charts and historical outcomes render. Initial HTTP 302 was Vercel SSO. New source-fingerprint and collection features still need deployment. CLI access remains EACCES.
Task 2: RED 5 missing-module failures then GREEN 5 collection tests; combined storage/repository/fallback suite 12 passed. User selected GitHub Actions plus repository snapshots. Hourly workflow and separate research-data branch implemented; Vercel builds disabled on data branch. Remote activation and seven observed daily cycles remain pending.
Task 3: RED then GREEN vintage tests. As-recorded CSV join requires timestamps and prevents later revisions changing earlier decisions. SOPR remains an external data gate; licensed CSV supported, no synthetic substitute.
Task 4: RED then GREEN signals tests. Prior-only MVRV threshold, explicit feature sets, common-date labels. Ruling: independent indicator-rule labels may derive funding from daily data, but price-only clustering must fit without funding in its feature matrix.
Task 5: GREEN evaluation tests; generated real bundled-data reports for 7/14/30 days and costs 0/10/25/50 bps. Five monthly events are insufficient for strong regime-specific claims. New untouched forward evidence remains pending.
Task 6: RED six missing-module tests then GREEN all six accounting tests. Added historical quote bundle import/export. Ruling: retained BTC is marked at expiry; label results expiry-accounting, with assumed fees and no spot exit fee. No margin-path or multi-year-history completion claim.
Task 7: Existing UI, localization and history tests passed (12 tests). Added bilingual educational fields, source fingerprint, common-date comparisons and historical option inputs. Full suite passed 50 tests before final small UI/documentation changes. Independent review follows.

Ruling: Preserve immutable versions instead of automatic destructive retention. Repository growth is documented; offloading must be selected before storage limits.
Ruling: Record implementation milestones separately from external data/infrastructure gates. The whole project is not complete solely because tests pass.
