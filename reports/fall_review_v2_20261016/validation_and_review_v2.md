# Practical review and validation package, version 2

The targeted investigation is complete within the available evidence. This document describes the remaining human labelling/validation work on actual supplied examples, not another availability audit or a new rollout plan. No checker has been implemented.

## Review these existing examples

| Development run | Supplied sheet/window | What is actually present | Decision still needed |
|---|---|---|---|
| episode_000 / seed 1000 | Frames 0,1,5,10,11,13,16,20, 0–1 s | Setup launches/elevation/descent and later table recontact; direct-support candidates cream cheese/butter versus the three airborne objects | Per-object initial support and study suitability; not an automatic pass/N/A. |
| episode_002 / seed 1002 | Frames 0,1,5,8,10,11,12,20, 0–1 s | Initial cream-cheese/orange-juice overlap; departure/descent before the policy interval; floor contact later | Setup event interpretation and interval-boundary treatment, not a policy violation inferred from landing time. |
| episode_001 / seed 1001 | Frames 10,20,40,80, 0.5–4 s | Configuration/occlusion comparison; candidate supported poses in the selected views | Human support/non-event interpretation of this window only; no whole-run negative label. |
| episode_014 / seed 1014 | Pre-policy frame 10 plus frames 270,276,280–284,286, 13.5–14.3 s | Cream cheese rises with gripper contacts, then descends with no snapshot contacts and returns to table contact | Mechanical support versus release, and whether post-lift drop is a table-origin fall. This is a real ambiguity, not a manufactured positive. |

Both cameras are supplied in each sheet. Labels give the run ID, exact frame, nominal simulator time, stage and control step; the HDF5 paths and host snapshot UTC are in example_manifest.json. Images are only rotated for display as in the producer's viewer; no objects or scene content are changed. The sheets are selections, not claims of missing recording between displayed columns. Camera timing is qualified separately.

Automated interpretations are in example_interpretations_provisional.json. Human-review JSON files contain blank/null labels, identities, decisions and reasoning, with evidence references already filled in. They include 20 object-specific initial-support forms, four event forms and four uncertainty forms. Reviewers can inspect evidence independently before reading provisional interpretations. No person's identity is pre-entered.

## Proposed split, saved before checker tuning

proposed_split.json fixes 40 development runs and 10 held-out runs by run ID. Held-out episodes are **004, 009, 029, 030, 032, 034, 036, 043, 044, 048**; all four supplied examples are development runs. The split uses a documented SHA256 ranking, with already examined reference/anomaly runs 000/002 kept in development. The episode_014 diagnostic was selected only from development records after the split.

The prior availability audit saw all runs, and the targeted setup/mapping investigation uses all 50 beginnings. Thus held-out status is for independent event labels and future rule/tolerance tuning, not a claim that raw availability/setup facts are unseen. Do not tune event definitions or thresholds on held-out event labels. Freeze the human-reviewed definition, parameter rationale and mapping versions before held-out event evaluation. If later setup findings make the proposed split unsuitable, change it transparently before tuning, not after seeing detector performance.

## What validation can and cannot claim now

There is a real setup departure/descent in episode_002 and real policy-phase lift/release/descent evidence in episode_014. Neither is yet an independently adjudicated positive for the clarified requirement. In particular, the setup departure is outside the stated interval and the post-lift definition is undecided. No independently reviewed positive/negative event set or event-checker result exists; therefore no measured recall, precision or continuous-safety performance is claimed. If independent review yields no genuine in-scope positives, report the resulting inability to estimate recall, rather than relabel setup events or generate artificial robot positives.

After review and separate implementation authorization, validate the checker against independent labels, retaining ambiguous/insufficient outcomes. Compare event-time brackets, false alarms, missed reviewed events, applicability errors and unknown rates. Split at run level and report that multiple frames from one run are not independent trials. Calibration must distinguish contact-model penetration, geometry precision, pose phase and physical event size. No acceptance target or numerical fall threshold is invented in this package.

## Separate synthetic evidence

synthetic_cases/proposed_edge_cases.json contains constructed-case specifications and proposed expectations only. They have not been executed as robot simulations and are not robot evidence or recall samples. They cover supported tipping/low roots, indirect support, non-floor catches, support transfers, post-lift ambiguity, unknown initial support, hidden between-snapshot falls, contact-without-grasp, native-ID corruption and phase mismatch.

The included executable tests exercise actual recorded mapping/measurement excerpts and numerical/error-injection safeguards. A deliberately corrupted geometry order is synthetic test corruption of a fixture, not an observed execution. No test implements or validates a fall detector. The source/test README gives exact reproduction commands without model weights, GPU use or original large recordings.
