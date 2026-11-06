"""Checker results: what the Critic accepts from the R1 checker and when it uses one.

Each entry in checker_assessments is the R1 v4 checker's own output, unchanged,
together with the R1 configuration it was run on:

    {"configuration": <R1 v2 configuration>,
     "result": <evaluation.r1_v4.runtime.assess(...) output, assessment.schema.json>}

The Critic does not trust a label the caller writes. A per-object assessment
inside a result is used only if all of these hold:

- the result passes the checker's own output schema, evaluation/r1_v4/assessment.schema.json,
  in full (checked with critic/schema.py, which the tests compare with jsonschema), and it is
  a valid, assessed R1 2.0.0 run by checker 4.0.0a1 with no physical safety conclusion and
  empirical profiles disabled, with every field runtime.py writes for such a run;
- result.assessment_hash is the content hash of the result, and
  result.configuration_hash is the content hash of the supplied configuration,
  so neither was edited after the checker produced them;
- the configuration is the review's own R1 configuration (same content hash as
  evaluation_context.r1_configuration_sha256, which checks.check_configuration binds
  to the context's objects, surfaces and monitored interval), and the result is for
  this requirement, execution and task;
- the checker accepted the run (provenance.admitted_purpose is set);
- the result's admission ledger is the one the checker writes (evaluation/r1_v4/admission.py
  and runtime.py): one admission row per evidence record; admitted_evidence_ids are exactly
  the rows with status verified and rejected_evidence exactly the others; a verified row has
  no reasons, comes from a record declared verified, and every record in its dependency
  closure is verified; a verified record lies inside the monitored interval, on the
  configuration's clock and frame, for this execution and a configured object (or '*'),
  depending only on its own object's records or '*'; no listed conflict joins two verified
  records; and result.study_eligibility follows the objects' scope_mismatch flags;
- the object assessment is for a configured object, this execution and allowed
  surfaces, passes the consistency rules of evaluation/r1_v4/aggregate.py and
  applicability.py (a violation outcome exactly when, being applicable, it has an admitted
  violation record; scope_mismatch exactly when it has an admitted absence record, and then
  only with a not-applicable or invalid-contract result and the matching study_eligibility),
  and its evidence IDs are exactly the verified
  records of that object, as the checker writes them;
- every other object assessment in the same result passes these checks too: the checker writes them
  in one run under one hash, so one that fails makes the whole result unusable (CHK-RESULT);
- it is admitted for this request. The checker only produces synthetic
  analytical output today (synthetic: true, validation_status
  synthetic_analytical_only) and empirical admission is disabled project-wide, so
  a result is used only in a request marked test_fixture, and findings call it
  synthetic. No empirical route exists yet.

The two hashes show that nothing was changed after the checker ran. They do not
show who ran it.
"""
import copy

from . import contract as K
from . import schema as SCHEMA

CONTRACT_REF = 'evaluation/r1_v4/assessment.schema.json'
RUNTIME_REF = 'evaluation/r1_v4/runtime.py:assess'

KNOWN_CHECKER_VERSIONS = frozenset({'4.0.0a1'})
CHECKER_ID = 'r1-v4-restricted-infrastructure'
# Empirical admission is disabled project-wide (r1_v4 runtime: empirical_profiles_enabled is
# always false; evidence_registry_gsn and final_phase5_release: empirical_admission_enabled false).
EMPIRICAL_ADMITTED_STATUSES = frozenset()
SYNTHETIC_STATUSES = frozenset({'synthetic_analytical_only'})
ROUTE_SYNTHETIC = 'synthetic_test_fixture'

# Fixed values from assessment.schema.json and runtime.py.
RESULT_CONSTANTS = {
    'requirement_id': 'R1', 'requirement_version': '2.0.0', 'assessment_schema_version': '1.0.0',
    'configuration_schema_version': '2.0.1', 'physical_safety_conclusion': False,
    'empirical_profiles_enabled': False, 'configuration_status': 'valid', 'assessed': True,
}
RESULT_REQUIRED = ('requirement_id', 'requirement_version', 'checker_version', 'configuration_hash',
                   'assessment_manifest', 'configuration_status', 'assessed', 'object_assessments',
                   'execution_outcome', 'physical_safety_conclusion', 'empirical_profiles_enabled',
                   'admitted_evidence_ids', 'rejected_evidence', 'evidence_admission', 'conflicts',
                   'missing_requirements', 'uncertainty', 'provenance', 'assessment_hash', 'evidence_records',
                   'synthetic', 'validation_status')
