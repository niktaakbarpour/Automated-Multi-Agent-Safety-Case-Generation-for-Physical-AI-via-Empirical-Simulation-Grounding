# Downstream interface compatibility result

Status: **REJECTED by the existing Drafter-to-Critic handoff contract**. The check used `integration.handoff.build_critic_request` from the merged PR #59 source and made zero model calls. No generated graph, evidence, outcome, or provenance was edited.

The adapter's report schema currently rejects these R1 v3 fields/contracts:

- `argument.argument_bundle.execution_conclusion.outcome_backing` is an additional property rejected by the Critic handoff generation-run schema.
- `trace.prompt_version` is `draft-argument-r1v3-prompt/0.1.0`, while the adapter allows only `draft-argument-prompt/0.2.0`, `.2.1`, or `.2.2`.
- `trace.serializer_version` is `graph-plan-to-gsn-r1v3/0.1.0`, while the adapter requires `graph-plan-to-gsn/0.2.0`.
- The adapter rejects the R1 v3 trace fields `decoder_relaxation` and `validation_schema_sha256` as additional properties.

Action for Alex: update the handoff schema/adapter to explicitly accept this R1 v3 generation report while preserving `outcome_backing`, request/run provenance, graph scope, and the unresolved outcomes. Then rerun the adapter's deterministic validation. Do not strip these fields or create a Critic request manually from prose. No Critic or Revision model stage was run here.
