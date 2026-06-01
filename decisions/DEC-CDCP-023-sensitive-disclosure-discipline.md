---
id: DEC-CDCP-023-sensitive-disclosure-discipline
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-039..042
date: 2026-05-30
status: approved
reversible: true
owner: security.threat-modeler
decision: |
  Credential incident investigations do not land as detailed public source
  artifacts. Public repos may carry only sanitized policy, status, and control
  changes; raw findings, scanner output, provider identifiers, exact paths,
  remediation command material, and revocation notes stay in local gitignored
  notes or provider consoles.
alternatives:
  - label: commit detailed investigation notes for traceability
    rejected_because: |
      Detailed notes make source control part of the exposure surface. The
      record becomes searchable, forkable, and cacheable even after later
      cleanup. Traceability is useful, but it must not outweigh minimizing the
      disclosure footprint during credential response.
  - label: rely on provider push protection only
    rejected_because: |
      Provider checks are necessary, but they mainly catch literal credential
      strings. They do not reliably block over-detailed writeups that reveal
      enough structure for a reader to reconstruct the incident.
  - label: keep all process knowledge only in chat
    rejected_because: |
      Chat-only process disappears from the repo's controls. The safe middle is
      to commit the rule and the gate, not the sensitive incident details.
rationale: |
  Security response has a different artifact boundary than ordinary product
  governance. Most DEC and runbook work benefits from rich written evidence.
  Credential response benefits from minimum disclosure: rotate externally,
  remove source exposure, add guardrails, and keep the detailed notes local.
  This decision makes that boundary explicit so future workflow agents cannot
  turn an investigation into another committed exposure.
evidence:
  - kind: decision
    ref: decisions/DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: repo
    ref: AthenaTheOwl/mcp-security-lab
  - kind: local-note
    ref: local gitignored incident notes retained outside public source
rollback: |
  Supersede this DEC with a stricter or looser disclosure policy. Do not restore
  detailed credential-response notes to public source control as part of rollback.
systems_map: |
  The system changes the publication boundary for security work. Investigation
  detail remains operational state; committed source receives only reusable
  controls and sanitized status.
transferable_principle: |
  Security artifacts should be written for the minimum audience that can act on
  them. Public repositories get durable controls, not operational breadcrumbs.
falsification_test: |
  If future credential incidents can be investigated, rotated, remediated, and
  audited without any local-only notes, then a richer committed artifact may be
  reconsidered. Until then, minimum disclosure is the safer default.
adoption_ladder:
  minimum_viable: "Local hooks block obvious sensitive disclosures before commit."
  mid_adoption: "CI gates block sensitive disclosure patterns in public repos."
  full_adoption: "Provider-side push protection is enabled wherever the platform allows it."
  monitoring_signals:
    - "No committed credential-response notes contain operational details."
    - "Sensitive disclosure gate runs in CI for public control repos."
    - "Workflow prompts require local-only storage for raw investigation output."
---
