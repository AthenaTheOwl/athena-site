# Portfolio health — 2026-06-29

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
| athena-site | https://athena-site-six.vercel.app | `Portfolio doors`, `entry points` | ✅ present |
| chip-supply-chain-map | https://chip-supply-chain-map.vercel.app | `chip-supply-chain-map` | ✅ present |
| supplier-risk-rag-agent | https://supplier-risk-rag-agent.streamlit.app | `streamlit` | ✅ present |
| ai-field-brief | https://ai-field-brief.vercel.app | `ai-field-brief`, `2026-W23` | ✅ present |

## File freshness

| Repo | Path | Age (days) | Threshold | Status |
|---|---|---|---|---|
| chip-supply-chain-map | src/data/nodes.csv | 34 | 180 | ✅ |
| supplier-risk-rag-agent | reports/baseline_eval_report.html | 60 | 90 | ✅ |
| ai-field-brief | briefs/INDEX.md | 6 | 14 | ✅ |

## Stale active repos (threshold: 90d)

| Repo | Last commit (days ago) | Status |
|---|---|---|
| athena-site | 2 | ✅ |
| chip-supply-chain-map | 2 | ✅ |
| supplier-risk-rag-agent | 2 | ✅ |
| ai-field-brief | 2 | ✅ |
| procurement-negotiation-lab | 0 | ✅ |
| ai-supply-chain-copilot-prd | 2 | ✅ |
| mcp-security-lab | 2 | ✅ |
| trace-to-eval-harness | 2 | ✅ |
| sports-prediction-os | 2 | ✅ |
| dispatch-optimizer | 2 | ✅ |
| LLM-evaluation-framework | 2 | ✅ |
| News-Bias-Multi-Agent-Pipeline | 2 | ✅ |

## Starforge cluster forks

| Repo | Forks | Status |
|---|---|---|
| starforge-narrative-tools | 0 | ✅ |
| starforge-renpy-demo | 0 | ✅ |
| starforge-rpg-prototype | 0 | ✅ |

## Royal Road

- https://www.royalroad.com/fiction/149065/starforge-canticles — ⏭️ skipped (HTTP 404; likely anti-bot block; check manually)

## Manifest drift

- doors.json: 21 entries ✅

## CDCP status

| Repo | Door | CDCP status | Drift |
|---|---|---|---|
| athena-site | 11 | meta-repo, cross-repo-schemas | ⚠️ local_root unresolved |
| chip-supply-chain-map | 12 | installed, operating-model, first-decs | ⚠️ local_root unresolved |
| supplier-risk-rag-agent | 13 | installed, operating-model, dreams-promoted, skills-graduated | ⚠️ local_root unresolved |
| ai-field-brief | 18 | installed, operating-model, dreams-promoted, skills-graduated | ⚠️ local_root unresolved |
| procurement-negotiation-lab | 17 | installed, operating-model, dreams-promoted, skills-graduated | ⚠️ local_root unresolved |
| ai-supply-chain-copilot-prd | 10 | markdown-only, decisions-ledger | ⚠️ local_root unresolved |
| mcp-security-lab | 19 | installed, operating-model, first-decs | ⚠️ local_root unresolved |
| trace-to-eval-harness | 20 | installed, operating-model, first-decs | ⚠️ local_root unresolved |
| sports-prediction-os | 21 | cdcp-lite, has_specs | ⚠️ local_root unresolved |

## Anthropic models

Manual quarterly check required.

Required models: claude-sonnet-4-6

Verify at: https://docs.anthropic.com/en/docs/about-claude/model-deprecations

---
All critical checks passed.
