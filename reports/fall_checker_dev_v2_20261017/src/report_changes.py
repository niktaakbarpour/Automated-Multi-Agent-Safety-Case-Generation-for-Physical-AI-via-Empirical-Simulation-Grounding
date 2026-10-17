"""Before/after detector-development comparison; no human labels assigned."""
import json,sys,collections,csv,gzip
from pathlib import Path

def count(records):
    types=collections.Counter();phase=collections.Counter();app=collections.Counter();n=0
    for r in records:
        for a in r['objects'].values():
            app[a['initial_applicability']]+=1
            for e in a['events']:n+=1;types[e['type']]+=1;phase[e['phase']+' / '+e['type']]+=1
    return dict(total=n,types=dict(types),phase_types=dict(phase),applicability=dict(app))

def compare_events(before,after):
    available=set(range(len(after)));matched=[];removed=[]
    for old in before:
        candidates=[]
        for i in available:
            new=after[i]
            if old['phase']!=new['phase']:continue
            a,b=old['descent_frames'];x,y=new['descent_frames']
            overlap=min(b,y)-max(a,x)
            if overlap>=0:candidates.append((overlap,-abs(old['confirmation_frame']-new['confirmation_frame']),i))
        if not candidates:removed.append(old);continue
        i=max(candidates)[-1];available.remove(i);new=after[i]
        fields=['type','descent_frames','confirmation_frame','departure_bracket']
        changes={k:{'before':old.get(k),'after':new.get(k)} for k in fields if old.get(k)!=new.get(k)}
        matched.append({'before':old,'after':new,'changed_legacy_fields':changes})
    return {'matching_method':'Greedy same-phase confirmation-window overlap, then nearest confirmation frame. Descriptive matching only, not identity of true physical events.',
            'matched':matched,'removed':removed,'added':[after[i] for i in sorted(available)]}

