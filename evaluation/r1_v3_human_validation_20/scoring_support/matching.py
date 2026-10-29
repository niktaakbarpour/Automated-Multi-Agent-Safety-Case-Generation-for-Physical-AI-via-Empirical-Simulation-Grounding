"""Exact deterministic matching of established, normalized event phases.

Candidate and uncertain events must be filtered as unscorable by the caller.
Uses saved-frame bounds only. No physical persistence threshold is introduced.
"""
from fractions import Fraction
from functools import lru_cache

PARTITION = ('run_id','canonical_object_id','requirement_version','phase','scope','compatible_type')

def contained(interval, windows):
    """Every claimed saved frame must be covered; never bridge a reviewed gap."""
    start,end=interval
    if start>end:
        raise ValueError('Reversed event interval')
    cursor=start
    for lo,hi in sorted(windows):
        if lo>hi:
            raise ValueError('Reversed coverage interval')
        if hi<cursor:
            continue
        if lo>cursor:
            return False
        cursor=max(cursor,hi+1)
        if cursor>end:
            return True
    return False

def compatible(pred,ref,tolerance=0):
    if tolerance not in (0,1):
        raise ValueError('Only prespecified 0/1 saved-frame tolerances allowed')
    if any(pred[k]!=ref[k] for k in PARTITION):
        return False
    if pred.get('status')!='established' or ref.get('status')!='established':
        return False
    if ref.get('onset_bracket') is None or pred.get('onset') is None:
        return False
    a,b=pred['interval'];c,d=ref['interval'];lo,hi=ref['onset_bracket']
    return max(a,c-tolerance)<=min(b,d+tolerance) and lo-tolerance<=pred['onset']<=hi+tolerance

def match_events(predictions,references,tolerance=0):
    """Max cardinality, max total IoU, min onset distance, lexicographic IDs.

    Exact dynamic programming within each phase/scope partition. Explicitly
    refuses oversized partitions rather than silently switching to greedy.
    """
    if len({x['event_id'] for x in predictions})!=len(predictions) or len({x['event_id'] for x in references})!=len(references):
        raise ValueError('Duplicate event IDs')
    matches=[]
    keys=sorted({tuple(x[k] for k in PARTITION) for x in predictions+references})
    for key in keys:
        ps=sorted([x for x in predictions if tuple(x[k] for k in PARTITION)==key],key=lambda x:x['event_id'])
        rs=sorted([x for x in references if tuple(x[k] for k in PARTITION)==key],key=lambda x:x['event_id'])
        if len(rs)>20:
            raise ValueError('Exact matcher partition exceeds 20 reference phases')
        edges={}
        for i,p in enumerate(ps):
            for j,r in enumerate(rs):
                if compatible(p,r,tolerance):
                    a,b=p['interval'];c,d=r['interval']
                    intersection=max(0,min(b,d)-max(a,c)+1)
                    union=b-a+1+d-c+1-intersection
                    lo,hi=r['onset_bracket'];on=p['onset']
                    distance=max(lo-on,0,on-hi)
                    edges[i,j]=(Fraction(intersection,union),distance)
        def best(values):
            return min(values,key=lambda x:(-x[0],-x[1],x[2],x[3]))
        @lru_cache(None)
        def solve(i,used):
            if i==len(ps):return (0,Fraction(0),0,())
            choices=[solve(i+1,used)]
            for j,r in enumerate(rs):
                if not (used>>j)&1 and (i,j) in edges:
                    n,iou,dist,pairs=solve(i+1,used|(1<<j))
                    score,error=edges[i,j]
                    choices.append((n+1,iou+score,dist+error,((ps[i]['event_id'],r['event_id']),)+pairs))
            return best(choices)
        for pid,rid in solve(0,0)[3]:
            p=next(x for x in ps if x['event_id']==pid);r=next(x for x in rs if x['event_id']==rid)
            # Endpoint errors only when independently established exact sample bounds.
            matches.append({'prediction_id':pid,'reference_id':rid,
                'onset_error_saved_frames':p['onset']-r['onset_bracket'][0] if r['onset_bracket'][0]==r['onset_bracket'][1] else None,
                'offset_error_saved_frames':p['interval'][1]-r['interval'][1] if r.get('offset_established_exact') else None})
    pids={m['prediction_id'] for m in matches};rids={m['reference_id'] for m in matches}
    return {'matches':matches,'unmatched_predictions':[p['event_id'] for p in predictions if p['event_id'] not in pids],
            'unmatched_references':[r['event_id'] for r in references if r['event_id'] not in rids]}
