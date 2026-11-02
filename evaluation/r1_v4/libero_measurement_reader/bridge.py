"""Typed V4 observations only; no empirical runtime registration or witnesses."""
from evaluation.r1_v4.contracts import Evidence,Truth,Validity,Interval

def observations(result):
 """Unknown physical truth even for structurally verified stored measurements."""
 if result.status!='verified_measurements':return ()
 records=[]
 for snapshot in result.frames:
  for channel in snapshot.channels:
   records.append(Evidence(
    id=f'{result.execution_id}:frame:{snapshot.index}:{channel.measurement.quantity}',
    kind='direct_measurement',claim='observation',truth=Truth.UNKNOWN,
    validity=Validity.VERIFIED,object_id='*',execution_id=result.execution_id,
    surfaces=(),interval=Interval(snapshot.endpoint_time,snapshot.endpoint_time),
    cells=(),dependencies=(),source_ref='sha256:'+channel.source_sha256,
    producer='libero-measurement-reader:1.0.0',frame=channel.frame,
    uncertainty=channel.uncertainty,payload=channel.measurement))
 return tuple(records)