def report(root,old):
    out=root/'outputs';b=json.loads((old/'outputs/sensitivity.json').read_text());n=json.loads((out/'sensitivity.json').read_text());p=json.loads((out/'persistence_only_ablation.json').read_text())
    oldmap={(r['run_id'],r['profile']):r for r in b};newmap={(r['run_id'],r['profile']):r for r in n};pmap={(r['run_id'],r['profile']):r for r in p}
    changes=[];stats={};profiledifferences=[]
    for profile in ['base','strict','broad']:
        stats[profile]={'before':count([r for r in b if r['profile']==profile]),'persistence_only':count([r for r in p if r['profile']==profile]),'after':count([r for r in n if r['profile']==profile])}
    for key,prior in oldmap.items():
        for name,a in prior['objects'].items():
            z=newmap[key]['objects'][name];ab=pmap[key]['objects'][name]
            changes.append({'run_id':key[0],'profile':key[1],'object':name,'applicability_before':a['initial_applicability'],'applicability_after':z['initial_applicability'],
              'applicability_changed':a['initial_applicability']!=z['initial_applicability'],'before_vs_after':compare_events(a['events'],z['events']),
              'before_vs_persistence_only':compare_events(a['events'],ab['events']),
              'classification_history':[(e['confirmation_frame'],e['classification_history']) for e in z['events']],
              'unconfirmed_descent_sequences':z['unconfirmed_descent_sequences']})
    # Compare profiles using the same original signature, plus final strengthened event type.
    def ending_signature(e):
        x=e.get('ending')
        if x is None or x.get('censored',False):return None
        return (x.get('reason',x.get('type')),x.get('reference',{}).get('frame',x.get('frame')))
    signature=lambda a:(a['initial_applicability'],[(e['type'],e['phase'],e['descent_frames'],ending_signature(e)) for e in a['events']])
    for run,profile in newmap:
        if profile=='base':continue
        for name,a in newmap[(run,profile)]['objects'].items():
            base=newmap[(run,'base')]['objects'][name]
            if signature(a)!=signature(base):profiledifferences.append({'run_id':run,'profile':profile,'object':name,'base':base,'profile_result':a})
    old_profiledifferences=[]
    for run,profile in oldmap:
        if profile=='base':continue
        for name,a in oldmap[(run,profile)]['objects'].items():
            if signature(a)!=signature(oldmap[(run,'base')]['objects'][name]):old_profiledifferences.append((run,profile,name))
    upgrades=[{'run_id':r['run_id'],'profile':r['profile'],'object':name,'event':e} for r in n for name,a in r['objects'].items() for e in a['events'] if len(e['classification_history'])>1]
    (out/'before_after.json').write_text(json.dumps({'statistics':stats,'object_profile_comparisons':changes,'matching_caveat':'Candidate segments are not confirmed physical events; overlap matching does not prove correspondence.'},indent=2))
    (out/'sensitivity_differences.json').write_text(json.dumps(profiledifferences,indent=2));(out/'classification_upgrades.json').write_text(json.dumps(upgrades,indent=2))
    ep14=next(r for r in n if r['profile']=='base' and 'trial014_' in r['run_id']);cream=ep14['objects']['cream_cheese_1']
    direct=[{'run_id':r['run_id'],'profile':r['profile'],'object':name,'event':e} for r in n for name,a in r['objects'].items() for e in a['events'] if e['type']=='direct_table_departure_descent_candidate']
    lines=['# Focused development checker v2 change report','','All results remain provisional and unvalidated. The reviewed release and its outputs are unchanged. No physical threshold, model, task, partition or sampling setting was changed. All 40 development runs were reassessed using hash-verified saved geometry/contact extracts; no original recording or held-out recording was opened.','','## Counts by profile','','| Profile | Before | Persistence-only fix | Full correction |','|---|---:|---:|---:|']
    for profile,x in stats.items():lines.append(f"| {profile} | {x['before']['total']} | {x['persistence_only']['total']} | {x['after']['total']} |")
    lines+=['','Counts describe candidate segments, including setup and unknown-origin descents, not independent or confirmed falls. Full type/phase counts and 600 object/profile comparisons are in outputs/before_after.json.','','## Type and interval changes','']
    for profile,x in stats.items():
        lines.extend([f"- {profile}: before {x['before']['types']}; after {x['after']['types']}.",f"  After by phase/type: {x['after']['phase_types']}."])
    appchanges=sum(x['applicability_changed'] for x in changes)
    matchedchanged=sum(bool(m['changed_legacy_fields']) for x in changes for m in x['before_vs_after']['matched']);removed=sum(len(x['before_vs_after']['removed']) for x in changes);added=sum(len(x['before_vs_after']['added']) for x in changes)
    lines+=['',f'Across all profiles: {appchanges} applicability changes; {matchedchanged} overlap-matched candidates change type, confirmation window, confirmation frame or departure bracket; {removed} prior candidates unmatched/removed and {added} new unmatched candidates. Matching is descriptive, based on same-phase interval overlap and nearest confirmation; it is not adjudicated physical-event identity.',
        '', 'Departure brackets now require an observed consecutive support-loss pair and remain separate from the contact-free window. Two counted intervals require three free endpoints. Confirmation windows may therefore start later; lifecycle spans continue through later evidence or an explicit ending/censor. The prior software test expecting a missing ending at termination was updated to expect explicit censoring; the initial failure and final test logs are preserved.',
        '', '## Episode 014', '',f"Base cream-cheese candidates after correction: {len(cream['events'])}. Unconfirmed sequences: {json.dumps(cream['unconfirmed_descent_sequences'])}",
        '', 'Frames 281→282 cannot count as a contact-free interval because frame 281 has gripper contact. Frames 282→283 supply one observed contact-free descent interval. Frame 284 returns to table contact, so 283→284 also cannot count. The previous candidate at frame 283 was therefore not supported by the documented two-interval persistence rule. Retaining the short sequence as unconfirmed evidence does not label it a non-event: this criterion can miss genuine short drops. Post-lift evidence remains separate from direct-table-fall scope and no requirement verdict is assigned.',
        '', '## Does the earlier no-direct-candidate finding still hold?', '',f"Final direct-table-departure candidates across profiles: {len(direct)}; base: {sum(x['profile']=='base' for x in direct)}. Inspect outputs/classification_upgrades.json for later strengthening and its exact supporting frames."]
    if direct and not any(d['profile']=='base' for d in direct):lines.append('The earlier no-direct-candidate finding still holds for the base profile, but no longer holds across every sensitivity profile. The newly strengthened candidate is a setup segment under the broad profile; it is not automatically a policy-interval requirement violation.')
    for d in direct:lines.append(f"- {d['profile']} / {d['run_id']} / {d['object']}: {d['event']['phase']}, confirmation {d['event']['confirmation_frame']}, final type {d['event']['type']}, classification changes {d['event']['classification_history']}.")
    lines+=['',f'{len(upgrades)} event/profile instances change type after confirmation. Unresolved contact/gripper history is retained and prevents an unsupported geometry-only upgrade. No direct-candidate finding is a statement of continuous safety or proof of no fall.',
        '', '## Applicability and sensitivity', '',f"Base applicability before: {stats['base']['before']['applicability']}; after: {stats['base']['after']['applicability']}. Unknown initial support is insufficient information, never a pass or verified non-applicability.",f'Prior profile-versus-base assessments differing using the same applicability/type/phase/window/observed-ending signature: {len(old_profiledifferences)}. Revised profile-versus-base assessments differing in applicability, final type, phase, confirmation window or observed ending type/frame: {len(profiledifferences)}. These use explicitly stated signatures; the exact before/after profile records are in before_after.json. Revised {len(profiledifferences)} object/profile comparisons differ from revised base; exact candidate intervals, final types and endings are exported. Differences caused by stricter endpoint persistence are distinguished by the persistence-only ablation. Unchanged physical parameter values do not make the detector validated.',
        '', '## Human review', '', 'Use REVIEW_GUIDE.md for exact clip names and blank forms. Initial support, physical event labels and requirement interpretation are separate. Labels, identities and decisions remain blank. Clips are unchanged consecutive excerpts with camera-phase qualifications. No human agreement, precision or recall is claimed. Software test success does not validate this detector.']
    (root/'CHANGE_REPORT.md').write_text('\n'.join(lines)+'\n')
    # All fifty run identities and objects remain visible, without held-out event data.
    cfg=json.loads((root/'config.json').read_text());split=json.loads((root/'proposed_split.json').read_text());rows=[]
    for r in n:
        if r['profile']!='base':continue
        for name,a in r['objects'].items():rows.append(dict(run_id=r['run_id'],object=name,partition='development',initial_applicability=a['initial_applicability'],evidence_status='provisional_support_candidate' if a['initial_applicability']=='direct_table_support_candidate' else 'insufficient_information',event_candidates=len(a['events']),requirement_assessment=a['requirement_verdict'],human_label=None,uncertainty='20 Hz endpoints; contact forces and image phase unverified; applicability and detector unvalidated'))
    for run in split['held_out']:
        for name in cfg['objects']:rows.append(dict(run_id=run,object=name,partition='held_out',initial_applicability='not_processed',event_candidates=None,requirement_assessment='not_assessed',human_label=None,uncertainty='Held-out event outcomes untouched'))
    (out/'all_run_object_index.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps({'statistics':stats,'applicability_changes':appchanges,'profile_differences':len(profiledifferences),'upgrades':len(upgrades),'direct_candidates':len(direct)},indent=2))

if __name__=='__main__':report(Path(sys.argv[1]),Path(sys.argv[2]))
