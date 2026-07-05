#!/usr/bin/env python3
"""Query the clean workflow search index."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data" / "workflow-search-index.json"

QUERY_EXPANSIONS = {
    "health": ["healthcare", "healthcare_admin", "document_transformation", "compliance_human_review"],
    "healthcare": ["healthcare", "healthcare_admin", "document_transformation", "compliance_human_review"],
    "medical": ["healthcare", "healthcare_admin"],
    "patient": ["healthcare", "healthcare_admin", "document_transformation"],
    "referral": ["healthcare", "document_transformation", "case_intake_review"],
    "education": ["education", "education_support"],
    "student": ["education", "education_support"],
    "real estate": ["real_estate", "evidence_due_diligence"],
    "property": ["real_estate", "evidence_due_diligence"],
    "due diligence": ["evidence_due_diligence", "real_estate", "public_evidence"],
    "public evidence": ["public_evidence", "evidence_due_diligence", "source_taxonomy"],
    "permit": ["public_evidence", "evidence_due_diligence", "compliance_human_review"],
    "document": ["document_processing", "document_transformation"],
    "pdf": ["document_processing", "document_transformation"],
    "ocr": ["document_processing", "document_transformation"],
    "human review": ["compliance_human_review", "case_intake_review"],
    "approval": ["compliance_human_review", "case_intake_review"],
    "case intake": ["case_intake_review", "legal_casework"],
    "legal": ["legal_casework", "case_intake_review"],
    "automation": ["automation", "automation_queue"],
    "queue": ["automation_queue", "automation"],
    "monitoring": ["monitoring", "automation_queue"],
    "research": ["research", "research_knowledge"],
    "codex": ["codex_config_candidate", "config_package_registry", "skill_package_reference"],
    "config package": ["codex_config_candidate", "config_package_registry"],
    "skill": ["skill_package_reference", "config_package_registry"],
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "find",
    "like",
    "me",
    "my",
    "of",
    "the",
    "to",
    "workflow",
    "workflows",
}

TIER_WEIGHT = {"gold": 14, "silver": 9, "bronze": 4, "needs_verification": 0}
USEFULNESS_WEIGHT = {
    "copy_or_adapt_now": 10,
    "strong_reference": 7,
    "translate_pattern_only": 4,
    "use_with_caution": 2,
    "verify_source_first": 0,
}

ECC_CONTRACT_TEMPLATES = {
    "healthcare": {
        "repeated_real_world_job": "Transform patient, referral, or source documents into a review-ready healthcare packet.",
        "domain": "healthcare",
        "input_contract": "patient/referral/source documents, forms, notes, and user-supplied constraints",
        "output_artifact": "clean packet, summary, checklist, and review-ready draft",
        "workflow_pattern": "DocumentTransformation + CaseIntake + ComplianceHumanReview",
        "agent_lanes": [
            "intake lane: identify source files, missing fields, and patient/referral context",
            "document lane: extract, normalize, and summarize source material",
            "validation lane: check provenance, completeness, PHI handling, and contradictions",
            "review lane: prepare handoff for clinician or administrative approval",
        ],
        "tool_or_source_boundary": "Use only user-provided documents, approved internal sources, or explicitly authorized systems; do not submit, diagnose, prescribe, or certify.",
        "validation_gate": "Require source traceability, required-field completeness, PHI boundary review, and human approval before final action.",
        "human_review_boundary": "Human review required before submission, clinical use, billing action, or patient-facing conclusion.",
        "safety_boundary": "Must not make medical, legal, coverage, or compliance conclusions without qualified human review.",
    },
    "education": {
        "repeated_real_world_job": "Turn student, course, curriculum, or assessment information into a structured education-support artifact.",
        "domain": "education",
        "input_contract": "student/course context, rubric, curriculum materials, assignments, assessment records, or support notes",
        "output_artifact": "lesson plan, feedback packet, support checklist, study plan, or assessment summary",
        "workflow_pattern": "EducationSupport + Assessment + HumanReview",
        "agent_lanes": [
            "intake lane: identify learner/course context and missing constraints",
            "content lane: map source material to curriculum or support goals",
            "assessment lane: draft feedback, rubric alignment, or next-step recommendations",
            "review lane: flag sensitive issues and prepare educator approval handoff",
        ],
        "tool_or_source_boundary": "Use provided educational material and approved school sources; do not make disciplinary, clinical, or high-stakes placement decisions.",
        "validation_gate": "Check rubric alignment, source coverage, missing context, age/safety sensitivity, and educator approval needs.",
        "human_review_boundary": "Teacher, advisor, or administrator reviews before student-facing or official use.",
        "safety_boundary": "Must not determine diagnoses, discipline, accommodations, grades, or placement without authorized human decision-makers.",
    },
    "real_estate": {
        "repeated_real_world_job": "Collect and qualify property, lease, permit, parcel, or transaction evidence for due diligence.",
        "domain": "real_estate",
        "input_contract": "property name/address, listing, parcel record, lease, deal memo, permit clue, or source documents",
        "output_artifact": "due-diligence memo, issue log, evidence packet, underwriting checklist, or closing handoff",
        "workflow_pattern": "EvidenceDueDiligence + DocumentAbstraction + HumanReview",
        "agent_lanes": [
            "identity lane: lock property, parcel, jurisdiction, and asset type",
            "record lane: collect public records, permits, listings, and official source traces",
            "document lane: abstract leases, deal documents, and provided files",
            "risk lane: flag gaps, contradictions, missing records, and manual follow-ups",
            "review lane: prepare source-attributed handoff for human decision",
        ],
        "tool_or_source_boundary": "Use public records, user-provided documents, and authorized databases; do not file, certify, transact, or provide legal conclusions.",
        "validation_gate": "Require source URLs, jurisdiction fit, entity/property identity checks, issue log, and manual follow-up list.",
        "human_review_boundary": "Human review required before investment, legal, financing, closing, or compliance action.",
        "safety_boundary": "Must not claim title, compliance, valuation certainty, legal sufficiency, or investment suitability without professional review.",
    },
    "document_processing": {
        "repeated_real_world_job": "Transform messy source documents into structured, traceable, review-ready artifacts.",
        "domain": "document_processing",
        "input_contract": "PDFs, scans, forms, transcripts, notes, files, or document sets",
        "output_artifact": "structured extraction, clean summary, redline, checklist, packet, or review draft",
        "workflow_pattern": "DocumentTransformation + ValidationGate + HumanReview",
        "agent_lanes": [
            "ingestion lane: identify file types, quality, and missing inputs",
            "extraction lane: extract text, fields, tables, or sections",
            "normalization lane: map data into the target schema or packet",
            "validation lane: check provenance, confidence, omissions, and contradictions",
            "review lane: prepare human approval handoff",
        ],
        "tool_or_source_boundary": "Use provided files and approved extraction tools; do not submit, sign, certify, or overwrite originals.",
        "validation_gate": "Require source traceability, extraction confidence, schema completeness, and unresolved-item list.",
        "human_review_boundary": "Human approval required before final submission, signature, publication, or operational action.",
        "safety_boundary": "Must not hide uncertain extraction, infer missing facts as true, or make regulated conclusions without review.",
    },
    "public_evidence": {
        "repeated_real_world_job": "Gather, qualify, and package public evidence about a place, entity, incident, permit, or claim.",
        "domain": "public_evidence",
        "input_contract": "place/entity name, address, link, claim, incident clue, source list, or user question",
        "output_artifact": "source-attributed evidence packet, confidence labels, caveats, and manual follow-up list",
        "workflow_pattern": "EvidenceAudit + PublicRecordsInvestigation + ComplianceBoundary + HumanReview",
        "agent_lanes": [
            "identity lane: confirm exact target and jurisdiction",
            "source lane: collect official, public-record, news, and source-taxonomy evidence",
            "context lane: gather relevant standards, process, or hazard context",
            "validation lane: check reachability, freshness, citation quality, and conflicts",
            "review lane: block overclaims and prepare manual-request handoff",
        ],
        "tool_or_source_boundary": "Use public sources and user-provided materials only; no credentials, bypasses, paid actions, filings, or third-party writes.",
        "validation_gate": "Require source URL, freshness/reachability signal, claim/source separation, confidence label, and caveat list.",
        "human_review_boundary": "Human review required before safety, compliance, legal, engineering, occupancy, or official conclusions.",
        "safety_boundary": "Absence of public evidence is not proof; must not certify compliance, safety, legality, or fault.",
    },
    "automation": {
        "repeated_real_world_job": "Process a queue of recurring business items with validation, exceptions, and human approval where needed.",
        "domain": "automation",
        "input_contract": "queue items, tickets, records, forms, emails, files, or event triggers",
        "output_artifact": "processed item, exception log, status update, draft action, or review queue",
        "workflow_pattern": "WorkQueueOps + BatchOps + ValidationGate + HumanReview",
        "agent_lanes": [
            "intake lane: normalize each queue item and assign status",
            "processing lane: perform allowed deterministic and agentic steps",
            "exception lane: detect missing fields, conflicts, and failed validations",
            "review lane: route uncertain or high-impact items to humans",
        ],
        "tool_or_source_boundary": "Operate only within approved read/write boundaries; external writes, payments, publishing, or irreversible actions require approval.",
        "validation_gate": "Require per-item status, retry/error handling, idempotency check, and exception report.",
        "human_review_boundary": "Human approval required for irreversible, high-impact, regulated, or uncertain actions.",
        "safety_boundary": "Must not silently skip failed items, hide uncertainty, or execute irreversible actions without explicit approval.",
    },
    "codex_config": {
        "repeated_real_world_job": "Turn a repeated real-world job into a reusable Codex/ECC workflow package.",
        "domain": "agent_workflows",
        "input_contract": "workflow idea, target users, source types, desired output artifact, safety limits, and example cases",
        "output_artifact": "Codex/ECC skill pack blueprint with SKILL.md contract, schemas, fixtures, validators, examples, and handoff docs",
        "workflow_pattern": "ConfigPackageRegistry + SkillPackageReference + EvalGate",
        "agent_lanes": [
            "contract lane: lock repeated job, trigger/refusal scope, input, and output",
            "pattern lane: compare catalog matches and extract what to copy or ignore",
            "package lane: draft skill, schemas, fixtures, validators, and examples",
            "review lane: validate trigger behavior, safety boundary, and handoff readiness",
        ],
        "tool_or_source_boundary": "Use local repo artifacts and approved references first; do not make external runtimes the architecture unless requested.",
        "validation_gate": "Require skill validation, fixture runs, schema checks, and one realistic transcript or sample output.",
        "human_review_boundary": "Human approval required before installing globally, publishing, or using in high-stakes workflows.",
        "safety_boundary": "Must not treat inspiration repos as source of truth; ECC owns the contract and validation gates.",
    },
    "generic": {
        "repeated_real_world_job": "Turn a repeated real-world task into a source-attributed, reviewable workflow artifact.",
        "domain": "general",
        "input_contract": "user-provided task description, source materials, constraints, and target output needs",
        "output_artifact": "workflow blueprint, evidence packet, checklist, report, or review-ready draft",
        "workflow_pattern": "WorkflowContract + ValidationGate + HumanReview",
        "agent_lanes": [
            "intake lane: identify repeated job, inputs, missing details, and refusal scope",
            "source lane: gather or inspect approved evidence and materials",
            "integration lane: produce the target artifact with traceability",
            "validation lane: run schema, source, completeness, and safety checks",
            "review lane: prepare human handoff and unresolved questions",
        ],
        "tool_or_source_boundary": "Use local, public, or explicitly authorized sources; block credentials, paid actions, publishing, and irreversible writes unless approved.",
        "validation_gate": "Require input completeness, source traceability, expected failure cases, and human-review boundary.",
        "human_review_boundary": "Human review required before external action, regulated conclusion, or final operational use.",
        "safety_boundary": "Must not overclaim, hide missing evidence, or act outside the approved tool/source boundary.",
    },
}


def tokenize(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if len(token) > 1 and token not in STOPWORDS]


def expand_terms(query: str) -> list[str]:
    normalized = query.lower()
    expanded: list[str] = []
    for phrase, terms in QUERY_EXPANSIONS.items():
        if phrase in normalized:
            expanded.extend(terms)
    return list(dict.fromkeys(expanded))


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64].strip("-") or "workflow"


def infer_contract_key(query: str, expanded: list[str], matches: list[dict[str, Any]]) -> str:
    normalized = query.lower()
    expanded_set = set(expanded)

    if {"codex_config_candidate", "config_package_registry", "skill_package_reference"} & expanded_set:
        return "codex_config"
    if "education" in expanded_set or "student" in normalized:
        return "education"
    if "real_estate" in expanded_set:
        return "real_estate"
    if "healthcare" in expanded_set:
        return "healthcare"
    if "document_processing" in expanded_set or "document_transformation" in expanded_set:
        return "document_processing"
    if {"public_evidence", "evidence_due_diligence", "source_taxonomy"} & expanded_set:
        return "public_evidence"
    if {"automation", "automation_queue", "monitoring"} & expanded_set:
        return "automation"

    for item in matches[:3]:
        row = item["row"]
        domain = row["normalized_domain"]
        family = row["workflow_family"]
        if domain in {"healthcare", "education", "real_estate", "document_processing", "automation"}:
            return domain
        if domain == "agent_workflows" or family == "config_package_registry":
            return "codex_config"
        if family in {"public_evidence", "evidence_due_diligence", "source_taxonomy"}:
            return "public_evidence"

    return "generic"


def build_ecc_contract(query: str, expanded: list[str], matches: list[dict[str, Any]]) -> dict[str, Any]:
    key = infer_contract_key(query, expanded, matches)
    template = dict(ECC_CONTRACT_TEMPLATES[key])
    top_rows = [item["row"] for item in matches[:3]]

    if top_rows:
        top = top_rows[0]
        if key == "generic":
            template["domain"] = top["normalized_domain"]
            template["workflow_pattern"] = top["workflow_family"]
            template["input_contract"] = top["input_contract"]
            template["output_artifact"] = top["output_artifact"]
            template["validation_gate"] = top["validation_gate"]
            template["human_review_boundary"] = top["human_review_boundary"]
            template["safety_boundary"] = top["safety_boundary"]

    candidate_slug_parts = [query]
    if top_rows:
        candidate_slug_parts.append(top_rows[0]["workflow_family"])
    template["suggested_skill_slug"] = slugify(" ".join(candidate_slug_parts))
    template["assumptions"] = build_contract_assumptions(query, expanded, top_rows, key)
    return template


def build_contract_assumptions(query: str, expanded: list[str], rows: list[dict[str, Any]], key: str) -> list[str]:
    assumptions = [
        "The user wants a reusable Codex/ECC workflow package, not a one-off answer.",
        "Local catalog matches are references for workflow shape; ECC remains the contract and validation method.",
    ]
    if key != "codex_config":
        assumptions.append("The workflow should become a skill only after the repeated job, input contract, and output artifact are stable.")
    if not rows:
        assumptions.append("No high-confidence local catalog match was found; use the generic ECC contract and refresh sources only if requested.")
    elif any(row["quality_tier"] == "needs_verification" for row in rows):
        assumptions.append("Some matches need source verification before copying their pattern.")
    if "latest" in query.lower() or "current" in query.lower() or "new" in query.lower():
        assumptions.append("The query asks for freshness; after local matching, verify current source state live.")
    return assumptions


def score_row(row: dict[str, Any], tokens: list[str], expanded: list[str], include_low: bool) -> tuple[int, list[str]]:
    if not include_low and row["quality_tier"] == "needs_verification":
        return 0, []

    haystack = row["searchable_text"]
    score = TIER_WEIGHT.get(row["quality_tier"], 0) + USEFULNESS_WEIGHT.get(row["codex_usefulness"], 0)
    reasons: list[str] = []

    for term in expanded:
        if term in {
            row["normalized_domain"],
            row["workflow_family"],
            row["fit"],
            row["quality_tier"],
            row["codex_usefulness"],
        }:
            score += 18
            reasons.append(term)
        elif term in haystack:
            score += 10
            reasons.append(term)

    for token in tokens:
        if token in haystack:
            score += 3
            if len(reasons) < 8:
                reasons.append(token)

    if row["source_url_status"] in {"exact_page_reachable", "canonicalized"}:
        score += 3
    if row["confidence"] in {"high", "medium-high"}:
        score += 4

    return score, sorted(set(reasons))


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def format_markdown(matches: list[dict[str, Any]]) -> str:
    lines = [
        "| Rank | ID | Workflow | Repo | Domain | Family | Tier | Usefulness | Copy | Source |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, item in enumerate(matches, start=1):
        row = item["row"]
        lines.append(
            "| {rank} | {id} | {name} | {repo} | {domain} | {family} | {tier} | {usefulness} | {copy} | {source} |".format(
                rank=index,
                id=row["workflow_id"],
                name=md_cell(row["workflow_name"]),
                repo=md_cell(row["source_repo"]),
                domain=row["normalized_domain"],
                family=row["workflow_family"],
                tier=row["quality_tier"],
                usefulness=row["codex_usefulness"],
                copy=md_cell(row["what_to_copy"][:160]),
                source=md_cell(row["canonical_source_url"]),
            )
        )
    return "\n".join(lines)


def summarize_patterns(matches: list[dict[str, Any]]) -> list[tuple[str, str, int]]:
    pattern_counts: dict[tuple[str, str], int] = {}
    for item in matches:
        row = item["row"]
        key = (row["workflow_family"], row["normalized_domain"])
        pattern_counts[key] = pattern_counts.get(key, 0) + 1
    return [
        (family, domain, count)
        for (family, domain), count in sorted(pattern_counts.items(), key=lambda item: (-item[1], item[0][0]))[:5]
    ]


def format_ecc_markdown(query: str, expanded: list[str], contract: dict[str, Any], matches: list[dict[str, Any]]) -> str:
    lines = [
        f"Query: {query}",
        f"Expanded terms: {', '.join(expanded) if expanded else '(none)'}",
        "",
        "## ECC read",
        "",
        f"- Repeated job: {contract['repeated_real_world_job']}",
        f"- Domain: {contract['domain']}",
        f"- Input contract: {contract['input_contract']}",
        f"- Output artifact: {contract['output_artifact']}",
        f"- Workflow pattern: {contract['workflow_pattern']}",
        f"- Agent lanes: {'; '.join(contract['agent_lanes'])}",
        f"- Tool/source boundary: {contract['tool_or_source_boundary']}",
        f"- Validation gate: {contract['validation_gate']}",
        f"- Human review: {contract['human_review_boundary']}",
        f"- Safety boundary: {contract['safety_boundary']}",
        f"- Suggested skill slug: `{contract['suggested_skill_slug']}`",
        "",
        "## Best workflow patterns",
        "",
    ]

    patterns = summarize_patterns(matches)
    if patterns:
        for family, domain, count in patterns:
            lines.append(f"- `{family}` in `{domain}` ({count} match{'es' if count != 1 else ''})")
    else:
        lines.append("- No catalog pattern matched strongly; use the generic ECC workflow contract.")

    lines.extend(
        [
            "",
            "## Best catalog matches",
            "",
            "| Rank | Match | Quality | Fit | What to copy | What to ignore | Source |",
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for index, item in enumerate(matches, start=1):
        row = item["row"]
        lines.append(
            "| {rank} | {name} ({repo}) | {tier} | {fit} | {copy} | {ignore} | {source} |".format(
                rank=index,
                name=md_cell(row["workflow_name"]),
                repo=md_cell(row["source_repo"]),
                tier=row["quality_tier"],
                fit=row["fit"],
                copy=md_cell(row["what_to_copy"][:180]),
                ignore=md_cell(row["what_to_ignore"][:140]),
                source=md_cell(row["canonical_source_url"]),
            )
        )

    lines.extend(
        [
            "",
            "## What to copy / what to ignore",
            "",
            "- Copy the repeated-job framing, input/output contracts, evidence surfaces, validation gates, and human-review boundaries from the strongest matches.",
            "- Ignore runtime assumptions, app-platform coupling, weak source claims, and any action outside the intended Codex/ECC skill package.",
            "",
            "## Recommended next build step",
            "",
            "Create a Codex/ECC workflow pack only after locking the repeated job, input contract, output artifact, validation gate, and safety boundary. Start with "
            f"`skills/{contract['suggested_skill_slug']}/SKILL.md`, then add schemas, fixtures, validators, examples, and a handoff note if the workflow repeats.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--domain")
    parser.add_argument("--family")
    parser.add_argument("--include-low", action="store_true", help="Include needs_verification rows")
    parser.add_argument("--ecc", action="store_true", help="Include an ECC mini-contract before catalog matches")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    tokens = tokenize(args.query)
    expanded = expand_terms(args.query)
    matches = []
    for row in payload["rows"]:
        if args.domain and row["normalized_domain"] != args.domain:
            continue
        if args.family and row["workflow_family"] != args.family:
            continue
        score, reasons = score_row(row, tokens, expanded, args.include_low)
        if score > 0 and (reasons or not tokens):
            matches.append({"score": score, "reasons": reasons, "row": row})

    matches.sort(
        key=lambda item: (
            -item["score"],
            ["gold", "silver", "bronze", "needs_verification"].index(item["row"]["quality_tier"]),
            item["row"]["source_repo"],
            item["row"]["workflow_name"],
        )
    )
    matches = matches[: args.limit]
    ecc_contract = build_ecc_contract(args.query, expanded, matches) if args.ecc else None

    if args.json:
        payload_out: dict[str, Any] = {"query": args.query, "expanded_terms": expanded, "matches": matches}
        if ecc_contract is not None:
            payload_out["ecc_contract"] = ecc_contract
        print(json.dumps(payload_out, indent=2))
    elif args.ecc:
        assert ecc_contract is not None
        print(format_ecc_markdown(args.query, expanded, ecc_contract, matches))
    else:
        print(f"Query: {args.query}")
        print(f"Expanded terms: {', '.join(expanded) if expanded else '(none)'}")
        print()
        print(format_markdown(matches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
