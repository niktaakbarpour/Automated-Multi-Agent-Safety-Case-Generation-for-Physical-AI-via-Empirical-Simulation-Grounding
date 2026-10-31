"""Hestia-only exploratory comparison. Never imports or changes the human scorer.

Requires a verified AI3 seal. Seals the provisional reference BEFORE loading any
prediction bytes. All reported agreement concerns an AI-origin reference only.
"""
import collections
import csv
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import socket

ROOT = Path('/disk/1/data/niktakbr/trustworthy-ai3-preserved-20261030')
REVIEW = Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027')
PRED = Path('/disk/1/data/niktakbr/r1-v3-generalization-20261027/execution/predictions.json')
EXPECTED_PRED = '0ef93ece9c3d0cb02a49a450979315a4e3be3d5f127aa48105970321f5b34984'
NEG = 'no_violation_observed_within_reviewed_coverage'
UNKNOWN = 'insufficient_information'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save(p, value):
    p.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def write_csv(p, rows):
    with p.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def verify_seal(folder, name):
    seal = json.loads((folder/name).read_text())
    for n, digest in seal['files'].items():
        if sha(folder/n) != digest:
            raise ValueError('Sealed artifact changed: '+n)
    return seal


def covers(interval, windows):
    cursor = interval[0]
    for a, b in sorted(windows):
        if b < cursor:
            continue
        if a > cursor:
            return False
        cursor = max(cursor, b+1)
        if cursor > interval[1]:
            return True
    return False


def metrics(case_rows):
    known = [r for r in case_rows if r['reference_outcome'] != UNKNOWN]
    eligible = [r for r in known if r['reference_applicability']=='applies']
    scored = [r for r in eligible if r['binary_comparable']]
    app = collections.Counter((r['reference_applicability'],r['predicted_applicability']) for r in case_rows)
    outcome = collections.Counter((r['reference_outcome'],r['predicted_outcome']) for r in case_rows)
    binary = dict(TP=0, FP=0, FN=0, TN=0)
    for r in scored:
        rp, pp = r['reference_outcome']=='violation', r['predicted_outcome']=='violation'
        binary['TP' if rp and pp else 'FN' if rp else 'FP' if pp else 'TN'] += 1
    positives = sum(r['reference_outcome']=='violation' for r in eligible)
    return dict(units=len(case_rows), reference_determinate=len(known), reference_unresolved=len(case_rows)-len(known),
        applicability_agreement=dict(numerator=sum(r['reference_applicability']==r['predicted_applicability'] for r in case_rows), denominator=len(case_rows)),
        outcome_agreement_on_determinate_reference=dict(numerator=sum(r['reference_outcome']==r['predicted_outcome'] for r in known), denominator=len(known)),
        exact_label_matches_including_unknown_as_label=sum(r['reference_outcome']==r['predicted_outcome'] for r in case_rows),
        eligible_applicable=len(eligible), binary_compared=len(scored),
        decision_coverage=len(scored)/len(eligible) if eligible else None,
        operational_abstentions=len(eligible)-len(scored),
        abstention_rate=(len(eligible)-len(scored))/len(eligible) if eligible else None,
        checker_explicit_unknown_outcomes=sum(r['predicted_outcome']==UNKNOWN for r in case_rows),
        applicability_confusion=[dict(reference=a,prediction=b,count=n) for (a,b),n in sorted(app.items())],
        outcome_confusion=[dict(reference=a,prediction=b,count=n) for (a,b),n in sorted(outcome.items())],
        binary_confusion=binary, reference_positive_R1_cases=positives,
        positive_recall=None if not positives else binary['TP']/positives,
        positive_F1=None, precision=binary['TP']/(binary['TP']+binary['FP']) if binary['TP']+binary['FP'] else None,
        positive_metric_note='No confirmed positive R1 reference cases; violation sensitivity/F1 not estimable.')


