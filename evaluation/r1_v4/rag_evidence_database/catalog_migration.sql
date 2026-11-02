CREATE TABLE rag_catalog(execution TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE VIRTUAL TABLE rag_catalog_fts USING fts5(execution UNINDEXED,text,tokenize='unicode61');
INSERT INTO rag_migrations VALUES('1.1.0','Add explicitly historical project source catalog; no measurement substitution');
