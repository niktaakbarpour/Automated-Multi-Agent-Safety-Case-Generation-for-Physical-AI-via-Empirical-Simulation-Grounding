"""Future per-case call boundary; not invoked during Task 7B."""

EXPECTED_ADAPTER_VERSION = "task8c-r1v3-source-adapter-1.0.0"


def execute_prepared_case(prepared, evaluate, checker_config):
    """Call only the frozen R1 v3 decision function on eligible prepared facts."""
    if prepared.get("adapter_version") != EXPECTED_ADAPTER_VERSION:
        raise ValueError("Adapter version is not the frozen Task 7B version")
    if not prepared.get("checker_eligible") or prepared.get("source_provenance_status") != "VERIFIED":
        raise ValueError("Source provenance is not verified; checker execution is forbidden")
    if prepared.get("frame_count") != 258 or len(prepared.get("frames", [])) != 258:
        raise ValueError("Prepared facts do not cover the complete frozen frame domain")
    if prepared.get("monitoring_start_frame") != 10 or prepared.get("terminal_frame") != 257:
        raise ValueError("Prepared facts violate the frozen R1 monitoring contract")
    return evaluate(prepared["frames"], "cream_cheese_1", prepared["case_id"], checker_config)