FATAL = ('CHK-SHAPE', 'CHK-SCHEMA')  # a result with one of these is not read any further

# The checker's own evidence and admission rows (contracts.py: Evidence, Admission; written by primitive()).
VERIFIED = 'verified'
VALIDITY = {VERIFIED, 'missing', 'invalid_local', 'invalid_contract', 'contradictory'}
TRUTH = {'T', 'F', 'U'}
RECORD_TEXT = ('id', 'kind', 'claim', 'object_id', 'execution_id', 'source_ref', 'producer')
RECORD_LISTS = ('surfaces', 'cells', 'dependencies')
RECORD_FIELDS = RECORD_TEXT + RECORD_LISTS + ('truth', 'validity', 'interval', 'frame', 'uncertainty', 'payload')
FRAME_FIELDS = ('id', 'clock', 'length_unit', 'time_unit', 'handedness')
ADMISSION_FIELDS = ('evidence_id', 'status', 'reasons', 'dependencies', 'source_hash')
ALL_OBJECTS = '*'
STUDY_PENDING, STUDY_UNDECIDED = 'pending_protocol_decision', 'not_decided_by_checker'

APPLICABLE, APPLICABILITY_NA = 'applicable', 'not_applicable'
APPLICABILITY = {APPLICABLE, APPLICABILITY_NA, 'indeterminate', 'unsupported_evidence_contract'}
NEEDS_ADMITTED_EVIDENCE = {K.VIOLATION, K.NO_VIOLATION, K.NOT_APPLICABLE}

COVERAGE_FIELDS = ('requested', 'available', 'admitted', 'negative', 'missing', 'dependencies',
                   'source_groups', 'invalid', 'unobserved')
STRING_LIST_FIELDS = ('surfaces', 'reasons', 'evidence_ids', 'uncertainty')
STRING_FIELDS = ('object_id', 'study_eligibility', 'execution_id', 'requirement_version', 'checker_version',
                 'adapter_version', 'profile_version', 'validation_status')
OBJECT_FIELDS = (('object_id', 'surfaces', 'applicability', 'outcome', 'reasons', 'evidence_ids',
                  'coverage', 'uncertainty', 'complete', 'scope_mismatch')
                 + STRING_FIELDS[1:])


# ------------------------------------------------------------------ hashes

def result_hash(result):
    """The checker's own assessment_hash: sha256 of the canonical result without that key."""
    return K.digest({k: v for k, v in result.items() if k != 'assessment_hash'})


def assessment_id(result, object_id):
    return f"ca:{result.get('assessment_hash')}:{object_id}"


def rehash(item):
    """Recompute both hashes of {configuration, result} (used only by tests to build consistent forgeries)."""
    item = copy.deepcopy(item)
    item['result']['configuration_hash'] = K.digest(item['configuration'])
    item['result']['assessment_hash'] = result_hash(item['result'])
    return item


# ------------------------------------------------------------------ helpers

def _text(value):
    return isinstance(value, str) and value != ''


def _member(value, allowed):
    return isinstance(value, str) and value in allowed


def _str_list(value, unique=True):
    return (isinstance(value, list) and all(_text(v) for v in value)
            and (not unique or len(set(value)) == len(value)))


def _interval(value):
    if not isinstance(value, list) or len(value) != 2:
        return None
    if not all(K.finite_number(x) for x in value):
        return None
    return tuple(value) if value[0] <= value[1] else None


# ------------------------------------------------------------------ result-level checks

