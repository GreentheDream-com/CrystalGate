#!/usr/bin/env python3
# Copyright © 2026 Derrick Covington.
# Published through Green The Dream Research Lab.
#
# Licensed under the PolyForm Noncommercial License 1.0.0.
# License: https://polyformproject.org/licenses/noncommercial/1.0.0
# Commercial licensing: derrick@greenthedream.com
#
# Required Notice: Copyright © 2026 Derrick Covington.
# Required Notice: Published through Green The Dream Research Lab.

"""Minimal, dependency-free CrystalGate routing demonstration.

This reference artifact intentionally implements only the finite, edge-additive
case described by Proposition 5 and Section 7 of the manuscript.  It is a
reproducible smoke test for the protocol, not a production verifier and not an
empirical validation of the broader framework.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable


ARTIFACT_VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parent
DEFAULT_SCHEMA = ROOT / "schema.json"
DEFAULT_CLAIMS = ROOT / "claims.json"
DEFAULT_OUTPUT = ROOT / "generated" / "route_reports.json"
RESEARCH_ARTIFACT_LICENSE = {
    "copyright": "Copyright © 2026 Derrick Covington.",
    "published_through": "Green The Dream Research Lab",
    "license": "CC BY-NC-ND 4.0",
    "license_url": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    "commercial_and_adaptation_permissions": "derrick@greenthedream.com",
    "required_notices": [
        "Copyright © 2026 Derrick Covington.",
        "Published through Green The Dream Research Lab.",
    ],
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_schema(schema: dict[str, Any]) -> None:
    types = set(schema.get("types", []))
    translators = schema.get("translators", [])
    translator_ids = [item["id"] for item in translators]
    gate_ids = [item["id"] for item in schema.get("gates", [])]

    if not 5 <= len(translators) <= 10:
        raise ValueError("The demonstration schema must contain five to ten translators.")
    if len(translator_ids) != len(set(translator_ids)):
        raise ValueError("Translator identifiers must be unique.")
    if len(gate_ids) != len(set(gate_ids)):
        raise ValueError("Gate identifiers must be unique.")

    for translator in translators:
        if translator["source"] not in types or translator["target"] not in types:
            raise ValueError(f"Unknown translator endpoint in {translator['id']}.")
        if float(translator.get("cost", 0.0)) < 0:
            raise ValueError(f"Translator cost must be nonnegative: {translator['id']}.")


def index_schema(schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    by_id = {item["id"]: item for item in schema["translators"]}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for translator in schema["translators"]:
        outgoing.setdefault(translator["source"], []).append(translator)
    for edges in outgoing.values():
        edges.sort(key=lambda edge: edge["id"])
    return by_id, outgoing


def lookup_gate(schema: dict[str, Any], gate_id: str) -> dict[str, Any]:
    for gate in schema["gates"]:
        if gate["id"] == gate_id:
            return gate
    raise ValueError(f"Unknown gate in profile: {gate_id}")


def evidence_record(claim: dict[str, Any], key: str | None) -> dict[str, Any]:
    if key and key in claim.get("evidence", {}):
        return claim["evidence"][key]
    return {"kind": "not_supplied", "artifact": None}


def evaluate_gate(spec: dict[str, Any], claim: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one declarative hard predicate or soft residual.

    The serialized status vocabulary remains pass/fail/unknown/na.  For a soft
    gate, a finite nonnegative residual serializes as ``pass`` for compatibility
    with the manuscript schema, while ``report_status`` is the less ambiguous
    human-facing label ``evaluated``.
    """

    requirement = spec.get("requirement", "required")
    severity = spec.get("severity", "hard")
    fact_key = spec.get("fact")
    residual_key = spec.get("residual_key")
    assumptions = list(spec.get("assumptions", []))

    if requirement == "na":
        status = "na"
        report_status = "not applicable"
        residual = None
        evidence_key = None
    elif severity == "soft":
        value = claim.get("residuals", {}).get(residual_key)
        evidence_key = residual_key
        if value is None:
            status = "unknown"
            report_status = "unknown"
            residual = None
        elif isinstance(value, (int, float)) and math.isfinite(value) and value >= 0:
            status = "pass"
            report_status = "evaluated"
            residual = float(value)
        else:
            status = "fail"
            report_status = "evaluation error"
            residual = None
    else:
        value = claim.get("facts", {}).get(fact_key)
        evidence_key = fact_key
        residual = 0.0 if value is True else None
        if value is True:
            status = "pass"
            report_status = "satisfied"
        elif value is False:
            status = "fail"
            report_status = "violated"
        else:
            status = "unknown"
            report_status = "unknown"

    note = None
    if severity == "soft" and status == "pass":
        note = (
            "Successfully evaluated; pass does not mean that the residual is small "
            "or below a mandatory limit."
        )

    return {
        "gate_id": spec["id"],
        "requirement": requirement,
        "severity": severity,
        "status": status,
        "report_status": report_status,
        "residual": residual,
        "weight": float(spec.get("weight", 0.0)),
        "assumptions": assumptions,
        "evidence": evidence_record(claim, evidence_key),
        "provenance": {
            "evaluator": "minimal_gatefinder",
            "version": ARTIFACT_VERSION,
            "claim_id": claim["id"],
        },
        "note": note,
    }


