# Obligation schema

Machine schema: OBLIGATION.schema.json. query_obligations contains stable IDs, original query spans/text or typed request paths, type/target, required families, temporal obligation references, execution/task/variant/object scope, mandatory flag, resolution status, uncertainty, verification requirements and contract references. IDs anchor identity (type/target/basis/scope); frozen artifact hashes protect the complete serialized object. IDs alone are not content attestations.

Types: measurement, temporal/temporal_uncertainty, scope, entity, component, source_family, assurance, interpretation, comparison, factual_support, availability and unresolved request content. A timestamp is a selector/proof requirement, never a substitute measurement. Conjoined entities/properties create distinct obligations. Duplicate canonical requirements merge, retaining traceable basis. Multiple instants without supported per-clause binding stay ambiguous. Components reference existing native array order; full raw arrays remain unchanged.

Resolution states: RESOLVED, CONDITIONAL, AMBIGUOUS, UNRESOLVED, UNSUPPORTED. Unsupported/unparsed content is retained. Comparisons/factual-support judgments are not computed: operands may be partial evidence while the comparison remains unfulfilled. Unknown clock/window/entity semantics cannot become completeness.

CONTRACT_REGISTRY.json resolves inherited labels to exact files/hashes. Raw IDs, derived interpretation IDs and source hashes retain original lineage. Registry metadata is retrospective release identity, never historical producer attestation. No observations are rewritten, re-normalized or newly indexed.
