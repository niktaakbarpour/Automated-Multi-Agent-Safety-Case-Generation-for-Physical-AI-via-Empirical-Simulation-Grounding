# Bounded API usage

Run on Hestia with the recorded environment and read the trusted manifest from the local Git release. The catalogue hash is ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e.

```python
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import Retriever, BundleRequest
r = Retriever('/disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite',
              'ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e')
try:
    result = r.retrieve(BundleRequest(
        query='Finger positions and arm speeds at frame 20.',
        execution_id='<eligible indexed execution>',
        task_id='<exact task ID>', variant_id='<exact variant ID>'))
finally:
    r.close()
```

A consumer must inspect each group, source/measurement contract, missing evidence and uncertainty. Do not convert COMPLETE into safety-claim sufficiency. Unreviewed natural-language decomposition remains experimental because issue 001 can omit an obligation. For a reviewed caller plan, `plan=(...)` names exact supported families and `frame_interval=(20,20)` supplies typed temporal scope; all source/variant/assurance constraints still apply. An explicit plan is a caller obligation specification, never source evidence.

Strict is default; verified_session is an explicit performance mode with hashed-identity invalidation. Metadata-only requests cannot satisfy units, measurement properties or physical interpretation assurance. Do not use the old legacy geometry route as a substitute for descriptor-bound verification. `compat.retrieve` documents the narrower strict legacy reference route.
