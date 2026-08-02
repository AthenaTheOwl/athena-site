# Portfolio health — 2026-08-02

## Deploys

| Repo | URL | Status |
|---|---|---|
| athena-site | https://athena-site-six.vercel.app | ✅ 200 |
| chip-supply-chain-map | https://chip-supply-chain-map.vercel.app | ✅ 200 |
| supplier-risk-rag-agent | https://supplier-risk-rag-agent.streamlit.app | ✅ 200 |
| ai-field-brief | https://ai-field-brief.vercel.app | ✅ 200 |
| procurement-negotiation-lab | https://procurement-negotiation-lab.vercel.app | ✅ 200 |

## Content fingerprint

| Repo | URL | Expected | Status |
|---|---|---|---|
| athena-site | https://athena-site-six.vercel.app | `Portfolio doors`, `entry points` | PASS |
| chip-supply-chain-map | https://chip-supply-chain-map.vercel.app | `chip-supply-chain-map` | PASS |
| supplier-risk-rag-agent | https://supplier-risk-rag-agent.streamlit.app | `streamlit` | PASS |
| ai-field-brief | https://ai-field-brief.vercel.app | `ai-field-brief`, `2026-W31` | PASS |

## File freshness

| Repo | Path | Age (days) | Threshold | Status |
|---|---|---|---|---|
| chip-supply-chain-map | src/data/nodes.csv | 68 | 180 | ✅ |
| supplier-risk-rag-agent | reports/baseline_eval_report.html | 0 | 90 | ✅ |
| ai-field-brief | briefs/INDEX.md | 0 | 14 | ✅ |

## Stale active repos (threshold: 90d)

| Repo | Last commit (days ago) | Status |
|---|---|---|
| athena-site | 0 | ✅ |
| chip-supply-chain-map | 7 | ✅ |
| supplier-risk-rag-agent | 0 | ✅ |
| ai-field-brief | 0 | ✅ |
| procurement-negotiation-lab | 0 | ✅ |
| ai-supply-chain-copilot-prd | 27 | ✅ |
| mcp-security-lab | 0 | ✅ |
| trace-to-eval-harness | 0 | ✅ |
| sports-prediction-os | 27 | ✅ |
| dispatch-optimizer | 27 | ✅ |
| LLM-evaluation-framework | 27 | ✅ |
| News-Bias-Multi-Agent-Pipeline | 36 | ✅ |

## Starforge cluster forks

| Repo | Forks | Status |
|---|---|---|
| starforge-narrative-tools | 0 | ✅ |
| starforge-renpy-demo | 0 | ✅ |
| starforge-rpg-prototype | 0 | ✅ |

## Royal Road

- https://www.royalroad.com/fiction/149065/starforge-canticles — ⏭️ skipped (HTTP 404; likely anti-bot block; check manually)

## Manifest drift

- doors.json: 24 entries ✅

## CDCP status

| Repo | Door | CDCP status | Drift |
|---|---|---|---|
| athena-site | 11 | meta-repo, cross-repo-schemas | — |
| chip-supply-chain-map | 12 | installed, operating-model, first-decs, dreams-promoted | ✅ |
| supplier-risk-rag-agent | 13 | installed, operating-model, dreams-promoted, skills-graduated | ✅ |
| ai-field-brief | 18 | installed, operating-model, dreams-promoted, skills-graduated | ✅ |
| procurement-negotiation-lab | 17 | installed, operating-model, dreams-promoted, skills-graduated | ✅ |
| ai-supply-chain-copilot-prd | 10 | markdown-only, decisions-ledger | ✅ |
| mcp-security-lab | 19 | installed, operating-model, first-decs, dreams-promoted | ✅ |
| trace-to-eval-harness | 20 | installed, operating-model, first-decs | ✅ |
| sports-prediction-os | 21 | has_specs | ✅ |

## Anthropic models

Manual quarterly check required.

Required models: claude-sonnet-4-6

Verify at: https://docs.anthropic.com/en/docs/about-claude/model-deprecations

---
All critical checks passed.
