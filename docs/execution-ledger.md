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


Final review: independent reviewer dispatched as required, but its turn failed at the account usage limit before producing findings. No independent approval is claimed. Author performed a separate self-review.
Final fixed: settlement endpoint failure discarded valid current quotes; preserve quote/instrument snapshots and report settlement failure separately. Two regression tests observed RED then GREEN.
Final fixed: dashboard on-chain path bypassed the scheduled archive; prefer recent validated collected data, then live API/official archive/bundle. Regression test observed RED then GREEN.
Final fixed: on-chain educational cards displayed the market venue; now show their own source/observation metadata.
Final verification: 54 tests passed, 188 existing/compatible deprecation warnings, no test failures. Actual-data research report regenerated with the final code fingerprint. Original running deployment verified in both English and Korean. New branch pushed successfully; preview deployment is available. Production update, collector activation and seven-day observation still to be verified.
Deferred minor: large option history export currently needs dataset partitioning to fit upload limits; operational limit is documented and no automatic destructive retention is installed.


### Live collection verification and archive fallback
Pushed implementation to main. First GitHub runner collection saved 1,095 on-chain rows, 458 option quotes, 970 instrument terms and 100 settlements. Bybit returned HTTP 403 and Binance HTTP 451. Added the distinct official Binance public archive source with SHA-256 checks, quote-volume normalization, complete funding-day checks and explicit missing unpublished derivatives. Nine targeted tests passed. Remote archive refresh still needs verification.


Release verification: commit 8ce36c2 pushed to main; production fingerprint f252fb0a4071 matches local. Full suite 57 passed; affected Streamlit suite 3 passed after notices. Both GitHub validation runs passed. Collector run 35747548984 published 730 verified Binance rows through 2026-09-21, with 21 missing funding days (last funding 2026-08-31), plus 457 current option quotes, 972 instruments and 100 settlements; on-chain daily cache held 1,095 rows. Overall workflow remains partial failure because Bybit returns 403. Production refresh visibly loaded Binance, displayed missing funding and an unclassified latest derivative regime. No invented funding or options return was substituted. Seven daily reliability cycles, SOPR entitlement and sufficient historical option/forward-evaluation evidence remain external completion gates.


## Priorities 1–4 actual-only release
User authorized implementation and requires actual data only. Native implementation continues; redundant skill approval stages are superseded by the user's direct execution request and higher-priority autonomy instructions. Spec and plan dated 2026-09-23 record scope.
Readiness/evidence tests observed RED (missing module) then GREEN (3 actual-data tests). Forward tests observed RED then GREEN (3 tests), including frozen artifacts, idempotency, strictly later entry, missing funding, fixed completed outcomes and changed feature-code rejection. UI tests use the verified actual bundled observations. Six UI/localization tests passed after removing obsolete assumed-fee control assertions.
Ruling: remove assumed-premium and preset-cost displays and unverified CSV uploads to satisfy actual-only scope. Gross observed price outcomes remain explicitly distinct from executed net returns; no fees are invented. Cost if wrong: those exploratory controls must be explicitly reintroduced outside actual-only mode.
Ruling: forward ledger uses the first UTC open after recording, not the historical signal day's already-past next open. This preserves causality under delayed public archives; cost is delayed paper execution relative to a real-time feed.
Ruling: frozen model artifact and feature-definition checksum are retained permanently; a changed protocol requires a new evaluation stream. No retrospective predictions are created.

Verification: complete suite 64 passed (295 warnings) after updating the legacy on-chain checkbox test to the explicit model selector. Separate local verification on actual checksum-verified Binance snapshot and real Coin Metrics bundle created 3 frozen artifacts and 9 records: price-only awaiting a future UTC entry, derivatives missing_inputs, zero completed outcomes. This verification archive is outside the repository and is not published as production evidence. Independent read-only review dispatched per executing-plans skill.

Independent final review: no Critical findings; two Important persistence findings (missing/recovered forward state could reset history; older market snapshots could backfill dates). Reproduced both with failing real-bundle regressions, then implemented fail-closed pointer/corruption/rollback handling, registry/ledger consistency and strictly increasing per-model signal dates.
Review reclassification: shared comparison columns and global feature constants affect the promised fixed model definition, so treated as Important contract issues rather than cosmetic minors. Fixed the comparison to use model_features and included referenced feature-list constants in the frozen definition hash. Added a regression that failed with an extra missing SOPR column. Strengthened completed-outcome immutability verification using deliberately revised copies of observed price fields. No such test copy is published or represented as actual data.

Final verification after review fixes: 69 passed, 412 warnings, no failures. Report regenerated against final source fingerprint 3ba85798a8e8. Independent review findings addressed; deployment and real collector initialization are the remaining release checks.

Release verification complete: implementation 10cebc2 deployed with fingerprint 3ba85798a8e8. Production collector registered 3 models and 9 real as-recorded observations; zero completed outcomes. Downloaded production ledger SHA-256 a74fa98c749da8f874ec705db068a5d190084d1964decbf6ddc18795c0c6eb81 matched manifest; all scheduled entries were strictly after recorded_at, and returns were absent. Production browser verified English evidence cards, Korean health/model controls, explicit derivative unclassified state, price-only restoration and Korean pending ledger.
CI follow-up: public test annotations exposed an older subprocess fallback test still contacting the real repository. Local network restrictions had masked it. Added offline repository-reader isolation in that test; five affected tests passed. CI now installs the verified lock and publishes readable JUnit failures. Both full GitHub validation runs for b167a22 passed (35826214585, 35826214291). No production calculation changed in these CI-only commits.
Collector remains partial failure because Bybit returns 403; successful Binance, on-chain, options and forward datasets are preserved and independently reported. Funding gaps, missing SOPR and zero matured forward outcomes are data limitations, not replaced with generated values. Priorities 1–4 are released; future outcome accumulation requires actual elapsed time.