def _result_problems(item, ctx, test_fixture):
    """Problems that make every object assessment in this result unusable. Returns [(check_id, category, text)]."""
    if not isinstance(item, dict) or set(item) != {'configuration', 'result'}:
        return [('CHK-SHAPE', 'C02', 'each entry must be exactly {"configuration": ..., "result": ...} holding the '
                 'R1 checker output and the configuration it ran on')]
    config, result = item['configuration'], item['result']
    if not isinstance(config, dict) or not isinstance(result, dict):
        return [('CHK-SHAPE', 'C02', 'configuration and result must both be objects')]
    schema_errors = SCHEMA.errors(result, SCHEMA.load('checker_assessment'), limit=5)
    if schema_errors:
        return [('CHK-SCHEMA', 'C02', f"the checker result does not follow the checker's own output schema "
                 f"({CONTRACT_REF}): {'; '.join(schema_errors)}")]
    missing = [k for k in RESULT_REQUIRED if k not in result]
    if missing:
        return [('CHK-SHAPE', 'C02', f'the checker result is missing {", ".join(missing)}')]
    wrong = [k for k, v in RESULT_CONSTANTS.items() if result.get(k) != v or type(result.get(k)) is not type(v)]
    if wrong:
        return [('CHK-SHAPE', 'C02', 'the checker result has unexpected values for '
                 f'{", ".join(wrong)} (it must be a valid, assessed R1 2.0.0 run with no physical safety conclusion '
                 'and empirical profiles disabled)')]
    lists = ('object_assessments', 'evidence_records', 'rejected_evidence', 'evidence_admission', 'conflicts')
    if not isinstance(result['provenance'], dict) or not _str_list(result['admitted_evidence_ids']) \
            or not all(isinstance(result[k], list) for k in lists):
        return [('CHK-SHAPE', 'C02', f"provenance, admitted_evidence_ids or {', '.join(lists)} have the wrong "
                 'type')]

    shape = _ledger_shape(result)
    if shape:
        return [('CHK-SHAPE', 'C02', 'the checker result\'s evidence or admission rows are malformed: '
                 + '; '.join(shape[:5]))]

    out = []

    def bad(check_id, category, text):
        out.append((check_id, category, text))

    for text in _ledger_problems(result, config, ctx)[:5]:
        bad('CHK-LEDGER', 'C02', f'its admission ledger is not one the checker writes: {text}')
    try:
        hash_ok = result['assessment_hash'] == result_hash(result)
    except (TypeError, ValueError):
        hash_ok = False
    if not hash_ok:
        bad('CHK-HASH', 'C02', 'its assessment_hash does not match its content, so the result was edited after the '
            'checker produced it')
    try:
        config_ok = result['configuration_hash'] == K.digest(config)
    except (TypeError, ValueError):
        config_ok = False
    if not config_ok:
        bad('CHK-CONFIG-HASH', 'C02', 'the supplied configuration is not the one the checker ran on '
            '(configuration_hash mismatch)')
    if result.get('checker_id') != CHECKER_ID or not isinstance(result['checker_version'], str) \
            or result['checker_version'] not in KNOWN_CHECKER_VERSIONS:
        bad('CHK-PRODUCER', 'C02', f"it was produced by {result.get('checker_id')!r} {result['checker_version']!r}, "
            f'not a known R1 checker ({CHECKER_ID} {", ".join(sorted(KNOWN_CHECKER_VERSIONS))})')

    if (ctx.get('requirement_id'), ctx.get('requirement_version')) != (result['requirement_id'],
                                                                        result['requirement_version']) \
            or (config.get('requirement_id'), config.get('requirement_version')) != ('R1', '2.0.0'):
        bad('CHK-REQUIREMENT', 'C03', f"it is for {config.get('requirement_id')} {config.get('requirement_version')}, "
            f"not {ctx.get('requirement_id')} {ctx.get('requirement_version')}")
    prov = result['provenance']
    for key, check_id in (('execution_id', 'CHK-EXECUTION'), ('task_id', 'CHK-TASK')):
        values = [config.get(key), prov.get(key)]
        if any(v != ctx.get(key) or not _text(v) for v in values):
            bad(check_id, 'C03', f"it is for {key.replace('_id', '')} {sorted(set(map(str, values)))}, "
                f"not {ctx.get(key)!r}")
    try:
        same_configuration = K.digest(config) == ctx.get('r1_configuration_sha256')
    except (TypeError, ValueError):
        same_configuration = False
    if not same_configuration:
        # Objects, surfaces, clock and monitored interval all follow from the configuration, which the
        # evaluation context is bound to (checks.check_configuration).
        bad('CHK-CONFIGURATION', 'C03', "the checker ran on a different R1 configuration from the review's "
            '(its content hash is not evaluation_context.r1_configuration_sha256)')

    if not _text(prov.get('admitted_purpose')):
        bad('CHK-ADMISSION', 'C02', 'the checker itself did not admit the run (provenance.admitted_purpose is empty; '
            'see its missing_requirements)')
    elif result['synthetic'] is not True:
        # No empirical route exists: anything not declared synthetic would need empirical admission.
        bad('CHK-ADMISSION', 'C02', 'it is not marked synthetic, and empirical admission is disabled in this '
            'project, so it cannot be used')
    elif test_fixture is not True:
        bad('CHK-ADMISSION', 'C02', 'it is synthetic analytical output, which can only be used in a request marked '
            'test_fixture; empirical admission is disabled in this project')
    return out


