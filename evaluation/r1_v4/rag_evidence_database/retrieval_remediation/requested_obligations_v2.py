"""Version 2 conservative query-obligation planner.

This planner is an explicit, lexicon-based extension to the frozen planner. It
does not claim general natural-language understanding. Its main safety property
is that an unresolved measurement-bearing phrase cannot disappear from the
plan and therefore cannot yield an unqualified complete retrieval result.
"""
from __future__ import annotations

import re

from .config import CHANNELS
from .planner import interpret as frozen_interpret

VERSION = "requested-obligations-2.0.0"

# These mappings follow the evidence names and reviewed terminology in
# RETRIEVAL_DESIGN.md. They map requests to recorded families, not semantics.
_GRIPPER = r"\b(?:finger(?:s)?|gripper|claw)\b"
_JOINT = r"\b(?:joint(?:s)?|arm(?:s)?)\b"
_POSITION = r"\b(?:position(?:s)?|configuration(?:s)?|config(?:uration)?|angle(?:s)?|posture|bend(?:ing)?|displacement(?:s)?|aperture|opening)\b"
_VELOCITY = r"\b(?:velocity|velocities|speed|speeds|rate|rates|joint rate)\b"

_AMBIGUOUS = re.compile(r"\b(?:joint|arm)\s+(?:state|reading|readings|value|values|measurement|measurements)\b", re.I)
_EXPLICIT_UNSUPPORTED = re.compile(
    r"(?:contact|pair).{0,15}force|tactile|taxel|load.cell|world.{0,20}(?:pose|position|velocity|transform)|cartesian|"
    r"camera exposure|sensor clock|sensor synchronization|same physical instant|same instant|simultaneous|synchroni[sz]|"
    r"physical support|supported by|falling|contact event|collision event|safety violation|physical calibration|calibration certificate",
    re.I,
)
_MEASUREMENT_CUE = re.compile(
    r"\b(?:measurements?|readings?|signals?|sensor data|values?|positions?|velocities?|configurations?|"
    r"angles?|displacements?|forces?|torques?|contact data|pressure|orientation|pose|state)\b", re.I
)
_REQUEST_CUE = re.compile(r"\b(?:show|report|collect|fetch|return|provide|retrieve|give|list|measure)\b", re.I)
_ALL_CHANNELS = re.compile(r"\b(?:all|six|every).{0,25}(?:measurement families|channels|recorded measurements)\b", re.I)


