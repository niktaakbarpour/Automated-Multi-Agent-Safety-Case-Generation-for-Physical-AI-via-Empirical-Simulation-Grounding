"""Replay the public M4 paper tables on CPU from the saved evidence."""
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
M4 = ROOT / "evaluation/m4_20261127"
RAG = ROOT / "evaluation/r1_v4/rag_evidence_database"
TABLES = ROOT / "report/m4_neurips_materials/tables.tex"


def run(*args):
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONOPTIMIZE", None)  # Existing validators use assertions.
    return subprocess.check_output([sys.executable, *args], cwd=ROOT, env=env, text=True)


def capture(pattern, text):
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"Missing evidence matching {pattern!r}")
    return match.group(1)


def rq1():
    metrics = (RAG / "readiness_evaluation/RETRIEVAL_METRICS.md").read_text()
    remediation = RAG / "retrieval_remediation"
    completeness = (remediation / "MULTISOURCE_COMPLETENESS.md").read_text()
    abstention = (remediation / "ABSTENTION_AND_INTEGRITY.md").read_text()
    failures = (M4 / "rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/FALSE_COMPLETE_ANALYSIS.md").read_text()
    rows = []
    for mode in ("exact", "semantic", "lexical"):
        line = capture(rf"\| {mode} \| (\d+ \| [^\n]+)", metrics)
        n, p1, _, r20, mrr = line.strip("| ").split(" | ")
        rows.append(["Historical retrieval", mode.title(), n, p1, r20, mrr])
    for label, pattern, source in [
        ("Multi-source bundle completeness", r"(\d+/\d+) complete required sets", completeness),
        ("Required family obligations", r"(\d+/\d+) required-family obligations", completeness),
        ("Critical abstentions", r"(\d+/\d+) critical requests abstained", abstention),
    ]:
        ratio = capture(pattern, source)
        rows.append(["Phase 5K V2", label, ratio.split("/")[1], ratio])
    ids = list(dict.fromkeys(re.findall(r"KH2-C2-(\d+)", failures)))
    rows.append(["Phase 5K V2", "Known false-complete cases", len(ids), "KH2-C2-" + "/".join(ids)])
    rows.append(["Historical retrieval", "Execution contexts", capture(r"share (\d+) execution contexts", metrics), "Clustered units"])
    return rows


def confusion(counts):
    return "/".join(str(counts[key]) for key in ("TP", "FP", "TN", "FN"))


def rq2():
    verified = json.loads(run("integration/verify_saved_results.py"))
    current = verified["calibration"]
    expanded = verified["generalization_coverage_only"]
    historical = json.loads((ROOT / "evaluation/r1_v3/results.json").read_text())
    counts = historical["counts"]
    applicable = counts["applicable_reference"]
    total = historical["total_units"]
    agreements = counts["applicable_correct"] + counts["non_applicable_correct"]
    return [
        ["Current reviewed calibration", current["applicability_agreement"],
         f"{current['applicable']}/{current['not_applicable']}", confusion(current["confusion"]),
         current["coverage"], current["abstention_rate"], f"{current['cases']} cases, {current['groups']} group"],
        ["Historical development reference", f"{agreements}/{total}", f"{applicable}/{counts['non_applicable_reference']}",
         confusion(historical["binary_counts"]), f"{historical['binary_denominator']}/{applicable}",
         f"{counts['eligible_abstentions']}/{applicable}", f"{total} object units"],
        ["60-execution expansion", "N/A", f"{expanded['applicable']}/{expanded['not_applicable']}", "--",
         expanded["coverage"], expanded["abstention_rate"], "Coverage only, unlabeled"],
        ["Independent human evaluation", *(["PENDING"] * 6)],
    ]


