CREATE TABLE IF NOT EXISTS simulation_runs (
    id UUID PRIMARY KEY,
    case_file_id UUID NOT NULL REFERENCES case_files (id),
    status TEXT NOT NULL,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CONSTRAINT chk_simulation_runs_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed')
    )
);

CREATE INDEX IF NOT EXISTS idx_simulation_runs_case_file_id
    ON simulation_runs (case_file_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_status
    ON simulation_runs (status);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_created_at
    ON simulation_runs (created_at);
