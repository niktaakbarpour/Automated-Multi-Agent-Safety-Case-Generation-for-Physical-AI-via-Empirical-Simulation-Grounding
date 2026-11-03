from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.config import DATABASE,DATABASE_SHA,CHANNELS,FAMILIES,FIELDS,UNITS
HERE=Path(__file__).parent
REPO=HERE.parents[3]
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5k1-working')
CATALOGUE=Path('/disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite')
CATALOGUE_SHA='ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e'
BASE_COMMIT='dda1353dc590613dc5f09682616f8e5e13fef570'
BASE_MANIFEST_SHA='e0006613de605ad14025c91ae23fd16ab373fb5f7acd1bf1449fdf0c626122ee'
VERSION='query-obligation-1.0.0'
SEED='phase5k1-independent-20261103'