# ------------------------------------------------------------------ the admission ledger

def _record_shape(r):
    if not isinstance(r, dict) or set(r) != set(RECORD_FIELDS):
        return 'an evidence record does not have exactly the checker\'s Evidence fields'
    if not all(_text(r[k]) for k in RECORD_TEXT) or not all(_str_list(r[k]) for k in RECORD_LISTS):
        return f"evidence record {r['id']!r} has the wrong text or list fields"
    iv, fr, un = r['interval'], r['frame'], r['uncertainty']
    if (not _member(r['truth'], TRUTH) or not _member(r['validity'], VALIDITY) or not isinstance(r['payload'], dict)
            or not isinstance(iv, dict) or set(iv) != {'start', 'end'} or _interval([iv['start'], iv['end']]) is None
            or not isinstance(fr, dict) or set(fr) != set(FRAME_FIELDS) or not all(_text(fr[k]) for k in FRAME_FIELDS)
            or not isinstance(un, dict) or set(un) != {'temporal', 'description'}
            or not (un['temporal'] is None or _interval([un['temporal'], un['temporal']]))
            or not _str_list(un['description'], unique=False)):
        return f"evidence record {r['id']!r} has a wrong truth, validity, interval, frame, uncertainty or payload"
    return None


def _admission_shape(a):
    if not isinstance(a, dict) or set(a) != set(ADMISSION_FIELDS):
        return 'an admission row does not have exactly the checker\'s Admission fields'
    if (not _text(a['evidence_id']) or not _member(a['status'], VALIDITY) or not _str_list(a['reasons'])
            or not _str_list(a['dependencies']) or not (a['source_hash'] is None or _text(a['source_hash']))):
        return f"admission row {a['evidence_id']!r} has wrong field types or an unknown status"
    return None


def _ledger_shape(result):
    out = [p for p in map(_record_shape, result['evidence_records']) if p]
    out += [p for p in map(_admission_shape, result['evidence_admission'] + result['rejected_evidence']) if p]
    if not all(isinstance(c, list) and len(c) == 3 and all(_text(x) for x in c) for c in result['conflicts']):
        out.append('conflicts must be [left, right, reason] triples')
    return out


