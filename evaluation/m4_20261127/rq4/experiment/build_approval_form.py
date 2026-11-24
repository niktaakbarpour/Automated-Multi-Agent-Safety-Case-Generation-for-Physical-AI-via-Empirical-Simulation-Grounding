"""Write the blank finding-approval form, rq4/FINDING_APPROVALS.csv (RQ4). CPU only.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/build_approval_form.py

One row per finding in each case's Critic report, bound to that report by its digest. The approver fills the
human columns by hand: decision (approved, declined or empty for undecided), approver, approved_on
(YYYY-MM-DD) and the attestation sentence:

    I read this finding and its target node myself and made this decision.

on_planted_defect_node only helps the approver find the finding the fixed rule names; it is not a decision.
The form is never overwritten once any human column has a value.
"""
from pathlib import Path
import csv
import io
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM  # noqa: E402


def blank_form():
    rows = []
    for case in CM.CASES:
        _, label = CM.load_case(case['case_id'])
        rows += CM.approval_form_rows(case['case_id'], CM.critic_report(case), label)
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=CM.APPROVAL_COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def main(argv):
    path = CM.APPROVALS_PATH
    if path.exists():
        _, rows = CM.read_csv(path)
        if any(r.get(k, '').strip() for r in rows for k in CM.HUMAN_COLUMNS):
            print(f'{path.name} already holds recorded decisions; it is not changed', file=sys.stderr)
            return 1
    path.write_text(blank_form(), encoding='utf-8')
    print(f'wrote {path.relative_to(CM.ROOT)}: fill decision, approver, approved_on and attestation by hand',
          file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
