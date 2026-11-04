from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5j-working')
DATABASE=Path('/disk/1/data/niktakbr/trustworthy-phase5i-working/expanded.sqlite')
DATABASE_SHA='f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8'
BASE_COMMIT='c46d768263b3499e0f89d7c7b3369c17d131cc3d'
SEED='phase5j-independent-readiness-v1'
MODES=('exact','lexical','semantic')
