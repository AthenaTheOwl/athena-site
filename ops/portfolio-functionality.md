# Portfolio functionality audit

This report checks whether each repo has a concrete proof surface: entrypoint, run/test evidence, deploy-target fit, and reviewer-facing docs.

## summary

| Verdict | Count |
|---|---:|
| functional | 47 |
| archive-functional | 1 |
| profile-index | 1 |
| likely-functional-needs-polish | 17 |
| ambiguous | 0 |
| needs-work | 0 |
| missing-local | 0 |

## highest-priority gaps

| Repo | Score | Target | Findings |
|---|---:|---|---|

## all repos

| Repo | Verdict | Score | Entrypoints | Proof | Findings |
|---|---|---:|---|---|---|
| leetcode | archive-functional | 70 |  | scripts/validate_archive.py |  |
| agent-notary-layer | functional | 80 | pyproject.toml, src/notary/__main__.py, streamlit_app.py | pyproject.toml, tests, tests/test_cli.py, tests/test_conformance.py |  |
| ai-field-brief | functional | 95 | package.json, vercel.json | docs/deploy.md, examples, package.json, scripts/validate_decisions.py |  |
| ai-supply-chain-copilot-prd | functional | 95 | index.html, package.json, vercel.json | examples, package.json, scripts/validate_decisions.py, vite.config.js |  |
| athena-site | functional | 95 | package.json | package.json, scripts/validate_schema_graph.py, scripts/validate_sensitive_disclosures.py, tests |  |
| binding-constraint | functional | 80 | pyproject.toml, streamlit_app.py | data, pyproject.toml, reports, tests |  |
| brief-matrix | functional | 80 | pyproject.toml, streamlit_app.py | data, pyproject.toml, scripts/validate_schemas.py, scripts/validate_tenants.py |  |
| capital-build-reconciler | functional | 80 | pyproject.toml, src/capital_reconcile/__main__.py, streamlit_app.py | pyproject.toml, reports, scripts/validate_pillars.py, scripts/validate_schemas.py |  |
| commit-provenance | functional | 80 | pyproject.toml, streamlit_app.py | pyproject.toml, reports, tests, tests/test_cli.py |  |
| dispatch-optimizer | functional | 80 | streamlit_app.py | tests, tests/test_integrity.py |  |
| dream-replay-cli | functional | 80 | pyproject.toml, src/dreamreplay/__main__.py, streamlit_app.py | data, pyproject.toml, scripts/validate_schemas.py, tests |  |
| earnings-pillar-diff | functional | 80 | pyproject.toml, streamlit_app.py | pyproject.toml, reports, scripts/validate_memo_schema.py, tests |  |
| eval-forge | functional | 80 | pyproject.toml, streamlit_app.py | examples, pyproject.toml, reports, tests |  |
| fab-risk-radar | functional | 80 | pyproject.toml, src/frr/__main__.py, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_schemas.py |  |
| facility-war | functional | 80 | pyproject.toml, src/facility_war/__main__.py, streamlit_app.py | pyproject.toml, reports, scripts/validate_schemas.py, tests |  |
| grid-silicon | functional | 80 | pyproject.toml, src/grid_silicon/__main__.py, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_schemas.py |  |
| interconnect-alpha | functional | 80 | pyproject.toml, streamlit_app.py | data, pyproject.toml, reports, tests |  |
| mcp-security-lab | functional | 80 | pyproject.toml, streamlit_app.py | examples, pyproject.toml, reports, scripts/validate_athena_mcp_surface.py |  |
| MIT-AI-Fall20 | functional | 80 | Lab0/tester.py, Lab1/tester.py, Lab2/tester.py, Lab3/tester.py | Lab0/tester.py, Lab1/tester.py, Lab2/tester.py, Lab3/test_problems.py |  |
| MIT-SDM-Thesis-on-System-Dynamics-Modeling-of-Bitcoin | functional | 80 | streamlit_app.py | scripts/validate_thesis_archive.py |  |
| modelswap-replay | functional | 80 | pyproject.toml, streamlit_app.py | pyproject.toml, reports, scripts/validate_schemas.py, tests |  |
| multitier-psi | functional | 80 | pyproject.toml, src/mtpsi/__main__.py, streamlit_app.py | data, examples, pyproject.toml, scripts/validate_schemas.py |  |
| negotiation-mechanism-replay | functional | 80 | pyproject.toml, src/replay/__main__.py, streamlit_app.py | examples, pyproject.toml, reports, scripts/validate_replay_schema.py |  |
| oulipo-memory-deck | functional | 80 | pyproject.toml, streamlit_app.py | pyproject.toml, tests, tests/test_no_network.py, tests/test_render.py |  |
| pattern-index | functional | 80 | pyproject.toml, src/pattern_index/__main__.py, streamlit_app.py | pyproject.toml, reports, scripts/validate_outcomes.py, scripts/validate_schemas.py |  |
| policy-replay | functional | 80 | pyproject.toml, src/policy_replay/__main__.py, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_schemas.py |  |
| portfolio-manifest | functional | 80 | pyproject.toml, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_decisions.py |  |
| power-ppa-forge | functional | 80 | pyproject.toml, streamlit_app.py | pyproject.toml, reports, scripts/validate_leakage_bound.py, scripts/validate_schemas.py |  |
| procurement-pattern-library | functional | 80 | pyproject.toml, streamlit_app.py | data, pyproject.toml, scripts/validate_outcomes.py, scripts/validate_patterns.py |  |
| ratepayer-exposure | functional | 95 | package.json | package.json |  |
| release-pillar-mapper | functional | 80 | pyproject.toml, src/release_mapper/__main__.py, src/release_pillar_mapper/__main__.py, streamlit_app.py | examples, pyproject.toml, reports, scripts/validate_release_event.py |  |
| repo-position-coupling-index | functional | 80 | pyproject.toml, src/coupling/__main__.py, streamlit_app.py | examples, pyproject.toml, reports, scripts/validate_coupling_index.py |  |
| review-queue | functional | 80 | pyproject.toml, streamlit_app.py | data, examples, pyproject.toml, scripts/validate_decisions.py |  |
| Robust-Facility-Location | functional | 80 | app.py, streamlit_app.py | DEPLOY.md |  |
| robust-siting-lab | functional | 80 | pyproject.toml, streamlit_app.py | pyproject.toml, reports, scripts/validate_schemas.py, tests |  |
| sealed-bid-sourcing | functional | 80 | pyproject.toml, src/sealed_bid_sourcing/__main__.py, streamlit_app.py | pyproject.toml, reports, scripts/validate_leakage_bound.py, scripts/validate_schemas.py |  |
| semiconductor-e2e-manufacturing-optimization | functional | 80 | app.py, streamlit_app.py | DEPLOY.md, validate.py |  |
| source-decay-ledger | functional | 80 | pyproject.toml, src/source_decay_ledger/__main__.py, streamlit_app.py | data, pyproject.toml, tests, tests/test_cli.py |  |
| sovereign-compute | functional | 80 | pyproject.toml, src/sovereign_compute/__main__.py, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_schemas.py |  |
| starforge-choicescript-demo | functional | 85 | package.json, vercel.json | package.json, tests |  |
| starforge-narrative-tools | functional | 80 | pyproject.toml, streamlit_app.py | pyproject.toml, tests, tests/test_corpus_integrity.py, tests/test_tooling_compiles.py |  |
| starforge-renpy-demo | functional | 80 | pyproject.toml | pyproject.toml, tests, tests/test_check_release.py, tests/test_clean_copy.py |  |
| starforge-rpg-prototype | functional | 80 | pyproject.toml | data, examples, pyproject.toml, scripts/validate_balance.py |  |
| starforge-twine-demo | functional | 90 | package.json, vercel.json | package.json, playwright.config.ts, tests |  |
| trace-ledger-spec | functional | 80 | pyproject.toml, streamlit_app.py | examples, pyproject.toml, tests, tests/test_cli.py |  |
| trace-to-eval-cli | functional | 80 | pyproject.toml, streamlit_app.py | examples, pyproject.toml, reports, scripts/validate_schemas.py |  |
| wafer-to-watt | functional | 80 | pyproject.toml, src/wtw/__main__.py, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_schemas.py |  |
| world-food-program-robust-simulator | functional | 80 | app.py, streamlit_app.py | DEPLOY.md, data, tests, tests/test_hybrid_nodes.py |  |
| brief-calibration | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | data, pyproject.toml, tests, tests/test_cli.py | README still contains scaffold/placeholder language |
| channel-atlas | likely-functional-needs-polish | 65 | pyproject.toml, src/channel_atlas/__main__.py, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_schemas.py | README still contains scaffold/placeholder language |
| chip-supply-chain-map | likely-functional-needs-polish | 80 | index.html, package.json, vercel.json | package.json, scripts/test_chaos_run_evidence.py, scripts/test_finalize_sandbox_ref.py, scripts/test_replay_determinism.py | README still contains scaffold/placeholder language |
| LLM-evaluation-framework | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | pyproject.toml, tests, tests/test_cli.py, tests/test_config.py | README still contains scaffold/placeholder language |
| News-Bias-Multi-Agent-Pipeline | likely-functional-needs-polish | 75 | app.py, main.py, streamlit_app.py | docs/deploy.md, scripts/validate_sensitive_disclosures.py, tests, tests/eval/test_bias_calls.py | README still contains scaffold/placeholder language |
| portfolio-thesis-plane | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_registry.py | README still contains scaffold/placeholder language |
| pre-mortem-ledger | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | data, examples, pyproject.toml, scripts/validate_premortem_schema.py | README still contains scaffold/placeholder language |
| procurement-negotiation-lab | likely-functional-needs-polish | 80 | app.py, package.json, pyproject.toml, vercel.json | _legacy/tests/test_algorithms.py, _legacy/tests/test_defaults.py, _legacy/tests/test_formula_engine.py, _legacy/tests/test_formulations.py | README still contains scaffold/placeholder language |
| promotion-vs-pip | likely-functional-needs-polish | 75 | package.json, print.example.html, print.html, vercel.json | package.json, scripts/build_site.js, scripts/render_cards.js, scripts/validate_cards.js | README still contains scaffold/placeholder language |
| proof-gate-runner | likely-functional-needs-polish | 65 | streamlit_app.py | examples, tests | README still contains scaffold/placeholder language |
| puc-docket-rag | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | data, pyproject.toml, scripts/validate_schemas.py, tests | README still contains scaffold/placeholder language |
| repo-triage | likely-functional-needs-polish | 65 | pyproject.toml, src/repo_triage/__main__.py, streamlit_app.py | data, pyproject.toml, scripts/validate_schemas.py, tests | README still contains scaffold/placeholder language |
| site-atlas | likely-functional-needs-polish | 80 | package.json | package.json | README still contains scaffold/placeholder language |
| sports-prediction-os | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | data, pyproject.toml, scripts/validate_sensitive_disclosures.py, tests | README still contains scaffold/placeholder language |
| supplier-risk-rag-agent | likely-functional-needs-polish | 65 | app.py, pyproject.toml, streamlit_app.py | data, pyproject.toml, reports, scripts/validate_decision_records.py | README still contains scaffold/placeholder language |
| thesis-pillar-tracker | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | pyproject.toml, reports, scripts/validate_pillar_schema.py, tests | README still contains scaffold/placeholder language |
| trace-to-eval-harness | likely-functional-needs-polish | 65 | pyproject.toml, streamlit_app.py | examples, pyproject.toml, reports, scripts/validate_decisions.py | README still contains scaffold/placeholder language |
| AthenaTheOwl | profile-index | 55 |  |  | no obvious executable entrypoint; README lacks explicit run/test verification; README still contains scaffold/placeholder language |
