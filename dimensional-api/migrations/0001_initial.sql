PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS dimensions(id TEXT PRIMARY KEY,label TEXT NOT NULL,dimensionality INTEGER NOT NULL CHECK(dimensionality BETWEEN 1 AND 11),coordinate_system TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1),created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dimension_edges(from_id TEXT NOT NULL REFERENCES dimensions(id),to_id TEXT NOT NULL REFERENCES dimensions(id),relation TEXT NOT NULL DEFAULT 'transform',PRIMARY KEY(from_id,to_id,relation));
CREATE TABLE IF NOT EXISTS traversal_records(id TEXT PRIMARY KEY,source_id TEXT NOT NULL,target_id TEXT NOT NULL,max_hops INTEGER NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dimension_mutations(dimension_id TEXT NOT NULL REFERENCES dimensions(id),version INTEGER NOT NULL,patch_json TEXT NOT NULL,actor TEXT NOT NULL,previous_hash TEXT,event_hash TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,PRIMARY KEY(dimension_id,version));
CREATE TRIGGER IF NOT EXISTS mutation_ledger_no_update BEFORE UPDATE ON dimension_mutations BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;
CREATE TRIGGER IF NOT EXISTS mutation_ledger_no_delete BEFORE DELETE ON dimension_mutations BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;
INSERT OR IGNORE INTO dimensions(id,label,dimensionality,coordinate_system,version,created_at) VALUES('d1','One-dimensional model',1,'scalar-axis',1,'2026-01-01T00:00:00.000Z'),('d2','Two-dimensional model',2,'cartesian-2d',1,'2026-01-01T00:00:00.000Z'),('d3','Three-dimensional model',3,'cartesian-3d',1,'2026-01-01T00:00:00.000Z');
INSERT OR IGNORE INTO dimension_edges(from_id,to_id,relation) VALUES('d1','d2','embed'),('d2','d3','embed'),('d3','d2','project');
