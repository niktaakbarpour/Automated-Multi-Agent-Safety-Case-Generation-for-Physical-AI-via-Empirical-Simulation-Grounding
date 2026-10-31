PRAGMA user_version=1;
CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY, requirement_id TEXT NOT NULL, requirement_version TEXT NOT NULL,
 execution_id TEXT NOT NULL, object_id TEXT NOT NULL, kind TEXT NOT NULL,
 body TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS scope ON evidence(requirement_id,requirement_version,execution_id,object_id,kind);
CREATE TRIGGER IF NOT EXISTS immutable_update BEFORE UPDATE ON evidence BEGIN SELECT RAISE(ABORT,'immutable evidence'); END;
CREATE TRIGGER IF NOT EXISTS immutable_delete BEFORE DELETE ON evidence BEGIN SELECT RAISE(ABORT,'immutable evidence'); END;