def synthetic_failure(gate_id: str, message: str, claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "requirement": "required",
        "severity": "hard",
        "status": "fail",
        "report_status": "violated",
        "residual": None,
        "weight": 0.0,
        "assumptions": [message],
        "evidence": {"kind": "registry_check", "artifact": None},
        "provenance": {
            "evaluator": "minimal_gatefinder",
            "version": ARTIFACT_VERSION,
            "claim_id": claim["id"],
        },
        "note": None,
    }


def classify_certificates(certificates: Iterable[dict[str, Any]]) -> str:
    required = [item for item in certificates if item["requirement"] == "required"]
    if any(item["status"] == "fail" for item in required):
        return "blocked"
    if any(item["status"] == "unknown" for item in required):
        return "potential"
    return "admissible"


def evaluate_route(
    route_ids: list[str],
    claim: dict[str, Any],
    schema: dict[str, Any],
    translator_index: dict[str, Any],
) -> dict[str, Any]:
    profile = schema["profiles"][claim["profile"]]
    certificates = [evaluate_gate(lookup_gate(schema, gate_id), claim) for gate_id in profile]
    current_type = claim["source_type"]
    edge_cost = 0.0
    resolved_route: list[dict[str, Any]] = []

    for translator_id in route_ids:
        translator = translator_index.get(translator_id)
        if translator is None:
            certificates.append(
                synthetic_failure(
                    "transition.registered",
                    f"Translator {translator_id!r} is not present in the schema registry.",
                    claim,
                )
            )
            break
        if current_type != translator["source"]:
            certificates.append(
                synthetic_failure(
                    "transition.composable",
                    f"Expected source type {current_type!r}, got {translator['source']!r}.",
                    claim,
                )
            )
            break
        if claim["objective"] not in translator.get("objectives", []):
            certificates.append(
                synthetic_failure(
                    "transition.objective_preserved",
                    f"Translator {translator_id!r} does not preserve objective {claim['objective']!r}.",
                    claim,
                )
            )
            break

        for check in translator.get("checks", []):
            certificates.append(evaluate_gate(check, claim))
        resolved_route.append(
            {
                "translator_id": translator["id"],
                "version": translator["version"],
                "source": translator["source"],
                "target": translator["target"],
                "cost": float(translator.get("cost", 0.0)),
                "preconditions": translator.get("preconditions", []),
                "postconditions": translator.get("postconditions", []),
            }
        )
        edge_cost += float(translator.get("cost", 0.0))
        current_type = translator["target"]

    if current_type != claim["target_type"]:
        certificates.append(
            synthetic_failure(
                "observable.target_reached",
                f"Route ended at {current_type!r}, not target {claim['target_type']!r}.",
                claim,
            )
        )

    status = classify_certificates(certificates)
    soft_cost = sum(
        item["weight"] * item["residual"]
        for item in certificates
        if item["status"] == "pass"
        and item["residual"] is not None
        and item["severity"] == "soft"
    )
    complexity_cost = float(schema.get("route_length_penalty", 0.0)) * len(resolved_route)
    total_cost = edge_cost + soft_cost + complexity_cost

    return {
        "translator_ids": route_ids,
        "resolved_edges": resolved_route,
        "route_status": status,
        "route_cost": round(total_cost, 6),
        "route_score": round(math.exp(-total_cost), 12),
        "certificates": certificates,
    }


def enumerate_routes(
    claim: dict[str, Any],
    outgoing: dict[str, list[dict[str, Any]]],
    max_edges: int,
) -> list[list[str]]:
    """Enumerate simple type-state paths for this deliberately small artifact."""

    routes: list[list[str]] = []

    def visit(current_type: str, path: list[str], visited_types: set[str]) -> None:
        if current_type == claim["target_type"]:
            routes.append(path.copy())
            return
        if len(path) >= max_edges:
            return
        for translator in outgoing.get(current_type, []):
            if claim["objective"] not in translator.get("objectives", []):
                continue
            target = translator["target"]
            if target in visited_types:
                continue
            visit(target, path + [translator["id"]], visited_types | {target})

    visit(claim["source_type"], [], {claim["source_type"]})
    return routes


