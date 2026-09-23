# Trader research release implementation plan

Goal: priorities 1–4 using actual observations only.
Architecture: shared model registry, data-health and evidence functions consumed by Streamlit; immutable forward registry and ledger snapshots maintained by the existing GitHub collector.
Spec: ../specs/2026-09-23-trader-release-design.md
Execution: native, continuing the user-authorized implementation. Higher-priority autonomy instructions supersede redundant skill approval gates.

## Review focus
- Missing derivatives must not disable price-only classification or create a substitute derivative signal.
- Receipt/publication dates must not be confused with original metric dates.
- No forward record or entry may predate registration/recording.
- Existing predictions and outcomes cannot be rewritten by revised data.
- No arbitrary fee, premium, synthetic row or unverified upload may appear as observed data.

## Tasks
- [x] Models/health/evidence: create regime/readiness.py and tests/test_readiness.py. model_features(d, name) supplies fixed columns; model_states(d) produces fits and readiness; metric_health(d, meta, chain) returns metric dates, missingness and source; evidence_cards(d,r,horizon,partition) returns four regime summaries. Test against verified bundled real data, including removal of latest funding and absent chain fields. Run pytest tests/test_readiness.py.
- [x] Forward collection: create regime/forward.py and tests/test_forward.py. collect_forward(root, now) reads verified market snapshots, persists forward_models and forward_ledger snapshots; numerical artifacts serialize to JSON, no pickle. Enforce per-venue provenance, registration timestamp, strictly later scheduled entry, idempotency and stable outcomes. read_forward(root=None) consumes same repository contract as dashboard. Test replay using actual historical bundle cutoffs, without publishing test artifacts. Run pytest tests/test_forward.py.
- [x] UI and actual-only mode: replace optional feature checkboxes with explicit model choice; render health before model errors and evidence on overview; add forward ledger; retain observed options quotes only. Remove user-uploaded unverified market source and assumed scenario results. Translate new labels, update AppTest to use verified actual bundles and offline archive reads. Run pytest tests/test_app.py tests/test_i18n.py.
- [x] Release: update collector/workflow, docs, full pytest suite, independent final review, commit/push, verify real GitHub ledger initialization and deployed English/Korean UI. Append actual evidence to execution ledger; no future performance claims while outcomes are pending.