def rq3(out):
    experiment = M4 / "rq3/experiment"
    archive = experiment / "real_run_20261122T142300Z"
    run(experiment / "score.py", "--batch", experiment / "batch", "--responses", archive / "RQ3_RESPONSES.jsonl", "--out-dir", out)
    run(experiment / "make_tables.py", "--results-dir", out, "--out", out / "RQ3_TABLES.md")
    for name in ("RQ3_TABLES.md", "RQ3_SUMMARY.csv", "RQ3_PER_CASE_RESULTS.csv"):
        if (out / name).read_bytes() != (archive / "scored_pr34_20261123" / name).read_bytes():
            raise ValueError(f"RQ3 frozen output mismatch: {name}")
    with (out / "RQ3_PER_CASE_RESULTS.csv").open(newline="") as stream:
        results = list(csv.DictReader(stream))
    config = (experiment.parent / "EXPERIMENT_CONFIG.md").read_text()
    independent = capture(r"(\d+) independent cases", config)
    capture(r"(blind review still pending)", config)
    columns = {}
    for condition in "TRC":
        requests = [r for r in results if r["condition"] == condition]
        valid = [r for r in requests if r["status"] == "valid"]
        mutations = [r for r in valid if r["case_type"] == "mutation"]
        controls = [r for r in valid if r["case_type"] == "clean_control"]

        def rate(rows, field):
            return f"{sum(int(r[field]) for r in rows)}/{len(rows)}"

        cases = len({r["case_id"] for r in valid})
        groups = len({r["parent_group_id"] for r in valid})
        correct_combined = (
            sum(int(r["rules_plus_model_detected"]) for r in mutations)
            + len(controls) - sum(int(r["rules_plus_model_false_positive"]) for r in controls)
        )
        values = {
            "Valid responses": f"{len(valid)}/{len(requests)}",
            "Semantic cases / parent groups": f"{cases} / {groups} development",
            "Independent source groups": independent,
            "Mutation detections, model-only": rate(mutations, "detected"),
            "Mutation detections, rules + model": rate(mutations, "rules_plus_model_detected"),
            "Clean-control false positives": rate(controls, "clean_control_false_positive"),
            "Reference-correct outputs, model-only": rate(valid, "reference_correct"),
            "Reference-correct outputs, rules + model": f"{correct_combined}/{len(valid)}",
        }
        for operator in ("M1", "M2", "M3"):
            values[f"{operator} mutation detections"] = rate([r for r in mutations if r["mutation_operator"] == operator], "detected")
        values["Independent label audit"] = "PENDING"
        for label, value in values.items():
            columns.setdefault(label, []).append(value)
    return [[label, *values] for label, values in columns.items()]


def verify_revision_example_count(output, expected, source):
    count = sum(line.startswith("PASS  ") for line in output.splitlines())
    if count != expected or "All checks passed." not in output.splitlines():
        raise ValueError(f"{source}: expected {expected} passing checks with a success summary, found {count}")
    return count


def rq4():
    fixture = json.loads(run("integration/verify_saved_fixture.py"))
    run("-m", "unittest", "discover", "-s", "drafter/revision/tests", "-t", ".", "-q")
    examples_output = run("-m", "drafter.revision.tools.check_examples")
    current_checks = verify_revision_example_count(examples_output, 145, "Current revision checker")
    revision = ROOT / "drafter/revision"
    transcript = (revision / "handoff/TEST_TRANSCRIPT.txt").read_text()
    examples = verify_revision_example_count(transcript, 149, "A0 revision transcript")
    print(f"Current revision examples: {current_checks} checks passed")
    print(f"Historical A0 transcript: {examples} passing checks for the manuscript row")
    tests = capture(r"# (\d+) tests", (revision / "README.md").read_text())
    controlled = next(case for case in fixture["cases"] if case["case"] == "controlled-negative")
    if controlled["saved_qwen_report"] != "completed, zero criticisms":
        raise ValueError("Controlled fixture outcome changed")
    return [
        ["Revision Agent CPU suite", f"{tests} tests; scripted validators and edits", "Real-model revision performance"],
        ["Saved revision examples", f"{examples} example checks", "Real-model second Critic cycle"],
        ["One-pass Qwen fixture", "Real Drafter/Critic calls; 0 criticisms on controlled guarantee", "Reliable semantic criticism"],
    ]


def check_table(manuscript, label, rows):
    block = manuscript.split(r"\label{" + label + "}", 1)[1].split(r"\end{tabular}", 1)[0]
    if label == "tab:rq3-conditions":
        header = "Measure & T: text-only & R: retrieval & C: admission-status only"
        if header not in block.split(r"\midrule", 1)[0]:
            raise ValueError(f"{label} condition headers changed")
    data = block.split(r"\midrule", 1)[1]
    actual = []
    for line in data.splitlines():
        if line.strip().endswith(r"\\"):
            line = re.sub(r"\\multicolumn\{3\}\{c\}\{([^{}]+)\}", r"\1", line)
            actual.append([v.strip() for v in line.strip()[:-2].split("&")])
    expected = [[str(value) for value in row] for row in rows]
    if actual != expected:
        raise ValueError(f"{label} manuscript mismatch\nexpected {expected}\nfound {actual}")
    print(f"PASS {label}")
    for row in expected:
        print(" | ".join(row))


def main():
    manuscript = TABLES.read_text()
    with TemporaryDirectory() as directory:
        for label, replay in [("tab:rq1", rq1), ("tab:rq2", rq2),
                              ("tab:rq3-conditions", lambda: rq3(Path(directory))), ("tab:rq4", rq4)]:
            check_table(manuscript, label, replay())


if __name__ == "__main__":
    main()
