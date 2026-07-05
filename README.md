# Workflow Search Catalog

Standalone searchable catalog of real-world workflow patterns, source repos, and
Codex/ECC config-package references.

## What Is Here

- `data/workflow-search-index.json` - clean 171-row searchable catalog.
- `data/workflow-search-index.csv` - spreadsheet-friendly catalog.
- `data/workflow-search-index-by-domain.json` - compact domain grouping.
- `reports/workflow-search-index.md` - human-readable summary and best matches.
- `scripts/query_workflow_catalog.py` - local search command.
- `scripts/build_workflow_search_index.py` - rebuilds the clean index from source-run JSON.
- `data/source-runs/` - reproducibility metadata and classified source rows, with logs excluded.

## Query Examples

```bash
python3 scripts/query_workflow_catalog.py "healthcare referral packet"
python3 scripts/query_workflow_catalog.py "education workflow"
python3 scripts/query_workflow_catalog.py "real estate due diligence"
python3 scripts/query_workflow_catalog.py "document processing human review"
python3 scripts/query_workflow_catalog.py "Codex config package"
```

## Quality Tiers

| Tier | Meaning |
| --- | --- |
| `gold` | Source reachable or canonicalized, high confidence, ready to copy/adapt. |
| `silver` | Useful reference with medium or better confidence. |
| `bronze` | Potentially useful but source needs repair or verification. |
| `needs_verification` | Searchable, but verify before relying on it. |

## Rebuild

```bash
python3 scripts/build_workflow_search_index.py
```

Then validate:

```bash
python3 -m json.tool data/workflow-search-index.json >/tmp/workflow-search-index.json
python3 -m json.tool data/workflow-search-index-by-domain.json >/tmp/workflow-search-index-by-domain.json
git diff --check
```

## Provenance

This repo was extracted from the local
`/Users/acecanacan/Documents/market-research-agent` workspace as an independent
catalog repository. Raw CLI logs are intentionally excluded; source manifests,
prompts, progress files, reports, schemas, and classified outputs are preserved
under `data/source-runs/`.
