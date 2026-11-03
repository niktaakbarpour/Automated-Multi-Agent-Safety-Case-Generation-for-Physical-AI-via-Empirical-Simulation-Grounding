# Per-category retrieval metrics

Family-level relevance; N excludes predefined critical cases. Baseline exact/lexical/semantic here use the existing primary six-channel endpoint. Geometry/metadata families are outside that endpoint; compare the common-channel subset in ABLATION_RESULTS.md. Full historical interfaces are replayed separately.

## bundle

| Category | N | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| C1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 |
| C2 | 24 | 1.000 | 0.938 | 0.938 | 1.000 |
| C3 | 22 | 1.000 | 1.000 | 1.000 | 1.000 |
| C4 | 24 | 1.000 | 0.979 | 1.000 | 1.000 |
| C5 | 0 | N/A | N/A | N/A | N/A |
| C6 | 6 | 1.000 | 1.000 | 1.000 | 1.000 |
| C7 | 12 | 1.000 | 1.000 | 1.000 | 1.000 |
| C8 | 0 | N/A | N/A | N/A | N/A |
| C9 | 24 | 1.000 | 1.000 | 1.000 | 1.000 |

P@1 descriptive Wilson 95%: [0.9725299002664176, 1.0]; suite-stratified execution bootstrap 95%: [1.0, 1.0].
Latency median/p95 seconds: {'max': 0.5185651825740933, 'median': 0.10261156363412738, 'p95': 0.2237644570413977}; mixed query/fault conditions, warmed shared process, not an isolated ranking benchmark.

## exact

| Category | N | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| C1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 |
| C2 | 24 | 0.625 | 0.729 | 0.750 | 0.701 |
| C3 | 22 | 0.000 | 0.000 | 0.000 | 0.000 |
| C4 | 24 | 0.292 | 0.382 | 0.521 | 0.468 |
| C5 | 0 | N/A | N/A | N/A | N/A |
| C6 | 6 | 1.000 | 1.000 | 1.000 | 1.000 |
| C7 | 12 | 0.000 | 0.000 | 0.000 | 0.000 |
| C8 | 0 | N/A | N/A | N/A | N/A |
| C9 | 24 | 0.917 | 0.938 | 0.938 | 0.951 |

P@1 descriptive Wilson 95%: [0.4603495271019867, 0.6254619346862266]; suite-stratified execution bootstrap 95%: [0.4927509590792839, 0.5895616342746698].
Latency median/p95 seconds: {'max': 0.4836875330656767, 'median': 0.052153574768453836, 'p95': 0.1354914589319378}; mixed query/fault conditions, warmed shared process, not an isolated ranking benchmark.

## field_single

| Category | N | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| C1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 |
| C2 | 24 | 1.000 | 0.875 | 0.875 | 1.000 |
| C3 | 22 | 1.000 | 1.000 | 1.000 | 1.000 |
| C4 | 24 | 1.000 | 0.312 | 0.312 | 1.000 |
| C5 | 0 | N/A | N/A | N/A | N/A |
| C6 | 6 | 1.000 | 1.000 | 1.000 | 1.000 |
| C7 | 12 | 1.000 | 0.875 | 0.875 | 1.000 |
| C8 | 0 | N/A | N/A | N/A | N/A |
| C9 | 24 | 1.000 | 0.938 | 0.938 | 1.000 |

P@1 descriptive Wilson 95%: [0.9725299002664176, 1.0]; suite-stratified execution bootstrap 95%: [1.0, 1.0].
Latency median/p95 seconds: {'max': 0.5186513205990195, 'median': 0.09993101703003049, 'p95': 0.18787903687916696}; mixed query/fault conditions, warmed shared process, not an isolated ranking benchmark.

## hybrid_single

| Category | N | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| C1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 |
| C2 | 24 | 1.000 | 0.875 | 0.875 | 1.000 |
| C3 | 22 | 1.000 | 1.000 | 1.000 | 1.000 |
| C4 | 24 | 1.000 | 0.312 | 0.312 | 1.000 |
| C5 | 0 | N/A | N/A | N/A | N/A |
| C6 | 6 | 1.000 | 1.000 | 1.000 | 1.000 |
| C7 | 12 | 1.000 | 0.875 | 0.875 | 1.000 |
| C8 | 0 | N/A | N/A | N/A | N/A |
| C9 | 24 | 1.000 | 0.938 | 0.938 | 1.000 |

P@1 descriptive Wilson 95%: [0.9725299002664176, 1.0]; suite-stratified execution bootstrap 95%: [1.0, 1.0].
Latency median/p95 seconds: {'max': 0.7558256331831217, 'median': 0.10532531095668674, 'p95': 0.21577743371017277}; mixed query/fault conditions, warmed shared process, not an isolated ranking benchmark.

## lexical

| Category | N | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| C1 | 24 | 0.500 | 0.750 | 0.750 | 0.625 |
| C2 | 24 | 0.125 | 0.438 | 0.438 | 0.277 |
| C3 | 22 | 0.000 | 0.000 | 0.000 | 0.000 |
| C4 | 24 | 0.458 | 0.486 | 0.521 | 0.624 |
| C5 | 0 | N/A | N/A | N/A | N/A |
| C6 | 6 | 0.833 | 1.000 | 1.000 | 0.917 |
| C7 | 12 | 0.000 | 0.000 | 0.000 | 0.000 |
| C8 | 0 | N/A | N/A | N/A | N/A |
| C9 | 24 | 0.500 | 0.562 | 0.562 | 0.562 |

P@1 descriptive Wilson 95%: [0.24399413765382028, 0.39845810489529077]; suite-stratified execution bootstrap 95%: [0.23703703703703705, 0.39571503102861216].
Latency median/p95 seconds: {'max': 0.6539264507591724, 'median': 0.041062230709940195, 'p95': 0.1219978763256222}; mixed query/fault conditions, warmed shared process, not an isolated ranking benchmark.

## semantic

| Category | N | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| C1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 |
| C2 | 24 | 0.417 | 0.750 | 0.750 | 0.625 |
| C3 | 22 | 0.000 | 0.000 | 0.000 | 0.000 |
| C4 | 24 | 0.750 | 0.500 | 0.521 | 0.795 |
| C5 | 0 | N/A | N/A | N/A | N/A |
| C6 | 6 | 0.667 | 1.000 | 1.000 | 0.833 |
| C7 | 12 | 0.000 | 0.000 | 0.000 | 0.000 |
| C8 | 0 | N/A | N/A | N/A | N/A |
| C9 | 24 | 0.750 | 0.938 | 0.938 | 0.875 |

P@1 descriptive Wilson 95%: [0.4603495271019867, 0.6254619346862266]; suite-stratified execution bootstrap 95%: [0.46041721367431604, 0.6212818181818182].
Latency median/p95 seconds: {'max': 0.4967042859643698, 'median': 0.06014947919175029, 'p95': 0.1652318404521793}; mixed query/fault conditions, warmed shared process, not an isolated ranking benchmark.

Intervals describe these authored clustered data. The execution bootstrap does not capture unseen-template uncertainty. Repeating templates across scopes is not independent linguistic sampling; all-P@1-success bootstrap intervals may degenerate at 1.0. No physical-safety accuracy is measured.
