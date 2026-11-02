CREATE TABLE rag_migrations(version TEXT PRIMARY KEY, description TEXT NOT NULL);
INSERT INTO rag_migrations VALUES('1.0.0','Add compatible RAG metadata and FTS5 to evidence schema 1');
CREATE TABLE rag_units(id TEXT PRIMARY KEY REFERENCES evidence(id), task TEXT NOT NULL, type TEXT NOT NULL, lo INTEGER NOT NULL, hi INTEGER NOT NULL, text TEXT NOT NULL, parent TEXT NOT NULL, stratum TEXT NOT NULL);
CREATE INDEX rag_temporal ON rag_units(type,lo,hi);
CREATE INDEX rag_task ON rag_units(task,type);
CREATE VIRTUAL TABLE rag_fts USING fts5(id UNINDEXED,text,tokenize='unicode61');
CREATE TABLE rag_jobs(execution TEXT PRIMARY KEY, input_digest TEXT NOT NULL, status TEXT NOT NULL, records INTEGER NOT NULL);
CREATE TABLE rag_builds(id TEXT PRIMARY KEY, manifest TEXT NOT NULL);
CREATE TABLE rag_failures(id INTEGER PRIMARY KEY, execution TEXT NOT NULL, reason TEXT NOT NULL);
