CREATE TABLE IF NOT EXISTS case_files (
    id UUID PRIMARY KEY,
    case_id TEXT NOT NULL,
    case_type TEXT NOT NULL,
    charge_or_claim TEXT NOT NULL,
    plaintiff_or_prosecution TEXT NOT NULL,
    defendant TEXT NOT NULL,
    case_file JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_files_case_id ON case_files (case_id);
CREATE INDEX IF NOT EXISTS idx_case_files_case_type ON case_files (case_type);
CREATE INDEX IF NOT EXISTS idx_case_files_created_at ON case_files (created_at);