def interpret_v2(text, catalogue, context):
    """Return an explicit obligation plan while reusing frozen scope parsing."""
    base = frozen_interpret(text, catalogue, context)
    result = dict(base)
    result.update(
        planner_version=VERSION,
        query_interpretation_status="RESOLVED",
        obligation_plan_status="COMPLETE",
        measurement_obligations=[],
        temporal_obligations=[],
        unresolved_obligations=[],
    )
    if base.get("status") == "INVALID SCOPE" or "frame_interval" not in base:
        result["query_interpretation_status"] = base.get("status", "AMBIGUOUS")
        result["obligation_plan_status"] = "INCOMPLETE"
        result["status"] = base.get("status", "AMBIGUOUS")
        return result
    unresolved_scope = base.get("reason") == "Saved-frame/action or explicit simulator-clock scope is required"

    normalized = text.lower().replace("_", " ")
    # Re-resolve the physical signal families under this version. The frozen
    # classifier's context propagation can attach (for example) "velocities"
    # to the preceding gripper clause when the following clause names joints.
    families = [f for f in base.get("families", []) if f not in CHANNELS]
    separators = list(re.finditer(r"\b(?:and|plus|along with|together with|with)\b|[,;]", normalized))
    bounds = [0] + [m.end() for m in separators]
    ends = [m.start() for m in separators] + [len(normalized)]
    clauses = []
    for start, end in zip(bounds, ends):
        left = start
        right = end
        while left < right and normalized[left].isspace():
            left += 1
        while right > left and normalized[right - 1].isspace():
            right -= 1
        if left < right:
            clauses.append((left, right, normalized[left:right]))

    previous_entity = None
    unsupported_terms = set(base.get("unsupported", []))
    for start, end, clause in clauses:
        has_gripper = bool(re.search(_GRIPPER, clause, re.I))
        has_joint = bool(re.search(_JOINT, clause, re.I))
        position = bool(re.search(_POSITION, clause, re.I))
        velocity = bool(re.search(_VELOCITY, clause, re.I))
        entity = "gripper" if has_gripper and not has_joint else "joint" if has_joint and not has_gripper else None
        if has_gripper and has_joint:
            result["unresolved_obligations"].append(
                {"span": clause, "start": start, "end": end, "status": "AMBIGUOUS", "reason": "multiple measurement subjects in one clause"}
            )
            continue
        if entity is not None:
            previous_entity = entity
        elif (position or velocity) and previous_entity:
            entity = previous_entity
        clause_families = []
        if entity == "gripper":
            if position:
                clause_families.append("raw.robot0_gripper_qpos")
            if velocity:
                clause_families.append("raw.robot0_gripper_qvel")
            if re.search(r"\bstate\b", clause, re.I):
                clause_families.extend(("raw.robot0_gripper_qpos", "raw.robot0_gripper_qvel"))
        elif entity == "joint":
            if position:
                clause_families.append("raw.robot0_joint_pos")
            if velocity:
                clause_families.append("raw.robot0_joint_vel")
        if re.search(r"\bopening mechanism\b", clause, re.I) and re.search(r"\b(?:displacement|opening|aperture)\b", clause, re.I):
            clause_families.append("raw.robot0_gripper_qpos")
        if entity is not None and not position and not velocity and not re.search(r"\bstate\b", clause, re.I):
            result["unresolved_obligations"].append(
                {"span": clause, "start": start, "end": end, "status": "AMBIGUOUS", "reason": "measurement subject has no explicit measurement property"}
            )
        for family in clause_families:
            result["measurement_obligations"].append(
                {"span": clause, "start": start, "end": end, "family": family, "mapping": family.rsplit("_", 1)[-1]}
            )
            if family not in families:
                families.append(family)
        if _MEASUREMENT_CUE.search(clause) and not clause_families and not _EXPLICIT_UNSUPPORTED.search(clause) and not _AMBIGUOUS.search(clause) and not _ALL_CHANNELS.search(normalized):
            cue = _MEASUREMENT_CUE.search(clause)
            result["unresolved_obligations"].append(
                {"span": cue.group(0), "start": start + cue.start(), "end": start + cue.end(), "status": "UNSUPPORTED_OR_UNMAPPED", "reason": "no reviewed evidence-family mapping"}
            )

    if re.search(r"\b(?:motor|actuator|actuators|motors)\b", normalized) and re.search(r"\b(?:force|output|effort|torque|load)\b", normalized):
        families.append("raw.simulator_actuator_force")
    if re.search(r"\bcontact\b", normalized) and re.search(r"\b(?:count|tally|number|entries|entry)\b", normalized):
        families.append("simulator.ncon")
    if _ALL_CHANNELS.search(normalized):
        families.extend(CHANNELS)

    # Existing planner families remain explicit obligations too. This keeps
    # reviewed metadata and evidence-reference terminology backward-compatible.
    mapped = {o["family"] for o in result["measurement_obligations"]}
    for family in families:
        if family not in mapped:
            result["measurement_obligations"].append(
                {"span": text, "start": 0, "end": len(text), "family": family, "mapping": "reviewed-family-lexicon"}
            )

    ambiguous = list(_AMBIGUOUS.finditer(normalized))
    for match in ambiguous:
        result["unresolved_obligations"].append(
            {"span": match.group(0), "start": match.start(), "end": match.end(), "status": "AMBIGUOUS", "reason": "measurement type is unspecified"}
        )

    # Surface measurement-bearing requests for which no supported or explicit
    # unsupported mapping exists. Scope terms like "at frame 20" are not cues.
    if _REQUEST_CUE.search(normalized) and _MEASUREMENT_CUE.search(normalized) and not result["measurement_obligations"] and not unsupported_terms and not ambiguous:
        cue = _MEASUREMENT_CUE.search(normalized)
        result["unresolved_obligations"].append(
            {"span": cue.group(0), "start": cue.start(), "end": cue.end(), "status": "UNSUPPORTED_OR_UNMAPPED", "reason": "no reviewed evidence-family mapping"}
        )

    if base.get("seconds_interval") is not None or re.search(r"\b(?:simulator|simulation)\s+(?:time|label)|\btimestamp\b|\brecorded time\b", normalized):
        result["temporal_obligations"].append({"kind": "recorded_simulator_label", "interval": base.get("seconds_interval"), "family": "recorded_time"})
        if "recorded_time" not in families:
            families.append("recorded_time")
            result["measurement_obligations"].append(
                {"span": text, "start": 0, "end": len(text), "family": "recorded_time", "mapping": "temporal-qualifier-evidence"}
            )

    explicit_clock_request = re.search(r"\b(?:timestamp|recorded time|simulator time|clock label)\b", normalized)
    if families == ["recorded_time"] and not explicit_clock_request:
        result["unresolved_obligations"].append(
            {"span": "measurement request", "start": 0, "end": len(text), "status": "AMBIGUOUS", "reason": "a temporal qualifier alone does not identify the requested measurement"}
        )

    families = list(dict.fromkeys(families))
    result["families"] = families
    has_ambiguous = bool(ambiguous or any(item["status"] == "AMBIGUOUS" for item in result["unresolved_obligations"]))
    if has_ambiguous or result["unresolved_obligations"] or unsupported_terms:
        result["query_interpretation_status"] = "AMBIGUOUS" if has_ambiguous else "PARTIAL"
        result["obligation_plan_status"] = "INCOMPLETE"
        result["status"] = "AMBIGUOUS" if has_ambiguous else "UNSUPPORTED"
        result["reason"] = "One or more requested evidence obligations are unresolved or unsupported"
    elif unresolved_scope:
        result["query_interpretation_status"] = "AMBIGUOUS"
        result["obligation_plan_status"] = "INCOMPLETE"
        result["status"] = "AMBIGUOUS"
        result["reason"] = base["reason"]
    elif not families:
        result["query_interpretation_status"] = "AMBIGUOUS"
        result["obligation_plan_status"] = "INCOMPLETE"
        result["status"] = "AMBIGUOUS"
        result["reason"] = "No reviewed evidence obligation was resolved"
    else:
        result["status"] = "RESOLVED"
    return result
