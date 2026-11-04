# Development and separation

New development: 96 scope instances of 12 forms on eight eligible executions, excluded from both final assessments. Exposed K failures are regressions only. No final cases became an unlabelled development set.

49 corrected-version test methods passed, plus 28 detected mutation trials. Coverage includes configuration/time/action, positions+velocities, arm+gripper configurations, gripper state+actuator output, parentheses, singular/plural registry heads, word order, unsupported world/clock/calibration/comparison requests, missing instants, unknown conjuncts, quotations, components, conditional cache, scope and tampering. Mutations remove model obligations AND plan families, alter scopes/attachments/clock values, and forge actual selected indices. These are finite automated tests, not human evaluation.

Initial diagnostics remain: a baseline extra-test output directory was missing; registry fixture names were corrected to excluded_reserved/excluded_preflight; a genuine coverage bug let request.query cover the entire request. Fixed before final freezing. Failed V1 results are preserved. The correction was separately frozen and assessed on fresh scopes/new wording. A secondary V1 audit explains a missing-default assurance scorer bug; original bad counters and outputs remain intact.
