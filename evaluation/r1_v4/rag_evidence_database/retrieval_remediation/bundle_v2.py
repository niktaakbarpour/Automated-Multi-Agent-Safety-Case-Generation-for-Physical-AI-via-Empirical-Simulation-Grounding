"""Versioned bundle adapter enforcing requested-obligation completeness."""
from dataclasses import replace

from .bundle import BundleRequest, Retriever as FrozenRetriever
from .requested_obligations_v2 import VERSION, interpret_v2


class RequestedObligationsRetriever:
    """Use frozen source verification/retrieval with a stricter v2 plan gate.

    This adapter does not change evidence admission or infer physical meaning.
    """

    def __init__(self, *args, **kwargs):
        self._retriever = FrozenRetriever(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._retriever, name)

    def close(self):
        self._retriever.close()

    def retrieve(self, request, mode="bundle"):
        from dataclasses import asdict

        if not isinstance(request, BundleRequest):
            raise TypeError("BundleRequest required")
        if not isinstance(request.query, str) or not request.query.strip() or len(request.query) > 2000:
            return self._retriever.retrieve(request, mode)
        row = self._retriever.catalogue.execute(
            "select body from catalogue where execution=?", (request.execution_id,)
        ).fetchone()
        if row is None:
            return self._retriever.retrieve(request, mode)
        import json

        catalogue = json.loads(row[0])
        plan = interpret_v2(request.query, catalogue, asdict(request))
        if plan["status"] != "RESOLVED":
            response = self._retriever.response(request, plan["status"], plan.get("reason", "Incomplete obligation plan"), plan)
            response.update(
                planner_version=VERSION,
                query_interpretation_status=plan["query_interpretation_status"],
                obligation_plan_status=plan["obligation_plan_status"],
                retrieval_completeness_status="NOT_RUN",
                physical_evidence_eligibility="NOT_EVALUATED",
            )
            return response

        # Feed the complete family list to the original retrieval engine. It
        # retains all pinned-source, scope, provenance, and frame checks.
        delegated = replace(request, plan=tuple(plan["families"]))
        response = self._retriever.retrieve(delegated, mode)
        response["interpretation"] = plan
        response["requested_families"] = list(plan["families"])
        response["planner_version"] = VERSION
        response["query_interpretation_status"] = plan["query_interpretation_status"]
        response["obligation_plan_status"] = plan["obligation_plan_status"]
        response["retrieval_completeness_status"] = response["completeness_status"]
        response["physical_evidence_eligibility"] = "NOT_EVALUATED"
        # Preserve exact source/scope failures. Retrieval completion can only
        # remain complete if all four layers are complete and the plan has no
        # unresolved or unsupported request.
        returned = {group.get("family") for group in response.get("groups", [])}
        all_available = all(group.get("status") == "AVAILABLE" for group in response.get("groups", []))
        if response["completeness_status"] == "COMPLETE WITHIN VERIFIED CONTRACT" and (
            not set(plan["families"]).issubset(returned) or not all_available
        ):
            response["completeness_status"] = "PARTIAL"
            response["retrieval_completeness_status"] = "PARTIAL"
        return response