def route_priority(route: dict[str, Any]) -> tuple[float, tuple[str, ...]]:
    return route["route_cost"], tuple(route["translator_ids"])


def summarize_search(route: dict[str, Any]) -> dict[str, Any]:
    return {
        "translator_ids": route["translator_ids"],
        "route_status": route["route_status"],
        "route_cost": route["route_cost"],
        "failed_gate_ids": [
            item["gate_id"]
            for item in route["certificates"]
            if item["requirement"] == "required" and item["status"] == "fail"
        ],
        "unresolved_gate_ids": [
            item["gate_id"]
            for item in route["certificates"]
            if item["requirement"] == "required" and item["status"] == "unknown"
        ],
    }


def adjudicate_claim(claim: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    translator_index, outgoing = index_schema(schema)
    proposed = evaluate_route(claim["proposed_route"], claim, schema, translator_index)
    candidates = [
        evaluate_route(route, claim, schema, translator_index)
        for route in enumerate_routes(claim, outgoing, int(schema.get("max_route_edges", 6)))
    ]
    admissible = [route for route in candidates if route["route_status"] == "admissible"]
    potential = [route for route in candidates if route["route_status"] == "potential"]

    if proposed["route_status"] == "admissible":
        verdict = "accepted"
        selected = proposed
        repair = None
    elif admissible:
        selected = min(admissible, key=route_priority)
        verdict = "rerouted"
        repair = {
            "failed_proposed_route": claim["proposed_route"],
            "alternate_route": selected["translator_ids"],
        }
    elif potential:
        selected = min(potential, key=route_priority)
        verdict = "underdetermined"
        repair = {
            "unresolved_gate_ids": [
                item["gate_id"]
                for item in selected["certificates"]
                if item["requirement"] == "required" and item["status"] == "unknown"
            ]
        }
    else:
        selected = proposed
        verdict = "rejected" if schema.get("closed_for_objective", False) else "underdetermined"
        repair = None

    failed = [
        item["gate_id"]
        for item in selected["certificates"]
        if item["requirement"] == "required" and item["status"] == "fail"
    ]
    unresolved = [
        item["gate_id"]
        for item in selected["certificates"]
        if item["requirement"] == "required" and item["status"] == "unknown"
    ]

    return {
        "manifest_version": "crystalgate.route-report.0.1",
        "claim_id": claim["id"],
        "claim": claim["statement"],
        "context": {
            "objective": claim["objective"],
            "requested_validity_level": claim["requested_validity_level"],
            "profile": claim["profile"],
            "facts": claim.get("facts", {}),
            "residuals": claim.get("residuals", {}),
        },
        "nodes": {
            "source_type": claim["source_type"],
            "target_type": claim["target_type"],
        },
        "proposed_route": claim["proposed_route"],
        "proposed_assessment": proposed["route_status"],
        "searched_routes": [summarize_search(route) for route in sorted(candidates, key=route_priority)],
        "selected_route": selected["resolved_edges"],
        "selected_route_ids": selected["translator_ids"],
        "certificates": selected["certificates"],
        "route_score": selected["route_score"],
        "route_cost": selected["route_cost"],
        "observable": claim["observable"],
        "verdict": verdict,
        "failed_obligations": failed,
        "unresolved_obligations": unresolved,
        "repair": repair,
        "provenance": {
            "schema_id": schema["schema_id"],
            "schema_version": schema["version"],
            "implementation": "gatefinder_demo.py",
            "implementation_version": ARTIFACT_VERSION,
        },
    }


def expected_verdict_check(claims: list[dict[str, Any]], reports: list[dict[str, Any]]) -> None:
    expected = {claim["id"]: claim["expected_verdict"] for claim in claims}
    actual = {report["claim_id"]: report["verdict"] for report in reports}
    if actual != expected:
        raise AssertionError(f"Verdict mismatch. Expected {expected!r}; got {actual!r}.")


def run(schema_path: Path, claims_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    schema = load_json(schema_path)
    claim_document = load_json(claims_path)
    claims = claim_document["claims"]
    validate_schema(schema)
    reports = [adjudicate_claim(claim, schema) for claim in claims]
    expected_verdict_check(claims, reports)
    return schema, reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Validate without writing output.")
    args = parser.parse_args()

    schema, reports = run(args.schema, args.claims)
    document = {
        "artifact": "minimal_gatefinder",
        "artifact_version": ARTIFACT_VERSION,
        "schema_id": schema["schema_id"],
        "artifact_license": RESEARCH_ARTIFACT_LICENSE,
        "reports": reports,
    }
    if not args.check:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    for report in reports:
        route = " -> ".join(report["selected_route_ids"])
        print(f"{report['claim_id']}: {report['verdict']} | {route}")
    print(f"Validated {len(reports)} claims against {len(schema['translators'])} translators.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
