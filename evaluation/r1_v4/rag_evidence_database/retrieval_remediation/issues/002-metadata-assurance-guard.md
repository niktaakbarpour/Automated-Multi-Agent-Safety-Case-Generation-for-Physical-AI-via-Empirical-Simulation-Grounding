# Resolved in assurance-guard-1: metadata cannot satisfy typed measurement requests

A post-V1 contract diagnostic found that source-hash-only queries ignored units, required measurement properties and physical-interpretation assurance. V1 is not a release candidate. Its frozen implementation, dataset, criteria and results remain archived under evaluation_v1/ and external work directories.

The correction rejects a typed measurement requirement when the resolved plan contains no measurement family. It does not change vocabulary, rankings, field selection or thresholds. Four focused tests were added. A new implementation/configuration freeze preceded a second assessment on 24 fresh execution scopes, with nine explicit metadata-only typed negative cases. All nine abstained. The template bank overlaps V1; V2 is a fresh-scope assessment, not an untouched linguistic holdout.