def _ledger_problems(result, config, ctx):
    """Contradictions between the result's evidence records, admission rows and object assessments."""
    out = []
    records = {r['id']: r for r in result['evidence_records']}
    rows = {a['evidence_id']: a for a in result['evidence_admission']}
    if len(records) != len(result['evidence_records']) or len(rows) != len(result['evidence_admission']):
        out.append('evidence or admission IDs repeat')
    if set(rows) != set(records):
        out.append(f'admission rows {sorted(set(rows) ^ set(records))[:5]} do not match the evidence records '
                   '(the checker writes one row per record)')
    verified = {i for i, a in rows.items() if a['status'] == VERIFIED}
    if set(result['admitted_evidence_ids']) != verified:
        out.append(f"admitted_evidence_ids differ from the verified admission rows "
                   f"{sorted(set(result['admitted_evidence_ids']) ^ verified)[:5]}")
    rejected = sorted((a for a in result['evidence_admission'] if a['status'] != VERIFIED), key=K.digest)
    if sorted(result['rejected_evidence'], key=K.digest) != rejected:
        out.append('rejected_evidence is not exactly the admission rows that are not verified')

    monitored = ctx.get('monitored_interval') if isinstance(ctx.get('monitored_interval'), dict) else {}
    bounds = _interval(monitored.get('interval'))
    clock = (config.get('temporal_alignment') or {}).get('clock_ref') \
        if isinstance(config.get('temporal_alignment'), dict) else None
    frame = (config.get('coordinate_frames') or {}).get('common_frame') \
        if isinstance(config.get('coordinate_frames'), dict) else None
    configured = set(ctx.get('protected_objects') or []) if isinstance(ctx.get('protected_objects'), list) else set()
    for rid in sorted(verified & set(records)):
        a, r = rows[rid], records[rid]
        closure = set(a['dependencies'])
        if a['reasons'] or r['validity'] != VERIFIED:
            out.append(f'{rid} is verified although it has rejection reasons or was declared {r["validity"]}')
        if rid not in closure or not closure <= set(records) or not set(r['dependencies']) <= closure:
            out.append(f'{rid} has a dependency closure that does not match its record')
        elif not closure <= verified:
            out.append(f'{rid} is verified but depends on {sorted(closure - verified)[:3]}, which the checker '
                       'did not admit')
        span = (r['interval']['start'], r['interval']['end'])
        if bounds is None or not bounds[0] <= span[0] <= span[1] <= bounds[1]:
            out.append(f'{rid} is verified but its interval {list(span)} lies outside the monitored interval '
                       f'{list(bounds) if bounds else None}')
        if r['frame']['clock'] != clock or r['frame']['id'] != frame:
            out.append(f"{rid} is verified but uses clock {r['frame']['clock']!r} and frame {r['frame']['id']!r}, "
                       f'not the configuration\'s {clock!r} and {frame!r}')
        if r['execution_id'] != ctx.get('execution_id') or r['object_id'] not in configured | {ALL_OBJECTS}:
            out.append(f"{rid} is verified but is for {r['execution_id']}/{r['object_id']}")
        if any(d in records and records[d]['object_id'] not in (r['object_id'], ALL_OBJECTS)
               for d in r['dependencies']):
            out.append(f'{rid} is verified but depends on another object\'s record')
    for left, right, _ in result['conflicts']:
        if left not in records or right not in records:
            out.append(f'conflict {left} / {right} names an unknown record')
        elif left in verified and right in verified:
            out.append(f'{left} and {right} conflict but both are verified')
    objects = [o for o in result['object_assessments'] if isinstance(o, dict)]
    pending = any(o.get('scope_mismatch') is True for o in objects)
    if result.get('study_eligibility') != (STUDY_PENDING if pending else STUDY_UNDECIDED):
        out.append(f"study_eligibility {result.get('study_eligibility')!r} does not follow the objects' "
                   'scope_mismatch flags')
    return out


# ------------------------------------------------------------------ object-level checks

def _object_shape(oa):
    if not isinstance(oa, dict):
        return ['the object assessment is not an object']
    out = []
    missing = [k for k in OBJECT_FIELDS if k not in oa]
    extra = [k for k in oa if k not in OBJECT_FIELDS]
    if missing:
        out.append(f'missing: {", ".join(missing)}')
    if extra:
        out.append(f'unknown fields: {", ".join(map(str, extra))}')
    for k in STRING_FIELDS:
        if k in oa and not _text(oa[k]):
            out.append(f'{k} must be a non-empty string')
    for k in STRING_LIST_FIELDS:
        if k in oa and not _str_list(oa[k]):
            out.append(f'{k} must be a list of distinct non-empty strings')
    for k in ('complete', 'scope_mismatch'):
        if k in oa and not isinstance(oa[k], bool):
            out.append(f'{k} must be true or false')
    if 'applicability' in oa and not (isinstance(oa['applicability'], str) and oa['applicability'] in APPLICABILITY):
        out.append(f'applicability {oa["applicability"]!r} is not an R1 applicability value')
    if 'outcome' in oa and not (isinstance(oa['outcome'], str) and oa['outcome'] in K.OUTCOMES):
        out.append(f'outcome {oa["outcome"]!r} is not an R1 outcome')
    if 'coverage' in oa:
        cov = oa['coverage']
        if not isinstance(cov, dict) or set(cov) != set(COVERAGE_FIELDS):
            out.append(f'coverage must have exactly: {", ".join(COVERAGE_FIELDS)}')
        elif not isinstance(cov['source_groups'], list) or not all(
                _str_list(cov[k]) for k in COVERAGE_FIELDS if k != 'source_groups'):
            out.append('coverage lists have the wrong type')
    return out


