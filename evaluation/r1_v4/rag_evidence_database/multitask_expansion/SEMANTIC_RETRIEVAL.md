# Optional local semantic retrieval

Earlier Phase5C probes showed literal FTS5 keyword success but five paraphrase
failures. FTS5 remains useful for exact instructions, object names and source
field terminology. Phase5E adds an optional separately versioned sidecar for
measurement-field paraphrases, retaining SQLite as the evidence source of truth.

The encoder is sentence-transformers/all-MiniLM-L6-v2, immutable revision
1110a243fdf4706b3f48f1d95db1a4f5529b4d41, Apache-2.0. Public model/tokenizer files
were downloaded to Hestia and verified against repository Git blob or LFS hashes.
The weights SHA-256 is
53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db.
The model card is https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2.
Only public file download requests were made; no hosted embedding API was used
and no project evidence or research query was uploaded. Runtime encoding is
local CPU inference with pinned library versions, two threads, deterministic
algorithms, attention-masked mean pooling, L2 normalization and 256-wordpiece
truncation. The sidecar manifest binds source DB hash, code, tokenizer/model
manifest, library versions and vector content.

Descriptors use object identity and source-field descriptions for six raw
measurement types. They exclude execution IDs, numerical values and inferred
physical events. Identical descriptors share one vector, with separate aliases
to every stable evidence ID. Documents and AI interpretations are not silently
embedded as physical observations; unsupported aliases are explicitly reported.

Every semantic query first executes the existing source-hash, dependency,
metadata, temporal and capability checks. Ranking then applies cosine similarity
within at most 100 valid candidates, with stable-ID tie-breaking. There is no
physical confidence threshold. Scores describe encoder similarity only. Core
coverage and uncertainty remain attached. Missing evidence, unsupported physical
checking and unresolved camera alignment remain unchanged. Queries have separate
semantic IDs binding the text, encoder and source-filter query.

The comparison uses prospectively fixed source-field paraphrases over six
measurement candidates at a specified execution/object/frame. Relevant targets
are field identities, not physical-event labels. These are small, hand-written,
descriptor-aware probes; they are not independently human-judged natural-language
relevance data. Recall@20 is weak with six candidates. Report failures and rankings
without tuning descriptions against evaluation outcomes. Exact source-target
retrieval metrics are reported separately from this paraphrase comparison.
