BEGIN IMMEDIATE;
CREATE TABLE rag_channel_schema(version TEXT PRIMARY KEY, schema_sha256 TEXT NOT NULL, selection_sha256 TEXT NOT NULL);
CREATE TABLE rag_channel_records(id TEXT PRIMARY KEY, execution TEXT NOT NULL REFERENCES rag_execution_env(execution), task TEXT NOT NULL, variant TEXT NOT NULL REFERENCES rag_env_variants(id), channel TEXT NOT NULL, object_id TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(execution,channel));
CREATE INDEX rag_channel_scope ON rag_channel_records(execution,task,variant,channel,object_id);
CREATE TABLE rag_channel_jobs(execution TEXT PRIMARY KEY, input_digest TEXT NOT NULL, record_digest TEXT NOT NULL, status TEXT NOT NULL);
CREATE VIRTUAL TABLE rag_channel_fts USING fts5(id UNINDEXED,text, tokenize='unicode61');
COMMIT;
