# Workflow Search Catalog

Standalone searchable catalog of real-world workflow patterns, source repos, and
Codex/ECC config-package references.

## Install / Run

Prerequisites:

- Node.js 18+
- Python 3

Run directly from GitHub:

```bash
npx --yes github:Eys-55/workflow-search-catalog "healthcare referral packet" --ecc --limit 7
```

After npm publishing, the command becomes:

```bash
npx workflow-search-catalog "healthcare referral packet" --ecc --limit 7
```

The CLI requires Python 3 because the catalog search engine is Python-backed.
Set `PYTHON=/path/to/python` if your Python executable is not `python3`,
`python`, or `py -3`.

## CLI

```bash
workflow-search-catalog "<workflow idea>" [--ecc] [--json] [--limit 7] [--domain DOMAIN] [--family FAMILY] [--include-low]
```

Recommended default:

```bash
workflow-search-catalog "real estate due diligence" --ecc --limit 7
```

Use `--ecc` to include the ECC mini-contract:

- repeated real-world job;
- input contract;
- output artifact;
- workflow pattern;
- agent lanes;
- source/tool boundary;
- validation gate;
- human-review boundary;
- safety boundary;
- suggested `skills/<slug>/SKILL.md` path.

Use `--json` when another script or agent needs structured output.

## What Is Here

The installable CLI package ships:

- `data/workflow-search-index.json` - clean 171-row searchable catalog.
- `data/workflow-search-index.csv` - spreadsheet-friendly catalog.
- `data/workflow-search-index-by-domain.json` - compact domain grouping.
- `reports/workflow-search-index.md` - human-readable summary and best matches.
- `scripts/query_workflow_catalog.py` - local search command.

The GitHub repository also preserves rebuild and audit metadata:

- `scripts/build_workflow_search_index.py` - rebuilds the clean index from source-run JSON.
- `data/source-runs/` - reproducibility metadata and classified source rows, with logs excluded.

## Query Examples

```bash
workflow-search-catalog "healthcare referral packet" --ecc --limit 7
workflow-search-catalog "education workflow" --ecc --limit 7
workflow-search-catalog "real estate due diligence" --ecc --limit 7
workflow-search-catalog "document processing human review" --ecc --limit 7
workflow-search-catalog "Codex config package" --ecc --limit 7
```

Use `--json` with `--ecc` when another script needs both the normalized
`ecc_contract` and ranked catalog matches.

## Quality Tiers

| Tier | Meaning |
| --- | --- |
| `gold` | Source reachable or canonicalized, high confidence, ready to copy/adapt. |
| `silver` | Useful reference with medium or better confidence. |
| `bronze` | Potentially useful but source needs repair or verification. |
| `needs_verification` | Searchable, but verify before relying on it. |

## Rebuild From GitHub Repo

Rebuild requires a full GitHub checkout because source-run metadata is excluded
from the npm package:

```bash
python3 scripts/build_workflow_search_index.py
```

Then validate:

```bash
python3 -m json.tool data/workflow-search-index.json >/tmp/workflow-search-index.json
python3 -m json.tool data/workflow-search-index-by-domain.json >/tmp/workflow-search-index-by-domain.json
git diff --check
```

## ECC Packaging Contract

This package is a catalog and router, not the runtime for the final workflow.
ECC remains the workflow design method:

- lock the repeated real-world job first;
- define input and output contracts;
- split source, integration, validation, and review lanes;
- preserve source evidence and caveats;
- add validation/eval gates before trusting output;
- keep human approval boundaries explicit;
- extract repeated workflows into `skills/<workflow>/SKILL.md`.

Catalog matches are references for what to copy or ignore. Do not treat any
external repo, app platform, or template as the source of truth for a final
high-stakes workflow.

## Release Checklist

Before publishing:

```bash
npm run release:check
npx --yes github:Eys-55/workflow-search-catalog "healthcare referral packet" --ecc --limit 1
```

Then publish only from a clean `main` branch:

```bash
npm publish --access public
```

The npm package intentionally ships only the CLI, clean search index, compact
domain index, CSV export, report, license, and README. Reproducibility metadata
stays in the GitHub repo but is excluded from the npm package.

## Provenance

This repo was extracted from the local
`/Users/acecanacan/Documents/market-research-agent` workspace as an independent
catalog repository. Raw CLI logs are intentionally excluded; source manifests,
prompts, progress files, reports, schemas, and classified outputs are preserved
under `data/source-runs/`.
