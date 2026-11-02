BEGIN IMMEDIATE;
CREATE TABLE h_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE h_models(variant TEXT PRIMARY KEY REFERENCES rag_env_variants(id),body TEXT NOT NULL);
CREATE TABLE h_execution(execution TEXT PRIMARY KEY REFERENCES rag_execution_env(execution),body TEXT NOT NULL);
CREATE TABLE h_semantics(raw_id TEXT PRIMARY KEY REFERENCES rag_channel_records(id),execution TEXT NOT NULL REFERENCES h_execution(execution),channel TEXT NOT NULL,body TEXT NOT NULL,UNIQUE(execution,channel));
CREATE TABLE h_jobs(execution TEXT PRIMARY KEY,input_digest TEXT NOT NULL,row_digest TEXT NOT NULL,status TEXT NOT NULL);
CREATE INDEX h_scope ON h_semantics(execution,channel);
COMMIT;