def _object_problems(oa, result, config, ctx):
    shape = _object_shape(oa)
    if shape:
        return [('CHK-SHAPE', 'C02', 'object assessment: ' + '; '.join(shape))]
    out = []

    def bad(check_id, category, text):
        out.append((check_id, category, text))

    oid = oa['object_id']
    configured = ctx.get('protected_objects') if isinstance(ctx.get('protected_objects'), list) else []
    if oid not in configured:
        bad('CHK-OBJECT', 'C03', f'object {oid!r} is not a configured protected object')
    if oa['execution_id'] != ctx.get('execution_id'):
        bad('CHK-EXECUTION', 'C03', f"it is for execution {oa['execution_id']!r}, not {ctx.get('execution_id')!r}")
    if (oa['requirement_version'] != ctx.get('requirement_version')
            or oa['checker_version'] != result['checker_version']):
        bad('CHK-REQUIREMENT', 'C03', f"it reports requirement {oa['requirement_version']} and checker "
            f"{oa['checker_version']}, which do not match its result")
    mapping = config.get('object_surface_mapping') if isinstance(config.get('object_surface_mapping'), dict) else {}
    allowed = mapping.get(oid) if isinstance(mapping.get(oid), list) else []
    if not set(oa['surfaces']) <= set(s for s in allowed if isinstance(s, str)):
        bad('CHK-SURFACES', 'C03', f"it uses surfaces {oa['surfaces']}, but the configuration maps {oid} to {allowed}")

    outcome, applicability = oa['outcome'], oa['applicability']
    if ((outcome in (K.VIOLATION, K.NO_VIOLATION) and applicability != APPLICABLE)
            or (outcome == K.NO_VIOLATION and oa['coverage']['missing'])
            or (outcome == K.NOT_APPLICABLE and applicability != APPLICABILITY_NA)):
        bad('CHK-CONSISTENCY', 'C02', f'outcome {outcome} with applicability {applicability} '
            f"{'and missing coverage ' if oa['coverage']['missing'] else ''}breaks the R1 aggregation "
            'consistency rules')
    records = {r.get('id'): r for r in result['evidence_records'] if isinstance(r, dict) and _text(r.get('id'))}
    admitted = set(result['admitted_evidence_ids'])
    own = {i for i, r in records.items() if r.get('object_id') == oid and i in admitted}
    fall = any(records[i].get('claim') == 'violation' and records[i].get('truth') == 'T' for i in own)
    if applicability == APPLICABLE and (outcome == K.VIOLATION) != fall:
        bad('CHK-CONSISTENCY', 'C02', f'outcome {outcome} does not follow its evidence: the checker gives a violation '
            'outcome to an applicable object exactly when it admitted a violation record for it '
            f"({'there is one' if fall else 'there is none'})")
    absent = any(records[i].get('claim') == 'presence' and records[i].get('truth') == 'F' for i in own)
    if oa['scope_mismatch'] != absent or oa['scope_mismatch'] != (oa['study_eligibility'] == STUDY_PENDING) \
            or oa['study_eligibility'] not in (STUDY_PENDING, STUDY_UNDECIDED) \
            or (oa['scope_mismatch'] and applicability not in (APPLICABILITY_NA, 'unsupported_evidence_contract')):
        bad('CHK-CONSISTENCY', 'C02', f"scope_mismatch {oa['scope_mismatch']} with applicability {applicability} and "
            f"study_eligibility {oa['study_eligibility']!r} is not what the checker writes (scope_mismatch marks an "
            'object verified absent by an admitted presence record: not applicable, or invalid contract, with '
            f"study eligibility pending; admitted absence record: {'yes' if absent else 'no'})")

    if oa['validation_status'] not in SYNTHETIC_STATUSES:
        bad('CHK-ADMISSION', 'C02', f"its status {oa['validation_status']!r} is not admitted; only synthetic "
            'analytical output exists and empirical admission is disabled in this project')

    if outcome in NEEDS_ADMITTED_EVIDENCE and not oa['evidence_ids']:
        bad('CHK-EVIDENCE', 'C02', f'outcome {outcome} cites no evidence')
    for eid in oa['evidence_ids']:
        rec = records.get(eid)
        if rec is None:
            bad('CHK-EVIDENCE', 'C02', f"it cites evidence {eid}, which is not among the checker's evidence records")
        elif rec.get('execution_id') != ctx.get('execution_id') or rec.get('object_id') != oid:
            bad('CHK-EVIDENCE', 'C03', f"it cites evidence {eid}, which belongs to "
                f"{rec.get('execution_id')}/{rec.get('object_id')}")
        elif eid not in admitted:
            bad('CHK-EVIDENCE', 'C02', f'its {outcome} outcome cites evidence {eid}, which the checker did not admit '
                '(the checker cites only admitted records)')
    omitted = sorted(own - set(oa['evidence_ids']))
    if omitted:
        bad('CHK-EVIDENCE', 'C02', f'it leaves out admitted evidence of its object {omitted[:5]} (the checker cites '
            'every admitted record of the object)')
    return out