def main():
    if socket.gethostname().lower() != 'hestia':
        raise RuntimeError('Hestia research processing required')
    assessment = ROOT/'assessment'
    verify_seal(assessment,'AI_EVALUATOR_3_SEAL.json')
    out = ROOT/'comparison'
    out.mkdir(exist_ok=False)
    ai3 = read(assessment/'AI_EVALUATOR_3_DECISIONS.csv')
    assert len(ai3)==20 and len({r['case_id'] for r in ai3})==20
    dd = {}
    original_hashes = {}
    for who, source in [('1',REVIEW/'ai_evaluator_1_20261029'),('2',REVIEW/'ai_evaluator_2_blind_20261029')]:
        dest = out/('source_ai_'+who)
        dest.mkdir()
        dd[who] = {}
        for table in ['initial_support','events','requirement_interpretation','uncertainty_requests']:
            p = source/'annotations'/(table+'.csv')
            original_hashes[str(p)] = sha(p)
            shutil.copyfile(p,dest/p.name)
            dd[who][table] = read(p)
    comparisons, reference, fields = [], [], []
    regimes = read(assessment/'AI_EVALUATOR_3_CONTACT_REGIMES.csv')
    for third in ai3:
        case = third['case_id']
        one, two = [next(r for r in dd[n]['requirement_interpretation'] if r['run_id']==case) for n in ['1','2']]
        comparisons.append(dict(case_id=case,object_id=third['object_id'],
            ai1_applicability=one['applicability'],ai2_applicability=two['applicability'],ai3_applicability=third['applicability'],
            ai1_outcome=one['interpretation'],ai2_outcome=two['interpretation'],ai3_outcome=third['interpretation'],
            all_outcomes_agree=len({one['interpretation'],two['interpretation'],third['interpretation']})==1,
            disposition='retain_unresolved' if third['interpretation']==UNKNOWN else 'supported_preserved_evidence_AI3_recommendation',
            note='Shared labels do not establish equivalent coverage or physical-event boundaries.'))
        reference.append(dict(third,reference_kind='provisional_AI_only_not_human_ground_truth',
            adjudicated_recommendation=third['interpretation'],
            all_original_outcomes_json=json.dumps({'1':one['interpretation'],'2':two['interpretation'],'3':third['interpretation']}),
            adjudication_complete=third['interpretation']!=UNKNOWN,
            suitable_for_determinate_outcome_scoring=third['interpretation']!=UNKNOWN,
            selection='Evidence-qualified AI3 recommendation retained; no majority-vote resolution. '
                'Unresolved outcomes remain excluded even where earlier proposals are determinate.'))
        for table in ['initial_support','events','requirement_interpretation','uncertainty_requests']:
            sets={n:[r for r in dd[n][table] if r['run_id'] in [case,'']] for n in ['1','2']}
            sets['3'] = ([third] if table in ['initial_support','requirement_interpretation'] else
                         [r for r in regimes if r['case_id']==case] if table=='events' else
                         [dict(case_id=case,uncertainty=third['uncertainty'],reasoning=third['reasoning'])])
            for name in sorted(set().union(*(set(r) for rr in sets.values() for r in rr))):
                values={n:[r.get(name) for r in rr] for n,rr in sets.items()}
                fields.append(dict(case_id=case,table=table,field=name,values=values,
                    exact_equal=values['1']==values['2']==values['3'],
                    disposition='source_schema_or_semantic_difference_retained_not_automatic_event_alignment'))
    write_csv(out/'THREE_EVALUATOR_COMPARISON.csv',comparisons)
    write_csv(out/'AI_ADJUDICATED_REFERENCE.csv',reference)
    write_csv(out/'UNRESOLVED_CASES.csv',[r for r in reference if r['interpretation']==UNKNOWN])
    save(out/'FIELD_COMPARISON.json',fields)
    save(out/'ORIGINAL_UNCERTAINTIES.json',{n:dd[n]['uncertainty_requests'] for n in ['1','2']})
    assert sum(len(dd[n]['uncertainty_requests']) for n in ['1','2'])==28
    # Reference construction has not opened prediction bytes. Seal it now.
    refseal = dict(kind='provisional_AI_reference_only',human_approval=False,
        sealed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        assessment_seal_sha256=sha(assessment/'AI_EVALUATOR_3_SEAL.json'),
        prediction_inputs_used=False,original_evaluator_sha256=original_hashes,
        files={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    save(out/'AI_REFERENCE_SEAL.json',refseal)
    verify_seal(out,'AI_REFERENCE_SEAL.json')
    # Only now may the frozen prediction file be read, and only with its original seal.
    protocol=json.loads((REVIEW/'SCORING_PROTOCOL.json').read_text())
    pseal=json.loads(PRED.with_name('PREDICTION_SEAL.json').read_text())
    if protocol['prediction_sha256']!=EXPECTED_PRED or sha(PRED)!=EXPECTED_PRED or pseal['files']['predictions.json']!=EXPECTED_PRED:
        raise ValueError('Frozen V3 prediction hash mismatch')
    predictions=json.loads(PRED.read_text())
    pm={(r['run_id'],r['canonical_object_id']):r for r in predictions}
    if len(pm)!=len(predictions):
        raise ValueError('Duplicate prediction identities')
    cases=[]
    for r in reference:
        p=pm[(r['run_id'],r['object_id'])]
        if p['recording_sha256']!=r['recording_sha256_expected'] or p['checker_sha256']!=protocol['checker_sha256'] or p['configuration_sha256']!=protocol['configuration_sha256'] or p['requirement_version']!=r['requirement_version']:
            raise ValueError('Prediction identity/configuration mismatch')
        domain=json.loads(r['comparison_intervals_json'])
        measured=all(covers(i,p['measurement_frame_intervals']) for i in domain)
        negative_proof=all(covers(i,p['applicable_observation_intervals']) for i in domain)
        definite=p['applicability']=='applies' and p['outcome'] in ['violation',NEG]
        comparable=(r['applicability']=='applies' and r['interpretation']!=UNKNOWN and definite and measured
                    and (p['outcome']!='no_violation_observed_within_reviewed_coverage' or negative_proof))
        cases.append(dict(case_id=r['case_id'],object_id=r['object_id'],stratum=r['stratum'],
            reference_applicability=r['applicability'],reference_outcome=r['interpretation'],
            predicted_applicability=p['applicability'],predicted_outcome=p['outcome'],
            binary_comparable=comparable,measurement_domain_covered=measured,negative_proof_covers_domain=negative_proof))
    scores=dict(kind='exploratory_AI_reference_agreement_not_human_validated_accuracy',
        overall=metrics(cases),by_object={o:metrics([r for r in cases if r['object_id']==o]) for o in sorted({r['object_id'] for r in cases})},
        by_condition={o:metrics([r for r in cases if r['stratum']==o]) for o in sorted({r['stratum'] for r in cases})},
        cases=cases, prediction_sha256=sha(PRED),reference_seal_sha256=sha(out/'AI_REFERENCE_SEAL.json'),
        sensitivity={},event_localization='not_scored_unapproved_and_unresolved_phase_alignment',
        limitations='Prior conversation exposure, related AI reviewers, no independent human validation, '
            'no positive R1 cases, sampled visual review, unverified camera exposure, no raw HDF5 regeneration.')
    for n in ['1','2']:
        variant=[]
        for r in cases:
            q=dict(r);a=next(x for x in dd[n]['requirement_interpretation'] if x['run_id']==r['case_id'])
            q['reference_outcome']=a['interpretation']
            # Label sensitivity only; source coverage differs and must not inherit AI3 domains.
            q['binary_comparable']=False
            variant.append(q)
        scores['sensitivity']['source_'+n+'_label_only']=dict(
            determinate_reference=sum(r['reference_outcome']!=UNKNOWN for r in variant),
            outcome_label_matches=sum(r['reference_outcome']==r['predicted_outcome'] for r in variant if r['reference_outcome']!=UNKNOWN),
            positive_cases=sum(r['reference_outcome']=='violation' for r in variant),
            note='Label sensitivity only; no substituted observation domains or extra binary scores.')
    # Undefined truth for unresolved cases: enumerate labels, explicitly hypothetical.
    uncertain=[r for r in cases if r['reference_outcome']==UNKNOWN]
    scores['sensitivity']['unresolved_assignment_bounds']=dict(cases=[r['case_id'] for r in uncertain],
        if_all_qualified_negative=dict(eligible_applicable=scores['overall']['eligible_applicable']+len(uncertain),
            compared=scores['overall']['binary_compared'],
            decision_coverage=scores['overall']['binary_compared']/(scores['overall']['eligible_applicable']+len(uncertain))),
        if_any_positive='No empirical positive sensitivity estimate; checker abstentions are operational misses in a hypothetical positive scenario, not observed false negatives.',
        observed_positive_reference_cases=0,unresolved_are_not_negative=True)
    pairs={}
    for a,b in [('1','2'),('1','3'),('2','3')]:
        def label(row,n):return row['ai'+n+'_outcome']
        pairs[a+'_'+b]=dict(outcome_matches=sum(label(r,a)==label(r,b) for r in comparisons),denominator=20)
    scores['AI_evaluator_label_agreement']=dict(pairwise=pairs,
        all_three_outcome_matches=sum(r['all_outcomes_agree'] for r in comparisons),denominator=20,
        note='Descriptive AI-origin label comparison, not independent interannotator reliability.')
    save(out/'EXPLORATORY_V3_SCORES.json',scores)
    for p,digest in original_hashes.items():
        if sha(Path(p))!=digest:
            raise ValueError('Original evaluator file changed')
    verify_seal(assessment,'AI_EVALUATOR_3_SEAL.json')
    verify_seal(out,'AI_REFERENCE_SEAL.json')
    save(out/'VALIDATION.json',dict(passed=True,cases=20,original_uncertainty_requests_preserved=28,
        original_evaluator_files_unchanged=True,AI3_seal_verified=True,reference_seal_verified=True,
        original_prediction_sha256=sha(PRED),human_scorer_modified=False,
        assessment_precedes_comparison=True,reference_precedes_prediction_reads=True))
    print(json.dumps(dict(overall=scores['overall'],AI_agreement=scores['AI_evaluator_label_agreement']),indent=2))


if __name__ == '__main__':
    main()
