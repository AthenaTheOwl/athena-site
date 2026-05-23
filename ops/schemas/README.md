# Cross-repo schemas

JSON Schemas (draft 2020-12) for the Cognitive Delivery Control Plane (CDCP)
artifact contracts. Each schema defines one record shape that the portfolio
shares across repos.

| File | Record |
|---|---|
| `decision.schema.json` | a DEC-* record (the *why* behind a change) |
| `dream-output.schema.json` | a weekly dream-job output with promotion candidates |
| `skill.schema.json` | a packaged reusable skill |
| `artifact.schema.json` | any typed output produced by a run |
| `run.schema.json` | a single agent run in a workspace or sandbox |

## Who uses these

Each product repo (chip-supply-chain-map, supplier-risk-rag-agent,
ai-field-brief, procurement-negotiation-lab, etc.) carries a
`scripts/validate_decisions.py` (or sibling validators) that fetches these
schemas at CI time and validates the repo's local `decisions/`, `dreams/`,
`skills/`, and `runs/` records against them.

Athena-site does not own the records. Athena-site owns the *contract* the
records must honor.

## How another repo references a schema

From a per-repo validator, fetch by raw URL:

```
https://raw.githubusercontent.com/AthenaTheOwl/athena-site/main/ops/schemas/decision.schema.json
```

A minimal Python validator looks like:

```python
import json, urllib.request, jsonschema

SCHEMA_URL = (
    "https://raw.githubusercontent.com/AthenaTheOwl/athena-site/"
    "main/ops/schemas/decision.schema.json"
)
schema = json.loads(urllib.request.urlopen(SCHEMA_URL).read())
for path in pathlib.Path("decisions").glob("DEC-*.json"):
    jsonschema.validate(json.loads(path.read_text(encoding="utf-8")), schema)
```

CI runs the validator; failures fail the build.

## Versioning policy

The schemas evolve under one rule: never break a downstream repo silently.

- **Backward-compatible change** (new optional field, looser enum, longer
  pattern): land it on `main`. Downstream repos pick it up on next CI run.
- **Breaking change** (new required field, tighter enum, renamed field):
  do not edit the existing file in place. Either bump to a major version
  (`decision.v2.schema.json` with a new `$id`) and migrate repos one by
  one, or land a sibling schema and deprecate the old one with a removal
  date in this README.

Downstream repos pin to `main` for now. When a v2 lands, repos that want to
stay on v1 should pin to a commit SHA in their validator URL.

## Local sanity check

```
python -c "import json, pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('ops/schemas').glob('*.schema.json')]"
```

Parses every schema file. CI runs the same line.
