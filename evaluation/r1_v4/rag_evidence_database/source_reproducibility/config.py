from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5i-working')
BASE=Path('/disk/1/data/niktakbr/trustworthy-phase5h-working/expanded.sqlite')
BASE_SHA='af8265755a8f4f1a360c6b39b99bf6ccd45a7313d9e6adf33b89acff7b67fb02'
BASE_COMMIT='82ff490cdf65728a053fe41b825a84408cd6e5dd'
VERSION='release-provenance-1.0.0'
PROVENANCE_SCOPE='release-evidence-graph-v1'
ASSURANCES=('verified_source_values','verified_physical_interpretation','provenance_complete','historical_producer_attestation')
CATEGORIES=('HISTORICAL_RECORD','RETROSPECTIVE_ARTIFACT','RECONSTRUCTED_ASSOCIATION','CONDITIONAL_INTERPRETATION','UNATTESTED')