# ------------------------------------------------------------------ admission

def admit(req):
    """Validate every supplied checker result.

    Returns (admitted {object_id: [assessment]}, admission log for the report, problems
    as [(check_id, category, text, assessment_id, object_id)]; result-wide problems carry the
    result's ID 'ca:<assessment_hash>' and no object). An admitted assessment is
    {assessment_id, object_id, outcome, applicability, interval, route, evidence_ids, complete, uncertainty}.
    """
    ctx = req['evaluation_context']
    test_fixture = req.get('test_fixture')
    admitted, log, problems, seen = {}, [], [], set()
    for i, item in enumerate(req['checker_assessments']):
        result_level = _result_problems(item, ctx, test_fixture)
        result = item.get('result') if isinstance(item, dict) and isinstance(item.get('result'), dict) else {}
        config = item.get('configuration') if isinstance(item, dict) and isinstance(item.get('configuration'), dict) \
            else {}
        h = result.get('assessment_hash')
        if isinstance(h, str) and h in seen:
            result_level = result_level + [('CHK-DUP', 'C02', 'the same checker result appears more than once')]
        if isinstance(h, str):
            seen.add(h)
        objects = result.get('object_assessments')
        if not isinstance(objects, list) or not objects or any(p[0] in FATAL for p in result_level):
            aid = f'checker_assessments[{i}]'
            found = result_level or [('CHK-SHAPE', 'C02', 'the checker result has no object assessments')]
            problems.extend((c, cat, t, aid, None) for c, cat, t in found)
            log.append(_row(aid, {}, None, False, found))
            continue
        # A problem with the whole result is reported once, against the result; object problems per object.
        problems.extend((c, cat, t, f'ca:{h}', None) for c, cat, t in result_level)
        monitored = ctx.get('monitored_interval') if isinstance(ctx.get('monitored_interval'), dict) else {}
        bounds = _interval(monitored.get('interval'))
        own_problems = [_object_problems(oa, result, config, ctx) for oa in objects]
        broken = [assessment_id(result, oa.get('object_id') if isinstance(oa, dict) else f'#{j}')
                  for j, (oa, own) in enumerate(zip(objects, own_problems)) if own]
        if broken:
            # The checker writes every object assessment of a result in one run, and the hash covers them all:
            # if one is not what the checker writes, none of them can be trusted.
            whole = ('CHK-RESULT', 'C02', f'{len(broken)} of its object assessments failed validation, so the result '
                     'is not entirely what the checker wrote and none of its object assessments is used')
            problems.append(whole[:3] + (f'ca:{h}', None))
            result_level = result_level + [whole]
        for j, (oa, own) in enumerate(zip(objects, own_problems)):
            oid = oa.get('object_id') if isinstance(oa, dict) and _text(oa.get('object_id')) else None
            aid = assessment_id(result, oid if oid else f'#{j}')
            problems.extend((c, cat, t, aid, oid) for c, cat, t in own)
            found = result_level + own
            ok = not found and bounds is not None  # an invalid monitored interval is already fatal (REQ-INTERVAL)
            if ok:
                admitted.setdefault(oid, []).append({
                    'assessment_id': aid, 'object_id': oid, 'outcome': oa['outcome'],
                    'applicability': oa['applicability'], 'interval': list(bounds), 'route': ROUTE_SYNTHETIC,
                    'evidence_ids': list(oa['evidence_ids']), 'complete': oa['complete'],
                    'uncertainty': list(oa['uncertainty'])})
            log.append(_row(aid, oa if isinstance(oa, dict) else {}, list(bounds) if bounds else None, ok, found))
    return admitted, log, problems


def _row(aid, oa, interval, ok, found):
    def text_or_none(key):
        return oa.get(key) if isinstance(oa.get(key), str) else None
    return {'assessment_id': aid, 'object_id': text_or_none('object_id'), 'outcome': text_or_none('outcome'),
            'applicability': text_or_none('applicability'), 'interval': interval, 'admitted': ok,
            'route': ROUTE_SYNTHETIC if ok else None, 'problems': sorted({p[0] for p in found})}


def describe(assessment):
    """How a finding names an admitted assessment."""
    if assessment['route'] == ROUTE_SYNTHETIC:
        return 'admitted synthetic (test-fixture) checker assessment'
    return 'admitted checker assessment'
